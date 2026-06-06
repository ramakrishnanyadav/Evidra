import asyncio
import httpx
import uuid

async def verify():
    print("=== Verification Sequence ===")
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000", timeout=10.0) as client:
        # Step 1: Startup Tab
        r1 = await client.post("/api/v1/candidates/jobs/demo-job-01/rerank?persona=startup_generalist")
        d1 = r1.json().get("data", [])
        if d1:
            print(f"1. Startup Top: {d1[0]['profile'].get('name')} (Score: {d1[0]['score']})")

        # Step 2: Enterprise Tab
        r2 = await client.post("/api/v1/candidates/jobs/demo-job-01/rerank?persona=enterprise_specialist")
        d2 = r2.json().get("data", [])
        if d2:
            print(f"2. Enterprise Top: {d2[0]['profile'].get('name')} (Score: {d2[0]['score']})")
            if d1 and d2 and d1[0]['profile']['id'] != d2[0]['profile']['id']:
                print("   [OK] Rankings reordered visibly")
            
        # Step 3: Research Tab
        r3 = await client.post("/api/v1/candidates/jobs/demo-job-01/rerank?persona=research_engineer")
        d3 = r3.json().get("data", [])
        if d3:
            print(f"3. Research Top: {d3[0]['profile'].get('name')} (Score: {d3[0]['score']})")
            
        # Step 5: Large PDF (Threadpool fix check)
        print("5. Generating large PDF for concurrency test...")
        with open("large_test.pdf", "wb") as f:
            f.write(b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Resources <<\n  /Font <<\n    /F1 4 0 R\n  >>\n>>\n/Contents 5 0 R\n>>\nendobj\n4 0 obj\n<<\n/Type /Font\n/Subtype /Type1\n/BaseFont /Helvetica\n>>\nendobj\n5 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 24 Tf\n100 700 Td\n(Hello World) Tj\nET\nendstream\nendobj\nxref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000289 00000 n \n0000000377 00000 n \ntrailer\n<<\n/Size 6\n/Root 1 0 R\n>>\nstartxref\n472\n%%EOF\n")
            # padding to make it larger
            f.write(b"0" * (1024 * 1024 * 2))
            
        print("   Uploading large PDF asynchronously while fetching candidates...")
        async def upload_large():
            with open("large_test.pdf", "rb") as f:
                try:
                    res = await client.post("/api/v1/candidates/upload", files={"file": ("large_test.pdf", f, "application/pdf")})
                    return res.status_code
                except Exception as e:
                    return str(e)
                    
        async def fetch_list():
            await asyncio.sleep(0.5) # ensure upload started
            try:
                res = await client.get("/api/v1/candidates", timeout=2.0)
                return res.status_code
            except Exception as e:
                return str(e)
            
        upload_task = asyncio.create_task(upload_large())
        fetch_task = asyncio.create_task(fetch_list())
        
        up_res, fetch_res = await asyncio.gather(upload_task, fetch_task)
        print(f"   Upload result: {up_res}")
        print(f"   Fetch during upload result: {fetch_res}")
        if fetch_res == 200:
            print("   [OK] Server accepted requests during processing (Threadpool working)")
            
        # Step 6: Null-GitHub candidate (Incomplete LLM output)
        print("6. Fetching candidate list to check if Pydantic parsing avoids 500 errors...")
        res = await client.get("/api/v1/candidates")
        if res.status_code == 200:
            print("   [OK] Candidate list loaded without 500 errors.")
            # check the default narrative
            data = res.json().get("data", [])
            for c in data:
                if c.get("reasoning", {}).get("narrative") == "Insufficient data for complete analysis.":
                    print("   [OK] Found incomplete LLM output correctly padded by default factory")
                    break
        else:
            print(f"   [FAIL] Candidate list failed with {res.status_code}: {res.text}")

if __name__ == "__main__":
    asyncio.run(verify())
