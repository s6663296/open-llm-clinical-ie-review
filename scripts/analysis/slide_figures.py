"""E1: build the slide figures and headline numbers from the extraction workbook.

Input : extraction/extraction_scope62.xlsx (sheets studies, results; built by scripts/extraction/merge.py)
        extraction/scope_restriction.csv (classroom scope; author_decision overrides the rule below)
Output: figures/slides/*.png  (1664 px wide, slide background, Traditional Chinese labels)
        analysis/slide_numbers.json (every number shown on the slides, with the study set used)

Final study set (classroom scope, decision 2026-11-14):
  author_decision == keep            -> in
  author_decision == exclude         -> out
  author_decision empty (provisional) -> in iff peer reviewed (R1) AND the study has >= 1 closed-LLM result row
                                         AND its note does not contain 'R2 not met'
Study level: median of each study's comparisons (open_vs_closed_by_study.png) so multi-task studies count once.
Open vs closed comparison: per (study, task, dataset), best open row (is_best_open=yes) vs best closed row
(model_class=closed LLM, is_best_comparator=yes), only when both use the same metric. gap = closed - open.
'Comparable' = open >= closed - TIE (TIE = 0.02 F1), stated on the slide.

Usage: .venv/bin/python scripts/analysis/slide_figures.py
"""
import csv
import json
import re
from collections import Counter
from pathlib import Path
from statistics import median

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from openpyxl import load_workbook  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / 'figures/slides'
TIE = 0.02
# Reference categorical palette (dataviz skill, validated): slot 1 blue = open, slot 2 orange = closed.
OPEN, CLOSED = '#2a78d6', '#eb6834'
INK, SOFT, GRID, BG = '#1B2A3A', '#4A5568', '#D5DBE3', '#F7F6F2'
FAMILY_ORDER = ['Llama', 'Qwen', 'Mistral', 'Gemma', 'DeepSeek', 'Phi', 'other']
FT = {'LoRA', 'QLoRA', 'full FT'}

plt.rcParams.update({
    'font.family': ['PingFang TC', 'Heiti TC', 'Arial Unicode MS', 'sans-serif'],
    'font.size': 20, 'axes.edgecolor': GRID, 'axes.labelcolor': SOFT, 'xtick.color': SOFT,
    'ytick.color': INK, 'axes.facecolor': BG, 'figure.facecolor': BG, 'savefig.facecolor': BG,
})


def sheet(wb, name):
    it = wb[name].iter_rows(values_only=True)
    head = list(next(it))
    return [{k: ('' if v is None else str(v).strip()) for k, v in zip(head, row)} for row in it if any(row)]


def split(v):
    return [x.strip() for x in v.split(';') if x.strip() and x.strip() not in ('NR', 'NA', 'none')]


def final_set(studies, results):
    scope = {r['study_id']: r for r in csv.DictReader(open(ROOT / 'extraction/scope_restriction.csv', encoding='utf-8-sig'))}
    closed_ids = {r['study_id'] for r in results if r['model_class'] == 'closed LLM'}
    keep, provisional = [], 0
    for s in studies:
        sc = scope.get(s['study_id'], {})
        d = sc.get('author_decision', '')
        if d == 'keep':
            keep.append(s)
        elif d == '':
            provisional += 1
            if sc.get('peer_reviewed') == 'yes' and s['study_id'] in closed_ids and 'R2 not met' not in s['note']:
                keep.append(s)
    return keep, provisional


def hbar(counts, title_n, path, color=OPEN, order=None, xlabel='研究數'):
    items = [(k, counts[k]) for k in order if counts.get(k)] if order else counts.most_common()
    items = items[::-1]
    h = max(3.2, 0.62 * len(items) + 1.2)
    fig, ax = plt.subplots(figsize=(16.64, h), dpi=100)
    ax.barh([k for k, _ in items], [v for _, v in items], color=color, height=0.62)
    for i, (_, v) in enumerate(items):
        ax.text(v + max(c for _, c in items) * 0.01, i, str(v), va='center', color=INK, fontsize=20)
    ax.set_xlabel(f'{xlabel}（n = {title_n}，一篇可計入多類）')
    style(ax, 'x')
    save(fig, path)


def style(ax, grid_axis):
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    ax.grid(axis=grid_axis, color=GRID, linewidth=1)
    ax.set_axisbelow(True)


def save(fig, name):
    FIG.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(FIG / name, dpi=100)
    plt.close(fig)


def pairs(results, ids):
    groups = {}
    for r in results:
        if r['study_id'] in ids:
            groups.setdefault((r['study_id'], r['task'], r['dataset']), []).append(r)
    out = []
    for (sid, task, ds), g in groups.items():
        o = [r for r in g if r['is_best_open'] == 'yes']
        c = [r for r in g if r['model_class'] == 'closed LLM' and r['is_best_comparator'] == 'yes']
        if o and c and o[0]['metric'] == c[0]['metric']:
            out.append(dict(study_id=sid, task=task, dataset=ds, metric=o[0]['metric'],
                            open_model=o[0]['model'], open_value=float(o[0]['value']), open_strategy=o[0]['strategy'],
                            closed_model=c[0]['model'], closed_value=float(c[0]['value']),
                            gap=round(float(c[0]['value']) - float(o[0]['value']), 4),
                            open_src=o[0]['value_src'], closed_src=c[0]['value_src']))
    return out


def main():
    wb = load_workbook(ROOT / 'extraction/extraction_scope62.xlsx', read_only=True)
    studies_all, results_all = sheet(wb, 'studies'), sheet(wb, 'results')
    studies, provisional = final_set(studies_all, results_all)
    ids = {s['study_id'] for s in studies}
    results = [r for r in results_all if r['study_id'] in ids]
    meta = {r['study_id']: r for r in csv.DictReader(open(ROOT / 'extraction/study_ids.csv', encoding='utf-8-sig'))}
    n = len(studies)

    # Year
    years = Counter(s['year'] for s in studies)
    fig, ax = plt.subplots(figsize=(16.64, 5.6), dpi=100)
    ks = sorted(years)
    ax.bar(ks, [years[k] for k in ks], color=OPEN, width=0.6)
    for k in ks:
        ax.text(k, years[k] + 0.3, str(years[k]), ha='center', color=INK)
    ax.set_ylabel('研究數')
    ax.set_xlabel(f'出版年（n = {n}）')
    style(ax, 'y')
    save(fig, 'year.png')

    lang = Counter(x for s in studies for x in set(split(s['note_language'])))
    hbar(lang, n, 'language.png')
    hbar(Counter(x for s in studies for x in set(split(s['text_type']))), n, 'text_type.png')
    hbar(Counter(x for s in studies for x in set(split(s['task_types']))), n, 'task_type.png')
    dom = Counter(s['clinical_domain'].strip().lower() for s in studies if s['clinical_domain'] not in ('', 'NR'))
    top = Counter(dict(dom.most_common(8)))
    if len(dom) > 8:
        top['其他'] = sum(dom.values()) - sum(top.values())
    hbar(top, n, 'clinical_domain.png')

    open_rows = [r for r in results if r['model_class'] == 'open LLM']
    fam = Counter(f for (_, f) in {(r['study_id'], r['model_family']) for r in open_rows})
    hbar(fam, n, 'model_family.png', order=FAMILY_ORDER)

    sizes = {}
    for r in open_rows:
        if re.fullmatch(r'\d+(\.\d+)?', r['params_b']):
            sizes[(r['study_id'], r['model'])] = float(r['params_b'])
    bins = [('1–10B', 1, 10), ('10–40B', 10, 40), ('40–100B', 40, 100), ('> 100B', 100, 1e9)]
    bc = Counter()
    for v in sizes.values():
        for lab, lo, hi in bins:
            if lo <= v < hi or (lab == '1–10B' and v < 1):
                bc[lab] += 1
                break
    fig, ax = plt.subplots(figsize=(16.64, 5.6), dpi=100)
    labs = [b[0] for b in bins]
    ax.bar(labs, [bc[l] for l in labs], color=OPEN, width=0.6)
    for l in labs:
        ax.text(l, bc[l] + 0.3, str(bc[l]), ha='center', color=INK)
    ax.set_ylabel('模型數（研究 × 模型）')
    ax.set_xlabel(f'參數量（有報告者 {len(sizes)} 個；n = {n} 篇研究）')
    style(ax, 'y')
    save(fig, 'params.png')

    strat = Counter(x for s in studies for x in set(split(s['strategies'])))
    hbar(strat, n, 'strategies.png')
    hbar(Counter(s['deployment'] for s in studies), n, 'deployment.png', xlabel='研究數（每篇一類）')

    # Open vs closed
    P = pairs(results, ids)
    P.sort(key=lambda p: p['gap'])
    if P:
        h = max(5, 0.42 * len(P) + 1.5)
        fig, ax = plt.subplots(figsize=(16.64, h), dpi=100)
        for i, p in enumerate(P):
            ax.plot([p['open_value'], p['closed_value']], [i, i], color=GRID, linewidth=3, zorder=1)
        ax.scatter([p['open_value'] for p in P], range(len(P)), s=110, color=OPEN, zorder=2,
                   edgecolors=BG, linewidths=2, label='最佳開源 LLM')
        ax.scatter([p['closed_value'] for p in P], range(len(P)), s=110, color=CLOSED, zorder=3,
                   edgecolors=BG, linewidths=2, label='最佳閉源 LLM')
        ax.set_yticks(range(len(P)))
        author = {s['study_id']: f"{s['first_author']} {s['year']}" for s in studies}
        ax.set_yticklabels([f"{author[p['study_id']]} · {p['task'][:20]}" for p in P], fontsize=15)
        ax.set_xlabel('效能（0–1；同一研究、同一任務與資料集內比較）')
        ax.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=2, frameon=False, fontsize=18)
        style(ax, 'x')
        save(fig, 'open_vs_closed_dumbbell.png')

        gaps = [p['gap'] for p in P]
        fig, ax = plt.subplots(figsize=(16.64, 4.6), dpi=100)
        lo, hi = int(min(gaps) * 20 - 1), int(max(gaps) * 20 + 2)  # 0.05-wide bins covering every gap
        edges = [x / 20 for x in range(lo, hi + 1)]
        ax.hist(gaps, bins=edges, color=OPEN, edgecolor=BG, linewidth=2)
        ax.axvline(0, color=INK, linewidth=2)
        ax.set_xlabel('效能差距（閉源 − 開源）；左側 = 開源較好')
        ax.set_ylabel('比較數')
        style(ax, 'y')
        save(fig, 'gap_hist.png')

        # Study level: one row per study (median over its comparisons) so multi-task studies do not dominate.
        by_study = {}
        for p in P:
            by_study.setdefault(p['study_id'], []).append(p)
        SP = sorted(({'study_id': sid, 'n': len(g),
                      'open_median': median(p['open_value'] for p in g),
                      'closed_median': median(p['closed_value'] for p in g),
                      'gap_median': round(median(p['gap'] for p in g), 4)} for sid, g in by_study.items()),
                    key=lambda d: d['gap_median'])
        # Two panels sized for one slide (1664 x 700 px): closed ahead | open comparable or better.
        panels = [('閉源領先（差距 > %.2f）' % TIE, [d for d in SP if d['gap_median'] > TIE][::-1]),
                  ('開源追平或較好（差距 ≤ %.2f）' % TIE, [d for d in SP if d['gap_median'] <= TIE])]
        fig, axes = plt.subplots(1, 2, figsize=(16.64, 7.0), dpi=100, sharex=True)
        for ax, (title, rows) in zip(axes, panels):
            for i, d in enumerate(rows):
                ax.plot([d['open_median'], d['closed_median']], [i, i], color=GRID, linewidth=3, zorder=1)
            ax.scatter([d['open_median'] for d in rows], range(len(rows)), s=70, color=OPEN, zorder=2,
                       edgecolors=BG, linewidths=1.5, label='最佳開源 LLM')
            ax.scatter([d['closed_median'] for d in rows], range(len(rows)), s=70, color=CLOSED, zorder=3,
                       edgecolors=BG, linewidths=1.5, label='最佳閉源 LLM')
            ax.set_yticks(range(len(rows)))
            ax.set_yticklabels([f"{author[d['study_id']]}（{d['n']}）" for d in rows], fontsize=13)
            ax.set_ylim(-0.7, max(len(r) for _, r in panels) - 0.3)
            ax.invert_yaxis()
            ax.set_xlim(0, 1.02)
            ax.tick_params(axis='x', labelsize=14)
            ax.set_title(f'{title}：{len(rows)} 篇', fontsize=17, color=INK, loc='left')
            style(ax, 'x')
        axes[0].legend(loc='lower left', bbox_to_anchor=(0, 1.07), ncol=2, frameon=False, fontsize=15)
        fig.supxlabel('效能（0–1）；每篇取其各比較的中位數，括號 = 比較數', fontsize=15, color=SOFT)
        save(fig, 'open_vs_closed_by_study.png')

        groups = {'開源：提示（zero/few-shot、CoT、RAG）': [], '開源：微調（LoRA、QLoRA、全參數）': []}
        for p in P:
            groups['開源：微調（LoRA、QLoRA、全參數）' if p['open_strategy'] in FT else '開源：提示（zero/few-shot、CoT、RAG）'].append(p['gap'])
        fig, ax = plt.subplots(figsize=(16.64, 4.6), dpi=100)
        for i, (lab, g) in enumerate(groups.items()):
            ax.scatter(g, [i] * len(g), s=110, color=OPEN, alpha=0.8, edgecolors=BG, linewidths=2)
            if g:
                ax.plot([median(g)] * 2, [i - 0.3, i + 0.3], color=INK, linewidth=3)
        ax.axvline(0, color=SOFT, linewidth=1.5, linestyle='--')
        ax.set_yticks(range(len(groups)))
        ax.set_yticklabels([f'{k}（{len(v)}）' for k, v in groups.items()])
        ax.set_ylim(-0.6, len(groups) - 0.4)
        ax.set_xlabel('效能差距（閉源 − 開源）；黑線 = 中位數')
        style(ax, 'x')
        save(fig, 'gap_by_strategy.png')

    gaps = [p['gap'] for p in P]
    scope_rows = list(csv.DictReader(open(ROOT / 'extraction/scope_restriction.csv', encoding='utf-8-sig')))
    r1 = sum(r['peer_reviewed'] == 'no' for r in scope_rows)
    numbers = dict(
        provisional_scope_rows=provisional,
        scope_total=len(scope_rows), scope_excluded_r1_preprint=r1,
        scope_excluded_r2_no_closed=len(scope_rows) - r1 - n,
        n_studies=n, study_ids=sorted(ids),
        n_distinct_open_models=len({r['model'].lower() for r in open_rows}),
        pct_non_english=round(100 * sum(any(l != 'English' for l in split(s['note_language'])) for s in studies) / n) if n else None,
        pct_finetune=round(100 * sum(bool(FT & set(split(s['strategies']))) for s in studies) / n) if n else None,
        pct_medical_model=round(100 * sum(s['medical_domain_model'] == 'yes' for s in studies) / n) if n else None,
        pct_local=round(100 * sum(s['deployment'] == 'local' for s in studies) / n) if n else None,
        years=dict(sorted(years.items())), model_family=dict(fam.most_common()), strategies=dict(strat.most_common()),
        deployment=dict(Counter(s['deployment'] for s in studies)), language=dict(lang.most_common()),
        n_comparisons=len(P), tie_threshold=TIE,
        n_open_comparable_or_better=sum(g <= TIE for g in gaps),
        n_closed_ahead=sum(g > TIE for g in gaps),
        median_gap=round(median(gaps), 3) if gaps else None,
        median_gap_prompting=round(median(groups['開源：提示（zero/few-shot、CoT、RAG）']), 3) if P and groups['開源：提示（zero/few-shot、CoT、RAG）'] else None,
        median_gap_finetuned=round(median(groups['開源：微調（LoRA、QLoRA、全參數）']), 3) if P and groups['開源：微調（LoRA、QLoRA、全參數）'] else None,
        n_finetuned_comparisons=len(groups['開源：微調（LoRA、QLoRA、全參數）']) if P else 0,
        n_pair_studies=len(SP) if P else 0,
        n_studies_open_comparable_or_better=sum(d['gap_median'] <= TIE for d in SP) if P else 0,
        n_studies_closed_ahead=sum(d['gap_median'] > TIE for d in SP) if P else 0,
        median_study_gap=round(median(d['gap_median'] for d in SP), 3) if P else None,
        study_level=SP if P else [],
        comparisons=P,
    )
    (ROOT / 'analysis/slide_numbers.json').write_text(json.dumps(numbers, ensure_ascii=False, indent=1), encoding='utf-8')
    print(json.dumps({k: v for k, v in numbers.items() if k not in ('comparisons', 'study_ids')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
