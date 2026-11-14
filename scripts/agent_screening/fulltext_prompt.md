# AI 全文篩選指引（雙 AI：Claude Sonnet、Claude Opus）

> 依 `protocol/protocol.md` 3.1–3.2。2026-11-14 建立。兩個模型各自獨立使用本指引，互不讀取對方結果；
> 一致者採用，分歧由作者裁定（ROADMAP 決策紀錄 2026-11-14）。

## 任務

對每篇全文 PDF（`fulltext/<record_id>.pdf`）判斷 **include／exclude**（全文階段不可用 unsure），
exclude 必須給一個排除代碼，並附**原文逐字引句與頁碼**作為依據。

## 納入條件（全部為「是」才 include）

- I1 至少一個開源 LLM：transformer 生成式預訓練模型，**參數量 ≥ 1B**，**權重可公開下載**（Llama、Mistral、Qwen、Gemma、DeepSeek、Phi、BioMistral、Meditron、Flan-T5-XL 以上等）。BERT 類（含 GatorTron 345M／3.9B／8.9B 等 encoder）、小型 T5、BioGPT 不算 LLM。開源模型只當比較對象也算符合。
- I2 臨床自由文本：真實病患照護文本（病歷、出院摘要、影像／病理報告等），含 MIMIC、n2c2／i2b2 等去識別化資料集。只用合成文本、或只用文獻中的病例報告 → 不符合。
- I3 資訊抽取：NER、關係抽取、屬性／否定判斷、結構化欄位抽取。輸出是文本中明確記載的預先定義欄位值 → 屬抽取，即使論文稱「分類」。
- I4 有量化評估：開源 LLM 的抽取結果以參考標準報告至少一項效能指標。
- I5 2022-01-01 之後；I6 期刊、完整會議論文或預印本；I7 英文論文。

## 排除代碼（取第一個符合者）

- X1 發表類型不符：回顧、社論、評論、僅會議摘要、protocol、無全文
- X2 非英文論文
- X3 未使用符合定義的 LLM（只用 BERT 類、< 1B 模型、傳統 ML、規則式）
- X4 只使用閉源 LLM，或開源模型權重實際無法公開下載
- X5 非臨床自由文本（含只用合成文本、只用文獻病例報告、只用結構化資料）
- X6 非資訊抽取任務：摘要、QA、ICD／SNOMED 自動編碼、文件層級分類或預測、病歷生成、對話
- X7 無量化評估（或開源 LLM 的抽取結果沒有效能數字）
- X8 重複報告（同一研究的另一版本；有同儕審查版時，預印本給 X8 並在 note 寫出主版本 record_id）

## 判斷原則

- 依全文內容判斷，尤其看 Methods（模型、資料、任務）與 Results（指標表格）。
- 每個判斷都要能指到原文；引句必須逐字摘自 PDF，並標頁碼（PDF 頁碼，從 1 起算）。
- 全文仍無法確定時，選較可能的一方，並在 reason 寫明不確定之處，供作者裁定時參考。

## 輸出格式

UTF-8 CSV，欄位依序：

```
record_id,decision,code,model_open,text_type,task,metric,reason,evidence
```

- decision：include／exclude；code：exclude 時填 X1–X8，include 留空。
- model_open：用到的開源 LLM 與參數量（無則填「無」）。
- text_type：臨床文本類型與資料集；task：抽取任務；metric：開源 LLM 的主要指標與數值。
- reason：一句繁體中文理由。
- evidence：1–3 句逐字英文引句，各句後標「(p.N)」，以 ` | ` 分隔。
