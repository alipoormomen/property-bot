import asyncio
from nocodb_client import create_property, get_user_properties

async def test():
    print('Creating property...')
    prop = await create_property(123456789, {
        'property_type': 'apartment',
        'transaction_type': 'sale',
        'city': 'Tehran',
        'area': 100
    })
    print('Result:', prop)
    
    print('Getting properties...')
    props = await get_user_properties(123456789)
    print('Found:', len(props))
    for p in props[:2]:
        print('  user_telegram_id:', p.get('user_telegram_id'))

asyncio.run(test())
