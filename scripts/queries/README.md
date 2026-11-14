# 檢索字串

- `scopus.txt`：貼至 Scopus Advanced search；另限制 2022–2026。
- `ieee.txt`：貼至 IEEE Xplore Advanced Search；另限制 2022–2026。`ieee_split_A1.txt` 與 `ieee_split_A2.txt` 為分批備用，須合併去重。
- `acm.txt`：貼至 ACM Digital Library Advanced Search；另限制 2022–2026。

介面實際解析可能改變，執行後把介面顯示的最終查詢字串與筆數記錄到 `searches/<日期>/<db>/search_log.json`：

```json
{"database": null, "interface": null, "query": null, "executed_at": null, "filters": null, "n_results": null, "exported_files": [], "notes": null}
```
