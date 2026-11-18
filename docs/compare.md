# Part B：三種儲存方案並行比較

比較對象：**SQLite / PostgreSQL / MongoDB**  
情境：XR 場景物件管理 API（`/objects` CRUD，Python + FastAPI + pytest）  
執行方式：主 Agent 同時派出 3 個子代理，各自輸出固定格式 JSON，再由主 Agent 彙整排序。

---

## 1. 並行執行記錄

| 方案 | 子代理工作階段 | 原始回報 |
|---|---|---|
| SQLite | `ses_e1154dc15ffekePGQidyGbStnU` | `bench/compare/sqlite.json` |
| PostgreSQL | `ses_e1154c5fbffeSl2epp4NX71EQs` | `bench/compare/postgresql.json` |
| MongoDB | `ses_e1154adc9ffe1cPtm5xy2jVfcE` | `bench/compare/mongodb.json` |

三份回報皆為合法 JSON，欄位結構一致，因此可直接程式化排序。

---

## 2. 評分面向與權重

| 面向 | 權重 | 說明 |
|---|---:|---|
| setup_complexity | 15% | 安裝與設定成本，分數越高越簡單 |
| runtime_performance | 20% | 讀寫延遲與吞吐 |
| deployment | 15% | 部署與維運複雜度，分數越高越簡單 |
| schema_flexibility | 15% | 欄位彈性與擴充性 |
| ecosystem | 15% | 與 FastAPI / Pydantic / pytest 的整合 |
| xr_fit | 20% | 對 XR 物件 CRUD 的适配度 |

計算方式：`加權分 = Σ(面向分數 × 權重)`，滿分 5。

---

## 3. 逐項分數

| 面向 | SQLite | PostgreSQL | MongoDB |
|---|---:|---:|---:|
| setup_complexity | 5 | 3 | 4 |
| runtime_performance | 4 | 4 | 4 |
| deployment | 5 | 3 | 3 |
| schema_flexibility | 4 | 5 | 5 |
| ecosystem | 5 | 5 | 5 |
| xr_fit | 4 | 4 | 4 |
| **加權總分** | **4.45** | **4.00** | **4.15** |

---

## 4. 排序比較表

| 排名 | 方案 | 加權分 | 一句 summary | 建議 |
|---:|---|---:|---|---|
| 1 | SQLite | 4.45 | 嵌入式單檔資料庫，安裝即用，適合中小型 XR 物件 CRUD | 原型與單機部署首選 |
| 2 | MongoDB | 4.15 | 彈性文件資料庫，快速迭代友善，但需獨立服務 | 重視欄位彈性與未來擴充時選用 |
| 3 | PostgreSQL | 4.00 | 可靠與 JSONB 彈性佳，但部署維運成本較高 | 多人協作、空間查詢或正式上線時選用 |

---

## 5. 各方案重點

### SQLite

**優點**

- 零安裝設定，Python 標準庫 `sqlite3` 直接可用
- 單檔部署與備份簡單，適合容器與邊緣環境
- 讀取延遲低，pytest 可用暫存檔快速自動化測試

**缺點**

- 並發寫入需序列化，高同時連線下受限
- 無內建空間索引，XR 位置運算需額外處理
- 跨裝置或多實例共享不如客戶端—伺服器資料庫

### MongoDB

**優點**

- 文件結構彈性，易於對應 3D 物件的階層與自訂屬性
- PyMongo / Motor / Beanie 與 FastAPI 整合成熟
- 水平擴充與 Atlas 託管方案完善

**缺點**

- 需額外部署與管理資料庫服務
- 本機開發與測試需啟動實例或搭配 `mongomock`
- 相較 SQLite 有網路延遲與資源開銷

### PostgreSQL

**優點**

- ACID 交易與成熟索引，適合多使用者並行 CRUD
- JSONB 兼顧固定欄位與彈性 XR 自訂屬性
- 可加 PostGIS 做空間查詢

**缺點**

- 需額外部署與維運資料庫服務
- 每次請求都有網路與連線池開銷
- 3D 幾何／空間運算需自行建模或依賴 PostGIS

---

## 6. 選擇結論

**選擇 SQLite。**

理由：本作業是單機原型，強調「可快速啟動、可完整測試、可清楚展示 CRUD 與驗證」。SQLite 在 setup、deployment 與 ecosystem 三項皆為 5 分，加權總分最高，且能讓 tester 在隔離的暫存資料庫中穩定執行 16 個測試。

取捨：放棄了 MongoDB / PostgreSQL 的結構彈性與空間查詢能力。若之後需求變成「多人即時協作」或「依位置做空間查詢」，應遷移至 PostgreSQL + PostGIS；此路徑已記錄在 `docs/spec.md`。
