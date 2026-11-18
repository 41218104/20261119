# XR 場景物件管理 API — 系統規格

版本：1.0  
角色：team/architect  
狀態：已核准，作為 coder / tester / reviewer 的共同依據

---

## 1. 目標

提供一個後端 API，管理 XR 場景中的 3D 物件。每個物件包含：

- `name`：物件名稱
- `model_url`：模型檔案網址（例如 `.glb` / `.gltf`）
- `position`：位置向量 `(x, y, z)`
- `rotation`：旋轉向量（歐拉角，弧度）`(x, y, z)`
- `scale`：縮放向量，三軸皆必須大於 0

API 必須支援 `/objects` 的 CRUD，具備輸入驗證，並有至少 10 個自動化測試。

---

## 2. 技術決策

| 項目 | 選擇 | 理由 |
|---|---|---|
| 語言 | Python 3.11+ | 作業建議，生態成熟 |
| 框架 | FastAPI | 型別驅動驗證、自動 OpenAPI、TestClient 好寫測試 |
| 驗證 | Pydantic v2 | 宣告式驗證，錯誤回傳 422 |
| 儲存 | SQLite | 單機、零設定、測試隔離容易；Part B 比較後仍選它 |
| 測試 | pytest + httpx TestClient | 可直接測 API，不需啟動外部伺服器 |

> Part B 的詳細比較見 `docs/compare.md`。若未來需要多人即時協作或空間查詢，可遷移至 PostgreSQL + PostGIS。

---

## 3. 資料模型

### Vector3

| 欄位 | 型別 | 限制 |
|---|---|---|
| x | float | 必填 |
| y | float | 必填 |
| z | float | 必填 |

### ScaleVector

| 欄位 | 型別 | 限制 |
|---|---|---|
| x | float | 必填，> 0 |
| y | float | 必填，> 0 |
| z | float | 必填，> 0 |

### ObjectCreate

| 欄位 | 型別 | 限制 |
|---|---|---|
| name | str | 1–100 字元 |
| model_url | HttpUrl | 必須是合法 http/https URL |
| position | Vector3 | 必填 |
| rotation | Vector3 | 必填 |
| scale | ScaleVector | 必填，各軸 > 0 |

### ObjectUpdate

所有欄位皆可選；未提供的欄位不變。不允許額外欄位（`extra="forbid"`）。

### ObjectOut

在 `ObjectCreate` 之上增加：

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | int | 自動遞增主鍵 |
| created_at | datetime | UTC ISO 8601 |
| updated_at | datetime | UTC ISO 8601 |

---

## 4. API 端點

| 方法 | 路徑 | 成功 | 說明 |
|---|---|---|---|
| GET | `/health` | 200 | 健康檢查，回 `{"status":"ok"}` |
| GET | `/objects` | 200 | 列出物件，支援 `skip`（≥0）與 `limit`（1–1000，預設 100）分頁 |
| POST | `/objects` | 201 | 建立物件，回傳完整物件 |
| GET | `/objects/{id}` | 200 | 取得單一物件；不存在回 404 |
| PUT | `/objects/{id}` | 200 | 部分更新；不存在回 404 |
| DELETE | `/objects/{id}` | 204 | 刪除；不存在回 404 |

錯誤格式：

```json
{ "detail": "Object 99 not found" }
```

驗證失敗由 FastAPI/Pydantic 回傳 422，含欄位層級錯誤。所有 CRUD 路由皆宣告 `response_model`；明確傳 `null`、額外欄位、`nan`/`inf` 一律回 422。資安修正紀錄見 `docs/security-review.md`。

---

## 5. 儲存設計

SQLite 表格 `objects`：

```sql
CREATE TABLE IF NOT EXISTS objects (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    model_url   TEXT    NOT NULL,
    position    TEXT    NOT NULL,  -- JSON: {"x":..,"y":..,"z":..}
    rotation    TEXT    NOT NULL,
    scale       TEXT    NOT NULL,
    created_at  TEXT    NOT NULL,
    updated_at  TEXT    NOT NULL
)
```

- 資料庫路徑由環境變數 `XR_DB_PATH` 決定；未提供時使用專案根目錄的 `xr_objects.db`。
- 所有 SQL 使用參數化查詢，禁止字串拼接。
- 使用 `threading.Lock` 保護寫入。
- 測試時由 fixture 把 `XR_DB_PATH` 指向暫存檔，確保隔離。

---

## 6. 測試策略

最少 10 個測試，必須涵蓋：

1. 健康檢查
2. 空列表
3. 建立成功並回傳欄位
4. 空名稱 → 422
5. 非法 URL → 422
6. scale <= 0 → 422
7. 依 id 取得
8. 取得不存在 → 404
9. 建立後列表包含新物件
10. 完整更新
11. 部分更新只改指定欄位
12. 更新不存在 → 404
13. 刪除成功 → 204
14. 刪除後取得 → 404
15. 刪除不存在 → 404

---

## 7. 團隊分工與權限

| 角色 | 讀 | 寫 | Shell | 說明 |
|---|---|---|---|---|
| 主 Agent | ✔ | ✔ | ✔ | 指揮、整合、最終交付 |
| team/architect | ✔ | `docs/spec.md` | ✘ | 只寫規格 |
| team/coder | ✔ | `app/**`、依賴檔 | ask | 依規格實作 |
| team/tester | ✔ | `tests/**` | ✔ | 可跑測試，不改功能碼 |
| team/reviewer | ✔ | ✘ | ✘ | 客觀審查 |
| team/doc-writer | ✔ | `README.md`、`docs/**`（spec 除外） | ✘ | 文件 |
| team/security | ✔ | `docs/security-review.md` | ✘ | OWASP 檢查（加分題，只寫審查報告） |

規則由上往下比對，最後符合者生效：先 deny 全部，再開放特定路徑。

---

## 8. 工作流程

1. architect 產出 `docs/spec.md`
2. 主 Agent 平行派出 3 個評估子代理，產出 `bench/compare/*.json`
3. 主 Agent 彙整成 `docs/compare.md` 並選型
4. coder 依規格實作 `app/`
5. tester 撰寫並執行 `tests/`
6. reviewer 與 security 並行審查
7. 有問題則交回 coder 修正，最多 3 輪
8. doc-writer 更新 `README.md` 與反思報告
9. 人類保留最後 commit / merge 決策
