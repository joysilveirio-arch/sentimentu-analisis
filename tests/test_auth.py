def test_login_success(client):
    r = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert r.status_code == 200
    assert r.get_json()["success"] is True

def test_login_fail(client):
    r = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert r.status_code == 401
    assert r.get_json()["success"] is False

def test_me_unauthenticated(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401

def test_me_authenticated(admin_client):
    r = admin_client.get("/api/auth/me")
    assert r.status_code == 200
    assert r.get_json()["data"]["role"] == "ADMIN"

def test_logout(client):
    client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    r = client.post("/api/auth/logout")
    assert r.status_code == 200
    r2 = client.get("/api/auth/me")
    assert r2.status_code == 401