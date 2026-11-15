"""Slide version of the PRISMA 2020 flow (Traditional Chinese, single database pathway + classroom scope step).

Reads analysis/prisma_counts.json and analysis/slide_numbers.json (scope step). The citation-tracking pathway
was not done (decision 2026-11-14) and is omitted here; figures/prisma_flow.* keeps the full two-pathway draft.
Output: figures/slides/prisma_slide.png

Usage: .venv/bin/python scripts/analysis/slide_prisma.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
INK, SOFT, LINE, BG, OPEN = '#1B2A3A', '#4A5568', '#9AA5B4', '#F7F6F2', '#2a78d6'
# Exclusion codes as defined in protocol/protocol.md 3.2 (and the screening prompts).
CODE = {'X1': '發表類型不符', 'X2': '非英文', 'X3': '未使用符合定義的 LLM', 'X4': '只用閉源 LLM',
        'X5': '非臨床自由文本', 'X6': '非抽取任務', 'X7': '無量化評估', 'X8': '同一研究的其他版本'}
plt.rcParams['font.family'] = ['PingFang TC', 'Microsoft JhengHei', 'Heiti TC', 'Arial Unicode MS', 'sans-serif']


def main():
    c = json.loads((ROOT / 'analysis/prisma_counts.json').read_text(encoding='utf-8-sig'))
    s = json.loads((ROOT / 'analysis/slide_numbers.json').read_text(encoding='utf-8'))
    db = c['database_counts']
    total = sum(db.values())
    sought = c['screened'] - c['title_abstract_excluded']
    ft = sorted(c['full_text_excluded_by_code'].items(), key=lambda kv: -kv[1])
    left = [
        (f'資料庫檢索\nn = {total:,}', '識別'),
        (f'標題／摘要篩選\nn = {c["screened"]:,}', '篩選'),
        (f'尋求全文\nn = {sought}', ''),
        (f'全文評估\nn = {c["full_text_assessed"]}', ''),
        (f'符合原始納入條件\nn = {c["included"]}', '納入'),
        (f'課堂版最終納入\nn = {s["n_studies"]}', ''),
    ]
    right = [
        f'移除重複\nn = {c["duplicates_removed"]}',
        f'排除\nn = {c["title_abstract_excluded"]}',
        f'未取得全文\nn = {c["full_text_not_retrieved"]}',
        f'全文排除 n = {sum(v for _, v in ft)}：' + '、'.join(f'{CODE.get(k, k)} {v}' for k, v in ft[:3]) + '\n' + '、'.join(f'{CODE.get(k, k)} {v}' for k, v in ft[3:]),
        f'課堂版收緊條件排除 n = {c["included"] - s["n_studies"]}\n預印本 {s["scope_excluded_r1_preprint"]}、無閉源直接比較 {s["scope_excluded_r2_no_closed"]}'
        + (f'、核對時發現不符原條件 {s["scope_excluded_other"]}' if s.get('scope_excluded_other') else ''),
    ]
    fig, ax = plt.subplots(figsize=(16.64, 7.4), dpi=100)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set(xlim=(0, 100), ylim=(-1, 100))
    ax.axis('off')
    ys = [93, 76, 59, 42, 25, 7]
    for i, ((label, _), y) in enumerate(zip(left, ys)):
        final = i == len(left) - 1
        ax.add_patch(FancyBboxPatch((4, y - 6), 26, 12, boxstyle='round,pad=0,rounding_size=1.2',
                                    facecolor=OPEN if final else '#FDFCF9', edgecolor=OPEN if final else LINE, linewidth=2))
        ax.text(17, y, label, ha='center', va='center', fontsize=17, color='#F7F6F2' if final else INK, fontweight=600 if final else 'normal')
        if i < len(left) - 1:
            ax.add_patch(FancyArrowPatch((17, y - 6), (17, ys[i + 1] + 6), arrowstyle='-|>', mutation_scale=18, color=SOFT, linewidth=1.8))
    for i, (label, y) in enumerate(zip(right, ys)):
        ry = (y + ys[i + 1]) / 2
        ax.add_patch(FancyBboxPatch((40, ry - 5.2), 58, 10.4, boxstyle='round,pad=0,rounding_size=1.2',
                                    facecolor='#FDFCF9', edgecolor=LINE, linewidth=1.5))
        ax.text(41.5, ry, label, ha='left', va='center', fontsize=14, color=SOFT, linespacing=1.3)
        ax.add_patch(FancyArrowPatch((17, ry), (40, ry), arrowstyle='-|>', mutation_scale=16, color=LINE, linewidth=1.5))
    out = ROOT / 'figures/slides/prisma_slide.png'
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=100, facecolor=BG)
    print(out)


if __name__ == '__main__':
    main()
