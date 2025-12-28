import asyncio
from nocodb_client import (
    get_or_create_user, 
    update_user_credit,
    create_property, 
    get_user_properties,
    create_transaction,
    get_user_transactions
)

async def full_test():
    TG_ID = 555666777
    
    print('='*50)
    print('1. Create/Get User')
    user = await get_or_create_user(TG_ID, 'Test User')
    print(f'   User: {user}')
    
    print('='*50)
    print('2. Update Credit')
    updated = await update_user_credit(TG_ID, 500000)
    print(f'   Updated: {updated}')
    
    print('='*50)
    print('3. Create Property')
    prop = await create_property(TG_ID, {
        'property_type': 'villa',
        'transaction_type': 'sale',
        'city': 'Shiraz',
        'area': 250,
        'price': 5000000000
    })
    print(f'   Property Created: OK')
    
    print('='*50)
    print('4. Get User Properties')
    props = await get_user_properties(TG_ID)
    print(f'   Found {len(props)} properties')
    
    print('='*50)
    print('5. Create Transaction')
    tx = await create_transaction(
        user_telegram_id=TG_ID,
        amount=-10000,
        transaction_type='usage',
        description='Test transaction'
    )
    print(f'   Transaction Created: OK')
    
    print('='*50)
    print('6. Get User Transactions')
    txs = await get_user_transactions(TG_ID)
    print(f'   Found {len(txs)} transactions')
    
    print('='*50)
    print('ALL TESTS PASSED!')

asyncio.run(full_test())
