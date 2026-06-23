with open(".github/workflows/quality.yml", "r") as f:
    text = f.read()

# Let's fix the git error by adding submodules: false to checkout explicitly, even if it's default
text = text.replace('uses: actions/checkout@v4', 'uses: actions/checkout@v4\n        with:\n          submodules: false')

# Fix artifacts warning (if-no-files-found: ignore)
text = text.replace('name: test-results-py${{ matrix.python-version }}\n          path: junit.xml', 'name: test-results-py${{ matrix.python-version }}\n          path: junit.xml\n          if-no-files-found: ignore')
text = text.replace('name: pip-audit-results-py${{ matrix.python-version }}\n          path: pip-audit.json', 'name: pip-audit-results-py${{ matrix.python-version }}\n          path: pip-audit.json\n          if-no-files-found: ignore')
text = text.replace('name: bandit-results-py${{ matrix.python-version }}\n          path: bandit.json', 'name: bandit-results-py${{ matrix.python-version }}\n          path: bandit.json\n          if-no-files-found: ignore')

with open(".github/workflows/quality.yml", "w") as f:
    f.write(text)
