# Ledge — Deployment Guide

**Current status:** published on PyPI as `ledge-lang`. Also installable
from source with `pip install -e .` for development work.

---

## Step 1 — Create the GitHub repository

1. Go to **https://github.com/new**
2. Fill in:
   - Repository name: `ledge`
   - Description: `A small experimental DSL for making AI uncertainty explicit in program flow`
   - Visibility: **Public**
   - Do NOT check "Add a README file" (we have our own)
3. Click **Create repository**

---

## Step 2 — Push the code

Open a terminal in the `ledge/` folder and run:

```bash
# Initialize git
git init
git add .
git commit -m "feat: Ledge v1.1.0 — initial public release"

# Point to your GitHub repo (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/ledge.git
git branch -M main
git push -u origin main
```

---

## Step 3 — Publish to PyPI (optional)

This lets people do `pip install ledge-lang`.

**One-time setup:**

```bash
pip install build twine

# Create a PyPI account at https://pypi.org/account/register/
# Create an API token at https://pypi.org/manage/account/token/
```

**Build and publish:**

```bash
python -m build
python -m twine upload dist/*
```

After this, anyone can install Ledge with:
```bash
pip install ledge-lang
```

---

## Step 4 — Add a GitHub topic and description

1. Go to your repo's main page
2. Click the gear icon next to "About" (top right of the code section)
3. Add:
   - Description: `A small experimental DSL for making AI uncertainty explicit in program flow`
   - Topics: `programming-language`, `interpreter`, `ai`, `python`, `language-design`, `ledge`

---

## Step 5 — Create a Release

1. On your repo, click **Releases** → **Create a new release**
2. Click **Choose a tag** → type `v1.1.0` → **Create new tag**
3. Release title: `Ledge v1.1.0`
4. Description:

```markdown
## Ledge v1.1.0

A small DSL for making AI uncertainty explicit in program flow.
The static analyzer rejects direct use of an Uncertain[T] value unless it
passes through a recognized confidence guard, `when(...)`, or the explicit
`unsafe_value_of(...)` escape hatch. See README.md for the precise contract.

### What's included
- Tree-walker interpreter and bytecode VM (1500-program differential)
- 284 conformance tests, 343 unit tests passing
- Runtime: Uncertain[T], AIDerived, UncertainChain, SHA-256 chained audit log
- Contracts (requires/ensures), streams, parallel execution
- Python FFI with safe-mode allowlist
- CLI: ledge run / check / demo / debug / fmt / audit / studio

### Install
```
pip install ledge-lang
ledge demo medical_triage    # runs without an API key
```

### Try a showcase example (requires clone)
```
git clone https://github.com/Mikhail-Balari/Ledge
cd Ledge
ledge run examples/showcase/medical_triage.ledge
```
```

5. Click **Publish release**

---

## Step 6 — Share it

### Posts to write

**Hacker News** — title suggestion:
> Ledge: a small DSL that turns "I forgot to check confidence" into a static error

**Reddit communities:**
- r/ProgrammingLanguages
- r/MachineLearning
- r/Python
- r/programming

---

## Maintenance commands

```bash
# Run tests
python tests/conformance.py
python -m pytest tests/unit/ -q

# Run the REPL locally
python -m ledge_lang

# Run a file
ledge run examples/showcase/triage_medico.ledge

# Check syntax
ledge check program.ledge

# Rebuild PyPI package after changes
python -m build
python -m twine upload dist/* --skip-existing
```
