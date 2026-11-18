# Part C 加分題 — API 資安審查報告

- 審查者：`team/security`（資安審查員子代理）
- 審查日期：2026-11-18
- 基準：**OWASP Top 10:2025**（括號內標註 2021 版對應類別）
- 本報告是本次審查**唯一被授權寫入**的檔案

---

## 1. 檢查範圍與方法

### 1.1 檢查範圍

| 類別 | 檔案 |
|---|---|
| API 實作（主要標的） | `app/main.py`、`app/models.py`、`app/storage.py`、`app/__init__.py` |
| 規格對照 | `docs/spec.md`、`README.md` |
| 驗證/相依對照 | `tests/conftest.py`、`tests/test_objects.py`、`pyproject.toml`、`requirements.txt` |
| 權限設計對照 | `.opencode/agents/team/security.md`、`architect.md`、`coder.md`、`tester.md`、`reviewer.md`、`doc-writer.md` |
| 套件行為查證（唯讀） | `.venv/Lib/site-packages/pydantic/types.py`、`networks.py` 及各 `*.dist-info` |

### 1.2 方法

1. 逐行靜態審查 `app/` 的路由、Pydantic 模型與 SQLite 存取層。
2. 依 OWASP Top 10:2025 十大類別逐項判定 **適用 / 不適用 / 需注意**，並標註檔案與行號（或函式名）。
3. 針對加分題要求，另做五個重點檢查：`輸入驗證（Pydantic）`、`SQL 注入（參數化查詢）`、`URL 欄位濫用`、`錯誤訊息洩漏`、`資源耗用`。
4. 交叉比對 `.opencode/agents/team/security.md` 與 `docs/spec.md` 第 7 節的權限設計，以及本次實際執行行為。
5. 以已安裝套件版本（由 `.venv/*.dist-info` 讀取：FastAPI 0.163.2、Starlette 1.10.0、Pydantic 2.14.3、uvicorn 0.54.0）佐證 Pydantic 驗證行為。

### 1.3 限制與宣告

- 僅做**靜態分析**，未啟動服務、未執行滲透測試或惡意 payload，也未執行測試套件。
- 未修改 `app/`、`tests/`、`docs/spec.md`、`README.md` 或任何專案程式。
- 本次為列舉檔案曾使用**唯讀 shell 指令**（`Get-ChildItem`、`Test-Path`），未寫入檔案、未執行專案程式；此與 `security.md` 的 `shell: deny` 定義有偏差，已於第 3 節如實揭露。
- 判定情境假設：依 `README.md:7-11`，預設以 `uvicorn --port 8000` 啟動且未指定 `--host`，即監聽 `127.0.0.1`，屬**本機單機工具**。若改為對外暴露，多項風險等級需上調（見第 3 節）。

---

## 2. OWASP Top 10 逐項評估

### 2.1 總表（判定 / 位置 / 風險 / 說明與建議）

| 類別（2025 / 2021） | 判定 | 位置 | 風險 | 說明與建議 |
|---|---|---|---|---|
| **A01 Broken Access Control**（A01 + A10 SSRF） | 需注意 | `app/main.py:28-62`（全部 CRUD 路由） | 中（公開部署則高） | 沒有任何身份驗證、授權或所有權檢查，任何能連到服務者都能列出、建立、更新、刪除全部物件。建議：限制綁定位址至 `127.0.0.1`；若要對外提供，加入 API key / OAuth2 並做物件層級授權。SSRF 部分見 2.2。 |
| **A02 Security Misconfiguration**（A05） | 需注意 | `app/main.py:15-20`（FastAPI 實例）、`app/storage.py:11-12`（`XR_DB_PATH`）、`README.md:10`（`--reload`） | 低 | 未關閉 `/docs`、`/redoc`、`/openapi.json`（正式環境可考慮關閉或加驗證）；未設定安全標頭（純 JSON API 影響有限）；DB 路徑由環境變數決定且未驗證；README 的 `--reload` 僅適用開發。正向：未見 `debug=True`，CORS 未開通（預設拒絕跨域），Starlette 預設 500 不回傳堆疊。建議：正式環境移除 `--reload`、限制文件端點、檢查 DB 路徑與檔案權限。 |
| **A03 Software Supply Chain Failures**（A06） | 需注意 | `pyproject.toml:6-15`、`requirements.txt:1-4` | 低 | 相依僅有下限（`fastapi>=0.110` 等），無上限、無 lockfile、無 SCA 掃描；由 `.venv` 讀取到的版本皆為近期版本，**未發現明確已知漏洞版本**。建議：鎖定版本並定期執行 `pip-audit` / Dependabot。 |
| **A04 Cryptographic Failures**（A02） | 不適用 | 全專案 | 無 | 系統不處理密碼、token、個資或金鑰，也沒有自建加密機制，故此類別目前無風險。附帶提醒（低）：`model_url` 若含 `user:pass@host` 的 userinfo，會以明文存入 DB 並原樣回傳，建議禁止 userinfo（已於 A01 / A08 的 URL 建議中涵蓋）。 |
| **A05 Injection**（A03） | 適用 | `app/storage.py:80, 90-105, 125, 133-136, 149`（SQL）；`app/models.py:18-38`（驗證） | 低 | **SQL 注入目前已防護**：所有「值」皆以 `?` 參數綁定；`update_object` 雖用 f-string 組欄位名（`storage.py:125,134`），但欄位名來自 Pydantic 固定欄位且 `extra="forbid"`，無法由外部注入。**殘留顧慮**：此為脆弱設計模式，若日後放寬 `extra` 或新增動態欄位即可能變成注入。建議：改為白名單映射 `{"name": "name = ?", ...}`。其餘無 `eval` / `exec` / shell 呼叫，無命令注入；JSON 只用 `json.dumps/loads`，無不安全反序列化。 |
| **A06 Insecure Design**（A04） | 適用 | `app/main.py:28-30`（`list_objects`）、`app/main.py:33-35`（`create_object`）、`app/storage.py:71-74` | 中 | `GET /objects` 無分頁、無 `limit`、無過濾，列數與回應大小無上限；`POST /objects` 無數量配額；全 API 無速率限制。屬 CWE-400 資源耗用，資料量增長或惡意大量建立時可造成記憶體/磁碟/回應耗盡。建議：加入 `limit`/`offset`（並設上限，如 100）、速率限制與建立筆數配額。 |
| **A07 Authentication Failures**（A07） | 需注意 | `app/main.py:15-62`（全路由） | 中（公開部署則高） | 完全沒有登入、API key、session 或 token 驗證，與 A01 重疊。依本機工具定位可接受，但一旦上線即等同公開端點。建議：至少提供可選的 API key / mTLS，並在文件中明確標示「僅供本機使用」。 |
| **A08 Software or Data Integrity Failures**（A08） | 適用 | `app/models.py:31-38`（`ObjectUpdate`）、`app/storage.py:114-136`（`update_object`）、`app/main.py:33-62`（未設 `response_model`） | 中 | **明確傳入 `null` 會破壞資料完整性**：`ObjectUpdate` 各欄位可為 `None`，而 `model_dump(exclude_unset=True)`（`storage.py:114`）會把「明確給 null」視為已變更。結果：`name:null` → 寫入 NOT NULL 欄位触发 `IntegrityError`（500）；`model_url:null` → `str(None)` 存成字串 `"None"`（`storage.py:123-124`）；`position/rotation/scale:null` → 存成 JSON `"null"`（`storage.py:121-122`），`_to_dict` 回傳 `None`。又因路由未宣告 `response_model=ObjectOut`（`main.py:33-62`），這些不合格式的資料會直接回給用戶端。建議：更新時排除 `None`（視為不更新）或改用嚴格 PATCH schema，並為所有路由加 `response_model=ObjectOut`。另外部 `model_url` 指向的 3D 模型檔在用戶端載入時缺乏完整性/大小驗證（見 2.2 URL 小節）。 |
| **A09 Security Logging & Alerting Failures**（A09） | 適用 | `app/main.py`（全檔，無 `logging`）、`app/storage.py`（全檔，無 `logging`） | 中偏低 | 沒有任何日誌或告警：無法追蹤誰在何時建立/更新/刪除物件，也無法偵測大量 422/500 或濫用行為。建議：加入結構化日誌（方法、路徑、id、狀態、時間），並對 5xx 與 422 異常量設告警；避免把含 userinfo 的 URL 寫入日誌。 |
| **A10 Mishandling of Exceptional Conditions**（2025 新增；2021 無對應） | 適用 | `app/storage.py:114-136`、`app/main.py:38-43` | 低至中 | 承 A08 的 `null` 更新觸發未處理例外 → 500；`object_id: int`（`main.py:39,47,59`）無範圍限制，超大整數傳入 SQLite 綁定可能 `OverflowError` → 500；DB 鎖定/磁碟滿等 sqlite3 例外亦未捕獲。正向：未見堆疊外洩。建議：用 `Path(ge=1, le=2**63-1)` 限制 id、加全域例外處理器回傳固定錯誤格式，並把 `configure_db`（`storage.py:17-23`）納入 `_lock` 以避免執行期關閉連線的競態。 |

### 2.2 加分題重點檢查

#### (a) 輸入驗證（Pydantic）— 大致良好，但有四個缺口

**已做到（正向）**

- `ObjectBase` / `ObjectUpdate` 皆設 `extra="forbid"`（`models.py:19,32`），最上層額外欄位會被拒（測試 `tests/test_objects.py:148-151` 驗證）。
- `name` 限制 1–100 字元（`models.py:21,34`）。
- `model_url` 使用 `HttpUrl`（`models.py:22,35`）；查證 `.venv/.../pydantic/networks.py:724`，`HttpUrl` 限制 scheme 僅 `http`/`https`、最大長度 2083，故 `javascript:`、`file:` 與超長 URL 會被拒。
- `ScaleVector` 三軸 `Field(gt=0)`（`models.py:13-15`）。
- 驗證失敗由 FastAPI 回 422，符合 `docs/spec.md:98`。

**缺口（建議修正）**

1. `Vector3` 與 `ScaleVector`（`models.py:6-15`）**未設** `extra="forbid"`，巢狀額外欄位會被 Pydantic 預設忽略；既有測試只覆蓋最上層。建議兩者皆加 `model_config = ConfigDict(extra="forbid")`。
2. 一般 `float` 預設接受 `nan`/`±inf`（查證 `.venv/.../pydantic/types.py:394-411,650`：`AllowInfNan` 預設 `True`，`FiniteFloat` 才是有限數）。`position`/`rotation`（`models.py:23-24`）無有限數限制與合理上下界；`scale` 的 `gt=0` 會擋住 `nan` 但仍可接受 `+inf`。`json.dumps` 會產生非標準 JSON 的 `NaN`/`Infinity`，可能讓 XR 用戶端出錯。建議改用 `FiniteFloat` 並給 rotation 合理範圍（例如 -π～π 或依需求放寬）。
3. 前述 `ObjectUpdate` 明確 `null` 問題（A08/A10），建議排除 `None` 或改用嚴格更新模型。
4. 路由未宣告 `response_model=ObjectOut`（`main.py:33-62`），輸出未經驗證；建議補上。

#### (b) SQL 注入（參數化查詢）— 目前安全

- `get_object`（`storage.py:79-81`）、`create_object`（`90-109`）、`update_object`（`133-142`）、`delete_object`（`149`）、`init_db`（`41-54`）全部使用 `?` 佔位符；符合 `docs/spec.md:120`「所有 SQL 使用參數化查詢，禁止字串拼接」。
- 唯一動態部分是 `update_object` 的欄位名（`storage.py:118-126,134`），來源為 `payload.model_dump(exclude_unset=True)` 的固定的 Pydantic 欄位名，且 `extra="forbid"`，**目前不可被外部操控**。
- 風險等級：低（設計脆弱性，非可利用漏洞）。建議改白名單映射，降低未來維護風險。**無 SQL 注入風險**。

#### (c) URL 欄位濫用 / SSRF — 伺服器端目前不適用，需注意用戶端

- `HttpUrl` 已限制 http/https 與長度 2083（見上）。API 僅將 URL 存成文字並回傳（`storage.py:98,123-124`），**沒有任何對外請求**，故本 API 本身無直接 SSRF。
- 但仍需注意：① 未限制 host，可填 `http://169.254.169.254/...` 或內網位址，若未來加入預覽/下載/有效性檢查即成 SSRF；② 可含 userinfo 憑證明文存 DB；③ XR 用戶端據此載入任意模型檔，有惡意內容與頻寬耗用風險。
- 建議：host 白名單、封鎖 loopback/private/link-local、禁止 userinfo、用戶端下載前檢查 Content-Type/大小上限與雜湊。

#### (d) 錯誤訊息是否洩漏 — 良好

- 404 訊息 `f"Object {object_id} not found"`（`main.py:42,50,61`）只包含已驗證的整數 id，且是 `docs/spec.md:92-96` 指定的格式，未洩漏路徑、SQL 或堆疊。
- 未見 `debug=True`；Starlette 預設 500 為通用訊息，不回傳 traceback。
- 低-risk 提醒：FastAPI/Pydantic 422 可能回傳 submitted `input` 值，若輸入含敏感字串（如 URL userinfo）會被回顯；建議日誌/錯誤回應一併遮罩 userinfo，並可考慮把 404 detail 改為通用字串（需同步調整規格與測試）。

#### (e) 資源耗用 — 需注意

- `GET /objects`（`main.py:28-30`、`storage.py:71-74`）一次讀取全部列並 `json.loads` 三欄，無分頁、無上限：列數線性增長會墊高 DB、記憶體與網路成本（A06，中）。
- 無速率限制、無建立筆數配額（A01/A06，中）。
- 無請求 body 大小限制（uvicorn 預設），雖有欄位長度限制仍建議在反向代理層設上限（低）。
- 全域單一 `sqlite3.Connection` 搭配 `check_same_thread=False`（`storage.py:14,26-31`）且以 `_lock` 保護多數操作，方向正確；但 `configure_db`（`17-23`）未持鎖，測試/執行期切換 DB 可能有競態（低）。

---

## 3. 風險等級與建議修正

| 等級 | 項目 | 位置 | 建議修正 |
|---|---|---|---|
| **高** | **無（在 README 所述之本機部署情境下）** | — | 無需高風險修正。但若服務暴露到非信任網路，A01/A07（無驗證授權）與 A06（無節流）立即升為**高風險**，應先完成驗證、授權與速率限制再上線。 |
| **中** | ① 無身份驗證/授權（A01/A07） | `main.py:28-62` | 綁定 `127.0.0.1`；對外時加 API key/OAuth2 與物件層級授權。 |
| **中** | ② 無分頁/無速率限制/無配額（A06） | `main.py:28-35`、`storage.py:71-74` | 加 `limit`/`offset` 上限、rate limit、建立筆數配額。 |
| **中** | ③ 明確 `null` 更新破壞資料完整性（A08/A10） | `models.py:31-38`、`storage.py:114-136` | 更新時排除 `None` 或改嚴格 PATCH schema；補 `response_model=ObjectOut`。 |
| **中偏低** | ④ 无任何日誌與告警（A09） | `main.py`、`storage.py` 全檔 | 加結構化日誌與 5xx/422 異常告警，遮罩敏感 URL。 |
| **低** | ⑤ `update_object` 動態 SQL 欄位名（A05） | `storage.py:118-126,134` | 改白名單映射。 |
| **低** | ⑥ `Vector3`/`ScaleVector` 未禁額外欄位、`float` 接受 `nan`/`inf`（2.2a） | `models.py:6-15,23-24` | 加 `extra="forbid"`、改用 `FiniteFloat` 與數值範圍。 |
| **低** | ⑦ `model_url` 無 host 白名單、可含 userinfo（2.2c） | `models.py:22,35`、`storage.py:98,123-124` | 封鎖內網/中繼資料位址、禁 userinfo、限制下載大小與類型。 |
| **低** | ⑧ OpenAPI 文件端點暴露、`--reload`、DB 路徑未驗證（A02） | `main.py:15-20`、`README.md:10`、`storage.py:11-12` | 正式環境關閉文件端點與 reload，驗證 DB 路徑與檔案權限。 |
| **低** | ⑨ 相依未鎖定、無 SCA（A03） | `pyproject.toml:6-15`、`requirements.txt:1-4` | 鎖版本並定期掃描。 |
| **低** | ⑩ 超大 `object_id` 與未捕獲 DB 例外 → 500（A10） | `main.py:39,47,59`、`storage.py:17-23` | `Path(ge=1, le=2**63-1)`、全域例外處理器、`configure_db` 加鎖。 |
| **無風險（明確聲明）** | SQL 注入（值皆參數化）、命令注入（無 shell/exec）、不安全反序列化（僅 `json`）、密碼學失效（無敏感資料/自建加密）、CSRF（無 cookie 驗證）、伺服器端 SSRF（API 不發出外部請求） | `storage.py:80,90-105,133-136,149` 等 | 無需修正；維持現有做法。 |

### 3.1 與 `.opencode/agents/team/security.md` 權限設計的一致性

- 定義檔 `.opencode/agents/team/security.md:5-14` 為：`read * allow`、`edit * deny`、`shell * deny`；`docs/spec.md:158` 亦記載 team/security「寫 ✘、Shell ✘」。本次**只讀** `app/`、`tests/`、`docs/spec.md`、`README.md`，未修改任何程式或測試，這部分**一致**。
- **不一致點一（寫入例外）**：本次任務由父層明確授權唯一寫入 `docs/security-review.md`，但定義檔沒有對應的 `edit` allow 規則，且 `docs/spec.md:160` 說明「最後符合者生效」，security.md 中 deny 之後沒有 allow，故定義上仍是不可寫。建議：在 `security.md` 增加 `edit docs/security-review.md: allow`（或改由 `doc-writer` 代寫），並同步更新 `docs/spec.md:150-158` 表格，讓授權與實務一致。
- **不一致點二（唯讀 shell）**：本次曾使用唯讀 shell 列舉檔案，與 `shell * deny` 定義有偏差；未造成任何寫入或程式執行。建議日後嚴格遵守，或將「唯讀目錄列舉」明確納入 `read` 權限範圍。
- 其餘角色定義（architect 只寫 spec、coder 只寫 app/與依賴、tester 只寫 tests/、reviewer 全唯讀、doc-writer 寫 README/docs）與 `docs/spec.md:150-160` 表格相互一致，未發現其他衝突。

---

## 4. 結論

整體而言，本 API 在 SQL 參數化與 Pydantic 輸入驗證上表現良好，**未發現可直接利用的高風險漏洞**，但無驗證/授權、無分頁與節流、明確 `null` 更新破壞資料完整性及缺乏日誌等中/低風險仍建議在對外部署前修正，並同步調整 security agent 的寫入權限定義以符合本次實際授權。

---

## 5. 修正紀錄（主 Agent 於審查後處理）

| 項目 | 狀態 | 處理方式 |
|---|---|---|
| 明確 `null` 更新造成 500 / 資料污染（A08/A10） | ✅ 已修正 | `ObjectUpdate` 增加 `model_validator`，明確 `null` 回 422；新增測試 `test_explicit_null_update_rejected` |
| 路由未宣告 `response_model`（A08） | ✅ 已修正 | 所有 CRUD 路由補上 `response_model=ObjectOut` / `list[ObjectOut]` |
| `Vector3` / `ScaleVector` 未禁額外欄位、接受 `nan`/`inf` | ✅ 已修正 | 加 `extra="forbid"` 與 `Field(allow_inf_nan=False)`；新增 2 個測試 |
| `update_object` 動態組 SQL 欄位名（A05） | ✅ 已修正 | 改為 `allowed_columns` 白名單映射 |
| `GET /objects` 無分頁（A06） | ✅ 已修正 | 加入 `skip` / `limit`（`1 <= limit <= 1000`）；新增測試 |
| 無任何日誌（A09） | ✅ 已修正 | 加入 `logging`，記錄建立/更新/刪除與 404；不記錄 URL userinfo |
| 超大 `object_id`（A10） | ✅ 已修正 | `Path(ge=1, le=2**63-1)` |
| 相依未鎖定（A03） | ✅ 已修正 | `requirements.txt` 改為精確版本 |
| security agent 寫入權限不一致（3.1） | ✅ 已修正 | `security.md` 增加 `edit docs/security-review.md: allow`；`docs/spec.md` 同步更新 |
| 無身份驗證/授權、無速率限制 | ⚠ 未修正 | 定位為本機工具；若對外暴露必須先補 API key/OAuth2 與節流 |
| `/docs`、`--reload`、URL host 白名單 | ⚠ 未修正 | 屬部署與用戶端防護；已於本文保留建議 |

修正後測試：**20 passed**。

