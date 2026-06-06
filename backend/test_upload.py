import httpx
import asyncio

async def t():
    with open('valid_resume.pdf', 'wb') as f:
        f.write(b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Resources <<\n  /Font <<\n    /F1 4 0 R\n  >>\n>>\n/Contents 5 0 R\n>>\nendobj\n4 0 obj\n<<\n/Type /Font\n/Subtype /Type1\n/BaseFont /Helvetica\n>>\nendobj\n5 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 24 Tf\n100 700 Td\n(This is a valid resume with enough text to bypass the length check. It must be more than 100 characters. We are adding enough text here to make sure it passes the check easily.) Tj\nET\nendstream\nendobj\nxref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000289 00000 n \n0000000377 00000 n \ntrailer\n<<\n/Size 6\n/Root 1 0 R\n>>\nstartxref\n472\n%%EOF\n')
    async with httpx.AsyncClient(timeout=120) as client:
        with open('valid_resume.pdf', 'rb') as f:
            res = await client.post('http://127.0.0.1:8000/api/v1/candidates/upload', files={'file': ('valid_resume.pdf', f, 'application/pdf')})
            print("HTTP", res.status_code)
            print(res.text)

asyncio.run(t())
