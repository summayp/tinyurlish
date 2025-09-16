import json, os, tempfile, shutil
import app as tiny

def setup_function(_):
    # swap DB for a temporary file
    tiny.DB_PATH = os.path.join(tempfile.gettempdir(), "tiny_test.db")
    if os.path.exists(tiny.DB_PATH):
        os.remove(tiny.DB_PATH)
    tiny.init_db()
    tiny.app.config.update(TESTING=True)

def test_shorten_and_follow():
    client = tiny.app.test_client()
    r = client.post("/shorten", json={"url":"example.com"})
    assert r.status_code == 200
    code = r.get_json()["code"]

    r2 = client.get(f"/{code}", follow_redirects=False)
    assert r2.status_code == 302
    assert r2.headers["Location"].startswith("https://example.com")

def test_recent():
    client = tiny.app.test_client()
    for i in range(3):
        client.post("/shorten", json={"url": f"example{i}.com"})
    r = client.get("/admin/recent")
    data = r.get_json()
    assert len(data) == 3
