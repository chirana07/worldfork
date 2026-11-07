import httpx
import pytest
from worldfork.gateway import BudgetExhausted, Gateway


async def test_fenced_json_is_unwrapped_but_raw_reply_is_preserved():
    raw = '```json\n{"action_id": 0}\n```'
    g = Gateway()
    await g.client.aclose()
    g.client = httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                200, json={"choices": [{"message": {"content": raw}}]}
            )
        )
    )
    try:
        assert await g.generate([]) == '{"action_id": 0}'
        assert g.attempts[0]["raw_response"] == raw
    finally:
        await g.close()


async def test_injected_unavailable_attempt_never_sends_and_is_counted():
    g = Gateway()
    try:
        with pytest.raises(httpx.ConnectError):
            await g.generate([], injected_failure=True)
        assert len(g.attempts) == 1
        assert g.attempts[0]["input_tokens"] == 0
        assert g.attempts[0]["status"] == "error"
    finally:
        await g.close()


async def test_attempt_cap_checked_before_http():
    g = Gateway()
    g.max_attempts = 0
    try:
        with pytest.raises(BudgetExhausted):
            await g.generate([])
        assert g.attempts == []
    finally:
        await g.close()


async def test_missing_usage_not_fabricated_as_zero():
    g = Gateway()

    async def handler(request):
        return httpx.Response(
            200, json={"model": "local", "choices": [{"message": {"content": "{}"}}]}
        )

    await g.client.aclose()
    g.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        assert await g.generate([]) == "{}"
        assert g.attempts[0]["input_tokens"] is None
        assert g.attempts[0]["usage_source"] is None
    finally:
        await g.close()


async def test_malformed_usage_is_unknown_and_following_call_still_works():
    g = Gateway()
    await g.client.aclose()
    g.client = httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": "{}"}}],
                    "usage": {"prompt_tokens": "42", "completion_tokens": 5},
                },
            )
        )
    )
    try:
        for _ in range(2):
            assert await g.generate([]) == "{}"
        assert all(a["input_tokens"] is None for a in g.attempts)
        assert all(a["output_tokens"] == 5 for a in g.attempts)
    finally:
        await g.close()


async def test_http_error_does_not_persist_configured_gateway_url():
    g = Gateway()
    g.base_url = "http://user:test-password@localhost/v1"
    await g.client.aclose()
    g.client = httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(503))
    )
    try:
        with pytest.raises(RuntimeError, match="^Gateway returned HTTP 503$"):
            await g.generate([])
        assert g.attempts[0]["error"] == "Gateway returned HTTP 503"
    finally:
        await g.close()
