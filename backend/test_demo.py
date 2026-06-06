from fastapi.testclient import TestClient
from main import app
import time

client = TestClient(app)

def run_tests():
    print("Testing /health")
    resp = client.get("/api/v1/health")
    print(resp.json())

    print("Testing /demo/seed")
    resp = client.post("/api/v1/demo/seed")
    print(resp.json())

    print("Testing /jobs/demo-job-01/rerank")
    start = time.time()
    resp = client.post("/api/v1/candidates/jobs/demo-job-01/rerank?persona=startup_generalist")
    end = time.time()
    print(f"Rerank response time: {(end-start)*1000:.2f} ms")
    if resp.status_code == 200:
        data = resp.json().get("data", [])
        print(f"Reranked {len(data)} candidates.")
        if data:
            print(f"Top candidate: {data[0]['profile']['name']} with score {data[0]['score']}")
    else:
        print(resp.json())

if __name__ == "__main__":
    run_tests()
