def test_assign_label(admin_client):
    r1 = admin_client.post("/api/data", json={
        "text": "sample text", "author_name": "AuthorX"
    })
    rid = r1.get_json()["data"]["id"]
    r2 = admin_client.post("/api/admin/labeling/assign", json={
        "record_id": rid, "label": "Positive"
    })
    assert r2.status_code == 200
    assert r2.get_json()["data"]["label"] == "Positive"

def test_label_nonexistent_record(admin_client):
    r = admin_client.post("/api/admin/labeling/assign", json={
        "record_id": 999999, "label": "Positive"
    })
    assert r.status_code == 404