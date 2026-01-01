import requests

NOCODB_URL = 'http://localhost:8080'
NOCODB_TOKEN = 'bS9qY4oNiZq3qxeMIKqBNGbekF74CFwcCKG--ZIV'
headers = {'xc-token': NOCODB_TOKEN, 'Content-Type': 'application/json'}

table_id = 'msqpjqrfa9oriyt'

fields = [
    {'title': 'user_id', 'uidt': 'Number'},
    {'title': 'amount', 'uidt': 'Number'},
    {'title': 'type', 'uidt': 'SingleLineText'},
    {'title': 'description', 'uidt': 'SingleLineText'},
    {'title': 'reference_id', 'uidt': 'SingleLineText'},
    {'title': 'status', 'uidt': 'SingleLineText'},
]

for f in fields:
    url = f'{NOCODB_URL}/api/v2/meta/tables/{table_id}/columns'
    r = requests.post(url, headers=headers, json=f)
    title = f['title']
    if r.status_code in [200, 201]:
        print(f'OK {title}')
    else:
        print(f'ERROR {title}: {r.status_code} - {r.text[:80]}')
