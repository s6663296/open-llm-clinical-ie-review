"""Render a two-pathway PRISMA-style flow with explicitly unknown counts."""
import argparse
import csv
import json
import textwrap
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch


def database_label(counts):
    """Render the database total and individual source counts."""
    if not isinstance(counts, dict):
        return 'Records identified from:\nDatabases (n = ?)'
    total = sum(counts.values()) if all(isinstance(v, int) for v in counts.values()) else '?'
    lines = ['Records identified from:', f'Databases (n = {total}):']
    lines.extend(f'{name} (n = {value if value is not None else "?"})' for name, value in counts.items())
    return '\n'.join(lines)


def box_height(label):
    """Return height in inches for a multiline label with padding."""
    return max(.65, len(label.splitlines()) * .16 + .24)


def main():
    """Draw identification, screening and inclusion with exclusion branches."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--counts', default='analysis/prisma_counts.json')
    parser.add_argument('--out-prefix', default='figures/prisma_flow')
    parser.add_argument('--results-numbers', default='analysis/results_numbers.json')
    parser.add_argument('--scope-numbers', default=None)
    args = parser.parse_args()
    data = json.loads(Path(args.counts).read_text(encoding='utf-8-sig'))
    def number(value):
        """Render unavailable counts with a question mark."""
        return '?' if value is None else str(value)
    def difference(a, b):
        """Subtract only when both inputs are known."""
        return a - b if a is not None and b is not None else None
    def reasons(value):
        """Render observed full-text exclusion reasons or an unknown."""
        return '\n'.join(f'{k} (n = {v})' for k, v in value.items()) if value else ('None (n = 0)' if value == {} else 'Reasons (n = ?)')
    results_path = Path(args.results_numbers)
    results = json.loads(results_path.read_text(encoding='utf-8-sig')) if results_path.exists() else {}
    scope = json.loads(Path(args.scope_numbers).read_text(encoding='utf-8-sig')) if args.scope_numbers else None
    provisional = False
    if scope is not None and 'provisional_scope_rows' in scope:
        with Path('extraction/scope_restriction.csv').open(encoding='utf-8-sig', newline='') as stream:
            provisional = any(not row.get('author_decision', '').strip() for row in csv.DictReader(stream))
    included_studies = results.get('N_STUDIES')
    if included_studies is None:
        included_studies = data.get('included')
    counts = data.get('database_counts')
    database = sum(counts.values()) if isinstance(counts, dict) and all(isinstance(v, int) for v in counts.values()) else None
    boxes = [
        (.01,.89,.22,.075,database_label(counts)),
        (.26,.89,.22,.075,f'Records removed before screening:\nDuplicate records (n = {number(data.get("duplicates_removed"))})'),
        (.52,.89,.22,.075,f'Records identified from:\nOther methods (n = {number(data.get("citation_identified"))})'),
        (.01,.74,.22,.065,f'Records screened\n(n = {number(data.get("screened"))})'),
        (.26,.74,.22,.065,f'Records excluded\n(n = {number(data.get("title_abstract_excluded"))})'),
        (.52,.74,.22,.065,f'Records screened\n(n = {number(data.get("citation_screened"))})'),
        (.77,.74,.22,.065,f'Records excluded\n(n = {number(data.get("citation_excluded"))})'),
        (.01,.60,.22,.065,f'Reports sought for retrieval\n(n = {number(difference(data.get("screened"), data.get("title_abstract_excluded")))})'),
        (.26,.60,.22,.065,f'Reports not retrieved\n(n = {number(data.get("full_text_not_retrieved"))})'),
        (.52,.60,.22,.065,f'Reports sought for retrieval\n(n = {number(difference(data.get("citation_screened"), data.get("citation_excluded")))})'),
        (.77,.60,.22,.065,f'Reports not retrieved\n(n = {number(data.get("citation_not_retrieved"))})'),
        (.01,.45,.22,.065,f'Reports assessed for eligibility\n(n = {number(data.get("full_text_assessed"))})'),
        (.26,.40,.22,.115,'Reports excluded:\n' + reasons(data.get('full_text_excluded_by_code'))),
        (.52,.45,.22,.065,f'Reports assessed for eligibility\n(n = {number(data.get("citation_assessed"))})'),
        (.77,.40,.22,.115,'Reports excluded:\n' + reasons(data.get('citation_excluded_by_code'))),
        (.26,.11,.48,.09,f'Studies included in review (n = {number(included_studies)})\nReports from databases (n = {number(data.get("included"))})\nReports from other methods (n = {number(data.get("citation_included"))})'),
    ]
    # Wide inclusion boxes have room for their complete counts.
    boxes = [(x, y, w, h, '\n'.join(textwrap.fill(line, width=65 if scope is not None and w > .4 else 31, break_long_words=True, break_on_hyphens=False) for line in label.split('\n'))) for x, y, w, h, label in boxes]
    top_extra = max(0, box_height(boxes[0][4]) - .9)
    reason_extra = max(0, max(box_height(boxes[i][4]) for i in (12, 14)) - 1.38)
    scope_extra = 2.6 if scope is not None else 0
    total_height = 12 + top_extra + reason_extra + scope_extra
    def map_y(y):
        return (y * 12 + scope_extra + (reason_extra if y >= .45 else 0) + (top_extra if y >= .89 else 0)) / total_height
    fig, ax = plt.subplots(figsize=(16, total_height))
    fig.subplots_adjust(left=.12, right=.98, bottom=.06, top=.98)
    ax.set(xlim=(0,1), ylim=(0,1))
    ax.axis('off')
    for x,y,w,h,label in boxes:
        bottom = map_y(y)
        if (x, y) == (.01, .89):
            bottom -= top_extra / total_height
        height = max(h * 12, box_height(label)) / total_height
        ax.add_patch(Rectangle((x,bottom),w,height,fill=False,linewidth=1))
        ax.text(x+.008,bottom+height/2,label,ha='left',va='center',fontsize=8,wrap=True)
    def arrow(start, end):
        """Draw a directed connector between flow boxes."""
        start_y = map_y(start[1])
        if start == (.12, .89):
            start_y -= top_extra / total_height
        ax.add_patch(FancyArrowPatch((start[0],start_y),(end[0],map_y(end[1])),arrowstyle='->',mutation_scale=10,linewidth=1))
    for x in (.12,.63):
        for top,bottom in ((.89,.805),(.74,.665),(.60,.515)):
            arrow((x,top),(x,bottom))
        arrow((x,.45),(x,.27))
        if scope is None:
            arrow((x,.27),(.50,.20))
        else:
            included_top = map_y(.11) + max(.09 * 12, box_height(boxes[-1][4])) / total_height
            ax.add_patch(FancyArrowPatch((x, map_y(.27)), (.50, included_top), arrowstyle='->', mutation_scale=10, linewidth=1))
    for y in (.922,.772,.632,.482):
        arrow((.23,y),(.26,y))
    for y in (.772,.632,.482):
        arrow((.74,y),(.77,y))
    for label,bottom,height in [('Identification',.86,.105),('Screening',.38,.44),('Included',.10,.11)]:
        mapped_bottom = .35 / total_height if label == 'Included' and scope is not None else map_y(bottom)
        mapped_height = map_y(bottom+height)-mapped_bottom
        ax.add_patch(Rectangle((-.095,mapped_bottom),.06,mapped_height,facecolor='#56B4E9',clip_on=False))
        ax.text(-.065,mapped_bottom+mapped_height/2,label,rotation=90,ha='center',va='center',fontsize=11)
    if scope is not None:
        suffix = ' (provisional)' if provisional else ''
        excluded = difference(scope.get('scope_total'), scope.get('n_studies'))
        exclusion_label = (f'Excluded by classroom scope restriction{suffix} (n = {number(excluded)}):\n'
                           f'Preprint (n = {number(scope.get("scope_excluded_r1_preprint"))})\n'
                           f'No direct closed-LLM comparison (n = {number(scope.get("scope_excluded_r2_no_closed"))})'
                           + (f'\nNot clinical text / no full text (n = {scope["scope_excluded_other"]})' if scope.get('scope_excluded_other') else ''))
        exclusion_label = '\n'.join(textwrap.fill(line, width=30, break_on_hyphens=False) for line in exclusion_label.splitlines())
        final_label = f'Studies included in classroom review{suffix}\n(n = {number(scope.get("n_studies"))})'
        def scope_box(x, bottom, width, height, label):
            ax.add_patch(Rectangle((x, bottom / total_height), width, height / total_height, fill=False, linewidth=1))
            ax.text(x + .008, (bottom + height / 2) / total_height, label, ha='left', va='center', fontsize=8)
        scope_box(.70, 1.7, .29, 1.25, exclusion_label)
        scope_box(.26, .35, .48, .8, final_label)
        def scope_arrow(start, end):
            ax.add_patch(FancyArrowPatch(start, end, arrowstyle='->', mutation_scale=10, linewidth=1))
        branch_y = 2.32 / total_height
        scope_arrow((.50, map_y(.11)), (.50, branch_y))
        scope_arrow((.50, branch_y), (.70, branch_y))
        scope_arrow((.50, branch_y), (.50, 1.15 / total_height))
    fig.text(.5,.015,'DRAFT – incomplete counts',ha='center',fontsize=9)
    prefix = Path(args.out_prefix)
    prefix.parent.mkdir(parents=True,exist_ok=True)
    for ext in ('png','pdf','svg'):
        fig.savefig(str(prefix)+'.'+ext,dpi=300,facecolor='white')
    plt.close(fig)


if __name__ == '__main__':
    main()
