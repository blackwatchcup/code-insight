import httpx
import json

async def test_auth_endpoints():
    async with httpx.AsyncClient(timeout=10) as client:
        # Test health check
        print("Testing health check...")
        resp = await client.get('http://localhost:8000/health')
        print(f"Health check: {resp.status_code} - {resp.text}")
        
        # Test projects endpoint
        print("\nTesting projects endpoint...")
        resp = await client.get('http://localhost:8000/api/v1/projects/')
        print(f"Projects: {resp.status_code} - {resp.text[:200]}")
        
        # Test auth register
        print("\nTesting auth register...")
        try:
            resp = await client.post(
                'http://localhost:8000/api/v1/auth/register',
                json={
                    "username": "testuser2",
                    "email": "testuser2@example.com",
                    "password": "test123"
                }
            )
            print(f"Register: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"Register error: {e}")
        
        # Test auth login
        print("\nTesting auth login...")
        try:
            resp = await client.post(
                'http://localhost:8000/api/v1/auth/login',
                data={
                    "username": "testuser",
                    "password": "test123"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            print(f"Login: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"Login error: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_auth_endpoints())
