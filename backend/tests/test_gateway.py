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
