# AI 預填萃取指引（D1 課堂版：模型、任務、效能）

> 依 `extraction/codebook.md`，課堂版只萃取部分欄位（ROADMAP 2026-11-14：模型、任務、效能）。
> 由 AI 預填、Agent 審查、作者核對；AI 產出僅為草稿。2026-11-15 建立。

## 輸入

- 批次清單 `extraction/ai_batches/batch_NN.list`：每行 `record_id<TAB>title`。
- 全文文字檔 `fulltext_text_full/<record_id>.txt`（`scripts/pdf_to_text.py --cap 200000`，完整全文、已去參考文獻；R0861、R1214、R1331 為 Europe PMC XML 全文，全篇記為 p.1），以 `=== p.N ===` 標頁（PDF 頁碼）。

## 輸出（每批兩個 UTF-8 CSV，含表頭，欄位順序固定）

### `batch_NN_studies.csv`：一篇一列，順序同 .list

```
record_id,title_match,first_author,year,country,note_language,text_type,clinical_domain,datasets,task_types,extraction_targets,open_models,medical_domain_model,closed_comparators,other_comparators,strategies,deployment,n_documents_test,note,evidence
```

- `title_match`：yes＝文字檔就是 .list 的那篇；version＝同一研究的其他版本（預印本／早期版／標題改過，作者與研究內容相同，書目標題錯誤也算），**照常完整萃取**，note 寫文字檔標題；no＝完全不同的論文，其他欄填 NA、results 不填，note 說明。
- `first_author`：第一作者姓。`year`：論文年份。`country`：通訊作者單位國家（看不到填 NR）。
- `note_language`：病歷文本語言，多個以 `; ` 分隔（例 `English; Chinese`）。
- `text_type`：radiology report / pathology report / discharge summary / progress note / operative note / clinical note (mixed) / other，可多個 `; `。
- `clinical_domain`：oncology / cardiology / neurology / … / general。
- `datasets`：資料集名稱（例 `MIMIC-III; n2c2 2018 Track 2; in-house`）。
- `task_types`：NER / RE / attribute / field extraction / other，可多個 `; `。
- `extraction_targets`：抽取目標，簡短英文（例 `medications, dosage, tumour stage`）。
- `open_models`：所有開源 LLM（≥1B、權重可下載），`名稱 版本 參數量`，`; ` 分隔（例 `Llama-3-70B-Instruct; Mistral-7B-Instruct-v0.2`）。
- `medical_domain_model`：是否用了醫療領域開源 LLM（如 Meditron、BioMistral、MedGemma、OpenBioLLM）：yes／no。
- `closed_comparators`：閉源 LLM（例 `GPT-4o`）或 `none`。`other_comparators`：BERT 類、規則式、傳統 ML 或 `none`。
- `strategies`：zero-shot / few-shot / CoT / LoRA / QLoRA / full FT / instruction tuning / RAG / quantization / constrained decoding / ensemble，可多個 `; `。
- `deployment`：local / private cloud / public API / NR（開源模型的執行位置）。
- `n_documents_test`：測試集文件數（整數或 NR）。
- `evidence`：支持模型與任務判斷的 1–3 段**逐字**引句，每段後接 `(p.N)`，段與段以 ` | ` 分隔。引句 ≥ 20 字元、不加引號、不改字。
- 沒有報告填 `NR`；不適用 `NA`。不可推估。

### `batch_NN_results.csv`：一個結果一列

```
record_id,task,dataset,model,model_class,params_b,strategy,metric,f1_avg,value,eval_level,is_best_open,is_best_comparator,value_src,value_quote,note
```

每篇只記**主要結果**，不需窮舉：
1. 每個主要任務（≤3 個）中**最佳的開源 LLM** 一列（`is_best_open=yes`）。
2. 同任務中每一類比較對象（閉源 LLM、BERT 類、規則式）的**最佳**一列（`is_best_comparator=yes`），沒有就不填。
3. 優先 F1；沒有 F1 才用 accuracy／precision／recall／其他。同一列只放一個指標。
4. 每篇至少一列 `is_best_open=yes`（若真的找不到開源 LLM 效能數字，填一列 value=NR 並在 note 說明）。

- `model_class`：open LLM / closed LLM / BERT-type / rule-based / other。
- `params_b`：參數量（十億，數字；例 `70`、`7`、`0.11`）或 NR。
- `strategy`：此列主要策略（zero-shot / few-shot / CoT / LoRA / QLoRA / full FT / RAG / other）。
- `metric`：F1 / precision / recall / accuracy / other（other 時在 note 寫名稱）。`f1_avg`：micro / macro / weighted / NR / NA。
- `value`：一律 0–1 小數（87.3% → 0.873；論文寫 0.873 → 0.873）。
- `eval_level`：entity / relation / field / document / NR。
- `value_src`：`p.N` 或 `Table 3 (p.N)`。
- `value_quote`：從文字檔**逐字**複製、含該數字的一小段（≥ 8 字元，可為表格列的片段），原文的數字寫法（例 `87.3`、`0.873`）必須出現在引句中。

## 原則

- 只依文字檔內容，不憑記憶或外部資料。
- 表格在文字檔中可能被打散；能確定欄列對應才填，不確定就在 note 寫 `uncertain table alignment`。
- CSV 內含逗號的欄位要用雙引號包住。
