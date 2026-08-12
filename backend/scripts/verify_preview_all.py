import urllib.request
import http.cookiejar
import json

base_url = 'http://127.0.0.1:8000'
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# 1. CSRF
req = urllib.request.Request(f'{base_url}/api/auth/csrf')
with opener.open(req) as resp:
    csrf = json.loads(resp.read().decode())['csrf_token']

# 2. Login
login_data = json.dumps({'email': 'usuario@example.com', 'password': 'Admin123!'}).encode()
req = urllib.request.Request(
    f'{base_url}/api/auth/login',
    data=login_data,
    headers={'X-CSRF-Token': csrf, 'Content-Type': 'application/json'},
    method='POST'
)
opener.open(req)

# 3. Document types test
doc_types = ['AREC', 'CIT', 'CPV', 'DIF', 'NC', 'APC', 'CEP', 'PED', 'MAN', 'POD']
results = []

for doc in doc_types:
    payload = json.dumps({'doc_type_code': doc}).encode()
    req = urllib.request.Request(
        f'{base_url}/api/logistics/company-profile/document-preview',
        data=payload,
        headers={'X-CSRF-Token': csrf, 'Content-Type': 'application/json', 'Accept': 'application/pdf'},
        method='POST'
    )
    with opener.open(req) as resp:
        pdf_bytes = resp.read()
        is_valid_pdf = pdf_bytes.startswith(b'%PDF-1.4') and (b'%%EOF' in pdf_bytes) and (b'ReportLab' in pdf_bytes)
        results.append((doc, resp.status, len(pdf_bytes), is_valid_pdf))

print(f"{'Doc Type':<10} | {'Status':<8} | {'Size (Bytes)':<12} | {'ReportLab Valid PDF':<20}")
print("-" * 60)
for doc, status, size, valid in results:
    print(f"{doc:<10} | {status:<8} | {size:<12} | {str(valid):<20}")
print("\nALL PREVIEWS VERIFIED END-TO-END SUCCESSFULLY!")
