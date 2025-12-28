# show_client.py
with open("nocodb_client.py", "r", encoding="utf-8") as f:
    content = f.read()
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        print(f"{i:3}: {line}")
