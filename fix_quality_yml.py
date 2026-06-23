with open(".github/workflows/quality.yml", "r") as f:
    text = f.read()

# Replace setup-python@v4 with setup-python@v5 to address node20 warning
text = text.replace('uses: actions/setup-python@v4', 'uses: actions/setup-python@v5')

# The `git.exe failed with exit code 128` happens because git doesn't trust the workspace.
# We can fix this by adding a step to mark the workspace as safe before checkout or inside the runner,
# or simply updating actions/checkout to a version that handles it better.
# Actually, actions/checkout@v4 is already being used. The error happens because the repo contains submodules that might have issues or something similar.
# In the log: fatal: No url found for submodule path 'Archon' in .gitmodules
# Let's just fix the submodule issue by removing Archon from .gitmodules if it's dead, or setting submodules: false in checkout (it is already false though...)

with open(".github/workflows/quality.yml", "w") as f:
    f.write(text)
