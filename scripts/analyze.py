"""Analyse verified extraction data without inventing missing observations."""
import argparse
import json
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from openpyxl import load_workbook
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from common import write_csv
from make_rob_form import overall

COLORS = ['#0072B2', '#E69F00', '#009E73', '#D55E00', '#CC79A7', '#56B4E9']
KEYS = ('study_id', 'task', 'dataset', 'metric', 'eval_level')
CLASSES = ('closed LLM', 'BERT-type', 'rule-based')


def pair_results(rows):
    """Pair best-open and comparator results only on complete matching keys."""
    groups = defaultdict(lambda: {'open': [], 'comparator': []})
    unpaired = []
    for row in rows:
        is_open = str(row.get('is_best_open') or '').lower() == 'yes'
        is_comp = str(row.get('is_best_comparator') or '').lower() == 'yes' and row.get('model_class') in CLASSES
        if not (is_open or is_comp):
            continue
        try:
            value = float(row.get('value'))
            if not 0 <= value <= 1:
                raise ValueError('outside 0-1')
        except (ValueError, TypeError):
            unpaired.append(dict(row, reason='invalid or missing value'))
            continue
        key = tuple(str(row.get(k) or '').strip().casefold() for k in KEYS)
        if not all(key):
            unpaired.append(dict(row, reason='missing matching key'))
            continue
        item = dict(row, value=value)
        if is_open:
            groups[key]['open'].append(item)
        if is_comp:
            groups[key]['comparator'].append(item)
    pairs = []
    for group in groups.values():
        opens = group['open']
        comparators = group['comparator']
        by_class = defaultdict(list)
        for comp in comparators:
            by_class[comp['model_class']].append(comp)
        if len(opens) != 1:
            for row in opens + comparators:
                unpaired.append(dict(row, reason='missing or ambiguous best open'))
            continue
        if not comparators:
            unpaired.append(dict(opens[0], reason='missing comparator'))
            continue
        for category, items in by_class.items():
            if len(items) != 1:
                for row in items:
                    unpaired.append(dict(row, reason='ambiguous comparator'))
                continue
            row = opens[0]
            pairs.append({**{key: row.get(key) for key in KEYS}, 'category': category, 'open_model': row.get('model'), 'comparator_model': items[0].get('model'), 'difference': row['value'] - items[0]['value']})
    return pairs, unpaired


def read_sheet(wb, name):
    """Read the workbook's heading and definition row format."""
    it = wb[name].iter_rows(values_only=True)
    headers = next(it)
    next(it)
    return [dict(zip(headers, row)) for row in it if any(v is not None for v in row)]


def split_values(value):
    """Split documented semicolon-separated multi-value cells."""
    return [v.strip() for v in re.split(r';\s*', str(value or '')) if v.strip()]


def save(fig, directory, name, suffix, n):
    """Write a labelled white-background figure in both formats."""
    fig.text(.99, .01, f'Source: extraction workbook; n={n}', ha='right', fontsize=8)
    fig.tight_layout(rect=(0, .04, 1, 1))
    for ext in ('png', 'pdf'):
        fig.savefig(directory / f'{name}{suffix}.{ext}', dpi=300, facecolor='white')
    plt.close(fig)


def main():
    """Generate descriptive analysis from verified study and result rows."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--extraction', default='extraction/extraction.xlsx')
    parser.add_argument('--rob', default='extraction/risk_of_bias.xlsx')
    parser.add_argument('--analysis-dir', default='analysis')
    parser.add_argument('--figures-dir', default='figures')
    parser.add_argument('--include-unverified', action='store_true')
    args = parser.parse_args()
    if not Path(args.extraction).exists():
        print('尚無已核對萃取資料')
        return
    wb = load_workbook(args.extraction, read_only=True, data_only=True)
    studies = read_sheet(wb, 'studies')
    results = read_sheet(wb, 'results')
    wb.close()
    if not args.include_unverified:
        studies = [s for s in studies if str(s.get('verified') or '').strip().lower() == 'yes']
        results = [r for r in results if str(r.get('verified') or '').strip().lower() == 'yes']
    studies = [s for s in studies if s.get('study_id')]
    ids = {s['study_id'] for s in studies}
    results = [r for r in results if r.get('study_id') in ids]
    if not studies:
        print('尚無已核對萃取資料')
        return
    analysis = Path(args.analysis_dir)
    figures = Path(args.figures_dir)
    analysis.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    suffix = '_UNVERIFIED' if args.include_unverified else ''
    n = len(studies)
    def csv_file(name, rows, fields):
        """Write a clearly named table to the selected analysis directory."""
        write_csv(analysis / f'{name}{suffix}.csv', rows, fields)
    characteristics = []
    for field in ('year', 'country', 'pub_type', 'text_type', 'note_language', 'task_types', 'dataset_public'):
        counts = Counter(value for row in studies for value in (split_values(row.get(field)) or ['NR']))
        characteristics.extend({'field': field, 'value': value, 'count': count, 'percent': round(count * 100 / n, 2)} for value, count in sorted(counts.items()))
    csv_file('tab_characteristics', characteristics, ['field', 'value', 'count', 'percent'])
    repro = [r for r in characteristics if r['field'] == 'deployment']
    for field in ('code_available', 'prompts_available', 'weights_available', 'data_available', 'deployment'):
        counts = Counter(str(row.get(field) or 'NR') for row in studies)
        repro.extend({'field': field, 'value': value, 'count': count, 'percent': round(count * 100 / n, 2)} for value, count in sorted(counts.items()))
    csv_file('tab_reproducibility', repro, ['field', 'value', 'count', 'percent'])
    pairs, unpaired = pair_results(results)
    summaries = []
    for category in CLASSES:
        diffs = [p['difference'] for p in pairs if p['category'] == category]
        summaries.append({'category': category, 'n': len(diffs), 'median': statistics.median(diffs) if diffs else '', 'min': min(diffs) if diffs else '', 'max': max(diffs) if diffs else '', 'better': sum(d >= .01 for d in diffs), 'worse': sum(d <= -.01 for d in diffs), 'equal': sum(abs(d) < .01 for d in diffs)})
    csv_file('tab_open_vs_comparator', summaries, ['category', 'n', 'median', 'min', 'max', 'better', 'worse', 'equal'])
    csv_file('tab_unpaired', unpaired, ['study_id', 'task', 'dataset', 'metric', 'eval_level', 'model', 'model_class', 'value', 'reason'])
    fig, ax = plt.subplots()
    years = sorted({str(s.get('year')) for s in studies if s.get('year')})
    bottom = [0] * len(years)
    for idx, typ in enumerate(sorted({str(s.get('pub_type') or 'NR') for s in studies})):
        values = [sum(str(s.get('year')) == y and str(s.get('pub_type') or 'NR') == typ for s in studies) for y in years]
        ax.bar(years, values, bottom=bottom, label=typ, color=COLORS[idx % 6])
        bottom = [a + b for a, b in zip(bottom, values)]
    ax.set_ylabel('Studies')
    ax.legend()
    save(fig, figures, 'fig_year_trend', suffix, n)
    families = Counter((r['study_id'], str(r.get('model_family'))) for r in results if r.get('model_class') == 'open LLM' and r.get('model_family') not in (None, '', 'NA'))
    family_counts = Counter(family for _, family in families)
    fig, ax = plt.subplots()
    ordered = sorted(family_counts.items(), key=lambda item: item[1])
    ax.barh([x[0] for x in ordered], [x[1] for x in ordered], color=COLORS[0])
    ax.set_xlabel('Studies')
    save(fig, figures, 'fig_model_families', suffix, n)
    tasks = sorted({x for s in studies for x in split_values(s.get('task_types'))})
    texts = sorted({x for s in studies for x in split_values(s.get('text_type'))})
    fig, ax = plt.subplots()
    if tasks and texts:
        matrix = [[sum(task in split_values(s.get('task_types')) and text in split_values(s.get('text_type')) for s in studies) for text in texts] for task in tasks]
        ax.imshow(matrix, cmap='Blues', aspect='auto')
        ax.set_xticks(range(len(texts)), texts, rotation=30, ha='right')
        ax.set_yticks(range(len(tasks)), tasks)
        for y, row in enumerate(matrix):
            for x, value in enumerate(row):
                ax.text(x, y, str(value), ha='center', va='center')
    save(fig, figures, 'fig_task_distribution', suffix, n)
    fig, ax = plt.subplots()
    for idx, category in enumerate(CLASSES):
        values = [p['difference'] for p in pairs if p['category'] == category]
        ax.scatter(values, [idx] * len(values), color=COLORS[idx], label=category)
    ax.axvline(0, color='black', linewidth=.8)
    ax.set_yticks(range(3), CLASSES)
    ax.set_xlabel('Open minus comparator')
    save(fig, figures, 'fig_open_vs_comparator', suffix, len(pairs))
    f1 = []
    for row in results:
        if row.get('model_class') == 'open LLM' and str(row.get('is_best_open') or '').lower() == 'yes' and str(row.get('metric') or '').lower() == 'f1':
            try:
                value = float(row['value'])
                if 0 <= value <= 1:
                    f1.append((row, value))
            except (TypeError, ValueError):
                pass
    strategies = ['zero-shot', 'few-shot', 'PEFT', 'full FT', 'RAG']
    fig, ax = plt.subplots()
    for i, strategy in enumerate(strategies):
        vals = [v for r, v in f1 if (r.get('strategy') in ('LoRA', 'QLoRA') if strategy == 'PEFT' else r.get('strategy') == strategy)]
        ax.scatter([i] * len(vals), vals, color=COLORS[i], alpha=.7)
        ax.text(i, 1.02, f'n={len(vals)}', ha='center')
    ax.set_xticks(range(len(strategies)), strategies, rotation=20)
    ax.set_ylabel('F1')
    ax.set_ylim(0, 1.1)
    save(fig, figures, 'fig_strategy', suffix, len(f1))
    fig, ax = plt.subplots()
    plotted = 0
    for i, strategy in enumerate(strategies):
        for row, value in f1:
            if not (row.get('strategy') in ('LoRA', 'QLoRA') if strategy == 'PEFT' else row.get('strategy') == strategy):
                continue
            try:
                params = float(row.get('params_b'))
                if params > 0:
                    ax.scatter(params, value, color=COLORS[i], label=strategy if not any(x.get_label() == strategy for x in ax.collections) else None)
                    plotted += 1
            except (ValueError, TypeError):
                continue
    ax.set_xscale('log')
    ax.set_xlabel('Parameters (billions)')
    ax.set_ylabel('F1')
    if plotted:
        ax.legend()
    save(fig, figures, 'fig_params_vs_f1', suffix, plotted)
    high = set()
    rob_complete = False
    if Path(args.rob).exists():
        rob = load_workbook(args.rob, read_only=True, data_only=True)
        assessments = {r.get('study_id'): overall([r.get(f'D{i}_judgement') for i in range(1, 5)]) for r in read_sheet(rob, 'consensus')}
        rob.close()
        high = {study_id for study_id, judgement in assessments.items() if judgement == 'High'}
        rob_complete = all(assessments.get(study_id) in ('Low', 'High', 'Unclear') for study_id in ids)
    scenarios = [('exclude_preprint', {s['study_id'] for s in studies if s.get('pub_type') != 'preprint'})]
    if rob_complete:
        scenarios.append(('exclude_high_rob', ids - high))
    else:
        print('敏感度分析：RoB 資料不存在或尚未完成，跳過排除 High')
    sensitivity = []
    for name, keep in scenarios:
        subset, _ = pair_results([r for r in results if r.get('study_id') in keep])
        for category in CLASSES:
            values = [p['difference'] for p in subset if p['category'] == category]
            sensitivity.append({'scenario': name, 'category': category, 'n': len(values), 'median': statistics.median(values) if values else '', 'min': min(values) if values else '', 'max': max(values) if values else '', 'better': sum(v >= .01 for v in values), 'worse': sum(v <= -.01 for v in values), 'equal': sum(abs(v) < .01 for v in values)})
    csv_file('tab_sensitivity', sensitivity, ['scenario', 'category', 'n', 'median', 'min', 'max', 'better', 'worse', 'equal'])
    numbers = {'N_STUDIES': n, 'N_PAIRED': len(pairs), 'N_UNPAIRED': len(unpaired)}
    for row in summaries:
        prefix = {'closed LLM': 'CLOSED_LLM', 'BERT-type': 'BERT_TYPE', 'rule-based': 'RULE_BASED'}[row['category']]
        for field in ('n', 'median', 'min', 'max', 'better', 'worse', 'equal'):
            numbers[f'{prefix}_{field.upper()}'] = row[field] if row[field] != '' else None
    (analysis / f'results_numbers{suffix}.json').write_text(json.dumps(numbers, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()

