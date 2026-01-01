# ابتدا این کد را در فایل test_nocodb.py ذخیره کنید
# مسیر: C:\Users\DELL\project\project\test_nocodb.py

import requests

# تنظیمات از .env شما
NOCODB_URL = "http://localhost:8080"
NOCODB_TOKEN = "bS9qY4oNiZq3qxeMIKqBNGbekF74CFwcCKG--ZIV"

headers = {
    "xc-token": NOCODB_TOKEN,
    "Content-Type": "application/json"
}

def test_connection():
    """تست اتصال به NocoDB"""
    print("=" * 50)
    print("Testing NocoDB Connection...")
    print("=" * 50)
    
    # 1. لیست Bases (پایگاه‌های داده)
    try:
        response = requests.get(f"{NOCODB_URL}/api/v2/meta/bases", headers=headers)
        print(f"\nStatus: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Connection successful!")
            print(f"\nBases found:")
            
            bases = data.get("list", [])
            for base in bases:
                base_id = base.get("id")
                base_title = base.get("title")
                print(f"   - {base_title} (ID: {base_id})")
                
                # گرفتن جداول هر Base
                get_tables(base_id)
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Connection Error: {e}")

def get_tables(base_id):
    """گرفتن لیست جداول یک Base"""
    response = requests.get(f"{NOCODB_URL}/api/v2/meta/bases/{base_id}/tables", headers=headers)
    
    if response.status_code == 200:
        tables = response.json().get("list", [])
        print(f"\n   Tables:")
        
        for table in tables:
            table_id = table.get("id")
            table_title = table.get("title")
            print(f"\n      Table: {table_title} (ID: {table_id})")
            
            # گرفتن فیلدهای هر جدول
            get_columns(table_id)

def get_columns(table_id):
    """گرفتن فیلدهای یک جدول"""
    response = requests.get(f"{NOCODB_URL}/api/v2/meta/tables/{table_id}", headers=headers)
    
    if response.status_code == 200:
        table_info = response.json()
        columns = table_info.get("columns", [])
        
        print(f"         Columns ({len(columns)}):")
        for col in columns:
            col_title = col.get("title")
            col_type = col.get("uidt")  # UI Data Type
            col_pk = col.get("pk", False)  # Primary Key
            col_id = col.get("id")
            
            pk_badge = " [PRIMARY KEY]" if col_pk else ""
            print(f"            - {col_title} ({col_type}){pk_badge} | ID: {col_id}")

if __name__ == "__main__":
    test_connection()
