import httpx

from app.core.config import get_settings
from app.main import app


async def test_backend_home_guides_to_frontend_and_favicon_is_not_missing():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://localhost"
    ) as client:
        response = await client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert get_settings().frontend_origin in response.text
        assert "Open application" in response.text
        assert (await client.get("/favicon.ico")).status_code == 204
