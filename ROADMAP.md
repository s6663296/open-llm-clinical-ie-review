# ROADMAP：開源 LLM 臨床病歷資訊抽取 — 系統性回顧

> 本檔是專案的**進度狀態檔**。Agent 每次開始工作先讀這裡，完成工作後回來更新。
> 報告規範：PRISMA 2020（https://www.prisma-statement.org/）。`#數字` = PRISMA 2020 checklist 項目編號。

---

## 📍 目前位置

- **階段**：B 完成 → C. 篩選（2026-11-14）
- **步驟**：A3 OSF 註冊（待使用者）＋ C1 標題／摘要篩選（待兩位篩選者）
- **已完成**：protocol v0.2 定案、驗證集確認；六來源正式檢索（2026-11-14，2,132 筆）；去重 → 1,389 筆（`data/records_dedup.csv`）；驗證集 10/10 檢出；正式篩選表 `screening/title_abstract.xlsx`（1,389 筆、50 筆校準樣本、全部附 Agent 建議：include 205／unsure 421／exclude 763，僅供參考）；PRISMA 流程圖（識別段）`figures/prisma_flow.*`；全部腳本與稿件 Methods／引言草稿
- **下一步（需要使用者）**：① 填 protocol 1.3、1.5（作者、第二篩選者、仲裁者、經費、利益衝突）→ ② 以 `protocol/osf_registration.md` 在 OSF 註冊（**須在篩選開始前**）→ ③ 人工確認 `data/formal_2026-11-14/possible_duplicates.csv` 的 83 組疑似重複 → ④ 兩位篩選者各自複製 `screening/title_abstract.xlsx`，先做 50 筆校準（`scripts/kappa.py --subset calibration`），κ ≥ 0.6 後篩完全部 → 交回後由 Agent 合併、算 κ、產生全文篩選表並下載 OA 全文
- **卡住／待使用者決定**：見下方「待決事項」

---

## 進度總覽

狀態：✅ 完成　🔄 進行中　⬜ 未開始　⏸ 暫緩

| 代號 | 步驟 | 狀態 | 產出 |
|---|---|---|---|
| A1 | 研究問題（PICO） | ✅ | 本檔「研究定義」；子問題草案在 `protocol/protocol.md` 2.2 |
| A2 | 納入／排除條件 | ✅ | 本檔「研究定義」；判斷規則與排除代碼在 `protocol/protocol.md` 3.1–3.2 |
| A3 | Protocol 與註冊 | 🔄 | `protocol/protocol.md` |
| B1 | 資料庫檢索 | ✅ | `<資料庫> 2022-2026/`、`搜尋條件.docx` |
| B2 | 匯入與去重 | 🔄 | `data/records_dedup.csv` |
| C1 | 標題／摘要篩選 | 🔄 | `screening/title_abstract.xlsx` |
| C2 | 全文篩選 | ⬜ | `screening/full_text.xlsx` |
| D1 | 資料萃取 | ⬜ | `extraction/extraction.xlsx` |
| D2 | 偏倚風險／品質評估 | ⬜ | `extraction/risk_of_bias.xlsx` |
| E1 | 綜合分析與圖表 | 🔄 | `analysis/`、`figures/` |
| E2 | 報告偏誤與確信度 | ⬜ | `analysis/certainty.md` |
| F1 | PRISMA 流程圖 | ⬜ | `figures/prisma_flow.*` |
| F2 | 論文撰寫 | 🔄 | `manuscript/` |
| F3 | 投稿前檢查 | 🔄 | `manuscript/prisma_checklist.*` |

---

## 研究定義（A1、A2 的決定記錄於此）

**研究問題（草案）**：開源／開放權重 LLM 在臨床自由文本資訊抽取任務上的使用方式與效能為何？

| PICO | 內容 |
|---|---|
| P | 臨床自由文本：病歷、出院摘要、影像報告、病理報告 |
| I | 開源／開放權重 LLM（Llama、Mistral、Qwen、Gemma、DeepSeek、Phi、BioMistral、Meditron…） |
| C | 閉源 LLM（GPT-4 等）、BERT 類模型、規則式方法、人工標註 |
| O | 抽取效能（F1、precision、recall、accuracy） |

**納入**：至少一個開源 LLM；臨床自由文本；資訊抽取任務（NER、關係抽取、結構化欄位抽取）；有量化評估；2022–2026。
**排除**：只用閉源模型；非抽取任務；無量化評估；回顧／社論／無全文。
**已定（2026-11-13）**：「開源」= 權重可公開下載（不要求 OSI 授權，授權類型另萃取）；納入 arXiv／medRxiv 預印本（做排除預印本的敏感度分析）；論文限英文、病歷語言不限。
**已定（2026-11-14）**：LLM 參數量 ≥ 1B；只用合成病歷者排除；X6 排除摘要、QA、自動編碼、文件層級分類／預測（輸出為文本中明確記載的欄位值仍算抽取）。

---

## 各步驟定義

每步包含：要做什麼、完成條件、agent 可以協助的事。

### A. 規劃

**A1 研究問題** — #3、#4
- 完成條件：使用者確認研究問題與 2–4 個子問題。
- Agent 協助：草擬子問題、檢查與納入條件是否一致。

**A2 納入／排除條件** — #5
- 完成條件：每條條件都能用「是／否」判斷；「開源」有明確定義。
- Agent 協助：把條件改寫成篩選時用的判斷規則與排除代碼。

**A3 Protocol 與註冊** — #24a–c
- 完成條件：`protocol/protocol.md` 定稿；已註冊於 OSF Registries，或決定不註冊並記錄理由。
- Agent 協助：依本檔內容起草 protocol。

### B. 檢索

**B1 資料庫檢索** — #6、#7
- 完成條件：每個資料庫的檢索式、日期、欄位、限制、筆數都記錄在下方「PRISMA 數字」。
- Agent 協助：檢查檢索式一致性、改寫成各資料庫語法、核對匯出檔筆數。
- 已知問題（2026-11-13 決定統一檢索式並重跑，新檢索式見 `protocol/protocol.md` 3.4；重跑後勾掉以下各項）：
  - [x] IEEE 檢索式多了 `LLM`、`Gemma`、`DeepSeek`、`open-source`、`discharge summaries`、`radiology reports`、`pathology reports`，其他三個資料庫沒有
  - [x] PubMed 缺 `LLM`、`Gemma`、`Phi`、`DeepSeek`、`open-weight`、`open-source`，未用 MeSH → 新檢索式已補齊並加入 MeSH（試跑 637 筆）
  - [x] Scopus 只有 10 筆，偏少；確認是否用 `TITLE-ABS-KEY()`、匯出是否完整
  - [x] ACM 633 筆，確認檢索欄位（全文 or 摘要）→ 初次結果大量離題（安全、法律、VR…），幾乎確定是全文檢索；正式檢索改用 Title／Abstract／Keyword
  - [x] `arXiv 2022-2026/` 資料夾為空，尚未匯出 → 改以 `scripts/search_arxiv.py` 執行（試跑 144 筆）

**B2 匯入與去重**
- 完成條件：`data/records_dedup.csv` 產生；去重前後筆數寫入「PRISMA 數字」。
- Agent 協助：寫 `scripts/` 下的腳本合併 `.bib`／`.ris`／`.csv`／`.txt`，以 DOI 與正規化標題去重，輸出篩選用表格。

### C. 篩選

**C1 標題／摘要篩選** — #8
- 完成條件：每筆都有 include／exclude 決定；分歧已解決；κ 已計算。
- Agent 協助：產生篩選表；可提供「建議」標記與理由，但**最終決定由使用者做**；計算 κ。

**C2 全文篩選** — #16a、#16b
- 完成條件：每篇排除文章都有排除代碼；最終納入篇數確定。
- Agent 協助：讀全文 PDF 對照納入條件給建議；彙整排除原因統計。

### D. 萃取與評估

**D1 資料萃取** — #9、#10a、#10b
- 欄位：作者／年份／國家／發表類型；病歷語言／類型／資料集／樣本數；任務與抽取目標；模型名稱／參數量／是否醫療領域模型；使用方式（zero-shot、few-shot、LoRA、全參數微調、RAG、量化）；部署與硬體；比較對象；指標與數值與評估層級；程式碼／資料公開、限制。
- 完成條件：每篇納入文章都萃取完成，並經使用者核對。
- Agent 協助：從 PDF 預先萃取並**標註出處頁碼**，由使用者核對。

**D2 偏倚風險／品質評估** — #11、#18
- 完成條件：工具已選定（改編 PROBAST／QUADAS-2 或依 TRIPOD-LLM 自訂）；每篇已評估。
- Agent 協助：設計評估表、預評並附理由。

### E. 綜合分析

**E1 綜合分析與圖表** — #12、#13a–f、#17、#19、#20a–d
- 預設做敘述性綜合（SWiM），除非指標夠一致可做統合分析。
- 圖表：年度趨勢、模型使用頻率、任務分布、開源 vs. 閉源、微調 vs. prompting。
- Agent 協助：寫分析與繪圖腳本、產生彙整表。

**E2 報告偏誤與確信度** — #14、#15、#21、#22
- Agent 協助：草擬 GRADE 評估或「不適用」的理由。

### F. 撰寫

**F1 PRISMA 流程圖** — 數字全部取自下方「PRISMA 數字」。
**F2 論文撰寫** — 依 PRISMA 2020 27 項與 PRISMA for Abstracts 撰寫。
**F3 投稿前檢查** — 填 PRISMA checklist 頁碼；確認流程圖、表格、內文數字一致；附錄放完整檢索式、萃取表、排除清單。

---

## PRISMA 數字

只填由檔案或腳本實際算出的數字。

| 資料庫 | 檢索日期 | 檢索欄位 | 限制 | 筆數 | 來源檔 |
|---|---|---|---|---|---|
| PubMed | 待確認 | [tiab] | 2022–2026 | 242 | `PubMed 2022-2026/csv-largelangu-set.csv` |
| Scopus | 2026-11-03 | 待確認 | 2022–2026 | 10 | `Scopus 2022-2026/export_*.csv` |
| ACM DL | 待確認 | 待確認 | 2022–2026 | 633 | `ACM 2022-2026/acm.bib` |
| IEEE Xplore | 2026-11-03 | All Metadata | 2022–2026 | 23 | `IEEE Xplore 2022-2026/export*.csv` |
| arXiv | | | | | `arXiv 2022-2026/`（空） |
| medRxiv（經 Europe PMC） | | | | | 尚未建立資料夾 |

試跑（2026-11-14，API，以 protocol 3.4 統一檢索式；非正式結果）：PubMed 637（涵蓋初次 PubMed 242 筆，遺漏 0）、arXiv 144、Europe PMC 預印本 147（其中 medRxiv 110）。驗證集 PubMed 收錄的 9/9 篇被檢出。來源：`searches/pilot_2026-11-14/*/search_log.json`。

初次檢索去重（`data/initial_2026-11-03/summary.json`）：908 → 移除 10 → 898；另有 4 組疑似重複（3 組為預印本 vs. 正式版，依規則不自動合併）。

**正式檢索（2026-11-14，protocol 3.4 統一檢索式；各來源 `searches/formal_2026-11-14/<db>/search_log.json`）**

| 資料庫 | 檢索日期 | 檢索欄位 | 限制 | 筆數 | 來源檔 |
|---|---|---|---|---|---|
| PubMed | 2026-11-14 | [tiab] + MeSH | 2022/01/01–2026/12/31 [dp] | 637 | `searches/formal_2026-11-14/pubmed/records.csv` |
| arXiv | 2026-11-14 | abs | submittedDate 2022–2026 | 144 | `searches/formal_2026-11-14/arxiv/records.csv`（同日 11:50 執行；12:40 後重跑遭 429 限流） |
| medRxiv（Europe PMC） | 2026-11-14 | TITLE_ABS | SRC:PPR, 2022–2026 | 110（預印本共 147） | `searches/formal_2026-11-14/europepmc/medrxiv_records.csv` |
| Scopus | 2026-11-14 | TITLE-ABS-KEY | PUBYEAR > 2021 | 970 | `searches/formal_2026-11-14/scopus/scopus_export_2026-11-14.csv` |
| IEEE Xplore | 2026-11-14 | All Metadata | 2022–2026 | 260 | `searches/formal_2026-11-14/ieee/export2026.11.13-23.45.39.csv` |
| ACM DL（Full-Text Collection） | 2026-11-14 | Title／Abstract／Keyword | 2022–2026 | 11 | `searches/formal_2026-11-14/acm/acm.bib` |

去重（`data/formal_2026-11-14/summary.json`）：2,132 → 移除 743 → **1,389**；疑似重複 83 組待人工確認。驗證集 10/10 檢出（`searches/formal_2026-11-14/validation_check.csv`）。正式結果涵蓋初次檢索的 IEEE 23/23、Scopus 10/10、PubMed 242/242。

> 上表為 2026-11-03 初次檢索。依 2026-11-13 決定，正式檢索將以 `protocol/protocol.md` 3.4 的統一檢索式重跑，屆時另列新表。

| 階段 | 筆數 |
|---|---|
| 去重前合計 | 2,132（正式檢索 2026-11-14；初次檢索為 908） |
| 移除重複 | 743（自動）；疑似重複 83 組待人工確認 |
| 標題／摘要篩選 | 1,389（待兩人篩選） |
| 標題／摘要排除 | |
| 全文取得失敗 | |
| 全文評估 | |
| 全文排除（依原因） | |
| 最終納入 | |
| Cohen's κ（C1／C2） | |

---

## 待決事項

- [x] 是否統一四個資料庫的檢索式並重跑？→ 統一並全部重跑
- [x] 「開源」定義 → 權重公開即可
- [x] 是否納入 arXiv／medRxiv 預印本？→ 納入，做敏感度分析
- [x] 語言限制 → 論文限英文，病歷語言不限
- [x] 篩選人數 → 兩人獨立
- [x] 是否註冊 OSF？→ 註冊於 OSF Registries
- [x] 子問題 RQ1–RQ4 是否採用？→ 全部採用
- [x] LLM 參數量門檻是否設 ≥ 1B？→ 設 ≥ 1B
- [x] 只用合成病歷的研究是否排除？→ 排除
- [x] 非抽取任務範圍 → 使用者授權 Agent 定案：摘要、QA、自動編碼、文件層級分類／預測皆排除（附判斷規則）
- [x] 偏倚風險工具 → 改編 QUADAS-2
- [x] 是否做前向引用追蹤？→ 做，前向＋後向皆用 OpenAlex API
- [ ] 第二位篩選者與仲裁者是誰？（protocol 3.5）
- [x] 檢索式驗證集 → Agent 挑選 10 篇，使用者 2026-11-14 確認（`data/validation_set.csv`）

---

## 決策紀錄

新的在下面。格式：`YYYY-MM-DD｜步驟｜決定｜理由`

- 2026-11-03（依 IEEE／Scopus 匯出檔名；PubMed、ACM 日期待確認）｜B1｜完成 PubMed、Scopus、ACM、IEEE 初次檢索，年份 2022–2026｜—
- 2026-11-13｜B1｜統一四個資料庫的檢索式並全部重跑；初次檢索匯出檔保留但不作為正式結果｜初次檢索式在各資料庫間詞彙與欄位不一致，影響可重現性（#7）。屬於與初次檢索的差異，需於 #24c 報告
- 2026-11-13｜A2｜「開源」定義為權重可公開下載，不要求 OSI 開放授權；授權類型列為萃取欄位｜涵蓋 Llama、Gemma 等主流模型，符合文獻中 open-weight 的常見用法
- 2026-11-13｜A2、B1｜納入 arXiv、medRxiv 預印本，並做排除預印本的敏感度分析；新增檢索 arXiv 與 medRxiv（經 Europe PMC）｜LLM 研究大量以預印本發表
- 2026-11-13｜A2｜論文限英文；病歷文本語言不限，列為萃取欄位｜檢索式為英文；非英語病歷是開源模型的重要應用場景
- 2026-11-13｜C1、C2｜標題／摘要與全文篩選皆由兩人獨立進行，分歧由第三人仲裁，計算 Cohen's κ｜PRISMA／Cochrane 標準做法
- 2026-11-13｜A3｜Protocol 註冊於 OSF Registries，於標題／摘要篩選開始前註冊｜接受方法學類回顧、可立即取得 DOI；PROSPERO 以健康結果為主，本題可能不符資格
- 2026-11-14｜A1｜子問題 RQ1–RQ4 全部採用｜—
- 2026-11-14｜A2｜LLM 定義加上參數量 ≥ 1B｜判斷明確、可重現；BERT 類與小型生成模型列為比較對象
- 2026-11-14｜A2｜只使用合成病歷的研究排除；合成＋真實者只萃取真實文本結果｜回顧焦點為真實臨床文本
- 2026-11-14｜A2｜X6 由使用者授權 Agent 定案：排除摘要、QA、ICD/SNOMED 自動編碼、文件層級分類／預測、病歷生成、對話；輸出為文本中明確記載之預先定義欄位值者仍屬抽取｜與 I3 定義一致，避免「分類」命名造成誤排
- 2026-11-14｜D2｜偏倚風險工具採改編 QUADAS-2 四領域並參照 TRIPOD-LLM｜無專用工具；QUADAS-2 適合「與參考標準比較」的評估研究
- 2026-11-14｜B1、C2｜以 OpenAlex API 對納入文章做前向與後向引用追蹤各一輪｜可腳本化、可重現
- 2026-11-14｜B1｜檢索式驗證集由使用者授權 Agent 從初次檢索紀錄挑選候選，使用者確認｜—
- 2026-11-14｜B1｜使用者確認驗證集 10 篇｜—
- 2026-11-14｜B1｜正式檢索由 Agent 執行：API 來源用腳本，Scopus／IEEE／ACM 由 Agent 以 Claude in Chrome 操作使用者瀏覽器｜使用者決定
- 2026-11-14｜B1｜六個來源於 2026-11-14 完成正式檢索（OSF 註冊之前；註冊仍在標題／摘要篩選開始前完成）｜使用者決定由 Agent 當日以 Chrome 代跑網頁資料庫。與 ROADMAP 原規劃「先註冊再檢索」順序不同，需於 #24c 與註冊表說明
- 2026-11-14｜B1｜arXiv 正式結果採用同日 11:50 的執行結果（與正式檢索式逐字相同、完整下載 144/144）｜同日稍後重跑遭 arXiv API 429 限流
- 2026-11-14｜B1｜IEEE 以單一 77 詞 Command Search 執行未拆分；ACM 使用 Full-Text Collection；Scopus 匯出欄名為中文，以 `scripts/scopus_header_en.py` 依欄位位置轉回英文欄名｜介面實際行為，見各 search_log.json
