import asyncio
import json
from fastapi.testclient import TestClient
from main import app, lifespan

def test_endpoints():
    with TestClient(app) as client:
        # 1. Test Health (before seed)
        print("Testing /api/v1/health...")
        response = client.get("/api/v1/health")
        print(f"Health Response: {response.status_code} {response.json()}")
        
        # 2. Test Seed
        print("\nTesting /api/v1/demo/seed...")
        response = client.post("/api/v1/demo/seed")
        print(f"Seed Response: {response.status_code} {response.json()}")
        
        # 3. Test Health (after seed)
        print("\nTesting /api/v1/health (after seed)...")
        response = client.get("/api/v1/health")
        print(f"Health Response: {response.status_code} {response.json()}")
        
        # 4. Test List Candidates
        print("\nTesting /api/v1/candidates...")
        response = client.get("/api/v1/candidates")
        print(f"List Response: {response.status_code}")
        data = response.json()
        print(f"Found {len(data['data'])} candidates")
        
        # 5. Test Get Candidate
        if data['data']:
            first_id = data['data'][0]['id']
            print(f"\nTesting /api/v1/candidates/{first_id}...")
            response = client.get(f"/api/v1/candidates/{first_id}")
            print(f"Get Response: {response.status_code}")
            print(f"Name: {response.json()['name']}")

if __name__ == "__main__":
    # In FastApi TestClient with lifespan, we just use the context manager
    test_endpoints()
