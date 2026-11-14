"""Match records by identifiers in descending order of specificity."""
import re
from collections import defaultdict

from common import normalize_doi, normalize_title


def normalize_arxiv(value):
    value = (value or '').strip().lower()
    value = re.sub(r'^https?://(?:www\.)?arxiv\.org/(?:abs|pdf)/', '', value)
    value = re.sub(r'^(?:arxiv:)', '', value)
    return re.sub(r'(?:v\d+)?(?:\.pdf)?$', '', value)


def match_rows(rows, candidates, arxiv=False):
    fields = [('doi', normalize_doi), ('pmid', lambda x: (x or '').strip())]
    if arxiv:
        fields.append(('arxiv_id', normalize_arxiv))
    fields.append(('title', normalize_title))
    indexes = []
    for field, normalize in fields:
        index = defaultdict(list)
        for i, candidate in enumerate(candidates):
            value = normalize(candidate.get(field, ''))
            if value:
                index[value].append(i)
        indexes.append(index)
    results = []
    for row in rows:
        found = None
        for (field, normalize), index in zip(fields, indexes):
            value = normalize(row.get(field, ''))
            if value and value in index:
                matches = index[value]
                found = matches[0] if len(matches) == 1 else None
                break
        results.append(found)
    return results
