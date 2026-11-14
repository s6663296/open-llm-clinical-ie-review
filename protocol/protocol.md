# Protocol：開源 LLM 用於臨床病歷資訊抽取 — 系統性回顧

> 依 **PRISMA-P 2015** 架構撰寫（Moher et al., Syst Rev 2015;4:1）。
> 狀態：**草案 v0.2（2026-11-14）**，尚未註冊。
> 標記 `【提議】` 的段落是起草時代為擬定、使用者尚未確認的內容；標記 `【待填】` 的是只有使用者能提供的資訊。

---

## 1. 行政資訊

### 1.1 標題（PRISMA-P #1）
Open-source large language models for information extraction from clinical free text: a systematic review protocol
（開源大型語言模型用於臨床自由文本資訊抽取：系統性回顧 protocol）

### 1.2 註冊（#2）
- 註冊處：OSF Registries（範本：Generalized Systematic Review Registration）
- 註冊編號／DOI：`【待填：註冊後填入】`
- 註冊時點：資料庫初次檢索已完成（2026-11-03），**標題／摘要篩選尚未開始**。註冊表中會如實說明這一點。

### 1.3 作者與貢獻（#3a、#3b）
- `【待填：作者姓名、單位、email、ORCID】`
- 通訊作者（protocol 負責人）：`【待填】`
- 貢獻（CRediT）：`【待填：構思、檢索、篩選者 1、篩選者 2、仲裁者、萃取、分析、撰寫】`

### 1.4 修訂（#4）
本 protocol 註冊後若有任何修改，記錄於本檔第 8 節「修訂紀錄」與 `ROADMAP.md` 決策紀錄，並於論文中依 PRISMA 2020 #24c 報告。

### 1.5 經費與利益衝突（#5a–c）
- 經費來源：`【待填，若無請寫「無」】`
- 贊助者角色：`【待填】`
- 利益衝突：`【待填】`

---

## 2. 前言

### 2.1 研究背景（#6）
臨床資訊大量存在於自由文本（病歷、出院摘要、影像與病理報告），把這些內容轉成結構化資料是臨床研究、品質監測與決策支援的前提。大型語言模型（LLM）在資訊抽取上展現出不需大量標註即可運作的能力，但商用閉源模型（如 GPT-4）需要把病歷送到外部伺服器，涉及隱私法規、成本與可重現性問題。開源／開放權重模型可在院內部署，是解決這些問題的主要選項。

`【待填：補上 2–3 篇既有回顧並說明本回顧與它們的差異 — 例如既有回顧未聚焦開源模型、未涵蓋 2024 年後的模型世代、或未系統比較 prompting 與微調。請由使用者提供實際文獻，Agent 不代為引用未經核實的文獻。】`

### 2.2 目的（#7）
主要問題：開源／開放權重 LLM 在臨床自由文本資訊抽取任務上的使用方式與效能為何？

子問題（2026-11-14 確認）：
- **RQ1 使用現況**：哪些開源 LLM（家族、參數量、是否醫療領域模型）被用於哪些抽取任務、文本類型與病歷語言？隨年份如何變化？
- **RQ2 適配策略**：研究採用哪些策略（zero-shot、few-shot、LoRA／QLoRA、全參數微調、RAG、量化），不同策略的效能差異為何？
- **RQ3 相對效能**：在同一研究、同一資料集上，開源 LLM 與閉源 LLM、BERT 類模型、規則式方法相比的效能如何？
- **RQ4 部署與可重現性**：研究是否在本地端部署、使用什麼硬體、是否公開程式碼／資料／prompt？

PICO：

| | 內容 |
|---|---|
| P | 臨床自由文本：病歷、出院摘要、病程紀錄、影像報告、病理報告等 |
| I | 開源／開放權重 LLM |
| C | 閉源 LLM、BERT 類模型、規則式方法、人工標註（若有） |
| O | 抽取效能（F1、precision、recall、accuracy 等） |

---

## 3. 方法

### 3.1 納入條件（#8）

每一條都必須能以「是／否」判斷。全部為「是」才納入。

| # | 條件 | 操作定義 |
|---|---|---|
| I1 | 使用至少一個開源 LLM | **LLM**：以 transformer 為基礎的生成式預訓練語言模型（decoder-only 或 encoder-decoder），**參數量 ≥ 1B**（排除 BERT 類與小型 T5／BioGPT 等；這些模型若出現，列為比較對象）。研究未報告參數量時，依模型官方說明判斷。**開源**：模型權重可公開下載（不論授權是否為 OSI 認可，例如 Llama、Gemma 社群授權也算）。授權類型另作萃取欄位。 |
| I2 | 輸入為臨床自由文本 | 來自真實病患照護過程的文本，含去識別化公開資料集（如 MIMIC、n2c2／i2b2）。**僅使用合成病歷文本的研究排除**；同時用合成與真實文本者納入，只萃取真實文本的結果。 |
| I3 | 任務為資訊抽取 | 從文本中辨識並輸出特定實體、關係或預先定義欄位的值。包括：NER、關係抽取、屬性／否定判斷、結構化欄位抽取（例如從病理報告抽出腫瘤分期）。 |
| I4 | 有量化評估 | 以參考標準（人工標註或既有結構化資料）報告至少一項效能指標。 |
| I5 | 發表期間 | 2022-01-01 至最終檢索日。 |
| I6 | 發表類型 | 期刊論文、完整會議論文、預印本（arXiv、medRxiv）。 |
| I7 | 論文語言 | 英文。**病歷文本語言不限**，並萃取為欄位。 |

### 3.2 排除條件與排除代碼

篩選時每篇排除文章給一個代碼（依下列順序，取第一個符合者）。

| 代碼 | 排除原因 |
|---|---|
| X1 | 發表類型不符：回顧、社論、評論、摘要僅有（conference abstract）、論文集導言、無全文 |
| X2 | 非英文論文 |
| X3 | 未使用 LLM（只用 BERT 類、傳統 ML、規則式） |
| X4 | 只使用閉源 LLM |
| X5 | 非臨床自由文本（例如生醫文獻、社群媒體、病患問卷、僅合成文本） |
| X6 | 非資訊抽取任務：摘要生成、問答（QA）、ICD／SNOMED 等自動編碼、文件層級分類或預測（如診斷預測、表型分類、預後預測）、病歷生成、對話。**判斷規則**：輸出是文本中明確記載的預先定義欄位值（如吸菸狀態、腫瘤分期、藥物劑量）→ 屬抽取，即使論文稱為「分類」；輸出需要超出文本內容的推論或為整份文件指派代碼 → X6 |
| X7 | 無量化評估 |
| X8 | 重複報告（同一研究的另一版本；見 3.5） |

### 3.3 資訊來源（#9）

| 來源 | 涵蓋 | 介面 |
|---|---|---|
| PubMed／MEDLINE | 生醫期刊 | pubmed.ncbi.nlm.nih.gov |
| Scopus | 跨領域期刊與會議 | scopus.com |
| IEEE Xplore | 電機／資訊期刊與會議 | ieeexplore.ieee.org |
| ACM Digital Library | 資訊領域期刊與會議 | dl.acm.org |
| arXiv | 資訊領域預印本 | arxiv.org（建議用 API，可重跑） |
| medRxiv | 醫學預印本 | 經 Europe PMC 檢索（medRxiv 原生介面不支援巢狀布林） |

補充來源：以 OpenAlex API 對所有納入文章做**後向**（參考文獻）與**前向**（被引用）引用追蹤，各執行一輪；以腳本執行（`scripts/`），記錄執行日期與筆數。追蹤到的紀錄與資料庫紀錄去重後，依相同標準兩人獨立篩選，並在 PRISMA 流程圖「其他方法」欄位報告。

所有資料庫在**同一天**完成正式檢索，檢索日記錄於 `ROADMAP.md`「PRISMA 數字」。

### 3.4 檢索策略（#10）

#### 3.4.1 概念區塊

檢索式 = 區塊 A（LLM）AND 區塊 B（臨床文本）AND 區塊 C（資訊抽取），限制 2022 年以後。檢索欄位統一為**標題＋摘要＋關鍵字**（IEEE 為 All Metadata）。

區塊 A 不要求出現「open-source」字樣，因為許多同時比較 GPT-4 與 Llama 的研究在摘要只寫「LLM」；是否為開源模型留到篩選階段判斷。

| 區塊 | 詞彙 |
|---|---|
| A. LLM | large language model*, large-language model*, LLM, LLMs, foundation model*, generative pre-trained, open-source, open source, open-weight*, Llama, Llama2, Llama3, Mistral, Mixtral, Qwen*, Gemma, DeepSeek, Phi-3, Phi-4, Vicuna, Falcon, BioMistral, Meditron, MedAlpaca, PMC-LLaMA, Clinical Camel |
| B. 臨床文本 | clinical note*, clinical text*, clinical narrative*, clinical document*, clinical report*, medical record*, health record*, EHR, EHRs, EMR, EMRs, discharge summar*, discharge letter*, progress note*, operative note*, operative report*, radiology report*, pathology report* |
| C. 資訊抽取 | information extraction, named entity recognition, NER, relation extraction, relationship extraction, entity extraction, concept extraction, data extraction, data abstraction, chart abstraction, structured data, structured information, structured output*, text mining |

#### 3.4.2 PubMed

```
("large language model*"[tiab] OR "large-language model*"[tiab] OR LLM[tiab] OR LLMs[tiab]
 OR "foundation model*"[tiab] OR "generative pre-trained"[tiab] OR "open-source"[tiab]
 OR "open source"[tiab] OR "open-weight*"[tiab] OR Llama[tiab] OR Llama2[tiab] OR Llama3[tiab]
 OR Mistral[tiab] OR Mixtral[tiab] OR Qwen*[tiab] OR Gemma[tiab] OR DeepSeek[tiab]
 OR "Phi-3"[tiab] OR "Phi-4"[tiab] OR Vicuna[tiab] OR Falcon[tiab] OR BioMistral[tiab]
 OR Meditron[tiab] OR MedAlpaca[tiab] OR "PMC-LLaMA"[tiab] OR "Clinical Camel"[tiab]
 OR "Large Language Models"[Mesh])
AND
("clinical note*"[tiab] OR "clinical text*"[tiab] OR "clinical narrative*"[tiab]
 OR "clinical document*"[tiab] OR "clinical report*"[tiab] OR "medical record*"[tiab]
 OR "health record*"[tiab] OR EHR[tiab] OR EHRs[tiab] OR EMR[tiab] OR EMRs[tiab]
 OR "discharge summar*"[tiab] OR "discharge letter*"[tiab] OR "progress note*"[tiab]
 OR "operative note*"[tiab] OR "operative report*"[tiab] OR "radiology report*"[tiab]
 OR "pathology report*"[tiab] OR "Electronic Health Records"[Mesh] OR "Medical Records"[Mesh])
AND
("information extraction"[tiab] OR "named entity recognition"[tiab] OR NER[tiab]
 OR "relation extraction"[tiab] OR "relationship extraction"[tiab] OR "entity extraction"[tiab]
 OR "concept extraction"[tiab] OR "data extraction"[tiab] OR "data abstraction"[tiab]
 OR "chart abstraction"[tiab] OR "structured data"[tiab] OR "structured information"[tiab]
 OR "structured output*"[tiab] OR "text mining"[tiab])
AND ("2022/01/01"[dp] : "2026/12/31"[dp])
```
> 試跑時請在 MeSH Database 確認 `"Large Language Models"[Mesh]` 存在；不存在就刪掉這一項。

#### 3.4.3 Scopus

```
TITLE-ABS-KEY(
  ("large language model*" OR "large-language model*" OR LLM OR LLMs OR "foundation model*"
   OR "generative pre-trained" OR "open-source" OR "open source" OR "open-weight*" OR Llama
   OR Llama2 OR Llama3 OR Mistral OR Mixtral OR Qwen* OR Gemma OR DeepSeek OR "Phi-3" OR "Phi-4"
   OR Vicuna OR Falcon OR BioMistral OR Meditron OR MedAlpaca OR "PMC-LLaMA" OR "Clinical Camel")
  AND
  ("clinical note*" OR "clinical text*" OR "clinical narrative*" OR "clinical document*"
   OR "clinical report*" OR "medical record*" OR "health record*" OR EHR OR EHRs OR EMR OR EMRs
   OR "discharge summar*" OR "discharge letter*" OR "progress note*" OR "operative note*"
   OR "operative report*" OR "radiology report*" OR "pathology report*")
  AND
  ("information extraction" OR "named entity recognition" OR NER OR "relation extraction"
   OR "relationship extraction" OR "entity extraction" OR "concept extraction" OR "data extraction"
   OR "data abstraction" OR "chart abstraction" OR "structured data" OR "structured information"
   OR "structured output*" OR "text mining")
) AND PUBYEAR > 2021
```
> 初次檢索只有 10 筆，很可能沒用 `TITLE-ABS-KEY()`，或檢索在 Basic search 的單一欄位。請用 Advanced document search 貼上整段。

#### 3.4.4 IEEE Xplore（Command Search）

三個區塊的詞彙同上，每個詞前加 `"All Metadata":`，年份用介面篩選 2022–2026。IEEE 每次檢索的詞數與萬用字元數有上限；超過時把區塊 A 拆成兩半分別檢索（A1 AND B AND C、A2 AND B AND C），匯出後合併去重，並在附錄記錄拆分方式。

#### 3.4.5 ACM Digital Library

用 Advanced Search，「Search within」選 **Title、Abstract、Author Keyword**（不要用預設的 Anywhere／全文；初次檢索 633 筆很可能是全文檢索所致）。三個區塊依序輸入，年份篩選 2022–2026。檢索後把 ACM 顯示的完整查詢字串複製到附錄。

#### 3.4.6 arXiv

arXiv 不支援片語內萬用字元，需展開詞形。建議以 arXiv API 執行（腳本放 `scripts/`，可重跑）：

```
(abs:"large language model" OR abs:"large language models" OR abs:LLM OR abs:LLMs OR abs:Llama
 OR abs:Mistral OR abs:Mixtral OR abs:Qwen OR abs:Gemma OR abs:DeepSeek OR abs:"open-weight"
 OR abs:"open-source" OR abs:BioMistral OR abs:Meditron)
AND (abs:"clinical notes" OR abs:"clinical note" OR abs:"clinical text" OR abs:"clinical narratives"
 OR abs:"medical records" OR abs:"health records" OR abs:EHR OR abs:EHRs OR abs:"discharge summaries"
 OR abs:"discharge summary" OR abs:"radiology reports" OR abs:"pathology reports" OR abs:"progress notes")
AND (abs:"information extraction" OR abs:"named entity recognition" OR abs:"relation extraction"
 OR abs:"entity extraction" OR abs:"concept extraction" OR abs:"data extraction" OR abs:"structured data")
AND submittedDate:[202201010000 TO 202612312359]
```

#### 3.4.7 medRxiv（經 Europe PMC）

在 Europe PMC 以相同三區塊、`TITLE:` 與 `ABSTRACT:` 欄位檢索，加 `SRC:PPR`（只取預印本）與 `PUB_YEAR:[2022 TO 2026]`，匯出後只保留來源為 medRxiv 的紀錄。正式執行前先試跑確認語法。

#### 3.4.8 檢索式驗證

正式檢索前：
1. 驗證集：使用者授權 Agent 從初次檢索紀錄中挑選摘要明確使用開源 LLM 做臨床文本抽取的 10 篇（`data/validation_set.csv`），使用者於 2026-11-14 確認採用。限制：候選取自初次檢索結果，無法檢驗「初次與新檢索都會漏掉」的研究；使用者可另外補充已知文獻。
2. 試跑各資料庫，確認驗證集文獻都能被檢出；漏掉的找出原因並補詞。
3. 修改過程記錄在第 8 節。

**試跑結果（2026-11-14，`searches/pilot_2026-11-14/`）**：
- PubMed：新檢索式回傳 637 筆；初次 PubMed 檢索的 242 筆全部被涵蓋（遺漏 0）；`"Large Language Models"[Mesh]` 經 MeSH 資料庫確認存在。
- 驗證集 10 篇中，PubMed 收錄的 9 篇全部被新 PubMed 檢索式檢出；V05（BURExtract-Llama）只在 ACM，待 ACM 正式檢索時確認。
- arXiv：144 筆；Europe PMC 預印本：147 筆，其中 medRxiv 110 筆。
- Scopus、IEEE Xplore、ACM 需由使用者在網頁介面執行（檢索字串見 `scripts/queries/`）。

### 3.5 研究紀錄管理（#11a–c）

**資料管理（#11a）**
- 原始匯出檔存於 `<資料庫> 2022-2026/`，唯讀。
- `scripts/` 下的腳本合併各格式匯出檔，以 DOI 與正規化標題（小寫、去標點）去重，輸出 `data/records_dedup.csv`。
- 篩選與萃取表格存於 `screening/`、`extraction/`，納入 git 版本控制。

**同一研究的多個版本**：預印本與正式發表版本、會議版與期刊延伸版視為同一研究的多份報告（PRISMA 2020 的 study vs. report）。以同儕審查版本為主要資料來源，其他版本只補充缺漏資訊。

**篩選流程（#11b）**
1. **校準**：兩位篩選者先獨立篩選隨機 50 筆，討論分歧並修正判斷規則；κ < 0.6 時再校準一輪。
2. **標題／摘要篩選**：兩人獨立篩選全部紀錄，標記 include／exclude／unsure。任一人標 include 或 unsure 即進入全文篩選。
3. **全文篩選**：兩人獨立依 3.1–3.2 判斷，排除者給代碼。
4. **分歧**：先討論；無共識時由第三位仲裁者（`【待填】`）決定。
5. **一致性**：分別計算兩階段的 Cohen's κ。
6. Agent（LLM）可提供篩選建議與理由，但**不作為任一位篩選者**，最終決定由人做。論文方法段會揭露此 AI 輔助的用法。

**資料萃取流程（#11c）**
- 使用預先設計的萃取表（`extraction/extraction.xlsx`），先以 3 篇試萃取並修訂欄位。
- 一人萃取、第二人逐欄核對；每個數值記錄原文頁碼或表格編號。
- 資料不清楚時，以 email 聯絡原作者一次，兩週未回覆則記為「未報告」。

### 3.6 萃取欄位（#12）

| 類別 | 欄位 |
|---|---|
| 研究 | 第一作者、年份、國家、發表類型（期刊／會議／預印本）、是否同儕審查 |
| 資料 | 病歷語言、文本類型、資料集名稱、是否公開資料集、機構數、文件數、標註方式與標註者一致性 |
| 任務 | 任務類型（NER／RE／欄位抽取／其他）、抽取目標（例如藥物、診斷、腫瘤分期）、臨床領域 |
| 模型 | 每個開源 LLM 的名稱、版本、參數量、是否醫療領域模型、授權類型 |
| 適配策略 | zero-shot、few-shot（樣本數）、chain-of-thought、LoRA／QLoRA、全參數微調、RAG、量化（位元數）、輸出格式約束 |
| 部署 | 本地或雲端、硬體（GPU 型號與數量）、推論時間或成本（若有報告） |
| 比較對象 | 閉源 LLM、BERT 類、規則式、人工，各自的名稱 |
| 結果 | 指標、數值、評估層級（entity／document／field）、比對方式（strict／lenient）、測試集大小、最佳開源模型與最佳比較對象的數值 |
| 可重現性 | 程式碼、prompt、模型權重（微調後）、資料是否公開 |
| 其他 | 作者自述的限制、作者選用開源模型的理由（例如隱私） |

### 3.7 結果指標與優先順序（#13）
- **主要結果**：抽取效能，以 F1 為優先；未報告 F1 時依序取 accuracy、precision／recall。同一研究有多個評估層級時，優先 entity-level strict；多個任務時全部萃取，分析時分任務呈現。
- **次要結果**：使用的模型與策略分布（RQ1、RQ2）、開源與閉源模型的研究內差距（RQ3）、部署與可重現性指標（RQ4）。

### 3.8 偏倚風險／品質評估（#14）
（2026-11-14 確認採用）
目前沒有專為「LLM 資訊抽取評估研究」設計的偏倚風險工具。提議改編 QUADAS-2 的四個領域，並參照 TRIPOD-LLM 的報告項目：

| 領域 | 判斷重點 |
|---|---|
| 1. 資料與樣本 | 測試資料是否具代表性；是否單一機構；樣本數是否足夠 |
| 2. 參考標準 | 標註者人數與資格、是否報告一致性、標註指引是否公開 |
| 3. 模型與評估流程 | 測試集是否與 prompt 開發／微調資料分離；是否有資料洩漏風險（公開資料集可能已在預訓練語料中）；是否只報告最佳 prompt |
| 4. 分析 | 指標定義是否清楚；是否報告變異（多次執行、信賴區間）；比較是否公平（同一資料、同一評估方式） |

每個領域判為低／高／不明風險，兩人獨立評估，分歧以討論解決。

### 3.9 資料綜合（#15a–d）
- **預設做敘述性綜合**，依 SWiM（Synthesis Without Meta-analysis）報告。研究間在資料集、任務、指標上的異質性預期很高，不做跨研究的統合分析（pooling）。
- **分組**：依任務類型、文本類型、適配策略、模型規模分組，以表格與圖呈現。
- **研究內比較（RQ3）**：同一研究同時評估開源與閉源模型（或 BERT 類）時，計算「最佳開源 − 最佳比較對象」的 F1 差值，彙整差值的中位數、範圍與方向（vote counting by direction of effect）。
- **共用資料集**：若有 ≥ 3 篇研究使用同一公開資料集與同一指標（例如 n2c2 2018 藥物抽取），以圖並列呈現各研究數值，但不合併。
- **敏感度分析**：(a) 排除預印本；(b) 排除偏倚風險為高的研究。比較結論是否改變。
- **圖表**：年度趨勢、模型使用頻率、任務分布、開源 vs. 閉源差值、微調 vs. prompting。

### 3.10 後設偏誤（#16）
評估選擇性報告：比對方法段宣稱的評估與結果段實際報告者；記錄研究是否只報告最佳設定。發表偏誤（只發表有利結果）以敘述方式討論，不做漏斗圖（研究間效應量不可比）。

### 3.11 證據確信度（#17）
GRADE 是為介入效果設計的，不完全適用於本回顧的方法學問題。計畫在 E2 階段決定採用改編 GRADE 或說明不適用的理由，並在論文中報告。`【待使用者在 E2 決定】`

---

## 4. 時程

| 階段 | 預計完成 |
|---|---|
| Protocol 定稿與 OSF 註冊 | `【待填】` |
| 檢索式試跑、驗證、正式檢索 | `【待填】` |
| 去重與標題／摘要篩選 | `【待填】` |
| 全文篩選 | `【待填】` |
| 萃取與品質評估 | `【待填】` |
| 分析與撰寫 | `【待填】` |

---

## 5. 倫理

本研究只使用已發表文獻，不涉及病患資料，不需倫理審查。

## 6. 傳播
結果將投稿至同儕審查期刊。完整檢索式、篩選紀錄、萃取表與分析腳本將公開於 OSF 專案頁面。

## 7. 已確認的提議事項（2026-11-14）

1. 子問題 RQ1–RQ4（2.2）：全部採用。
2. LLM 參數量門檻 ≥ 1B（3.1 I1）：採用。
3. 只用合成病歷的研究排除（3.1 I2）：採用。
4. 非抽取任務的範圍（3.2 X6）：摘要、QA、自動編碼、文件層級分類／預測皆排除，並加上判斷規則。
5. 偏倚風險工具：改編 QUADAS-2（3.8）。
6. 引用追蹤：以 OpenAlex 做前向與後向各一輪（3.3）。

## 8. 修訂紀錄

| 日期 | 節次 | 修改 | 理由 |
|---|---|---|---|
| 2026-11-03 | 3.4 | 在 protocol 定稿前，已以未統一的檢索式完成 PubMed、Scopus、ACM、IEEE 初次檢索（共 908 筆）。 | 先行探索性檢索。 |
| 2026-11-13 | 3.4 | 決定統一四個資料庫的檢索式並全部重跑，新增 arXiv 與 medRxiv；初次檢索的匯出檔保留不刪除，但不作為正式檢索結果。 | 初次檢索式在各資料庫間不一致（詞彙與欄位不同），影響可重現性（PRISMA 2020 #7）。 |
| 2026-11-14 | 2.2、3.1、3.2、3.3、3.8 | 確認子問題、≥ 1B 門檻、排除僅合成文本、X6 範圍與判斷規則、改編 QUADAS-2、以 OpenAlex 做前向／後向引用追蹤。 | 註冊前定案。 |
