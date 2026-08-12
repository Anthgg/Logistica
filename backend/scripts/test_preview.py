import urllib.request
import urllib.parse
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
with opener.open(req) as resp:
    print('Login status:', resp.status)

# 3. Test Preview with doc_type_code = 'PED' or 'AREC' or others
for doc in ['PED', 'AREC', 'ODS', 'CIT', 'DIF', 'GUIA', 'GRT', 'OC', 'APC', 'CEP', 'NC']:
    payload = json.dumps({'doc_type_code': doc}).encode()
    req = urllib.request.Request(
        f'{base_url}/api/logistics/company-profile/document-preview',
        data=payload,
        headers={'X-CSRF-Token': csrf, 'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        with opener.open(req) as resp:
            data = resp.read()
            print(f'Doc {doc}: Status {resp.status}, bytes: {len(data)}')
    except urllib.error.HTTPError as e:
        print(f'Doc {doc}: Error {e.code} -> {e.read().decode()}')
