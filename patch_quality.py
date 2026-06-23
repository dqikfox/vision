with open('.github/workflows/quality.yml', 'r') as f:
    content = f.read()

content = content.replace('uses: actions/checkout@v4', 'uses: actions/checkout@v4')
content = content.replace('uses: actions/setup-python@v4', 'uses: actions/setup-python@v5')
content = content.replace('uses: actions/upload-artifact@v4', 'uses: actions/upload-artifact@v4')

with open('.github/workflows/quality.yml', 'w') as f:
    f.write(content)
