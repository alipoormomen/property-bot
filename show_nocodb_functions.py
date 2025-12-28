# show_nocodb_functions.py
import re

with open("nocodb_client.py", "r", encoding="utf-8") as f:
    content = f.read()

# نمایش تابع create_property
match = re.search(r'(async def create_property.*?)(?=\nasync def |\nclass |\Z)', content, re.DOTALL)
if match:
    print("="*60)
    print("🏠 تابع create_property:")
    print("="*60)
    lines = match.group(1).split('\n')
    for i, line in enumerate(lines[:40], 1):
        print(f"{i:3}: {line}")

print("\n")

# نمایش تابع create_transaction
match = re.search(r'(async def create_transaction.*?)(?=\nasync def |\nclass |\Z)', content, re.DOTALL)
if match:
    print("="*60)
    print("💳 تابع create_transaction:")
    print("="*60)
    lines = match.group(1).split('\n')
    for i, line in enumerate(lines[:30], 1):
        print(f"{i:3}: {line}")
