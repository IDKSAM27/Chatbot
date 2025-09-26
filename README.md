## Language Agnostic Chatbot

A multilingual chatbot for colleges that answers FAQ's in multiple languages.

## .env format:

```bash
SECRET_KEY=
HOST=0.0.0.0
PORT=8000
DEVELOPMENT=True

# Db fallback
DATABASE_URL=sqlite:///site.db

GEMINI_KEY=

# Optional logging database (sqlite_logger.py uses db.sqlite3 by default)
SQLITE_LOG_DB=db.sqlite3
```


## How to create python secret key for .env?:

```bash
python -c "import secrets; print(secrets.token_hex(16))"
```

## How to Run?:

```bash
pip install -r requirements.txt
```
```bash
python main.py
```

`Then Visit 'localhost:8000`
