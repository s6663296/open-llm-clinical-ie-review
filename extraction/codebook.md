# 萃取 codebook（D1）

依 `protocol/protocol.md` 3.6、3.7。`extraction/extraction.xlsx` 由 `scripts/make_extraction_form.py` 依本檔產生；**改欄位先改本檔再重產表格**。

## 原則

- 一列 = 一個「研究 × 任務 × 資料集 × 模型 × 設定」的結果（長表格，`results` 工作表）；研究層級資訊放 `studies` 工作表，以 `study_id` 連結。
- 每個數值欄位都有對應的 `*_src` 欄，填原文位置：`p5`、`Table 3`、`Fig 2`、`Suppl Table S4`。沒有出處的值不得填入。
- 未報告 → `NR`；不適用 → `NA`；不清楚 → `unclear` 並在 `note` 說明。不可推估。
- 數值一律以 0–1 小數記錄（論文寫 87.3% → 0.873），`metric_scale_original` 記原始刻度。
- Agent 預先萃取（`extractor=agent`），作者逐欄對照原文核對（`verifier`），核對後 `verified=yes`；作者修正過的欄位要記錄（2026-11-14：單一作者，不設第二位核對者）。

## `studies` 工作表（一列一研究）

| 欄位 | 定義 | 允許值 |
|---|---|---|
| study_id | 研究代號 `S001`… | |
| record_ids | 對應去重表的 record_id（多份報告以 `; ` 分隔） | |
| primary_report | 主要資料來源的 record_id（同儕審查版優先） | |
| first_author, year | 第一作者姓、主要報告年份 | |
| country | 通訊作者單位國家（ISO 名稱） | |
| pub_type | 發表類型 | journal / conference / preprint |
| peer_reviewed | | yes / no |
| note_language | 病歷文本語言（多個以 `; ` 分隔） | 例：English; Chinese |
| text_type | 文本類型 | radiology report / pathology report / discharge summary / progress note / operative note / clinical note (mixed) / other |
| clinical_domain | 臨床領域 | oncology / cardiology / … / general |
| datasets | 資料集名稱 | 例：MIMIC-III; n2c2 2018 Track 2; in-house |
| dataset_public | 是否有公開資料集 | all / some / none |
| n_institutions | 文本來源機構數 | 整數 / NR |
| n_documents_test | 測試集文件數 | 整數 / NR |
| annotation_method | 參考標準 | manual (expert) / manual (non-expert) / existing structured data / mixed / NR |
| n_annotators | 標註者人數 | 整數 / NR |
| iaa | 標註者一致性（指標與值，例 `kappa 0.82`） | |
| task_types | 任務類型 | NER / RE / attribute / field extraction / other（可多選） |
| extraction_targets | 抽取目標（自由文字，例：medications, dosage, tumour stage） | |
| open_models | 所有開源 LLM，`名稱 版本 參數量`，`; ` 分隔 | 例：Llama-3-70B-Instruct; Mistral-7B-Instruct-v0.2 |
| medical_domain_model | 是否用了醫療領域預訓練／微調的開源 LLM | yes / no |
| licences | 開源模型授權 | Llama community / Apache-2.0 / Gemma terms / MIT / other / NR |
| closed_comparators | 閉源 LLM 比較對象 | 例：GPT-4o; none |
| bert_comparators | BERT 類比較對象 | |
| rule_comparators | 規則式／傳統 ML 比較對象 | |
| human_comparator | 是否與人工比較（非參考標準） | yes / no |
| strategies | 使用過的策略（多選） | zero-shot / few-shot / CoT / LoRA / QLoRA / full FT / instruction tuning / RAG / quantization / constrained decoding / ensemble |
| few_shot_k | few-shot 範例數（多個以 `; `） | |
| quant_bits | 量化位元數 | 4 / 8 / 16 / NR / NA |
| deployment | 部署位置 | local / private cloud / public API / NR |
| hardware | GPU 型號與數量 | 例：4× A100 80GB |
| inference_time_cost | 推論時間或成本（原文） | |
| code_available | | yes / no / on request |
| prompts_available | | yes (full) / partial / no |
| weights_available | 微調後權重是否公開 | yes / no / NA |
| data_available | | yes / restricted (DUA) / no |
| reason_open_model | 作者自述選用開源模型的理由 | privacy / cost / reproducibility / local deployment / other / NR（可多選） |
| limitations | 作者自述限制（簡述） | |
| note | | |
| extractor, verifier, verified | | |
| *_src | 各欄出處（`country_src`、`n_documents_test_src`…） | |

## `results` 工作表（一列一結果）

| 欄位 | 定義 | 允許值 |
|---|---|---|
| result_id | `S001-R01`… | |
| study_id | | |
| task | 任務名稱（原文用語） | |
| task_type | | NER / RE / attribute / field extraction / other |
| dataset | | |
| test_n | 測試集大小與單位 | 例：`500 documents`、`2,345 entities` |
| model | 模型名稱與版本（原文） | |
| model_class | | open LLM / closed LLM / BERT-type / rule-based / other |
| model_family | 開源 LLM 家族 | Llama / Mistral / Qwen / Gemma / DeepSeek / Phi / other / NA |
| params_b | 參數量（十億） | 數值 / NR |
| medical_domain | 是否醫療領域模型 | yes / no |
| strategy | 此列結果使用的策略（主要一項） | zero-shot / few-shot / CoT / LoRA / QLoRA / full FT / RAG / other |
| strategy_detail | 補充（例 `5-shot + JSON schema`） | |
| quantized | | yes / no / NR |
| metric | | F1 / precision / recall / accuracy / other |
| f1_avg | F1 平均方式 | micro / macro / weighted / NR / NA |
| value | 0–1 | |
| ci_or_sd | 變異（原文） | |
| n_runs | 重複執行次數 | |
| eval_level | | entity / relation / field / document |
| matching | | strict / lenient / relaxed / NR |
| metric_scale_original | | 0-1 / percent |
| is_best_open | 此研究此任務中最佳開源 LLM 結果 | yes / no |
| is_best_comparator | 此研究此任務中該類別最佳比較對象 | yes / no |
| value_src | 出處 | 例：`Table 3` |
| note | | |
| extractor, verifier, verified | | |

## 試萃取
先以 3 篇試萃取（protocol 3.5），把需要修改的欄位寫進本檔「修訂紀錄」。

## 修訂紀錄
| 日期 | 修改 | 理由 |
|---|---|---|
| 2026-11-14 | 初版 | 依 protocol 3.6、3.7 |
