import httpx
from app.config import settings

class InsForgeClient:
    def __init__(self):
        self.base_url = settings.insforge_url
        self.headers = {
            "apikey": settings.insforge_service_key,
            "Authorization": f"Bearer {settings.insforge_service_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        
    async def insert(self, table: str, data: list[dict] | dict):
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/rest/v1/{table}", 
                headers=self.headers, 
                json=data
            )
            resp.raise_for_status()
            return resp.json()

    async def update(self, table: str, query_params: dict, data: dict):
        async with httpx.AsyncClient() as client:
            resp = await client.patch(
                f"{self.base_url}/rest/v1/{table}",
                headers=self.headers,
                params=query_params,
                json=data
            )
            resp.raise_for_status()
            return resp.json()

    async def delete(self, table: str, query_params: dict):
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{self.base_url}/rest/v1/{table}",
                headers=self.headers,
                params=query_params
            )
            resp.raise_for_status()
            # Delete response can be empty or list
            return resp.json() if resp.content else None

    async def select(self, table: str, query_params: dict):
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/rest/v1/{table}",
                headers=self.headers,
                params=query_params
            )
            resp.raise_for_status()
            return resp.json()

    async def download_file(self, bucket: str, path: str) -> bytes:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/storage/v1/object/authenticated/{bucket}/{path}",
                headers=self.headers
            )
            resp.raise_for_status()
            return resp.content

db_client = InsForgeClient()
