"""Summarise confirmed RoB judgements and plot their distribution."""
import argparse
from collections import Counter
from pathlib import Path
from openpyxl import load_workbook
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from common import write_csv


def main():
    """Read consensus assessments and save tables and figures."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default='extraction/risk_of_bias.xlsx')
    parser.add_argument('--analysis-dir', default='analysis')
    parser.add_argument('--figures-dir', default='figures')
    args = parser.parse_args()
    path = Path(args.input)
    if not path.exists():
        print('尚無風險評估資料')
        return
    wb = load_workbook(path, read_only=True, data_only=True)
    sheet = wb['consensus']
    it = sheet.iter_rows(values_only=True)
    headers = next(it)
    next(it)
    rows = [dict(zip(headers, row)) for row in it if row[0]]
    wb.close()
    domains = [f'D{i}_judgement' for i in range(1, 5)]
    rows = [r for r in rows if any(r.get(d) in ('Low', 'High', 'Unclear') for d in domains)]
    if not rows:
        print('尚無風險評估資料')
        return
    summary = [{'domain': d, **{v: sum(r.get(d) == v for r in rows) for v in ('Low', 'High', 'Unclear')}} for d in domains]
    write_csv(Path(args.analysis_dir) / 'rob_summary.csv', summary, ['domain', 'Low', 'High', 'Unclear'])
    figdir = Path(args.figures_dir)
    figdir.mkdir(parents=True, exist_ok=True)
    colors = {'Low': '#009E73', 'High': '#D55E00', 'Unclear': '#E69F00'}
    fig, ax = plt.subplots(figsize=(7, max(2, len(rows) * .35)))
    for y, row in enumerate(rows):
        for x, domain in enumerate(domains):
            value = row.get(domain)
            ax.scatter(x, y, s=250, c=colors.get(value, '#CCCCCC'), edgecolors='black')
    ax.set_xticks(range(4), domains)
    ax.set_yticks(range(len(rows)), [str(r['study_id']) for r in rows])
    ax.invert_yaxis()
    ax.set_title(f'Risk of bias: consensus (n={len(rows)})')
    fig.tight_layout()
    for ext in ('png', 'pdf'):
        fig.savefig(figdir / f'rob_traffic_light.{ext}', dpi=300)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(7, 4))
    left = [0] * 4
    for value in ('Low', 'High', 'Unclear'):
        sizes = [r[value] for r in summary]
        ax.barh(domains, sizes, left=left, label=value, color=colors[value])
        left = [a + b for a, b in zip(left, sizes)]
    ax.legend()
    ax.set_xlabel('Studies')
    ax.set_title(f'Risk of bias: consensus (n={len(rows)})')
    fig.tight_layout()
    for ext in ('png', 'pdf'):
        fig.savefig(figdir / f'rob_summary.{ext}', dpi=300)
    plt.close(fig)


if __name__ == '__main__':
    main()
