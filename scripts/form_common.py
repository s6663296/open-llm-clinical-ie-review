"""Shared parsers and formatting for extraction workbooks."""
import re
from pathlib import Path
from openpyxl.styles import Font
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]


def codebook_tables():
    """Parse the two field tables from the original Markdown."""
    text = (ROOT / 'extraction/codebook.md').read_text(encoding='utf-8')
    result = {}
    for name in ('studies', 'results'):
        section = text.split('## `' + name + '`', 1)[1].split('\n## ', 1)[0]
        rows = []
        for line in section.splitlines():
            if line.startswith('|'):
                cells = [x.strip() for x in line.strip().strip('|').split('|')]
                if len(cells) == 3 and cells[0] != '欄位' and not cells[0].startswith('---'):
                    rows.append(cells)
        result[name] = rows
    return result


def questions():
    """Parse numbered signalling questions from all four domains."""
    text = (ROOT / 'extraction/rob_tool.md').read_text(encoding='utf-8')
    return re.findall(r'^\|\s*([1-4]\.\d+)\s*\|\s*(.*?)\s*\|', text, re.M)


def validation(ws, column, choices, start=3):
    """Attach a list validation to a generous range of blank rows."""
    dv = DataValidation(type='list', formula1='"' + ','.join(choices) + '"')
    dv.showErrorMessage = True
    dv.error = '請從清單中選擇'
    ws.add_data_validation(dv)
    letter = get_column_letter(column)
    dv.add(f'{letter}{start}:{letter}10000')


def format_sheet(ws):
    """Set visible headings and frozen field descriptions."""
    ws.freeze_panes = 'A3'
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for cell in ws[2]:
        cell.font = Font(italic=True, color='777777')
    for column in ws.columns:
        ws.column_dimensions[column[0].column_letter].width = 24
