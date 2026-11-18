import json
import math

from fastapi.testclient import TestClient


def payload(**overrides):
    data = {
        "name": "Cube",
        "model_url": "https://example.com/models/cube.glb",
        "position": {"x": 0.0, "y": 1.5, "z": -2.0},
        "rotation": {"x": 0.0, "y": 1.57, "z": 0.0},
        "scale": {"x": 1.0, "y": 1.0, "z": 1.0},
    }
    data.update(overrides)
    return data


def create(client: TestClient, **overrides):
    return client.post("/objects", json=payload(**overrides))


# 1. 健康檢查
def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# 2. 空列表
def test_list_empty(client):
    response = client.get("/objects")
    assert response.status_code == 200
    assert response.json() == []


# 3. 建立成功並回傳欄位
def test_create_object(client):
    response = create(client, name="Chair")
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Chair"
    assert data["model_url"] == "https://example.com/models/cube.glb"
    assert data["position"] == {"x": 0.0, "y": 1.5, "z": -2.0}
    assert data["scale"] == {"x": 1.0, "y": 1.0, "z": 1.0}
    assert "created_at" in data and "updated_at" in data


# 4. 空名稱 → 422
def test_create_empty_name_rejected(client):
    response = create(client, name="")
    assert response.status_code == 422


# 5. 非法 URL → 422
def test_create_invalid_url_rejected(client):
    response = create(client, model_url="not-a-url")
    assert response.status_code == 422


# 6. scale <= 0 → 422
def test_create_nonpositive_scale_rejected(client):
    response = create(client, scale={"x": 1.0, "y": 0.0, "z": 1.0})
    assert response.status_code == 422


# 7. 依 id 取得
def test_get_object(client):
    created = create(client).json()
    response = client.get(f"/objects/{created['id']}")
    assert response.status_code == 200
    assert response.json()["name"] == "Cube"


# 8. 取得不存在 → 404
def test_get_missing_object_returns_404(client):
    response = client.get("/objects/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Object 999 not found"


# 9. 建立後列表包含新物件
def test_list_after_create(client):
    create(client, name="Table")
    response = client.get("/objects")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Table"


# 10. 完整更新
def test_update_object(client):
    created = create(client).json()
    update = {
        "name": "Cube-Large",
        "model_url": "https://example.com/models/large.glb",
        "position": {"x": 1.0, "y": 2.0, "z": 3.0},
        "rotation": {"x": 0.1, "y": 0.2, "z": 0.3},
        "scale": {"x": 2.0, "y": 2.0, "z": 2.0},
    }
    response = client.put(f"/objects/{created['id']}", json=update)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Cube-Large"
    assert data["position"] == {"x": 1.0, "y": 2.0, "z": 3.0}
    assert data["scale"] == {"x": 2.0, "y": 2.0, "z": 2.0}


# 11. 部分更新只改指定欄位
def test_partial_update(client):
    created = create(client).json()
    response = client.put(
        f"/objects/{created['id']}",
        json={"name": "Renamed"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Renamed"
    assert data["position"] == created["position"]
    assert data["model_url"] == created["model_url"]


# 12. 更新不存在 → 404
def test_update_missing_object_returns_404(client):
    response = client.put("/objects/999", json={"name": "Ghost"})
    assert response.status_code == 404


# 13. 刪除成功 → 204
def test_delete_object(client):
    created = create(client).json()
    response = client.delete(f"/objects/{created['id']}")
    assert response.status_code == 204
    assert response.content == b""


# 14. 刪除後取得 → 404
def test_get_deleted_object_returns_404(client):
    created = create(client).json()
    client.delete(f"/objects/{created['id']}")
    assert client.get(f"/objects/{created['id']}").status_code == 404


# 15. 刪除不存在 → 404
def test_delete_missing_object_returns_404(client):
    response = client.delete("/objects/999")
    assert response.status_code == 404


# 16. 額外欄位 → 422
def test_extra_field_rejected(client):
    response = create(client, color="red")
    assert response.status_code == 422


# 17. 明確傳 null → 422（不再造成 500）
def test_explicit_null_update_rejected(client):
    created = create(client).json()
    response = client.put(f"/objects/{created['id']}", json={"name": None})
    assert response.status_code == 422


# 18. nan / inf → 422（直接送 JSON 字串，避開 httpx 用戶端序列化限制）
def test_non_finite_vector_rejected(client):
    headers = {"Content-Type": "application/json"}

    body = json.dumps(payload(position={"x": math.nan, "y": 0.0, "z": 0.0}))
    response = client.post("/objects", content=body, headers=headers)
    assert response.status_code == 422

    body = json.dumps(payload(scale={"x": math.inf, "y": 1.0, "z": 1.0}))
    response = client.post("/objects", content=body, headers=headers)
    assert response.status_code == 422


# 19. 巢狀額外欄位 → 422
def test_nested_extra_field_rejected(client):
    position = {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
    response = create(client, position=position)
    assert response.status_code == 422


# 20. 分頁 limit / skip
def test_pagination(client):
    for name in ("A", "B", "C"):
        create(client, name=name)
    response = client.get("/objects", params={"skip": 1, "limit": 1})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "B"
