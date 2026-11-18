# 反思報告

> 本檔為 1–2 頁反思報告模板。標示「待填」處請依實際 OpenCode 工作階段填入，不要假造數字。

---

## 1. 單一 Agent vs. 多 Subagent

| 項目 | 單一 Agent | 3 個 Subagent | 待填說明 |
|---|---|---|---|
| 耗時 | 待填 | 待填 | 可從 OpenCode session 的 `time.busy` 觀察 |
| input token | 待填 | 待填 | 可從 session 的 `tokens.input` 觀察 |
| cache read | 待填 | 待填 | 可從 session 的 `tokens.cache.read` 觀察 |
| context 狀態 | 任務越多越擁擠 | 主 Agent 只收摘要 | 描述是否有品質下降 |

**觀察**：這次的 Part B 由 3 個子代理各自讀取同一份規格、輸出固定 JSON，主 Agent 只做驗證與排序。優點是 context 隔離與格式一致；代價是三份 context 的花費。

---

## 2. 哪個子代理表現最好／最差

| 子代理 | 表現 | 調整 |
|---|---|---|
| SQLite 評估 | 待填 | 輸出最緊湊，JSON 可直接解析 |
| PostgreSQL 評估 | 待填 | note 較長，可要求縮短 |
| MongoDB 評估 | 待填 | 結構完整，繁體中文一致 |

**最好的子代理**：待填（建議從「輸出格式穩定度」與「是否一次通過 JSON 驗證」判斷）

**最差的子代理**：待填

**調整方式**：

- Prompt 측：明確要求「只回傳 JSON，不要多餘文字」與固定欄位名稱
- 權限：評估型子代理給 read-only，避免誤改專案檔案
- `steps`：限制步數，避免子代理反覆查資料

---

## 3. 學到的心法

1. **交接靠檔案**：`docs/spec.md` 與 `bench/compare/*.json` 讓每個全新 context 的子代理都能接手。
2. **一人一職**：architect 只寫規格、tester 只寫測試、reviewer 不能改檔。
3. **結構化回報**：固定 JSON 才能自動排序成 `docs/compare.md`。
4. **審查與實作分離**：reviewer 沒有編輯權，才不會「自己出題、自己改考卷」。
5. **人類保留最後決策**：commit / merge 前由你 review。

---

## 4. 加分題

- [x] `team/security.md`：依 OWASP Top 10 檢查 API，唯讀不修改
- [ ] WebXR 頁面即時顯示 API 中的 3D 物件（未實作）
