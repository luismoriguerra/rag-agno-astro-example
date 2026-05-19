import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_deleted_session_not_listed(client: AsyncClient, mock_headers: dict[str, str]) -> None:
    created = await client.post("/api/chat/sessions", headers=mock_headers)
    session_id = created.json()["id"]
    await client.delete(f"/api/chat/sessions/{session_id}", headers=mock_headers)

    listed = await client.get("/api/chat/sessions", headers=mock_headers)
    assert all(s["id"] != session_id for s in listed.json()["sessions"])
