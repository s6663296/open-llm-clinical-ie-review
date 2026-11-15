"""Apply the 2026-11-14 scope restriction (classroom version) to the 174 included studies and suggest a decision.

Restriction (user decision): keep only studies that are
  R1 peer reviewed: the record is a journal/conference publication (not arXiv/medRxiv/other preprint), and
  R2 compare at least one open LLM with at least one closed LLM (GPT, Claude, Gemini, PaLM...) on the same task.
Suggestion only: R1 from record metadata; R2 from closed-model mentions in the full text
(count, pages co-occurring with a metric word) plus the C2 screening notes (model/metric/reason columns).
  keep  = closed LLM in C2 notes AND >= 5 full-text mentions
  check = only one of these signals -> read Methods/Results
  exclude = preprint, or closed LLM absent / only mentioned in passing
The author confirms every row (author_decision).

Output: extraction/scope_restriction.csv  (study_id, record_id, title, venue, year, peer_reviewed,
closed_models_found, closed_pages_with_metric, suggestion, reason, author_decision)
Rerunning keeps author_decision values already filled in.

Usage: .venv/bin/python scripts/extraction/restrict_scope.py
"""
import csv
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREPRINT = re.compile(r'arxiv|medrxiv|biorxiv|research square|ssrn|preprints?\b|techrxiv|jmir preprints', re.I)
CLOSED = re.compile(r'\b(GPT-?4o?(?:-mini|-turbo)?|GPT-?3\.5(?:-turbo)?|GPT-?5|ChatGPT|o1|o3-mini|Claude[\w\- .]*?\d?|'
                    r'Gemini[\w\- .]*?\d?(?:\.\d)?|PaLM ?2?|Med-PaLM|Bard|Grok)\b', re.I)
METRIC = re.compile(r'\b(F1|F-?score|precision|recall|accuracy|sensitivity)\b', re.I)
OUT = ROOT / 'extraction/scope_restriction.csv'
FIELDS = ('study_id record_id title venue year peer_reviewed closed_models_found '
          'closed_pages_with_metric suggestion reason author_decision').split()


def pages(path):
    parts = re.split(r'=== p\.(\d+) ===', path.read_text(encoding='utf-8'))
    return {int(parts[i]): parts[i + 1] for i in range(1, len(parts) - 1, 2)}


def main():
    screen = {r['record_id']: r for r in csv.DictReader(open(ROOT / 'screening/full_text.csv', encoding='utf-8-sig'))}
    keep = {}
    if OUT.exists():
        keep = {r['record_id']: r['author_decision'] for r in csv.DictReader(open(OUT, encoding='utf-8-sig'))}
    rows = []
    for s in csv.DictReader(open(ROOT / 'extraction/study_ids.csv', encoding='utf-8-sig')):
        rec = screen[s['record_id']]
        peer = not (rec['preprint'] == 'yes' or PREPRINT.search(rec['venue']))
        pg = pages(ROOT / s['text_file'])
        found = Counter()
        metric_pages = []
        for n, txt in pg.items():
            hits = [m.group(1).strip() for m in CLOSED.finditer(txt)]
            # 'o1'/'o3' and 'Bard' are noisy as plain words; keep them only with a GPT/Claude/Gemini hit nearby
            found.update(h for h in hits if h.lower() not in ('o1',))
            if hits and METRIC.search(txt):
                metric_pages.append(n)
        total = sum(found.values())
        note = ' '.join(rec[k] for k in ('model_open', 'metric', 'sonnet_reason', 'opus_reason', 'note'))
        in_notes = bool(CLOSED.search(note))
        top = '; '.join(f'{k} ({v})' for k, v in found.most_common(5))
        if not peer:
            sug, why = 'exclude', 'R1: preprint'
        elif not found:
            sug, why = 'exclude', 'R2: no closed LLM mentioned in full text'
        elif in_notes and total >= 5:
            sug, why = 'keep', f'closed LLM in C2 screening notes and {total} mentions in full text'
        elif in_notes or (total >= 5 and metric_pages):
            sug, why = 'check', f'one signal only (C2 notes={in_notes}, {total} mentions); verify head-to-head comparison'
        else:
            sug, why = 'exclude', f'R2 likely not met: closed LLM only mentioned {total}x and not in C2 notes (probably background)'
        rows.append(dict(study_id=s['study_id'], record_id=s['record_id'], title=s['title'], venue=rec['venue'],
                         year=rec['year'], peer_reviewed='yes' if peer else 'no', closed_models_found=top,
                         closed_pages_with_metric=';'.join(map(str, metric_pages[:10])), suggestion=sug,
                         reason=why, author_decision=keep.get(s['record_id'], '')))
    with open(OUT, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(Counter(r['suggestion'] for r in rows), Counter(r['reason'] for r in rows if r['suggestion'] == 'exclude'))


if __name__ == '__main__':
    main()
