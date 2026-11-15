# HANDOFF：給接手的 AI（Claude、Codex 等）

> 先讀 `AGENTS.md`（規則）與 `ROADMAP.md`（目前位置、決策紀錄、待決事項）。本檔補充**資料流、怎麼重跑、已知陷阱**，以及最近一次工作做了什麼。
> 最後更新：2026-11-14（Claude Code，Opus 5.5）

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
| D1 合併 | 各批 CSV | `scripts/extraction/merge.py` | `extraction/extraction_scope62.xlsx`（含審查欄）、`extraction/extraction_scope62_summary.json` |
| E1 圖表 | `extraction_scope62.xlsx`、`scope_restriction.csv` | `scripts/analysis/slide_figures.py` | `figures/slides/*.png`、`analysis/slide_numbers.json` |
| F2 簡報 | 上面全部 | 手動（Slides artifact） | `slides/project/`、artifact 見 ROADMAP |

欄位與允許值的單一來源：`scripts/extraction/fields.py`。

## 3. 從零重跑（新機器）

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/extraction/restore_fulltext.py        # 約 10 分鐘；medRxiv 會 429，腳本自動退避
.venv/bin/python scripts/extraction/make_batches.py --scope extraction/scope_restriction.csv
.venv/bin/python scripts/extraction/merge.py
.venv/bin/python scripts/analysis/slide_figures.py
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
- **重跑 merge.py 不會蓋掉審查欄**（`agent_review`、`agent_note`、`verified`、`verifier_note`），但改了 Codex CSV 後要重跑 merge 才會進 xlsx。

## 5. 判斷權（不要越界）

- 納入／排除、萃取值的最終判斷屬於使用者。AI 只填建議欄（`suggestion`、`agent_review`）。
- `scope_restriction.csv` 的 `author_decision` 只能由使用者填；空白時 `slide_figures.py` 用暫定規則（R1 同儕審查＋有閉源結果列＋note 無 `R2 not met`），並在 `slide_numbers.json` 記 `provisional_scope_rows`。
- 簡報上的數字只能來自 `analysis/slide_numbers.json` 或 `analysis/prisma_counts.json`，不要手算或推估。

## 6. 最近一次工作（2026-11-14）

見 ROADMAP「📍 目前位置」與決策紀錄最後幾條。重點：
1. 還原 174 篇全文、編號分批、寫萃取指引與驗證腳本。
2. 使用者決定課堂版收緊到「同儕審查＋與閉源 LLM 直接比較」，腳本建議 62 篇候選。
3. Codex 萃取 62 篇（3 批）→ Agent 審查 → 合併 → 圖表 → 填入簡報。
4. 審查結果與待作者核對事項寫在 §7。

## 7. 審查結果與待作者核對

（萃取完成後填寫）
