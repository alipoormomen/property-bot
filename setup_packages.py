import requests

NOCODB_URL = 'http://localhost:8080'
NOCODB_TOKEN = 'bS9qY4oNiZq3qxeMIKqBNGbekF74CFwcCKG--ZIV'
headers = {'xc-token': NOCODB_TOKEN, 'Content-Type': 'application/json'}

table_id = 'mh9bjt95kgyqgij'

fields = [
    {'title': 'name', 'uidt': 'SingleLineText'},
    {'title': 'credit_amount', 'uidt': 'Number'},
    {'title': 'price', 'uidt': 'Number'},
    {'title': 'description', 'uidt': 'SingleLineText'},
    {'title': 'is_active', 'uidt': 'Checkbox'},
    {'title': 'sort_order', 'uidt': 'Number'},
]

for f in fields:
    url = f'{NOCODB_URL}/api/v2/meta/tables/{table_id}/columns'
    r = requests.post(url, headers=headers, json=f)
    title = f['title']
    if r.status_code in [200, 201]:
        print(f'OK {title}')
    else:
        print(f'ERROR {title}: {r.status_code} - {r.text[:80]}')
