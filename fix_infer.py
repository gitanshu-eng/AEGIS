import re

with open('D:/AEGIS-local/api.py', encoding='utf-8') as f:
    content = f.read()

# Extract the two infer route blocks
infer_block = re.search(
    r'(@app\.post\("/api/infer"\).*?@app\.get\("/api/infer/status"\).*?\n\n)',
    content, re.DOTALL
)

if not infer_block:
    print('ERROR: could not find infer blocks - check manually')
else:
    # Remove from current location
    content_clean = content.replace(infer_block.group(0), '')
    # Insert before the catch-all
    content_new = content_clean.replace(
        '@app.get("/{full_path:path}")',
        infer_block.group(0) + '@app.get("/{full_path:path}")'
    )
    with open('D:/AEGIS-local/api.py', 'w', encoding='utf-8') as f:
        f.write(content_new)
    print('Done - infer routes moved above catch-all')
