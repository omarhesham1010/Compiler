# Compiler Studio — Spring 2026

A 3-phase mini compiler with a modern web UI.

- **Phase 1 — Scanner** (`compiler/lexer.py`): classifies tokens into Identifiers, Reserved Words, Variables, Numbers, Strings, Symbols.
- **Phase 2 — Semantic Analyzer** (`compiler/parser_semantic.py`): validates `if (...) { ... }` grammar, undeclared variables, redeclarations, type mismatches.
- **Phase 3 — Memory** (`compiler/memory.py`): executes declarations + assignments, computes expressions with full operator precedence, returns a step-by-step trace.

## Run

```bash
pip install -r requirements.txt
python manage.py runserver
```

Open http://127.0.0.1:8000/

## Demo

- Press `Ctrl+Enter` to run, or just type — analysis is live (debounced 400 ms).
- Pick a sample from the **Load sample…** dropdown.
- Switch tabs: **Tokens** / **Errors** / **Memory**.
- In the Memory tab, drag the slider to scrub through execution and watch variables update.
- Export the token table as JSON or CSV for the documentation screenshots.

## Project Structure

```
compiler/                 ← pure-Python core (no Django imports)
  tokens.py               ← Token + TokenType
  lexer.py                ← Phase 1
  parser_semantic.py      ← Phase 2
  memory.py               ← Phase 3
  pipeline.py             ← run_all(source)
analyzer/                 ← Django app (thin wrapper)
compiler_project/         ← Django settings
static/                   ← CSS + JS
```
