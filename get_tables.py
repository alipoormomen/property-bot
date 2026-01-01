import requests

NOCODB_URL = 'http://localhost:8080'
NOCODB_TOKEN = 'bS9qY4oNiZq3qxeMIKqBNGbekF74CFwcCKG--ZIV'
headers = {'xc-token': NOCODB_TOKEN}

base_id = 'pc46egoicxp880q'
r = requests.get(f'{NOCODB_URL}/api/v2/meta/bases/{base_id}/tables', headers=headers)
for t in r.json().get('list', []):
    print(f"{t['title']}: {t['id']}")
