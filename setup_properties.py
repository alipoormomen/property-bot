import requests

NOCODB_URL = 'http://localhost:8080'
NOCODB_TOKEN = 'bS9qY4oNiZq3qxeMIKqBNGbekF74CFwcCKG--ZIV'
headers = {'xc-token': NOCODB_TOKEN, 'Content-Type': 'application/json'}

table_id = 'm99miticq7yjzjs'

fields = [
    {'title': 'user_id', 'uidt': 'Number'},
    {'title': 'transaction_type', 'uidt': 'SingleLineText'},
    {'title': 'property_type', 'uidt': 'SingleLineText'},
    {'title': 'usage_type', 'uidt': 'SingleLineText'},
    {'title': 'city', 'uidt': 'SingleLineText'},
    {'title': 'neighborhood', 'uidt': 'SingleLineText'},
    {'title': 'area', 'uidt': 'Number'},
    {'title': 'bedroom_count', 'uidt': 'Number'},
    {'title': 'floor', 'uidt': 'Number'},
    {'title': 'total_floors', 'uidt': 'Number'},
    {'title': 'unit_count', 'uidt': 'Number'},
    {'title': 'build_year', 'uidt': 'Number'},
    {'title': 'has_elevator', 'uidt': 'Checkbox'},
    {'title': 'has_parking', 'uidt': 'Checkbox'},
    {'title': 'has_storage', 'uidt': 'Checkbox'},
    {'title': 'price_total', 'uidt': 'Number'},
    {'title': 'deposit', 'uidt': 'Number'},
    {'title': 'rent', 'uidt': 'Number'},
    {'title': 'owner_name', 'uidt': 'SingleLineText'},
    {'title': 'owner_phone', 'uidt': 'SingleLineText'},
    {'title': 'additional_features', 'uidt': 'LongText'},
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
