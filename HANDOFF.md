# HANDOFF：給接手的 AI（Claude、Codex 等）

> 先讀 `AGENTS.md`（規則）與 `ROADMAP.md`（目前位置、決策紀錄、待決事項）。本檔補充**資料流、怎麼重跑、已知陷阱**，以及最近一次工作做了什麼。
> 最後更新：2026-11-15（Claude Code，Opus 5.5）

## 1. 專案一句話

PRISMA 2020 系統性回顧：開源（權重可下載、≥1B）LLM 用於臨床自由文本資訊抽取。課堂報告，產出是**簡報**（30–40 分鐘），不投稿。

## 2. 資料流（每一步的輸入 → 腳本 → 輸出）

| 步驟 | 輸入 | 腳本 | 輸出 |
|---|---|---|---|
| B1 檢索 | 六來源 | `scripts/search_*.py`、網頁匯出 | `searches/formal_2026-11-14/` |
| B2 去重 | 上一步 | `scripts/import_records.py` 等 | `data/records_dedup.csv`（1,389） |
| C1 標題摘要 | 去重表 | `scripts/agent_screening/*` | `screening/title_abstract_final.*`（進全文 552） |
| C2 全文 | 552 | `scripts/agent_screening/merge_ft.py`、`finalize_ft.py` | `screening/full_text.*`（納入 174） |
| D1 全文還原 | `screening/full_text.csv`、`fulltext/fetch_log*.csv` | `scripts/extraction/restore_fulltext.py` | `fulltext/`（PDF/XML）、`fulltext_text_ft/`（頁碼文字）、`extraction/fulltext_restore_log.csv` |
| D1 編號分批 | 174 篇 | `scripts/extraction/make_batches.py [--scope …]` | `extraction/study_ids.csv`（S001–S174）、`extraction/batches/*.list` |
| 課堂版範圍 | 174 篇 | `scripts/extraction/restrict_scope.py` | `extraction/scope_restriction.csv`（keep／check／exclude＋author_decision） |
| D1 萃取 | 指引 `extraction/d1_codex_brief.md` | Codex（見 §4）＋`scripts/extraction/check_batch.py` | `extraction/codex/batch_NN_{studies,results}.csv` |
| D1 交叉核對 | 課堂版 `extraction/codex/*`、174 版 `extraction/results.csv` | `scripts/extraction/crosscheck.py`（只讀；以 record_id 對應，模型名容許變體） | `extraction/review/crosscheck_62_vs_174.csv`、`_summary.json` |
| D1 審查修正 | `extraction/review/agent_patches.json` | `scripts/extraction/agent_patch.py`（冪等；改動記入 `agent_edits.csv`） | 修改 `extraction/codex/batch_NN_*.csv` |
| D1 合併 | 各批 CSV | `scripts/extraction/merge.py` | `extraction/extraction_scope62.xlsx`（含審查欄）、`extraction/extraction_scope62_summary.json` |
| E1 圖表 | `extraction_scope62.xlsx`、`scope_restriction.csv` | `scripts/analysis/slide_figures.py`、`slide_prisma.py` | `figures/slides/*.png`、`analysis/slide_numbers.json` |
| F2 簡報 | 上面全部 | 手動（Slides artifact） | `slides/project/`、`slides/assets.json`（圖 → `/_blob/` 對照）、artifact 見 ROADMAP |

欄位與允許值的單一來源：`scripts/extraction/fields.py`。

## 3. 從零重跑（新機器）

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/extraction/restore_fulltext.py        # 約 10 分鐘；medRxiv 會 429，腳本自動退避
.venv/bin/python scripts/extraction/make_batches.py --scope extraction/scope_restriction.csv
.venv/bin/python scripts/extraction/agent_patch.py           # 已套用者不會重複套用
.venv/bin/python scripts/extraction/merge.py
.venv/bin/python scripts/analysis/slide_figures.py
.venv/bin/python scripts/analysis/slide_prisma.py
.venv/bin/python -m unittest discover -s tests
```

## 4. 已知陷阱

- **全文不在 git**：`fulltext/*.pdf`、`fulltext_text_ft/` 被 gitignore。用 `restore_fulltext.py` 依 C2 下載紀錄重抓並核對 sha256。
- **sha256 不同不一定是錯檔**：medRxiv 每次下載都重產 PDF。腳本會改比對標題（`ok_title_match`）；標題是預印本版而不同者，已人工確認記在 `extraction/fulltext_manual_checks.csv`（`ok_manual`）。新出現的 `sha256_mismatch` 要人工看第一頁。
- **R0861、R1214、R1331** 的 OA PDF 是錯的文件，固定改用 Europe PMC XML（無頁碼，一律引 `p.1`）。
- **R0382** 只有 AJR 中文翻譯摘要（`ok_abstract_only`），是否保留待作者決定。
- **預印本版全文**：174 篇中 105 篇的萃取文字是預印本版（`study_ids.csv` 的 `text_version`），數值依該版；簡報限制頁已註明。
- **Codex CLI**：本機 `~/.codex/config.toml` 預設模型 `gpt-6-astra` 在使用者的 ChatGPT 帳號不可用，要加 `-m gpt-6-luna`。範例：
  `codex exec -m gpt-6-luna -s workspace-write "<依 extraction/d1_codex_brief.md 處理 batch_NN…>" < /dev/null`
  （不加 `< /dev/null` 會等 stdin。）不要改使用者的 Codex 設定檔。
- **check_batch.py 的數值驗證**：`value_reported` 必須在 `value_src` 標的頁面出現（忽略空白）。從圖讀值、補充資料的數值一律不萃取。
- **Agent 修正走 `agent_patch.py`**：在 `extraction/review/agent_patches.json` 加 set／add／delete 操作，跑腳本後再跑 `check_batch.py`。補列的 `extractor` 為 `agent`（檢查器已允許）。不要手改 CSV，否則 `agent_edits.csv` 沒有紀錄。
- **Excel 不收控制字元**：PDF 文字可能帶換頁符號等；`merge.py` 只在寫 xlsx 時移除，CSV 保持原樣。
- **檢查器拒收 value_reported = 1／0**：S052 的 GPT-4o F1 = 1.00（LV function、mitral stenosis）因此沒有萃取，那兩項不成配對。若要補，需放寬 `check_batch.py` 的 trivial-value 規則。
- **多任務研究在比較中權重較大**：一篇可貢獻多組任務比較（S052 13 組、S071／S159 各 8 組）。簡報主圖用研究層級（每篇取中位數），任務層級數字只放在分布頁。
- **簡報圖片要重新上傳**：重跑出圖後 PNG 會變，需用 upload_asset 重新上傳並改投影片中的 `/_blob/<id>`；目前對照在 `slides/assets.json`。
- **重跑 merge.py 不會蓋掉審查欄**（`agent_review`、`agent_note`、`verified`、`verifier_note`），但改了 Codex CSV 後要重跑 merge 才會進 xlsx。

## 5. 判斷權（不要越界）

- 納入／排除、萃取值的最終判斷屬於使用者。AI 只填建議欄（`suggestion`、`agent_review`）。
- `scope_restriction.csv` 的 `author_decision` 只能由使用者填；空白時 `slide_figures.py` 用暫定規則（R1 同儕審查＋有閉源結果列＋note 無 `R2 not met`），並在 `slide_numbers.json` 記 `provisional_scope_rows`。
- 簡報上的數字只能來自 `analysis/slide_numbers.json` 或 `analysis/prisma_counts.json`，不要手算或推估。

## 6. 最近一次工作（2026-11-15）

1. Agent 審查課堂版 batch 02–13（57 篇），連同 batch 01 共 62 篇：ok 24、fix 8、query 30（`extraction/review/agent_review.csv`）。
2. 修正以 `agent_patch.py` 套用（`agent_patches.json`；42＋10 筆改動記於 `agent_edits.csv`），13 批再次全數通過 `check_batch.py`。
3. `merge.py` → `extraction/extraction_scope62.xlsx`（62 篇、472 列）；`slide_figures.py` 新增研究層級兩欄啞鈴圖 `open_vs_closed_by_study.png` 與 `study_level`／`n_pair_studies` 等數字，直方圖範圍改為依資料決定。
4. 簡報 31 張全部填入（數字只取自 `slide_numbers.json`、`prisma_counts.json`，標「暫定」），已發布到 artifact。

## 6b. 2026-11-15 追加

- Codex 新增 `crosscheck.py`（62 vs 174 交叉核對；priority 1 = 暫定 38 篇中不一致或 agent fix，共 25 篇）與 `tests/test_crosscheck.py`。
- `scripts/prisma_flow.py` 加 `--scope-numbers`，完整版流程圖含課堂版收緊一層；`author_decision` 有空白時標 provisional。174 方框改為 `results_numbers.json` 無值時退回 `prisma_counts.json` 的 `included`。

## 6c. 課堂版定案（2026-11-15）

- 使用者授權 Agent 處理 §7：`scope_restriction.csv` 已填 `author_decision`＋新欄 `decision_reason`（R1／R2／X…）；`slide_figures.py` 在全部填寫時依 `decision_reason` 開頭計排除原因（新增 `scope_excluded_other`），`slide_prisma.py`、`prisma_flow.py` 顯示第三類。
- 對原文核對：`extraction/review/verify_report.csv`（Codex）；採用的修正在 `agent_patches.json`（reason 以 `[verify 2026-11-15]` 開頭）。
- 陷阱：`check_batch.py` 要求每個任務恰一列 `is_best_open=yes`，並列最佳只能標一列；要讓某任務不配對，取消閉源列的 `is_best_comparator`。
- 陷阱：`pdf_to_text.py` 會丟掉參考文獻之後的內容，PDF 附錄（如 S001 p.25）不在文字檔。
- 陷阱：圖表字型在 Windows 用 Microsoft JhengHei（已加入字型清單）。
- 簡報 artifact 改為 https://claude.ai/artifact/8F5RhJ4iBYFrGwgTjYBKt8 （原連結屬另一帳號）。

## 6d. 學術版 PPTX（2026-11-15）

- 重跑：`node slides/pptx/build_deck.js` → `.venv/Scripts/python.exe slides/pptx/finalize.py` → `powershell -File slides/pptx/render.ps1` → `finalize.py --sheets`（`qa/sheetN.png` 六張一頁供目視）。首次需 `cd slides/pptx && npm install`。
- 陷阱：PowerPoint 匯出檔名為「投影片N.PNG」，`--sheets` 會改名為 `sNN.png`。build 內的 `must()` 斷言檢查標題措辭仍符合資料（例如 Llama 最常見），資料變了會中止，需改措辭。
- 陷阱：`slide_prisma.py` 的排除代碼標籤曾與 protocol 3.2 不符，已修正；代碼定義以 protocol 3.2 為準。
- 不要用 Codex 背景任務改 `slide_figures.py`：中途停止後其子程序仍在跑，曾把中文標籤寫成問號（已還原）。

## 7. 審查結果與待作者核對（已於 6c 處理，保留供參考）

**暫定範圍**：`author_decision` 全空，`slide_figures.py` 用暫定規則 → 38 篇（36 篇有配對、88 組任務比較）。作者定案後重跑 `slide_figures.py`、`slide_prisma.py`，並更新簡報數字與圖。

**Agent 修正（fix，8 篇）**
| 研究 | 修正 |
|---|---|
| S002、S005 | batch 01，見 `agent_edits.csv` |
| S043 | pub_type preprint → journal（已刊於 Ophthalmology Science，萃取文字為 medRxiv 版） |
| S077 | DeepSeek-V3.2 為開放權重，改列開源；更正 Codex 混用 binary／macro F1 與誤植 GPT-5.2 數值（p.8 Table III/IV） |
| S100 | 癌別辨識最佳閉源改為 Path-GPT-4o-mini-FT 99%（p.4），原誤取 Mistral-Medium 90% |
| S108 | 補 GPT-4o 0.96 閉源列（p.6 Table 1） |
| S135 | 最佳開源改為 DeepSeek-R1 0.79，補 GPT-5 0.93（p.6 Table 2） |
| S170 | 刪除 BC5CDR（PubMed 摘要、非臨床文本）10 列 |

**需要作者判斷（query 中非單純「R2 不符」者）**
- S057（R0382）只有摘要：保留或排除（ROADMAP 待決事項）。
- S102：原文 p.6 數值前後不一致（Llama 0.74 vs 0.94），目前取 0.94 vs 0.93。
- S121：Table 2 中 Gemma 2 的 AVG 列疑似排版錯誤，最佳開源可能是 Gemma 2 而非 Qwen 2.5。
- S135：資料為已發表病例報告，是否算臨床病歷文本。
- S170：剩餘 HPO 配對用 BiolarkGSC+，作者稱為臨床筆記，原始語料為文獻摘要。
- S001：閉源 Gemini 3 Flash 數值只在附錄 A.4（batch 01）。
- S030、S060：有閉源實測但不能配對（只在圖／補充表；樣本不同）。
- S022、S118、S119、S164：開源數值只在圖或補充資料。
- 其餘 query 為「R2 不符：無閉源直接比較」，建議課堂版排除（S016、S023、S032、S035、S039、S044、S066、S070、S096、S099、S116、S128、S154、S156、S161、S163、S167、S168、S173）。
