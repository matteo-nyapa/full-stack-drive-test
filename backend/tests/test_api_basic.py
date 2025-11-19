import pytest
from httpx import AsyncClient

from app.main import app
from app.config import files_collection


@pytest.mark.asyncio
async def test_health_check():
  async with AsyncClient(app=app, base_url="http://test") as ac:
    resp = await ac.get("/health")
  assert resp.status_code == 200
  assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_list_files_empty(monkeypatch):
  # Nos aseguramos de que la colección esté vacía antes del test
  await files_collection.delete_many({})

  async with AsyncClient(app=app, base_url="http://test") as ac:
    resp = await ac.get("/files")
  assert resp.status_code == 200
  data = resp.json()
  assert isinstance(data, list)
  assert data == []
