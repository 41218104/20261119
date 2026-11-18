# XR 場景物件管理 API

以 Vibe Coding 方式，透過 OpenCode 的 Subagent 團隊完成的作業專案。

## 快速開始

```powershell
cd D:\20261112
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

OpenAPI 文件：<http://127.0.0.1:8000/docs>

## 執行測試

```powershell
.\.venv\Scripts\python.exe -m pytest
```

目前結果：**20 passed**。資安審查與修正紀錄見 `docs/security-review.md`。

## API

| 方法 | 路徑 | 說明 |
|---|---|---|
| GET | `/health` | 健康檢查 |
| GET | `/objects` | 列出全部物件 |
| POST | `/objects` | 建立物件 |
| GET | `/objects/{id}` | 取得單一物件 |
| PUT | `/objects/{id}` | 部分更新 |
| DELETE | `/objects/{id}` | 刪除 |

建立範例：

```bash
curl -X POST http://127.0.0.1:8000/objects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Cube",
    "model_url": "https://example.com/models/cube.glb",
    "position": {"x": 0, "y": 1.5, "z": -2},
    "rotation": {"x": 0, "y": 1.57, "z": 0},
    "scale": {"x": 1, "y": 1, "z": 1}
  }'
```

## 專案結構

```text
D:\20261112
├── .opencode/agents/team/   # Subagent 定義（architect / coder / tester / reviewer / doc-writer / security）
├── app/                     # FastAPI 應用程式
├── bench/compare/           # Part B 三個子代理的原始 JSON 回報
├── docs/
│   ├── spec.md              # Part A 架構規格
│   ├── compare.md           # Part B 並行比較表
│   ├── reflection.md        # 反思報告
│   └── security-review.md   # OWASP 資安審查與修正紀錄
├── tests/                   # 16 個自動化測試
├── pyproject.toml
└── requirements.txt
```

## 資料庫

預設使用專案根目錄的 `xr_objects.db`。可用環境變數覆蓋：

```powershell
$env:XR_DB_PATH = "D:\20261112\custom.db"
```

## 還原點

初始兩份簡報抽取檔案已備份於 `_restore_point_before_assignment.zip`。若要回到初始狀態，解壓該檔並覆蓋即可。

## 注意事項

- 繳交所需的「主 Agent 派工畫面」與「至少 2 個子代理子 session」截圖需由你在 OpenCode 介面自行擷取；文字記錄已寫在 `docs/compare.md`。
- 反思報告中的時間與 token 比較為模板，實際數值請依你的 OpenCode 工作階段填入。
