#!/usr/bin/env bash
# Run Codex D1 extraction for the given batch numbers (default: all), N in parallel.
# Usage: scripts/extraction/run_codex.sh [-j 4] [01 02 ...]
# Model: gpt-6-luna (the config default gpt-6-astra is not available on this ChatGPT account).
set -u
cd "$(dirname "$0")/../.."
J=4
if [ "${1:-}" = "-j" ]; then J=$2; shift 2; fi
BATCHES=("$@")
if [ ${#BATCHES[@]} -eq 0 ]; then
  BATCHES=($(ls extraction/batches/batch_*.list | sed -E 's/.*batch_([0-9]+)\.list/\1/'))
fi
mkdir -p extraction/codex extraction/codex/logs
run_one() {
  b=$1
  P="你是系統性回顧的資料萃取員。請完整閱讀並嚴格遵守 extraction/d1_codex_brief.md（特別是「工作方式」一節），處理 extraction/batches/batch_$b.list 這一批（最多 5 篇）。全文在 fulltext_text_ft/<record_id>.txt，書目資料在 extraction/study_ids.csv。只寫入 extraction/codex/batch_${b}_studies.csv 與 extraction/codex/batch_${b}_results.csv，不要修改其他任何檔案（其他批次同時在寫自己的檔案）。完成後執行 .venv/bin/python scripts/extraction/check_batch.py extraction/batches/batch_$b.list extraction/codex/batch_${b}_studies.csv extraction/codex/batch_${b}_results.csv，把所有 ERROR 修到 0。絕不捏造：沒有原文依據就不要填該列，數值必須照原文印出並附頁碼與逐字 value_context。最後用繁體中文回報：篇數、結果列數、WARN 數、所有 QUERY 篇與原因。"
  codex exec -m gpt-6-luna -c model_reasoning_effort='"high"' -s workspace-write "$P" < /dev/null > "extraction/codex/logs/batch_$b.log" 2>&1
  .venv/bin/python scripts/extraction/check_batch.py "extraction/batches/batch_$b.list" "extraction/codex/batch_${b}_studies.csv" "extraction/codex/batch_${b}_results.csv" 2>&1 | tail -1 | sed "s/^/batch_$b: /"
}
export -f run_one
printf '%s\n' "${BATCHES[@]}" | xargs -P "$J" -I{} bash -c 'run_one {}'
