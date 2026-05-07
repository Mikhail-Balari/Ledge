# Ledge — GitHub Deployment Guide

**Estado actual:** instalable con `pip install -e .`
El paquete no está en PyPI público todavía.

---

## Step 1 — Create the GitHub repository

1. Go to **https://github.com/new**
2. Fill in:
   - Repository name: `ledge`
   - Description: `The first programming language designed for AI-first software`
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
   - Description: `The first programming language designed for AI-first software`
   - Topics: `programming-language`, `interpreter`, `ai`, `python`, `language-design`, `ledge`

---

## Step 5 — Create a Release

1. On your repo, click **Releases** → **Create a new release**
2. Click **Choose a tag** → type `v1.1.0` → **Create new tag**
3. Release title: `Ledge v1.1.0`
4. Description:

```markdown
## Ledge v1.1.0

AI-first programming language with mandatory uncertainty types, automatic audit trail, and contracts.

### What's included
- Complete interpreter: lexer, parser, tree-walking evaluator
- 284/284 conformance tests, 324/326 unit tests passing
- AI-native types: Uncertain[T], audit trail, confidence enforcement
- Contracts (requires/ensures), streams, parallel execution
- Python FFI: full ecosystem in one line
- CLI: ledge run / ledge check / ledge version

### Install
pip install -e .  (PyPI release coming)

### Try it
ledge run examples/showcase/triage_medico.ledge
```

5. Click **Publish release**

---

## Step 6 — Share it

### Posts to write

**Hacker News** — title suggestion:
> Ledge: A programming language where AI uncertainty is a first-class type

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
