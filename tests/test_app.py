import os, tempfile, uuid
import app as tiny

def setup_function(_):
    # use a unique temp DB per test session to avoid Windows file locks
    tiny.DB_PATH = os.path.join(tempfile.gettempdir(), f"tiny_test_{uuid.uuid4().hex}.db")
    tiny.init_db()
    tiny.app.config.update(TESTING=True)

def teardown_function(_):
    try:
        os.remove(tiny.DB_PATH)
    except Exception:
        pass

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
