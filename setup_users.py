import requests

NOCODB_URL = 'http://localhost:8080'
NOCODB_TOKEN = 'bS9qY4oNiZq3qxeMIKqBNGbekF74CFwcCKG--ZIV'
headers = {'xc-token': NOCODB_TOKEN, 'Content-Type': 'application/json'}

table_id = 'mckjx30dsuf2nrf'

fields = [
    {'title': 'telegram_id', 'uidt': 'Number'},
    {'title': 'username', 'uidt': 'SingleLineText'},
    {'title': 'first_name', 'uidt': 'SingleLineText'},
    {'title': 'last_name', 'uidt': 'SingleLineText'},
    {'title': 'phone', 'uidt': 'SingleLineText'},
    {'title': 'credit', 'uidt': 'Number'},
    {'title': 'total_charged', 'uidt': 'Number'},
    {'title': 'is_admin', 'uidt': 'Checkbox'},
    {'title': 'is_active', 'uidt': 'Checkbox'},
]

for f in fields:
    url = f'{NOCODB_URL}/api/v2/meta/tables/{table_id}/columns'
    r = requests.post(url, headers=headers, json=f)
    title = f['title']
    if r.status_code in [200, 201]:
        print(f'OK {title}')
    else:
        print(f'ERROR {title}: {r.status_code} - {r.text[:80]}')
