"""課堂版 39 篇資料集：參數量補填提案、matching 候選清單、給教授的資料包。

不修改 extraction/codex/*.csv（原始萃取）；所有提案寫到 extraction/review/，資料包寫到 extraction/export/。
Usage: python scripts/extraction/dataset_tools.py
"""
import csv, glob, json, re
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[2]
TRUE = {'1', 'true', 'yes', 'y'}


def rd(p):
    return list(csv.DictReader(open(p, encoding='utf-8-sig')))


keep = {r['study_id'] for r in rd(ROOT / 'extraction/scope_restriction.csv') if r['author_decision'] == 'keep'}
S, R = [], []
for f in sorted(glob.glob(str(ROOT / 'extraction/codex/batch_*_studies.csv'))):
    S += [r for r in rd(f) if r['study_id'] in keep]
for f in sorted(glob.glob(str(ROOT / 'extraction/codex/batch_*_results.csv'))):
    R += [r for r in rd(f) if r['study_id'] in keep]
ids = {r['study_id']: r for r in rd(ROOT / 'extraction/study_ids.csv')}
scope = {r['study_id']: r for r in rd(ROOT / 'extraction/scope_restriction.csv')}

# ---------- 1. params_b ----------
PUBLIC = {'phi-4': ('14', 'Phi-4 官方模型卡 14B'), 'deepseek-r1': ('671', 'DeepSeek-R1 官方模型卡 671B（MoE 總參數）'),
          'flan-t5-xxl': ('11', 'Flan-T5-XXL 11B'), 'flan-ul2': ('20', 'Flan-UL2 20B'),
          'mixtral-8x7b': ('46.7', 'Mixtral 8x7B 總參數約 46.7B')}


def propose(model):
    m = re.sub(r'-A\d+(\.\d+)?B', '', model)           # 排除 MoE 活躍參數 -A3B
    h = re.search(r'(?<![\w.])(\d+(?:\.\d+)?)\s*[Bb](?![a-zA-Z])', m)
    if h and not re.search(r'\d\s*x\s*\d+(\.\d+)?\s*[Bb]', m, re.I):
        return h.group(1), 'name', f'模型名稱含「{h.group(0)}」'
    for k, (v, why) in PUBLIC.items():
        if k in model.lower():
            return v, 'public_card', why
    return '', '', ''


prop = []
for r in R:
    if r['model_class'] != 'open LLM' or r['params_b'] not in ('', 'NR'):
        continue
    v, kind, why = propose(r['model'])
    prop.append({'result_id': r['result_id'], 'study_id': r['study_id'], 'model': r['model'], 'params_b_proposed': v,
                 'basis': kind or '無法由名稱判斷（需查原文）', 'note': why})
out = ROOT / 'extraction/review/params_fill_proposal.csv'
with open(out, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(prop[0])); w.writeheader(); w.writerows(prop)
pmap = {p['result_id']: p for p in prop}

# ---------- 2. matching 候選 ----------
KW = re.compile(r'(strict|lenient|relaxed|exact match|partial match|overlap|token[- ]level|span[- ]level|micro[- ]?F1|macro[- ]?F1)', re.I)
cand = {}
for r in R:
    if r['matching'] == 'NR' and r['metric'] == 'F1' and r['eval_level'] in ('entity', 'field', 'relation'):
        cand.setdefault(r['study_id'], []).append(r)
rows = []
for sid, rs in sorted(cand.items()):
    rec = ids[sid]['record_id']
    p = ROOT / 'fulltext_text' / f'{rec}.txt'
    hits = []
    if p.exists():
        t = p.read_text(encoding='utf-8', errors='ignore')
        for m in KW.finditer(t):
            hits.append(t[max(0, m.start() - 50):m.end() + 50].replace('\n', ' '))
            if len(hits) >= 3: break
    rows.append({'study_id': sid, 'record_id': rec, 'first_author': next(s['first_author'] for s in S if s['study_id'] == sid),
                 'n_rows_matching_NR': len(rs), 'text_hits': ' || '.join(hits) if hits else ('（精簡全文無關鍵字，需讀原文）' if p.exists() else '（本機無全文）')})
out2 = ROOT / 'extraction/review/matching_candidates.csv'
with open(out2, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

# ---------- 3. 資料包 ----------
wb = Workbook()


def sheet(name, header, data, widths=None):
    ws = wb.create_sheet(name)
    ws.append(header)
    for c in ws[1]: c.font = Font(bold=True)
    for d in data: ws.append([('' if v is None else v) for v in d])
    ws.freeze_panes = 'A2'
    for i, h in enumerate(header, 1):
        ws.column_dimensions[get_column_letter(i)].width = (widths or {}).get(h, min(40, max(10, len(h) + 2)))
    return ws


wb.remove(wb.active)
pc = json.load(open(ROOT / 'analysis/prisma_counts.json', encoding='utf-8'))
sn = json.load(open(ROOT / 'analysis/slide_numbers.json', encoding='utf-8'))
nb = sum(1 for r in R if r['is_best_open'].lower() in TRUE)
readme = [
    ['資料集', '開源 LLM 臨床病歷資訊抽取系統性回顧（課堂版）— 39 篇研究、%d 個結果列' % len(R)],
    ['產生方式', 'scripts/extraction/dataset_tools.py，讀 extraction/codex/*.csv（原始萃取）與 scope_restriction.csv（keep）'],
    ['萃取流程', 'Codex 依指引預填並附頁碼，腳本檢查數值出現在該頁；Agent 審查並對原文核對 119 個最佳結果列（verify_report.csv）。'],
    ['核對狀態', '「Agent 依作者授權核對」，作者尚未逐篇人工核對（verified 欄為空）。'],
    ['數值單位', '效能值以 0–1 小數記錄（value）；原始刻度見 metric_scale_original；value_src／value_context 為原文出處。'],
    ['params_b', '原始欄位未改。params_b_proposed 為提案：basis=name 取自模型名稱；public_card 取自公開模型卡，需作者確認；空白＝需查原文。'],
    ['已知限制', 'matching 欄 71% 為 NR；7 篇無開源對閉源配對（S001、S022、S030、S102、S118、S119、S164）；S001 年份 2027 為期刊卷期年（首發為 2026，見 doi）。'],
    ['工作表', 'studies／results／best_results／data_quality／prisma／params_proposal／matching_candidates'],
]
sheet('README', ['項目', '說明'], readme, {'項目': 14, '說明': 120})
for ws in [wb['README']]:
    for row in ws.iter_rows(min_row=2):
        row[1].alignment = Alignment(wrap_text=True, vertical='top')

sh = ['study_id', 'record_id', 'doi', 'venue', 'text_version'] + [k for k in S[0] if k not in ('study_id', 'record_id', 'year')]
sheet('studies', ['study_id', 'record_id', 'year', 'doi', 'venue', 'text_version'] + sh[5:],
      [[s['study_id'], s['record_id'], s['year'], ids[s['study_id']]['doi'], ids[s['study_id']]['venue'], ids[s['study_id']]['text_version']] + [s[k] for k in sh[5:]] for s in S])
rh = list(R[0]) + ['params_b_proposed', 'params_basis']
sheet('results', rh, [[r[k] for k in R[0]] + [pmap.get(r['result_id'], {}).get('params_b_proposed', ''), pmap.get(r['result_id'], {}).get('basis', '')] for r in R])
best = [r for r in R if r['is_best_open'].lower() in TRUE or r['is_best_comparator'].lower() in TRUE]
bh = ['study_id', 'task', 'dataset', 'model', 'model_class', 'strategy', 'metric', 'value', 'eval_level', 'matching', 'is_best_open', 'is_best_comparator', 'value_src']
sheet('best_results', bh, [[r[k] for k in bh] for r in sorted(best, key=lambda r: (r['study_id'], r['task'], r['is_best_open']))])


def cnt(rs, pred): return sum(1 for r in rs if pred(r))


dq = [
    ['結果列總數', len(R)], ['matching = NR', cnt(R, lambda r: r['matching'] == 'NR')], ['params_b 空白（全部）', cnt(R, lambda r: r['params_b'] in ('', 'NR'))],
    ['params_b 空白（開源 LLM）', cnt(R, lambda r: r['model_class'] == 'open LLM' and r['params_b'] in ('', 'NR'))],
    ['  其中可提案補填', sum(1 for p in prop if p['params_b_proposed'])], ['test_n 空白', cnt(R, lambda r: r['test_n'] in ('', 'NR'))],
    ['指標 F1 / accuracy / other', f"{cnt(R, lambda r: r['metric']=='F1')} / {cnt(R, lambda r: r['metric']=='accuracy')} / {cnt(R, lambda r: r['metric']=='other')}"],
    ['最佳開源列數', nb],
]
sheet('data_quality', ['項目', '數值'], dq, {'項目': 34, '數值': 20})
sheet('prisma', ['項目', '數值'], [[k, pc[k] if not isinstance(pc[k], (dict, list)) else json.dumps(pc[k], ensure_ascii=False)] for k in pc if not k.startswith('citation')]
      + [['課堂版納入', sn['n_studies']], ['課堂版排除：預印本 R1', sn['scope_excluded_r1_preprint']], ['課堂版排除：無閉源比較 R2', sn['scope_excluded_r2_no_closed']], ['課堂版排除：其他', sn['scope_excluded_other']]], {'項目': 34, '數值': 60})
sheet('params_proposal', list(prop[0]), [list(p.values()) for p in prop])
sheet('matching_candidates', list(rows[0]), [list(r.values()) for r in rows], {'text_hits': 100})
x = ROOT / 'extraction/export/dataset_39_for_review.xlsx'
wb.save(x)
for name, d in (('studies_39.csv', S), ('results_39.csv', R)):
    with open(ROOT / 'extraction/export' / name, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(d[0])); w.writeheader(); w.writerows(d)
print('proposals', len(prop), 'with value', sum(1 for p in prop if p['params_b_proposed']), 'by basis', {b: sum(1 for p in prop if p['basis'] == b) for b in {p['basis'] for p in prop}})
print('matching candidate studies', len(rows), 'rows', sum(r['n_rows_matching_NR'] for r in rows), 'with hits', sum(1 for r in rows if '關鍵字' not in r['text_hits'] and '無全文' not in r['text_hits']))
