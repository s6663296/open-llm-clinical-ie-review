# 正式檢索日操作手冊（B1 → B2 → C1）

前提：protocol 已定稿、已在 OSF 註冊（protocol 3.3：六個來源要在**同一天**檢索）。
以下 `<D>` 代表當天日期，例如 `2026-11-20`。所有指令在 repo 根目錄、PowerShell 執行。

## 1. API 來源（約 5 分鐘）

```powershell
.venv\Scripts\python.exe scripts\search_pubmed.py    --out searches\formal_<D>\pubmed
.venv\Scripts\python.exe scripts\search_arxiv.py     --out searches\formal_<D>\arxiv
.venv\Scripts\python.exe scripts\search_europepmc.py --out searches\formal_<D>\europepmc
```

每支腳本都會寫出 `search_log.json`（查詢原文、時間、筆數）。

## 2. 網頁介面來源（手動）

| 資料庫 | 貼上的檔案 | 介面設定 | 匯出格式 |
|---|---|---|---|
| Scopus | `scripts/queries/scopus.txt` | Advanced document search，整段貼上 | CSV，勾選「Citation information」+「Abstract & keywords」 |
| IEEE Xplore | `scripts/queries/ieee.txt`（若超過長度限制，改用 `ieee_split_A1.txt`、`ieee_split_A2.txt` 各跑一次） | Advanced Search → Command Search；年份 2022–2026 | CSV（Export → Citations → CSV） |
| ACM DL | `scripts/queries/acm.txt` | Advanced Search → 編輯查詢；年份 2022–2026 | BibTeX（全選 → Export Citations） |

每個資料庫：
1. 匯出檔放 `searches/formal_<D>/<scopus|ieee|acm>/`。
2. 在同一資料夾建立 `search_log.json`，格式見 `scripts/queries/README.md`，填入**介面顯示的最終查詢字串**、執行時間、篩選條件、筆數、匯出檔名。
3. 介面若改寫了查詢（例如 ACM 自動加欄位），以介面顯示的版本為準記錄。

## 3. 驗證集檢核

```powershell
.venv\Scripts\python.exe scripts\check_validation.py --validation data\validation_set.csv `
  --records searches\formal_<D>\pubmed\records.csv `
  --records searches\formal_<D>\arxiv\records.csv `
  --records searches\formal_<D>\europepmc\medrxiv_records.csv `
  --out searches\formal_<D>\validation_check.csv
```

V05（BURExtract-Llama）只在 ACM：去重後確認它出現在 `records_dedup.csv`。若驗證文獻漏檢，先找原因（詞彙、欄位），修改檢索式後**全部重跑**，並把修改寫進 protocol 第 8 節。

## 4. 去重（B2）

建立 `data/sources_formal_<D>.json`（可複製 `data/sources_pilot_pool_2026-11-14.json` 改路徑；PubMed／arXiv／medRxiv 用 `unified_csv`，Scopus 用 `scopus_csv`，IEEE 用 `ieee_csv`，ACM 用 `bibtex`），然後：

```powershell
.venv\Scripts\python.exe scripts\import_records.py --config data\sources_formal_<D>.json --out data\formal_<D>
copy data\formal_<D>\records_dedup.csv data\records_dedup.csv
```

人工檢查 `data\formal_<D>\possible_duplicates.csv`：確定是重複的，記在 `data\formal_<D>\manual_duplicates.csv` 並在 PRISMA 數字中加入。

## 5. 篩選表（C1）

```powershell
.venv\Scripts\python.exe scripts\make_screening_sheet.py --records data\records_dedup.csv `
  --out screening\title_abstract.xlsx --stage title_abstract `
  --agent-suggestions screening\agent_suggestions_pilot_pool.csv
```

- 對應不到試跑建議的新紀錄，可請 Agent 補建議。
- 兩位篩選者各自拿一份副本填 R1／R2 欄（不要看對方的欄位，也建議先遮住 `agent_*` 欄，自己判斷後再參考）。
- 先做 `calibration=yes` 的 50 筆，算 κ：
  `.venv\Scripts\python.exe scripts\kappa.py --sheet screening\title_abstract.xlsx --stage title_abstract --subset calibration`
- κ ≥ 0.6 後篩完全部，再算 `--subset all`。

## 6. 更新紀錄

```powershell
.venv\Scripts\python.exe scripts\prisma_counts.py --summary data\formal_<D>\summary.json --title-abstract screening\title_abstract.xlsx --out analysis\prisma_counts.json
.venv\Scripts\python.exe scripts\prisma_flow.py --counts analysis\prisma_counts.json
```

把數字填進 `ROADMAP.md`「PRISMA 數字」，`manuscript/values.json` 填 `SEARCH_DATE`。
