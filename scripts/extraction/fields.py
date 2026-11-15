"""D1 classroom subset: field lists and allowed values (single source for brief, checker, merge).

Subset of extraction/codebook.md (2026-11-14 decision: models, tasks, performance only).
Multi-valued fields use '; ' as separator. NR = not reported, NA = not applicable.
"""

STUDY_FIELDS = [
    'study_id', 'record_id', 'first_author', 'year', 'pub_type',
    'note_language', 'note_language_src',
    'text_type', 'text_type_src',
    'clinical_domain',
    'datasets', 'datasets_src',
    'task_types',
    'extraction_targets', 'extraction_targets_src',
    'open_models', 'open_models_src',
    'medical_domain_model',
    'closed_comparators', 'bert_comparators', 'rule_comparators', 'comparators_src',
    'strategies', 'strategies_src',
    'deployment', 'deployment_src',
    'note', 'extractor',
]

RESULT_FIELDS = [
    'result_id', 'study_id', 'task', 'task_type', 'dataset', 'test_n',
    'model', 'model_class', 'model_family', 'params_b', 'medical_domain',
    'strategy', 'strategy_detail', 'quantized',
    'metric', 'f1_avg', 'value_reported', 'metric_scale_original', 'value',
    'eval_level', 'matching', 'is_best_open', 'is_best_comparator',
    'value_src', 'value_context', 'note', 'extractor',
]

# Single-valued controlled fields.
ALLOWED = {
    'pub_type': {'journal', 'conference', 'preprint'},
    'medical_domain_model': {'yes', 'no'},
    'deployment': {'local', 'private cloud', 'public API', 'mixed', 'NR'},
    'task_type': {'NER', 'RE', 'attribute', 'field extraction', 'other'},
    'model_class': {'open LLM', 'closed LLM', 'BERT-type', 'rule-based', 'other'},
    'model_family': {'Llama', 'Mistral', 'Qwen', 'Gemma', 'DeepSeek', 'Phi', 'other', 'NA'},
    'medical_domain': {'yes', 'no', 'NA'},
    'strategy': {'zero-shot', 'few-shot', 'CoT', 'LoRA', 'QLoRA', 'full FT', 'RAG', 'other', 'NA'},
    'quantized': {'yes', 'no', 'NR', 'NA'},
    'metric': {'F1', 'precision', 'recall', 'accuracy', 'other'},
    'f1_avg': {'micro', 'macro', 'weighted', 'NR', 'NA'},
    'metric_scale_original': {'0-1', 'percent'},
    'eval_level': {'entity', 'relation', 'field', 'document', 'patient', 'NR'},
    'matching': {'strict', 'lenient', 'relaxed', 'NR', 'NA'},
    'is_best_open': {'yes', 'no'},
    'is_best_comparator': {'yes', 'no'},
}

# Multi-valued controlled fields ('; ' separated).
MULTI = {
    'task_types': ALLOWED['task_type'],
    'text_type': {'radiology report', 'pathology report', 'discharge summary', 'progress note',
                  'operative note', 'clinical note (mixed)', 'other'},
    'strategies': {'zero-shot', 'few-shot', 'CoT', 'LoRA', 'QLoRA', 'full FT', 'instruction tuning',
                   'RAG', 'quantization', 'constrained decoding', 'ensemble', 'other'},
}

# A *_src column must be filled (format 'p.N' optionally followed by a table/figure label)
# whenever its value columns are not NR/NA/none.
SRC_OF = {
    'note_language_src': ['note_language'],
    'text_type_src': ['text_type'],
    'datasets_src': ['datasets'],
    'extraction_targets_src': ['extraction_targets'],
    'open_models_src': ['open_models'],
    'comparators_src': ['closed_comparators', 'bert_comparators', 'rule_comparators'],
    'strategies_src': ['strategies'],
    'deployment_src': ['deployment'],
}

EMPTY_OK = {'NR', 'NA', 'none'}
