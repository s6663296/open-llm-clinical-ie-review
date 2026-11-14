# AI 標題／摘要篩選指引（Claude Sonnet）

> 依 `protocol/protocol.md` 3.1–3.2。2026-11-14 補跑第 7、13、14、19–21、28、33–35、41、42、48、49、54–56 批時存檔；
> 先前 39 批的原始指引未存檔，本檔依 protocol 與既有輸出格式重建（需於論文揭露）。

## 任務

讀 `screening/ai_screen_sonnet/batch_NNN.txt`（每筆為 record_id、TITLE、ABSTRACT），只依標題與摘要，
對每筆給出 include／exclude／unsure，寫成 `screening/ai_screen_sonnet/batch_NNN.csv`。

## 納入條件（全部為「是」才 include）

- I1 至少一個開源 LLM：transformer 生成式預訓練模型，參數量 ≥ 1B，權重可公開下載（Llama、Mistral、Qwen、Gemma、DeepSeek、Phi、BioMistral、Meditron 等）。BERT 類、小型 T5、BioGPT 不算 LLM。
- I2 臨床自由文本：真實病患照護文本（病歷、出院摘要、影像／病理報告等），含去識別化公開資料集（MIMIC、n2c2／i2b2）。只用合成文本者排除。
- I3 資訊抽取：NER、關係抽取、屬性／否定判斷、結構化欄位抽取。
- I4 有量化評估：以參考標準報告至少一項效能指標。
- I5 2022-01-01 之後；I6 期刊、完整會議論文或預印本；I7 英文論文。

## 排除代碼（取第一個符合者）

- X1 發表類型不符：回顧、社論、評論、僅會議摘要、論文集導言／目錄、protocol、無全文
- X2 非英文論文
- X3 未使用 LLM（只用 BERT 類、傳統 ML、規則式）
- X4 只使用閉源 LLM（GPT、Claude、Gemini 等）
- X5 非臨床自由文本（生醫文獻、社群媒體、病患問卷、僅合成文本、結構化資料）
- X6 非資訊抽取任務：摘要生成、QA、ICD／SNOMED 自動編碼、文件層級分類或預測、病歷生成、對話。
  判斷規則：輸出是文本中明確記載的預先定義欄位值（吸菸狀態、腫瘤分期、藥物劑量）→ 屬抽取，即使論文稱為「分類」；需超出文本的推論或替整份文件指派代碼 → X6
- X7 無量化評估
- X8 重複報告（標題摘要階段通常不用）

## 判斷原則

- 確定不符合某條 → exclude，給代碼。
- 摘要資訊不足以判斷（例如只說「LLMs」未列模型、無法確定是否開源、無法確定是否真實文本、任務邊界模糊）→ unsure。
- 寧可 unsure，不要錯誤排除。只有摘要明確顯示不符合時才 exclude。
- 只說「LLM」而未列任何模型名、也未提閉源模型 → I1 無法判斷 → unsure（除非其他條件已明確不符）。

## 輸出格式

UTF-8 CSV，欄位依序：

```
record_id,doi,pmid,arxiv_id,title,agent_suggestion,agent_code,agent_reason,agent_signals
```

- doi、pmid、arxiv_id 留空（合併前以腳本自 `data/records_dedup.csv` 補回）；title 照抄原標題。
- agent_suggestion：include／exclude／unsure。
- agent_code：exclude 時填 X1–X8；include／unsure 留空。
- agent_reason：一句繁體中文理由，說明關鍵依據（模型、文本、任務、指標）。
- agent_signals：1–4 個片語，以 `; `（分號＋空格）分隔，每個片語必須是標題或摘要中**逐字出現**的字串（不分大小寫）。不可改寫、不可省略中間字。
- 以標準 CSV 跳脫（含逗號或引號的欄位加雙引號）。檔中筆數須與 txt 中筆數相同、順序相同。
