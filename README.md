# TinyURLish (Flask)

A tiny, **original** URL shortener microservice using Flask + SQLite. Includes tests and optional Dockerfile.

## Features
- Create short codes for URLs (POST /shorten)
- Redirect from short code (GET /<code>)
- List recent entries (GET /admin/recent) — simple JSON
- SQLite persistence

## Local Dev
```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=app.py
flask run
```

## API
- `POST /shorten` JSON: `{ "url": "https://example.com" }` -> `{ "code": "abc123" }`
- `GET /<code>` -> 302 redirect to the original URL
- `GET /admin/recent` -> last 20 mappings

## Tests
```bash
pytest -q
```

## Docker (optional)
```bash
docker build -t tinyurlish .
docker run -p 5000:5000 tinyurlish
```

## License
MIT
