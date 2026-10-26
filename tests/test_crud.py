def test_admin_can_create_record(admin_client):
    r = admin_client.post("/api/data", json={
        "text": "test record", "author_name": "Test", "sentiment": "Neutral"
    })
    assert r.status_code == 200
    assert r.get_json()["success"] is True

def test_user_cannot_create_record(user_client):
    r = user_client.post("/api/data", json={"text": "x", "author_name": "y"})
    assert r.status_code == 403

def test_list_records(admin_client):
    admin_client.post("/api/data", json={"text": "hello", "author_name": "A"})
    r = admin_client.get("/api/data")
    assert r.status_code == 200
    assert len(r.get_json()["data"]) >= 1

def test_update_record(admin_client):
    r1 = admin_client.post("/api/data", json={"text": "old", "author_name": "X"})
    rid = r1.get_json()["data"]["id"]
    r2 = admin_client.put(f"/api/data/{rid}", json={"text": "new"})
    assert r2.get_json()["data"]["text"] == "new"

def test_delete_record(admin_client):
    r1 = admin_client.post("/api/data", json={"text": "del", "author_name": "Y"})
    rid = r1.get_json()["data"]["id"]
    r2 = admin_client.delete(f"/api/data/{rid}")
    assert r2.status_code == 200
    assert admin_client.get(f"/api/data/{rid}").status_code == 404

def test_admin_can_create_user(admin_client):
    r = admin_client.post("/api/admin/users", json={
        "username": "newuser", "password": "pass123", "role": "USER"
    })
    assert r.status_code == 200

def test_user_cannot_manage_users(user_client):
    r = user_client.get("/api/admin/users")
    assert r.status_code == 403