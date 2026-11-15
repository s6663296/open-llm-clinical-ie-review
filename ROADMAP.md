# ROADMAP：開源 LLM 臨床病歷資訊抽取 — 系統性回顧

> 本檔是專案的**進度狀態檔**。Agent 每次開始工作先讀這裡，完成工作後回來更新。
> 報告規範：PRISMA 2020（https://www.prisma-statement.org/）。`#數字` = PRISMA 2020 checklist 項目編號。

---

## 📍 目前位置

- **階段**：課堂版 62 篇 Agent 審查完成、簡報已填入暫定結果（2026-11-15）；等作者定案範圍與核對萃取
- **步驟**：作者 ① 在 `extraction/scope_restriction.csv` 填 `author_decision`；② 核對 `extraction/extraction_scope62.xlsx`（至少 `agent_review` 為 fix／query 者，填 `verified`）；③ 決定 HANDOFF §7 列出的個別問題。之後重跑 `slide_figures.py`、`slide_prisma.py`，重新上傳圖並更新簡報數字。174 篇版 `extraction/extraction.xlsx` 與 `review_flags.csv` 15 篇仍待作者核對
- **專案性質（2026-11-14 改）**：課堂報告，產出為**簡報**、不投稿、不註冊 OSF；深度為「篩選完成＋部分欄位萃取（模型、任務、效能）」
- **進行中**：Sonnet 重篩全部 1,389 筆已完成（56/56 批，合併為 `screening/ai_screen_sonnet.csv`：include 264／unsure 327／exclude 798，`screening/ai_screen_sonnet_summary.json`）；複核表 `screening/step2_verify.xlsx` 已產生（依 AI include → unsure → exclude 排序）。50 筆校準樣本為 Agent 初判（`screening/step1_blind50.xlsx`：include 9／unsure 18／exclude 23），使用者已看過並採用，改以「兩個 AI 一致性＋人工核對」報告；與 Sonnet 的 11 筆分歧已由使用者裁定（`screening/step1_blind50_disagreements.xlsx`；9/11 與 Sonnet 相同）；50 筆最終判斷 `screening/calibration50_final.csv`：include 13／unsure 12／exclude 25。判斷指引存於 `scripts/agent_screening/screening_prompt.md`（前 39 批原始指引未存檔，此檔依 protocol 3.1–3.2 重建，需於論文揭露）
- **已完成**：protocol v0.2 定案、驗證集確認；六來源正式檢索（2026-11-14，2,132 筆）；去重 → 1,389 筆（`data/records_dedup.csv`）；驗證集 10/10 檢出；正式篩選表 `screening/title_abstract.xlsx`（1,389 筆、50 筆校準樣本、全部附 Agent 建議：include 205／unsure 421／exclude 763，僅供參考）；83 組疑似重複的判讀建議 `data/formal_2026-11-14/possible_duplicates_review.csv`（只有 EHRchitect 2 組需人工確認）；AI 建議 include／unsure 的 626 筆已先下載 OA 全文 298 篇（`fulltext/`，PDF 不進 git；取不到的 328 篇在 `fulltext/manual_retrieval.csv`，篩選後只對進全文階段者用機構權限逐篇取得）；PRISMA 流程圖（識別段）`figures/prisma_flow.*`；全部腳本與稿件 Methods／引言草稿
- **C1 完成（2026-11-14）**：雙 AI（Sonnet、Opus）獨立篩選 1,389 筆，二元 κ = 0.90；一致排除 759、一致進全文 511、分歧 69 筆由使用者裁定（53 排除／16 進全文）、校準 50 筆由使用者決定。最終排除 837、進全文 **552**（include 249／unsure 303）。結果 `screening/title_abstract_final.xlsx`／`.csv`，進全文清單 `screening/to_full_text.csv`；`screening/step2_verify.xlsx` 已被雙 AI 流程取代，不使用
- **C2 AI 篩選（2026-11-14）**：277 篇取得全文（`fulltext_text/`，`scripts/pdf_to_text.py --condensed`；R0861、R1214、R1331 原下載檔為錯誤文件，改以 `scripts/pmc_xml_to_text.py` 取 Europe PMC 全文；R0891 無正確 OA 版，記為未取得）。Sonnet 判全部 277 篇（`screening/ft_sonnet/`），Opus 獨立複查 Sonnet 排除的 75 篇（`screening/ft_opus/`，73 篇同意排除）。同一研究多版本 33 組依 protocol 3.5 以同儕審查版為主、預印本給 X8（已因 X1–X7 排除者保留原代碼）。合併：`scripts/agent_screening/merge_ft.py` → `screening/ft_ai_merged.csv`（AI：include 173／exclude 102／分歧 2；`screening/ft_ai_merged_summary.json`）
- **C2 完成（2026-11-14）**：分歧 11 列由使用者授權 Agent 裁定（`screening/step4_ft_disagreements.xlsx` my_* 欄，理由逐列記錄）；`scripts/agent_screening/finalize_ft.py` → `screening/full_text.xlsx`／`.csv`。全文評估 277：納入 **174**、排除 103（X4 28、X8 27、X6 21、X3 13、X5 10、X7 3、X1 1）；未取得 275。PRISMA 數字 `analysis/prisma_counts.json`、流程圖 `figures/prisma_flow.*` 已更新
- **D1 準備完成（2026-11-14）**：174 篇編號 S001–S174（`extraction/study_ids.csv`，依 record_id 排序），分 7 批（`extraction/batches/batch_01–07.list`，每批 ≤ 25）。全文以 `scripts/extraction/restore_fulltext.py` 依 C2 下載紀錄重新取得並核對 sha256，轉成完整（非精簡）頁碼文字 `fulltext_text_ft/`（不進 git），紀錄 `extraction/fulltext_restore_log.csv`：174/174 取得（sha256 相符 142；medRxiv 等伺服器重產 PDF 致 sha256 不同但標題相符 17、標題為預印本版經 Agent 人工確認同一研究 14〔`extraction/fulltext_manual_checks.csv`〕；R0382 OA 檔僅為 AJR 中文翻譯摘要，只能從摘要萃取，待作者決定）。萃取文字中 105 篇為預印本版（`extraction/study_ids.csv` 的 `text_version`），與 C2 篩選所用版本相同；簡報須說明數值部分來自預印本版。萃取指引 `extraction/d1_codex_brief.md`（欄位子集見 `scripts/extraction/fields.py`），驗證 `scripts/extraction/check_batch.py`（數值須出現在所標頁碼），合併 `scripts/extraction/merge.py` → `extraction/extraction_scope62.xlsx`
- **D1 流程**：
  1. Codex 依 `extraction/d1_codex_brief.md` 逐批產出 `extraction/codex/batch_NN_studies.csv`、`batch_NN_results.csv`，`check_batch.py` 錯誤為 0 才算完成
  2. `merge.py` 合併成 `extraction/extraction_scope62.xlsx`（重跑不會覆蓋審查欄）
  3. Agent 審查：每篇核對開源模型清單與 `is_best_open` 列的數值／出處，處理 `QUERY:` 與 WARN，填 `agent_review`（ok／fix／query）與 `agent_note`
  4. 作者核對：至少看 `agent_review` 為 fix／query 者與各篇最佳開源結果，填 `verified`；`QUERY:` 中疑似誤納入者由作者決定是否排除（排除則更新 PRISMA 數字）
  5. E1：以 `results` 工作表做模型、任務、開源 vs 閉源等彙整圖表
- **課堂版範圍收緊（2026-11-14）**：174 篇再限「同儕審查（R1）＋同一研究內與閉源 LLM 直接比較（R2）」，目標約 40 篇。`scripts/extraction/restrict_scope.py` → `extraction/scope_restriction.csv`：建議 keep 30、check 32、exclude 112（R1 預印本 51；R2 全文未提閉源 27、只順帶提及 34）。只對 keep＋check 62 篇萃取（`extraction/batches/` 13 批、每批 ≤ 5 篇，`make_batches.py --scope`），萃取時確認 R2；作者於 `author_decision` 欄定案後，最終數字與 PRISMA 加一層「課堂版收緊條件排除」
- **簡報骨架（2026-11-14）**：31 張、30–40 分鐘，Slides artifact https://claude.ai/artifact/9PFD1Di4iUAFgQjnoJqn5A ，原始檔 `slides/project/`（deck.json、deck.css、slides/*.html）。已填入的數字只取自 `analysis/prisma_counts.json`；結果頁皆為圖表佔位框（標明圖型與資料欄位），`[__]` 待萃取與 E1 腳本產生後填入
- **課堂版 62 篇萃取（2026-11-15）**：Codex 13 批全部通過 `check_batch.py`（修正檢查器兩個誤判：表格相鄰數字邊界、引文結尾連字號；Codex 非逐字引文以 `scripts/extraction/fix_context.py` 換成原文行，數值不變，記錄於 `extraction/review/agent_edits.csv`）。batch 01 已審查（`extraction/review/agent_review.csv`：ok 2、fix 2、query 1）。正文無開源 LLM 數值、標 QUERY 待作者判斷：S022（只有圖）、S118、S119、S164、S173
- **兩套萃取並存**：174 篇 AI 預填（`scripts/agent_extraction/`、`extraction/ai_batches/`、`extraction/extraction.xlsx`）與課堂版 62 篇（`scripts/extraction/`、`extraction/codex/`、`extraction/extraction_scope62.xlsx`），可交叉核對
- **課堂版審查與簡報（2026-11-15）**：Agent 審查 62 篇（`extraction/review/agent_review.csv`：ok 24／fix 8／query 30）；修正以 `scripts/extraction/agent_patch.py` 套用（S043、S077、S100、S108、S135、S170，紀錄 `agent_edits.csv`），13 批再通過檢查。`merge.py` → `extraction/extraction_scope62.xlsx`（62 篇、472 列）。暫定範圍（author_decision 空白）38 篇，其中 36 篇有開源 vs 閉源配對、88 組任務比較：研究層級開源追平或較好 18／閉源領先 18（差距中位數 0.022）；任務層級 36／52（中位數 0.036）；微調組中位數 0.012（19 組）、提示組 0.059（69 組）（`analysis/slide_numbers.json`）。簡報 31 張已填入並發布，數字標「暫定」；圖對照 `slides/assets.json`
- **下一步**：① 作者定案 `author_decision`、核對萃取、裁定 HANDOFF §7 問題；② 重跑出圖並更新簡報；③ `figures/prisma_flow.*`（完整版）加課堂版一層（簡報用 `figures/slides/prisma_slide.png` 已含）
- **D1 AI 預填（2026-11-15）**：174 篇以完整全文（`fulltext_text_full/`，`pdf_to_text.py --cap 200000`；R0861、R1214、R1331 用 Europe PMC XML）萃取。指引 `scripts/agent_extraction/extraction_prompt.md`；18 批（每批 10 篇），Codex 完成 11 批後用量用盡，其餘 7 批由 Claude Sonnet 子代理完成；10 篇全文為同一研究的預印本／舊版（`title_match=version`）另批重萃取。每批皆通過 `scripts/agent_extraction/check_batch.py`（引句逐字、數值出現在引句、頁碼）。合併 `scripts/agent_extraction/merge_batches.py` → `extraction/extraction.xlsx`（＋`studies.csv`／`results.csv`）：174 研究、472 個結果列；13 篇最佳開源 LLM 數值只在圖或補充資料（value=NR）。Agent 抽查 8 筆數值與原文表格對應皆正確。需作者判斷的 15 篇列於 `extraction/review_flags.csv`（多為疑似 X6 文件層級分類、2 篇 GatorTron 系列權重是否公開）
- **E1 草稿**：`scripts/analyze.py --include-unverified` 已產生 `analysis/*_UNVERIFIED.csv`、`figures/fig_*_UNVERIFIED.*`（未核對，僅供預覽；核對後去掉該旗標重跑）
- **174 篇下一步**：作者核對萃取 → 重跑 `analyze.py`
- **A3 狀態**：課堂版 protocol v0.5 已整理方法、經費與利益衝突資訊及三篇背景文獻；作者分工為使用者要求的隨機提議，實際貢獻待完成後確認。未事先註冊。
- **卡住／待使用者決定**：見下方「待決事項」

---

## 進度總覽

狀態：✅ 完成　🔄 進行中　⬜ 未開始　⏸ 暫緩

| 代號 | 步驟 | 狀態 | 產出 |
|---|---|---|---|
| A1 | 研究問題（PICO） | ✅ | 本檔「研究定義」；子問題草案在 `protocol/protocol.md` 2.2 |
| A2 | 納入／排除條件 | ✅ | 本檔「研究定義」；判斷規則與排除代碼在 `protocol/protocol.md` 3.1–3.2 |
| A3 | Protocol（不註冊） | ✅ 課堂版完成；實際作者貢獻待結案確認 | `protocol/protocol.md` |
| B1 | 資料庫檢索 | ✅ | `<資料庫> 2022-2026/`、`搜尋條件.docx` |
| B2 | 匯入與去重 | ✅ | `data/records_dedup.csv` |
| C1 | 標題／摘要篩選 | ✅ | `screening/title_abstract_final.xlsx` |
| C2 | 全文篩選 | ✅ | `screening/full_text.xlsx` |
| D1 | 資料萃取（部分欄位：模型、任務、效能） | 🔄 174 篇 AI 預填待作者核對；課堂版 62 篇 Agent 審查完成、待作者核對 | `extraction/extraction.xlsx`（174）、`extraction/extraction_scope62.xlsx`（62） |
| D2 | 偏倚風險／品質評估 | ⏸ 課堂版不做 | `extraction/risk_of_bias.xlsx` |
| E1 | 綜合分析與圖表 | 🔄 課堂版圖表已產生（暫定範圍） | `analysis/`、`figures/` |
| E2 | 報告偏誤與確信度 | ⏸ 課堂版不做 | `analysis/certainty.md` |
| F1 | PRISMA 流程圖 | 🔄 簡報版含課堂版一層（暫定） | `figures/prisma_flow.*` |
| F2 | 簡報製作（原為論文撰寫） | 🔄 31 張已填入暫定數字 | `slides/`（既有 `manuscript/` 草稿供取材） |
| F3 | 投稿前檢查 | ⏸ 不投稿 | `manuscript/prisma_checklist.*` |

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
| 移除重複 | 743（自動）；疑似重複 83 組皆判定非重複（81 組為同一研究不同版本，連結處理；EHRchitect 2 組為原文＋勘誤），篩選筆數維持 1,389 |
| 標題／摘要篩選 | 1,389 |
| 標題／摘要排除 | 837（X1 209、X2 4、X3 143、X4 166、X5 104、X6 191、X7 20）；進全文 552 |
| 全文取得失敗 | 275（無 OA 版本 169；出版商拒絕自動下載 403／404 105；OA 檔為錯誤論文且無正確 OA 版 1〔R0891〕；依決定不以機構權限補取）（`screening/ft_ai_merged.csv`） |
| 全文評估 | 277 |
| 全文排除（依原因） | 103：X4 28、X8 27、X6 21、X3 13、X5 10、X7 3、X1 1（`screening/full_text.xlsx`） |
| 最終納入 | 174 篇報告＝174 篇研究（同一研究的其他版本已以 X8 排除） |
| 課堂版收緊（暫定，作者未定案） | 174 → 38：排除預印本 51、無閉源直接比較 85（`analysis/slide_numbers.json`） |
| Cohen's κ（C1／C2） | C1 全部 1,389 筆，Sonnet vs Opus：二元 0.90、三類 0.87（`analysis/sonnet_vs_opus.json`）；分歧 69 筆作者裁定。校準 50 筆，**兩個 AI 篩選者**（Agent 初判 vs Sonnet）：三類 0.66、二元 0.72（`analysis/blind50_agent_vs_sonnet.json`）；非人工盲測，不報告人工 κ／AI 敏感度 |

---

## 待決事項

- [x] 是否統一四個資料庫的檢索式並重跑？→ 統一並全部重跑
- [x] 「開源」定義 → 權重公開即可
- [x] 是否納入 arXiv／medRxiv 預印本？→ 納入，做敏感度分析
- [x] 語言限制 → 論文限英文，病歷語言不限
- [x] 篩選人數 → 兩人獨立
- [x] 是否註冊 OSF？→ 註冊於 OSF Registries（2026-11-14 改為不註冊：課堂報告）
- [x] 子問題 RQ1–RQ4 是否採用？→ 全部採用
- [x] LLM 參數量門檻是否設 ≥ 1B？→ 設 ≥ 1B
- [x] 只用合成病歷的研究是否排除？→ 排除
- [x] 非抽取任務範圍 → 使用者授權 Agent 定案：摘要、QA、自動編碼、文件層級分類／預測皆排除（附判斷規則）
- [x] 偏倚風險工具 → 改編 QUADAS-2
- [x] 是否做前向引用追蹤？→ 做，前向＋後向皆用 OpenAlex API
- [x] 標題／摘要篩選方式 → LLM 篩選＋一位人工複核（2026-11-14）
- [x] 前向／後向引用追蹤：課堂版是否仍要做？→ 2026-11-14 暫不做（保留日後補做）
- [x] 全文篩選方式 → 2026-11-14 定案：AI 讀重點段落；Sonnet 判全部、Opus 複查排除，分歧由作者裁定（protocol 3.5）
- [x] 檢索式驗證集 → Agent 挑選 10 篇，使用者 2026-11-14 確認（`data/validation_set.csv`）
- [ ] 課堂版收緊範圍逐篇定案：`extraction/scope_restriction.csv` 的 `author_decision`（keep／exclude），check 32 篇可待萃取確認 R2 後再決定
- [ ] R0382（AJR 胰臟囊性病變，Rasromani 等）只取得中文翻譯摘要、無全文：只用摘要萃取並標註，或改記為「全文未取得」排除？（Agent 建議：保留並只萃取摘要數值，簡報註明；若排除，納入數改為 173）

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
- 2026-11-14｜C2｜全文取得：開放取用 PDF 先以腳本下載；機構訂閱 PDF 於人工篩選後，只對進入全文階段者以使用者機構登入逐篇低速取得｜避免批量下載違反出版商授權
- 2026-11-14｜C1｜標題／摘要篩選改為 LLM（Claude Sonnet）篩選全部紀錄，一位人工逐筆複核；另以 50 筆盲測樣本計算人工與 AI 的 κ 與敏感度；人工修正率入結果｜使用者決定（人力限制）。屬 protocol 修訂（OSF 註冊前），於 #8、#23c、#24c 揭露
- 2026-11-14｜C1｜使用者決定以單人作業延續既有流程（Sonnet 篩選＋50 筆盲測＋一人逐筆複核）；評估過的雙人／三人與雙 AI 方案暫不採用｜使用者希望人工時間不要太多；全文篩選方式仍待決
- 2026-11-14｜C1｜Sonnet 補跑剩餘 17 批，全部 1,389 筆完成；判斷指引存檔為 `scripts/agent_screening/screening_prompt.md`｜前 39 批原始指引未存檔，依 protocol 3.1–3.2 重建，需於 #8／#24c 揭露
- 2026-11-14｜A3、F｜專案改為課堂報告：產出簡報、不投稿、不註冊 OSF；做到篩選完成＋部分欄位萃取（模型、任務、效能）；偏倚風險、確信度、投稿前檢查暫緩｜使用者決定（課堂報告）。簡報中說明「未事先註冊」
- 2026-11-14｜B2｜EHRchitect 2 組疑似重複判定為「原文＋勘誤」，非重複，兩筆皆保留由篩選排除；B2 完成，篩選筆數維持 1,389｜使用者決定。勘誤是另一份出版物，非同一紀錄重複收錄
- 2026-11-14｜C1｜50 筆校準樣本實為 Agent 初判（非人工盲測）；使用者看過並採用。報告方式改為「兩個 AI 篩選者一致性（Agent vs Sonnet，二元 κ 0.72）＋作者逐筆核對、報告人工修正率」，不報告人工 κ 與 AI 敏感度｜使用者決定；如實揭露，不將 AI 初判表述為人工盲測。屬 protocol 3.5 第 2 步之變更
- 2026-11-14｜C1｜校準 50 筆完成：39 筆兩個 AI 一致、作者採用；11 筆分歧由作者裁定（9 筆同 Sonnet、2 筆同 Agent）。最終 include 13／unsure 12／exclude 25｜使用者決定
- 2026-11-14｜C1｜使用者請 Agent 以 Claude Opus 獨立複審全部紀錄（取代逐筆人工複核）；兩個 AI 一致者採用，分歧由使用者裁定｜使用者希望減少人工時間。報告為「雙 AI 獨立篩選＋作者裁定分歧」，不得表述為人工逐筆複核
- 2026-11-14｜C1｜使用者裁定 69 筆雙 AI 分歧（53 排除、16 進全文；44 筆未填代碼者經使用者確認採排除方 AI 之代碼）；C1 完成：排除 837、進全文 552｜使用者決定
- 2026-11-14｜C2｜全文篩選：AI 只讀重點段落（摘要、方法、結果）；Sonnet 判全部，Opus 獨立複查 Sonnet 判排除者，分歧由使用者裁定；誤納入者於萃取階段再檢出。指引 `scripts/agent_screening/fulltext_prompt.md`｜使用者決定（降低 AI 用量與人工時間）
- 2026-11-14｜C2｜開放取用以外無法取得的全文，不以機構權限補取，記為 PRISMA「Reports not retrieved」｜使用者決定（課堂報告、人力限制）
- 2026-11-14｜B1、C2｜前向／後向引用追蹤暫不做，日後視需要補做｜使用者決定（課堂版、尚不確定是否需要）。屬與原決定之差異，簡報方法段註明「未做引用追蹤」
- 2026-11-14｜C2｜使用者決定 C2 依原流程完成（Sonnet 判全部、Opus 複查排除、作者裁定分歧）；D1 萃取改由 Codex 預填、Agent 審查、作者核對｜節省 Claude 用量
- 2026-11-14｜C2｜Agent 處理：OA 下載檔為錯誤文件者（附錄、他篇論文、舊版預印本）改取 Europe PMC 正式版全文（R0861、R1214、R1331），取不到者記為未取得（R0891）；同一 PDF 對應兩筆紀錄的 33 組依 protocol 3.5 處理｜依既有規則執行，非方法變更；簡報可說明全文來源
- 2026-11-14｜C2｜使用者授權 Agent 裁定全文篩選分歧 11 列（2 篇雙 AI 分歧、2 組同一全文判斷相反、6 篇排除代碼不同）：R1363 納入，其餘排除（章節辨識、住院層級 IHCA 判定屬 X6；代碼不同者取確定成立且順序在前的代碼）；C2 完成：納入 174、排除 103、未取得 275｜使用者決定授權。簡報須說明分歧由 Agent 裁定、非作者逐筆裁定
- 2026-11-14｜D1｜使用者授權 Agent 自行規劃 D1：課堂版欄位子集（模型、任務、效能，另保留語言、文本類型、資料集、比較對象、策略、部署）；數值選取依 protocol 3.7（F1 優先、整體值、每模型最佳設定＋各類最佳比較對象）；新增 `value_reported` 欄由腳本對頁驗證；不從圖讀值、不萃取補充資料；疑似誤納入者標 `QUERY:` 由作者裁定｜減少萃取量、讓 Codex 預填可機器驗證。屬 codebook 修訂（見 `extraction/codebook.md` 修訂紀錄），簡報方法段說明萃取由 AI 預填、Agent 審查、作者核對
- 2026-11-14｜A2、D1｜課堂版事後收緊納入條件：174 篇再限同儕審查（排除預印本）且同一研究內有開源與閉源 LLM 的直接效能比較，目標約 40 篇；PRISMA 加一層排除並於簡報限制頁說明｜使用者決定（30–40 分鐘報告，聚焦 RQ3）。屬與 protocol 之差異，原 174 篇結果保留
- 2026-11-14｜F2｜簡報以 Slides artifact 製作，骨架 31 張（背景、方法、結果概覽、RQ1–RQ3、討論）；圖表留佔位待 E1 產生｜使用者請 Agent 先架骨架
- 2026-11-14｜A3｜使用者確認無專案經費、無贊助、無需揭露的利益衝突；採用三篇已查證的既有回顧，並要求隨機分配作者工作｜課堂報告；隨機分配僅為提議，實際貢獻於結案時確認。
- 2026-11-15｜D1｜萃取改用完整全文（非篩選用精簡版）；欄位依課堂版範圍精簡為模型、任務、效能（`scripts/agent_extraction/extraction_prompt.md`）；Codex 用量用盡後其餘批次改由 Claude Sonnet 預填；全文為同一研究其他版本者照常萃取並標 `version`；文字檔未載年份者採書目年份｜Pilot 發現精簡版全文缺結果表；依既有「Codex 額度用盡改用 Sonnet」做法。簡報方法段說明「AI 預填（Codex＋Claude Sonnet）＋作者核對」
- 2026-11-15｜D1｜兩套萃取並存：174 篇 AI 預填（`extraction/extraction.xlsx`）與課堂版 62 篇 Codex 萃取（`extraction/extraction_scope62.xlsx`）皆保留｜使用者決定（遠端與本地平行完成兩套，保留可交叉核對）
- 2026-11-15｜D1｜使用者請 Agent 審查課堂版 batch 02–13 並修正萃取：Agent 以 `agent_patch.py` 記錄修正（更正最佳模型、補漏列、刪除非臨床文本 BC5CDR 列），補列標 `extractor=agent`，檢查器改為接受｜依既有「Agent 審查、作者核對」流程；所有改動逐筆記錄可回溯
- 2026-11-15｜E1｜RQ3 主圖改為研究層級（每篇取各任務比較的中位數），任務層級分布另列｜Agent 判斷：一篇最多貢獻 13 組比較，任務層級會讓少數研究主導結果。屬分析呈現方式之補充，非方法變更；兩種數字都在 `slide_numbers.json`
