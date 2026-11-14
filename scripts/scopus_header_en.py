"""Rewrite a localized Scopus CSV export with the standard English headers (by column position).

Scopus localizes CSV headers to the interface language, and in Chinese both "Authors" and
"Author Keywords" become "作者", which breaks name-based parsing. The column order is the same
as the English export, so headers are replaced by position. The original file is not modified.

Usage: python scripts/scopus_header_en.py <localized.csv> <out_en.csv>
"""
import csv
import sys

EN_HEADERS = [
    "Authors", "Author full names", "Author(s) ID", "Title", "Year", "Source title", "Volume",
    "Issue", "Art. No.", "Page start", "Page end", "Cited by", "DOI", "Link", "Affiliations",
    "Authors with affiliations", "Abstract", "Author Keywords", "Index Keywords",
    "Correspondence Address", "Editors", "Publisher", "ISSN", "ISBN", "CODEN", "PubMed ID",
    "Language of Original Document", "Abbreviated Source Title", "Document Type",
    "Publication Stage", "Open Access", "Source", "EID",
]
ZH_HEADERS = [
    "作者", "Author full names", "作者身分", "文獻標題", "年份", "來源出版物名稱", "卷", "期",
    "論文編號", "起始頁碼", "結束頁碼", "被引用文獻", "DOI", "連結", "機構", "帶機構的作者", "摘要",
    "作者", "索引關鍵字", "通訊地址", "編者", "出版商", "ISSN", "ISBN", "CODEN", "PubMed ID",
    "原始文獻語言", "來源出版物名稱縮寫", "文獻類型", "出版階段", "開放取用", "來源出版物", "EID",
]


def main(src, dst):
    """Copy src to dst, replacing the localized header row with English headers."""
    with open(src, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    header = rows[0]
    if header != ZH_HEADERS:
        sys.exit(f"Unexpected header; refusing to map by position: {header}")
    with open(dst, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerow(EN_HEADERS)
        writer.writerows(rows[1:])
    print(f"{len(rows) - 1} records written to {dst}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
