import asyncio
import httpx
from httpx import RemoteProtocolError
import time
import uuid

async def get_auth_token():
    base_url = "http://localhost:8001"
    run_id = uuid.uuid4().hex[:8]
    TEST_EMAIL = f"eval_{run_id}@example.com"
    TEST_PASSWORD = "evalpassword123"
    TEST_ORG = f"Evidra Eval Organization {run_id}"

    async with httpx.AsyncClient() as client:
        login_response = await client.post(
            f"{base_url}/api/v1/auth/login",
            data={"username": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        if login_response.status_code == 200:
            return login_response.json()["access_token"]

        register_response = await client.post(
            f"{base_url}/api/v1/auth/register",
            json={
                "organization_name": TEST_ORG,
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
        )
        if register_response.status_code != 200:
            print("Registration failed:", register_response.json())
        return register_response.json()["access_token"]

async def run_tests():
    print("--- Backend API Evaluation ---")
    base_url = "http://localhost:8001/api/v1"
    
    token = await get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient(timeout=300.0, headers=headers) as client:
        try:
            # 1. Health check
            print("\nTest: Health check")
            res = await client.get(f"{base_url}/health")
            print(f"Status: {res.status_code}")
            print(f"Response: {res.json()}")
            if res.status_code == 200:
                print("=> PASS")
            else:
                print("=> FAIL")

            # 2. Seed database
            print("\nTest: Seed database")
            res = await client.post(f"{base_url}/demo/seed")
            print(f"Status: {res.status_code}")
            print(f"Response: {res.json()}")
            if res.status_code == 200:
                print("=> PASS")
            else:
                print("=> FAIL")

            # 3. List candidates
            print("\nTest: List candidates")
            res = await client.get(f"{base_url}/candidates")
            data = res.json().get("data", [])
            print(f"Candidates returned: {len(data)}")
            arjun = next((c for c in data if "Arjun" in str(c.get("name", ""))), None)
            if len(data) >= 10 and arjun:
                print("=> PASS (Arjun present)")
            else:
                print("=> FAIL")

            # 4. Rerank startup persona
            print("\nTest: Rerank startup persona")
            start = time.time()
            res = await client.post(f"{base_url}/candidates/jobs/00000000-0000-0000-0000-000000000001/rerank?persona=startup_generalist")
            dur = (time.time() - start) * 1000
            data1 = res.json().get("data", [])
            if data1 and "Arjun" in str(data1[0]['profile'].get('name', '')):
                print(f"=> PASS (Arjun is #1, time: {dur:.1f}ms)")
            else:
                print(f"=> FAIL (Arjun is NOT #1, Top is {data1[0]['profile'].get('name') if data1 else 'None'})")

            # 5. Rerank enterprise persona
            print("\nTest: Rerank enterprise persona")
            res = await client.post(f"{base_url}/candidates/jobs/00000000-0000-0000-0000-000000000001/rerank?persona=enterprise_specialist")
            data2 = res.json().get("data", [])
            if data2 and data1 and data1[0]['profile']['id'] != data2[0]['profile']['id']:
                print(f"=> PASS (Different #1: {data2[0]['profile'].get('name', '')})")
            else:
                print(f"=> FAIL (Still {data2[0]['profile'].get('name') if data2 else 'None'})")

            # 6. Rerank research persona
            print("\nTest: Rerank research persona")
            res = await client.post(f"{base_url}/candidates/jobs/00000000-0000-0000-0000-000000000001/rerank?persona=research_engineer")
            data3 = res.json().get("data", [])
            if data3 and data1 and data2 and data3[0]['profile']['id'] not in [data1[0]['profile']['id'], data2[0]['profile']['id']]:
                print(f"=> PASS (Different #1: {data3[0]['profile'].get('name', '')})")
            else:
                print(f"=> FAIL (Found {data3[0]['profile'].get('name') if data3 else 'None'})")

            # 7. Fetch Arjun specifically
            print("\nTest: Fetch Arjun specifically")
            if arjun:
                res = await client.get(f"{base_url}/candidates/{arjun['id']}")
                p = res.json()
                hs = p.get("hidden_strengths", [])
                if len(hs) > 0 and hs[0].get("domain") == "Backend Systems" and hs[0].get("confidence") == "high":
                    print("=> PASS (Arjun full profile correct)")
                else:
                    print(f"=> FAIL (Hidden strengths: {hs})")
            else:
                print("=> FAIL (Arjun not found in DB to fetch)")

            # 8. Fetch null GitHub candidate
            print("\nTest: Fetch null GitHub candidate")
            null_github = next((c for c in data if c.get("github_signals") is None), None)
            if null_github:
                res = await client.get(f"{base_url}/candidates/{null_github['id']}")
                p = res.json()
                ai = p.get("authenticity_index", {})
                if "analysis pending" in ai.get("signal_note", ""):
                    print("=> PASS (Null Github candidate fetched correctly without 500)")
                else:
                    print(f"=> FAIL (Signal note: {ai.get('signal_note')})")
            else:
                print("=> FAIL (No null github candidate found)")

            # 9. PDF upload valid
            print("\nTest: PDF upload valid")
            try:
                with open("valid_resume.pdf", "wb") as f:
                    f.write(b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Resources <<\n  /Font <<\n    /F1 4 0 R\n  >>\n>>\n/Contents 5 0 R\n>>\nendobj\n4 0 obj\n<<\n/Type /Font\n/Subtype /Type1\n/BaseFont /Helvetica\n>>\nendobj\n5 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 24 Tf\n100 700 Td\n(This is a valid resume with enough text to bypass the length check. It must be more than 100 characters. We are adding enough text here to make sure it passes the check easily.) Tj\nET\nendstream\nendobj\nxref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000289 00000 n \n0000000377 00000 n \ntrailer\n<<\n/Size 6\n/Root 1 0 R\n>>\nstartxref\n472\n%%EOF\n")
                with open("valid_resume.pdf", "rb") as f:
                    res = await client.post(f"{base_url}/candidates/upload", files={"file": ("valid_resume.pdf", f, "application/pdf")})
                print(f"Status: {res.status_code}")
                if res.status_code == 200:
                    print("=> PASS")
                else:
                    print("=> FAIL")
            except RemoteProtocolError:
                print("=> FAIL (RemoteProtocolError, likely LLM failure)")

            # 10. PDF upload invalid
            print("\nTest: PDF upload invalid")
            with open("invalid_resume.pdf", "wb") as f:
                f.write(b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Resources <<\n  /Font <<\n    /F1 4 0 R\n  >>\n>>\n/Contents 5 0 R\n>>\nendobj\n4 0 obj\n<<\n/Type /Font\n/Subtype /Type1\n/BaseFont /Helvetica\n>>\nendobj\n5 0 obj\n<<\n/Length 20\n>>\nstream\nBT\n/F1 24 Tf\n100 700 Td\n(Short) Tj\nET\nendstream\nendobj\n")
            with open("invalid_resume.pdf", "rb") as f:
                res = await client.post(f"{base_url}/candidates/upload", files={"file": ("invalid_resume.pdf", f, "application/pdf")})
            print(f"Status: {res.status_code}")
            if res.status_code == 422:
                print("=> PASS")
            else:
                print("=> FAIL")

            # 11. Chat query
            print("\nTest: Chat query")
            res = await client.post(f"{base_url}/chat", json={"messages": [{"role": "user", "content": "Who is the strongest backend candidate?"}], "job_id": "00000000-0000-0000-0000-000000000001"})
            print(f"Status: {res.status_code}")
            if res.status_code == 200:
                print("=> PASS")
            else:
                print("=> FAIL")

            # 12. Rerank response time
            print("\nTest: Rerank response time")
            start = time.time()
            res = await client.post(f"{base_url}/candidates/jobs/00000000-0000-0000-0000-000000000001/rerank?persona=startup_generalist")
            dur = (time.time() - start) * 1000
            print(f"Time: {dur:.1f}ms")
            if dur < 200:
                print("=> PASS")
            else:
                print("=> FAIL")
            
            # 13. DOCX upload valid
            print("\nTest: DOCX upload valid")
            try:
                with open("valid_resume.docx", "rb") as f:
                    res = await client.post(f"{base_url}/candidates/upload", files={"file": ("valid_resume.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")})
                print(f"Status: {res.status_code}")
                if res.status_code == 200:
                    print("=> PASS")
                else:
                    print("=> FAIL")
            except RemoteProtocolError:
                print("=> FAIL (RemoteProtocolError)")

            # 14. DOCX upload invalid
            print("\nTest: DOCX upload invalid")
            try:
                with open("invalid_resume.docx", "rb") as f:
                    res = await client.post(f"{base_url}/candidates/upload", files={"file": ("invalid_resume.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")})
                print(f"Status: {res.status_code}")
                if res.status_code == 422:
                    print("=> PASS")
                else:
                    print("=> FAIL")
            except RemoteProtocolError:
                print("=> FAIL (RemoteProtocolError)")

            # 15. Verify embedding generation
            print("\nTest: Verify embedding generation")
            if arjun:
                arjun_id = arjun['id']
                from db.database import AsyncSessionLocal
                from sqlalchemy import select
                from models.db import CandidateRecord
                async with AsyncSessionLocal() as session:
                    import uuid
                    result = await session.execute(select(CandidateRecord).where(CandidateRecord.id == uuid.UUID(arjun_id)))
                    arjun_db = result.scalar_one_or_none()
                    if arjun_db and arjun_db.embedding is not None and len(arjun_db.embedding) == 384:
                        print("=> PASS (Embedding generated with 384 dimensions)")
                    else:
                        print("=> FAIL (Embedding missing or wrong dimension)")
            else:
                print("=> FAIL (Arjun not found to verify embedding)")
            
            # 16. Semantic Chat
            print("\nTest: Semantic Chat")
            res = await client.post(f"{base_url}/chat", json={
                "messages": [{"role": "user", "content": "Who has hidden backend engineering capability?"}],
                "job_id": "00000000-0000-0000-0000-000000000001"
            })
            if res.status_code == 200:
                print("=> PASS (Semantic search returned response)")
            else:
                print(f"=> FAIL (Semantic search failed: {res.status_code})")
                
            # 17. Explainability Endpoint
            print("\nTest: Explainability Endpoint")
            if arjun:
                res = await client.get(f"{base_url}/candidates/{arjun['id']}/explain?persona=startup_generalist")
                if res.status_code == 200:
                    data = res.json()
                    if "factors" in data and len(data["factors"]) > 0:
                        print("=> PASS (Explainability returned factors)")
                    else:
                        print(f"=> FAIL (Missing factors: {data})")
                else:
                    print(f"=> FAIL (Endpoint failed: {res.status_code})")
            else:
                print("=> FAIL (Arjun not found to test explainability)")

            # 18. Semantic Search API
            print("\nTest: Semantic Search API")
            res = await client.post(f"{base_url}/candidates/search", json={
                "query": "backend engineer with fast learning ability"
            })
            if res.status_code == 200:
                data = res.json().get("data", [])
                if len(data) > 0:
                    print(f"=> PASS (Semantic search returned {len(data)} candidates)")
                else:
                    print("=> FAIL (No candidates returned)")
            else:
                print(f"=> FAIL (Search failed: {res.status_code})")

        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_tests())
