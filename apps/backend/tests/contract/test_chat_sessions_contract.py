import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_session_lifecycle(client: AsyncClient, mock_headers: dict[str, str]) -> None:
    create = await client.post("/api/chat/sessions", headers=mock_headers)
    assert create.status_code == 201
    session = create.json()
    session_id = session["id"]

    listed = await client.get("/api/chat/sessions", headers=mock_headers)
    assert listed.status_code == 200
    assert any(s["id"] == session_id for s in listed.json()["sessions"])

    detail = await client.get(f"/api/chat/sessions/{session_id}", headers=mock_headers)
    assert detail.status_code == 200
    assert detail.json()["id"] == session_id

    deleted = await client.delete(f"/api/chat/sessions/{session_id}", headers=mock_headers)
    assert deleted.status_code == 204
