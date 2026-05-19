import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_stop_unknown_run_returns_404(
    client: AsyncClient, mock_headers: dict[str, str]
) -> None:
    response = await client.post(
        "/api/chat/runs/00000000-0000-0000-0000-000000000099/stop",
        headers=mock_headers,
    )
    assert response.status_code == 404
