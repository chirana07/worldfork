"""Measured local inference through Bifrost, never direct Ollama in a scored run."""

import asyncio
import os
import time
import uuid

import httpx


def unwrap_json_reply(raw: str) -> str:
    lines = raw.strip().splitlines()
    if len(lines) >= 3 and lines[0] in {"```json", "```"} and lines[-1] == "```":
        return "\n".join(lines[1:-1])
    return raw


class BudgetExhausted(RuntimeError):
    pass


class Gateway:
    def __init__(self, model=None, temperature=0.2, seed=1):
        self.base_url = os.getenv(
            "WORLDFORK_GATEWAY", "http://127.0.0.1:8080/v1"
        ).rstrip("/")
        self.model = model or os.getenv("WORLDFORK_MODEL", "ollama/qwen3.5:4b")
        self.temperature, self.seed = temperature, seed
        self.attempts = []
        self.max_attempts = 64
        self.token_limit = 120000
        self.client = httpx.AsyncClient(timeout=180)

    async def describe_model(self):
        try:
            response = await self.client.get(
                "http://127.0.0.1:11434/api/tags", timeout=3
            )
            response.raise_for_status()
            name = self.model.removeprefix("ollama/")
            item = next(
                (m for m in response.json().get("models", []) if m["name"] == name),
                None,
            )
            return {
                "name": name,
                "digest": item.get("digest") if item else None,
                "details": item.get("details") if item else None,
                "source": "local_ollama_tags",
            }
        except (httpx.HTTPError, ValueError, KeyError):
            return {"name": self.model, "digest": None, "source": "unavailable"}

    async def generate(
        self,
        messages,
        *,
        run_id="smoke",
        role="support",
        injected_failure=False,
        schema=None,
    ):
        observed_tokens = sum(
            (a.get("input_tokens") or 0) + (a.get("output_tokens") or 0)
            for a in self.attempts
        )
        if (
            len(self.attempts) >= self.max_attempts
            or observed_tokens >= self.token_limit
        ):
            raise BudgetExhausted(
                "Model-attempt or observed-token limit reached before request"
            )
        attempt = {
            "id": str(uuid.uuid4()),
            "role": role,
            "configured_model": self.model,
            "status": "started",
            "input_tokens": None,
            "output_tokens": None,
            "usage_source": None,
            "injected": injected_failure,
            "temperature": self.temperature,
            "seed": self.seed,
            "max_output_tokens": 192,
            "reasoning_effort": "none" if "qwen3.5" in self.model else None,
        }
        started = time.monotonic()
        self.attempts.append(attempt)
        try:
            if injected_failure:
                attempt.update(
                    input_tokens=0,
                    output_tokens=0,
                    usage_source="injected_no_provider_request",
                )
                raise httpx.ConnectError(
                    "Injected model-unavailable fault; no provider request sent"
                )
            response = await self.client.post(
                self.base_url + "/chat/completions",
                json={
                    **({"reasoning_effort": "none"} if "qwen3.5" in self.model else {}),
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "temperature": self.temperature,
                    "max_tokens": 192,
                    "seed": self.seed,
                    "response_format": (
                        {
                            "type": "json_schema",
                            "json_schema": {
                                "name": "worldfork_action",
                                "strict": True,
                                "schema": schema,
                            },
                        }
                        if schema
                        else {"type": "json_object"}
                    ),
                },
                headers={"x-wf-run-id": run_id, "x-wf-attempt-id": attempt["id"]},
            )
            response.raise_for_status()
            data = response.json()
            usage = data.get("usage", {})
            attempt.update(
                status="ok",
                actual_model=data.get("model"),
                input_tokens=usage.get("prompt_tokens"),
                output_tokens=usage.get("completion_tokens"),
                usage_source="bifrost_response" if usage else None,
                response_id=data.get("id"),
                raw_response=data["choices"][0]["message"].get("content"),
            )
            return unwrap_json_reply(data["choices"][0]["message"]["content"])
        except asyncio.CancelledError:
            attempt.update(
                status="cancelled", error="Request cancelled; provider usage unknown"
            )
            raise
        except Exception as exc:
            attempt.update(status="error", error=str(exc)[:500])
            raise
        finally:
            attempt["elapsed_ms"] = round((time.monotonic() - started) * 1000, 2)

    async def close(self):
        await self.client.aclose()
