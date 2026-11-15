# D1 萃取指引（交給 Codex 預填用）

本檔是 Codex 預填 D1 資料萃取的完整指示，也是 `extraction/extraction_scope62.xlsx` 的欄位定義（merge 時會放進 `codebook` 工作表）。
欄位與允許值的程式版本在 `scripts/extraction/fields.py`，兩者如有不一致，以 `fields.py` 為準，並回報。

## 背景

這是一篇系統性回顧，題目是開源（權重可下載）LLM 用於臨床自由文本資訊抽取。全文篩選後共納入 174 篇。
課堂版只萃取**模型、任務、效能**三類欄位（2026-11-14 決定），完整 codebook 見 `extraction/codebook.md`，本次不做的欄位不用填。

課堂版另收緊範圍（2026-11-14 決定）：只保留**同儕審查**且**同一研究內有開源 LLM 與閉源 LLM（GPT、Claude、Gemini、PaLM 等）直接比較**的研究。
`extraction/batches/` 只含腳本篩出的 62 篇候選（`extraction/scope_restriction.csv` 的 keep 30／check 32），其中約一半需要你在萃取時確認：

- 有閉源 LLM 在**同一任務、同一測試資料**上的效能數字 → 照常萃取，閉源最佳結果標 `is_best_comparator=yes`。
- 閉源 LLM 只出現在引言、相關研究、資料標註或產生合成資料，沒有可比較的效能數字 → 仍萃取開源結果，並在 study 的 `note` 寫 `QUERY: R2 not met (<閉源模型的實際用途>, p.N)`。
- **不可以寫「未確認」「not verified」**：你必須讀完 Methods 與 Results，找出閉源模型實際做了什麼。驗證腳本會擋下這類 note。

## 工作方式（上一輪因沒讀全文被退件，請照做）

上一輪產出被退件：每篇只填一列、很多值填 `0`、出處一律 `p.1`、閉源比較寫「未確認」。這一輪：

- 每篇都要**逐頁讀到 Results 結束**，特別是所有 Table。先用 `grep -n` 找 `Table`、`F1`、`GPT`、`Claude`、`Gemini` 定位，再讀那幾頁的完整內容。
- 有閉源比較的研究，results 至少會有兩列：最佳開源（`is_best_open=yes`）與最佳閉源（`is_best_comparator=yes`），而且必須是**同一任務、同一資料集、同一指標**。
- 一篇有多個開源模型時，每個開源模型各取最佳設定一列（見下方「哪些數值要萃取」）。
- 數值、頁碼、`value_context` 都必須能在文字檔中找到；找不到就不要填這一列。

## 你的工作

一次處理一批（`extraction/batches/batch_NN.list`，每行 `study_id<TAB>record_id<TAB>title`，每批最多 25 篇）。

1. 逐篇讀 `fulltext_text_ft/<record_id>.txt`。檔案中的 `=== p.N ===` 是 PDF 頁碼。R0861、R1214、R1331 來自 Europe PMC XML，沒有頁碼，全部算 `p.1`。
2. 產出兩個 CSV（UTF-8、逗號分隔、有標題列，欄位順序與下面完全相同）：
   - `extraction/codex/batch_NN_studies.csv`：一篇一列，順序與 `.list` 相同
   - `extraction/codex/batch_NN_results.csv`：一個效能數值一列
3. 執行驗證，**錯誤要修到 0 才算完成**：
   ```
   .venv/bin/python scripts/extraction/check_batch.py extraction/batches/batch_NN.list \
       extraction/codex/batch_NN_studies.csv extraction/codex/batch_NN_results.csv
   ```
4. 回報：本批完成篇數、結果列數、WARN 數量，以及你在 `note` 裡標 `QUERY:` 的篇數與原因。

## 絕對規則

- **只填原文寫的東西**。不推估、不換算原文沒給的數字、不從圖讀數值、不用自己的知識補模型參數量。原文沒寫就填 `NR`。
- 每個事實欄位都要有出處欄（`*_src`、`value_src`），格式是 `p.N`，後面可接表格或圖號，例如 `p.6 Table 3`；多個出處用 `; ` 分隔，例如 `p.3; p.7 Table 2`。
- `value_reported` 必須是原文中**照印出來的數字**（例如 `87.3`、`0.873`），驗證腳本會到 `value_src` 標的那一頁找這串數字，找不到就是錯誤。
- 補充資料（Supplementary）不在文字檔裡，不萃取；只出現在補充資料的數值記在 study 的 `note`。
- 判斷不了、或懷疑這篇其實不符合納入條件（例如沒有 ≥1B 的開源生成式 LLM、只用合成病歷、任務不是抽取），照樣盡量萃取，並在 study 的 `note` 寫 `QUERY: <原因>`。最後是否排除由作者決定。
- 多值欄位用 `; `（分號＋空格）分隔。`NR` = 原文未報告；`NA` = 不適用；`none` = 確定沒有（只用於比較對象欄位）。
- `extractor` 一律填 `codex`。
- **書目欄位依紀錄、數值依全文**：`year`、`pub_type` 依 `extraction/study_ids.csv` 的 `year`／`venue`（期刊名 → journal；會議論文集 → conference；arXiv／medRxiv 等 → preprint），不依手上全文的版本。`study_ids.csv` 的 `text_version` 是 `preprint` 時（105 篇），表示全文是同一研究的預印本版，數值照預印本萃取，並在 study 的 `note` 寫 `text: preprint version`。
- `text_version` 為 `abstract_only`（目前只有 R0382）：只從摘要萃取，study 的 `note` 寫 `QUERY: abstract only`。

## studies 欄位（一篇一列）

| 欄位 | 內容 | 允許值 / 格式 |
|---|---|---|
| study_id, record_id | 照 `.list` | |
| first_author | 第一作者姓氏 | |
| year | 該報告的出版年 | 2022–2027 |
| pub_type | 發表類型 | journal / conference / preprint |
| note_language (+_src) | 病歷文本語言 | 例：`English; Chinese` |
| text_type (+_src) | 文本類型（可多選） | radiology report / pathology report / discharge summary / progress note / operative note / clinical note (mixed) / other |
| clinical_domain | 臨床領域，自由文字但簡短 | 例：oncology、cardiology、general |
| datasets (+_src) | 資料集名稱 | 例：`MIMIC-IV; n2c2 2018 Track 2; in-house` |
| task_types | 任務類型（可多選） | NER / RE / attribute / field extraction / other |
| extraction_targets (+_src) | 抽取目標，簡短列出 | 例：`medications; dosage; tumour stage` |
| open_models (+_src) | 所有開源 LLM，`名稱 版本 參數量` | 例：`Llama-3-70B-Instruct; Mistral-7B-Instruct-v0.2` |
| medical_domain_model | 是否用了醫療領域的開源 LLM（如 Meditron、BioMistral、MedGemma） | yes / no |
| closed_comparators | 閉源 LLM 比較對象 | 例：`GPT-4o`；沒有填 `none` |
| bert_comparators | BERT 類比較對象 | 例：`ClinicalBERT`；沒有填 `none` |
| rule_comparators | 規則式／傳統 ML 比較對象 | 沒有填 `none` |
| comparators_src | 上面三欄的出處（三欄都是 `none` 可留空） | |
| strategies (+_src) | 用過的策略（可多選） | zero-shot / few-shot / CoT / LoRA / QLoRA / full FT / instruction tuning / RAG / quantization / constrained decoding / ensemble / other |
| deployment (+_src) | 開源模型在哪裡跑 | local / private cloud / public API / mixed / NR |
| note | 補充、`QUERY:` 標記 | |
| extractor | `codex` | |

## results 欄位（一個數值一列）

| 欄位 | 內容 | 允許值 / 格式 |
|---|---|---|
| result_id | `S001-R01`、`S001-R02`… | 每篇從 R01 起編 |
| study_id | | |
| task | 任務名稱（原文用語） | |
| task_type | | NER / RE / attribute / field extraction / other |
| dataset | 測試資料集 | |
| test_n | 測試集大小與單位 | 例：`500 documents`、`2,345 entities`；未報告 `NR` |
| model | 模型名稱與版本（原文寫法） | |
| model_class | | open LLM / closed LLM / BERT-type / rule-based / other |
| model_family | 開源 LLM 家族；非開源填 `NA` | Llama / Mistral / Qwen / Gemma / DeepSeek / Phi / other / NA |
| params_b | 參數量（十億），原文沒寫填 `NR` | 例：`70`、`7.2` |
| medical_domain | 是否醫療領域模型；非 LLM 填 `NA` | yes / no / NA |
| strategy | 此列主要策略；非 LLM 填 `NA` | zero-shot / few-shot / CoT / LoRA / QLoRA / full FT / RAG / other / NA |
| strategy_detail | 補充 | 例：`5-shot + JSON schema` |
| quantized | | yes / no / NR / NA |
| metric | | F1 / precision / recall / accuracy / other（other 時在 note 寫指標名） |
| f1_avg | F1 的平均方式；metric 不是 F1 時填 `NA` | micro / macro / weighted / NR / NA |
| value_reported | 原文印出的數字，不含 % | 例：`87.3` |
| metric_scale_original | | percent / 0-1 |
| value | 換成 0–1 的數值（percent 除以 100） | 例：`0.873` |
| eval_level | | entity / relation / field / document / patient / NR |
| matching | | strict / lenient / relaxed / NR / NA |
| is_best_open | 同一 task＋dataset 中最好的開源 LLM 結果 | yes / no（每組恰好一列 yes） |
| is_best_comparator | 同一 task＋dataset 中，該類（closed / BERT / rule）最好的比較對象 | yes / no（每類最多一列 yes） |
| value_src | 出處 | 例：`p.6 Table 3` |
| value_context | 從 `value_src` 那一頁**逐字複製**的一小段原文（≥ 25 字元），必須包含 `value_reported` 這個數字，最好也包含模型名或欄名 | 例：`Llama-3-8B 0.912 0.887 0.899` |
| note | | |
| extractor | `codex` | |

## 哪些數值要萃取（避免表格爆量）

依 protocol 3.7：

1. **指標**：有 F1 就只取 F1；沒有 F1 才取 accuracy；兩者都沒有才取 precision 和 recall。同時有 micro 和 macro 時取 micro。
2. **評估層級**：同一結果有多個層級時，優先 entity-level strict。
3. **整體數值**：取整體（overall／average）的數字，不取各實體類別的細項。原文只有細項、沒有整體數值時，各細項各一列，並在 note 寫 `no overall`。
4. **模型與設定**：每個任務＋資料集，取
   - 每個開源 LLM 的**最佳設定**一列（例如同一模型 zero-shot 與 LoRA 都有，兩列都取；但同一策略下不同 prompt 變體只取最好的）；
   - 閉源 LLM、BERT 類、規則式各取最佳的一列（有的話）。
5. 多個任務或資料集全部萃取，分開列；但**合成（synthetic）病歷上的結果不萃取**（protocol：合成＋真實者只取真實文本結果）。
7. 有 95% CI 或 ± 時，`value_reported` 只填點估計值。
6. 同一篇超過 40 列時，驗證會出 WARN，請檢查是否違反上面規則。

## 範例（虛構，只示範格式）

studies：
```
S000,R0000,Smith,2025,journal,English,p.3,radiology report,p.3,oncology,in-house,p.3,NER,tumour size; stage,p.2,Llama-3-8B-Instruct; Mistral-7B-Instruct-v0.2,p.4,no,GPT-4o,ClinicalBERT,none,p.5,zero-shot; LoRA,p.4,local,p.4,,codex
```
results：
```
S000-R01,S000,tumour attributes,NER,in-house,200 reports,Llama-3-8B-Instruct,open LLM,Llama,8,no,LoRA,r=16,no,F1,micro,91.2,percent,0.912,entity,strict,yes,no,p.6 Table 2,Llama-3-8B-Instruct (LoRA) 90.4 92.0 91.2,,codex
S000-R02,S000,tumour attributes,NER,in-house,200 reports,GPT-4o,closed LLM,NA,NR,no,zero-shot,,NA,F1,micro,93.5,percent,0.935,entity,strict,no,yes,p.6 Table 2,GPT-4o (zero-shot) 94.1 92.9 93.5,,codex
```
