# 反思報告

> 數據來源：OpenCode `session_v2` 資料表（工作階段 ID 見下表）。耗時以 `time_updated − time_created` 計算；token 取自 `tokens_input` / `tokens_output` / `tokens_cache_read`。全部為實際值，未假造。

---

## 1. 單一 Agent vs. 多 Subagent

### 1.1 本次實際測得的子代理數據

| 子代理 | 工作階段 ID | 耗時 | input token | output token | cache read |
|---|---|---:|---:|---:|---:|
| SQLite 評估 | `ses_e1154dc15ffekePGQidyGbStnU` | 25.30 s | 7,513 | 856 | 37,120 |
| PostgreSQL 評估 | `ses_e1154c5fbffeSl2epp4NX71EQs` | 39.17 s | 14,896 | 873 | 62,464 |
| MongoDB 評估 | `ses_e1154adc9ffe1cPtm5xy2jVfcE` | 13.12 s | 8,245 | 759 | 20,992 |
| **合計** | — | **77.58 s**（序列相加） | **30,654** | **2,488** | **120,576** |
| **並行實際 wall-clock** | — | **39.17 s**（取最慢者） | 30,654 | 2,488 | 120,576 |

### 1.2 比較表

| 項目 | 單一 Agent（序列推估） | 3 個 Subagent（並行實測） | 說明 |
|---|---:|---:|---|
| 耗時 | 77.58 s | **39.17 s** | 並行節省約 **49.5%**；序列值為三個 session 實測耗時相加 |
| input token | 30,654 | 30,654 | **沒有節省**：三個獨立 context 各自消耗，與序列相同 |
| cache read | 120,576 | 120,576 | **沒有節省**，甚至因重複讀取同一份規格而倍增 |
| context 狀態 | 任務越多越擁擠 | 主 Agent 只收摘要 | 子代理各自隔離，主 Agent 只接收 JSON 結論 |

> 註：本次**未另外執行「單一 Agent 全程處理 Part B」的對照實驗**。上表「單一 Agent」欄是以三個子代理的實測值相加推估序列情況，並非獨立實測；並行欄則為真實 wall-clock 時間。

**觀察**：Part B 由 3 個子代理各自讀取同一份規格、輸出固定 JSON，主 Agent 只做驗證與排序。並行把耗時砍了一半，但 token 與 cache read 完全沒省——這正是簡報中「Token 成本倍增」的實證。**時間換token**：適合趕時間的獨立任務，不適合預算敏感或任務彼此相依的情況。

---

## 2. 哪個子代理表現最好／最差

| 子代理 | 耗時 | input | 表現 | 調整 |
|---|---:|---:|---|---|
| MongoDB 評估 | **13.12 s** | 8,245 | **最好**：最快完成，輸出結構完整，JSON 一次通過驗證 | 可作為其他評估代理的 prompt 範本 |
| SQLite 評估 | 25.30 s | 7,513 | 中等：input 最少、輸出最緊湊，JSON 可直接解析 | 維持現有 prompt |
| PostgreSQL 評估 | **39.17 s** | **14,896** | **最差**：最慢且 input 最高，note 明顯較長 | 要求縮短 note、限制查證範圍與 `steps` |

**最好的子代理**：MongoDB 評估。依「輸出格式穩定度」與「是否一次通過 JSON 驗證」判斷，三者都通過驗證，但 MongoDB 耗時最短（13.12 s）且結構完整。

**最差的子代理**：PostgreSQL 評估。耗時最長（39.17 s）、input 最高（14,896），note 長度明顯多於另外兩份，是三者中效率最低者。

**調整方式**：

- Prompt 端：明確要求「只回傳 JSON，不要多餘文字」與固定欄位名稱
- 權限：評估型子代理給 read-only，避免誤改專案檔案
- `steps`：限制步數（本次設 12–15），避免子代理反覆查資料
- 對 PostgreSQL 這類分析較深的任務，可再要求「note 每項限 25 字以內」以壓縮輸出

---

## 3. 學到的心法

1. **交接靠檔案**：`docs/spec.md` 與 `bench/compare/*.json` 讓每個全新 context 的子代理都能接手。
2. **一人一職**：architect 只寫規格、tester 只寫測試、reviewer 不能改檔。
3. **結構化回報**：固定 JSON 才能自動排序成 `docs/compare.md`。
4. **審查與實作分離**：reviewer 沒有編輯權，才不會「自己出題、自己改考卷」。
5. **人類保留最後決策**：commit / merge 前由你 review。
6. **並行省時不省錢**：實測耗時減半，但 token 總量不變；任務切分前要先算清楚取捨。

---

## 4. 加分題

- [x] `team/security.md`：依 OWASP Top 10 檢查 API，唯讀不修改
- [x] 資安審查實際執行：`ses_e1152ecbeffeJNuIkGfNYLPl3F`，耗時 222.65 s、input 53,105、cache read 555,520，產出 `docs/security-review.md`
- [ ] WebXR 頁面即時顯示 API 中的 3D 物件（未實作）
