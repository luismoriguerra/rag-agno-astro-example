import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_message_submission_returns_run(client: AsyncClient, mock_headers: dict[str, str]) -> None:
    session = await client.post("/api/chat/sessions", headers=mock_headers)
    session_id = session.json()["id"]

    response = await client.post(
        f"/api/chat/sessions/{session_id}/messages",
        headers=mock_headers,
        json={"content": "What is DuckDuckGo?"},
    )
    assert response.status_code == 202
    body = response.json()
    assert body["run"]["id"]
    assert body["message"]["role"] == "user"
