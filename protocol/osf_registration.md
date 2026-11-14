# OSF Registries 註冊表草稿

範本：**Generalized Systematic Review Registration**（OSF Registries → Register → 選此範本）。
以下依該範本的主要欄位整理，內容取自 `protocol/protocol.md` v0.2。欄位名稱以實際表單為準；表單有、本檔沒有的欄位，請從 protocol 對應節次複製。英文為貼上用。
**註冊前**：填完 protocol 1.3、1.5 的【待填】，並把 `protocol/protocol.md` 轉成 PDF 一起上傳。

---

**Title**
Open-weight large language models for information extraction from clinical free text: a systematic review

**Description**
A systematic review of studies that evaluate open-weight (publicly downloadable) large language models for extracting entities, relations, or predefined fields from real clinical free text (clinical notes, discharge summaries, radiology and pathology reports), reported according to PRISMA 2020.

**Contributors**: 【待填】

**Type of review**: Systematic review (methodological / technology evaluation)

**Review stage at registration**
Exploratory database searches (PubMed, Scopus, IEEE Xplore, ACM DL) were run on 3 November 2026 with non-harmonised search strings. Formal searches of all six sources with the final harmonised strategy were completed on 14 November 2026 (2,132 records; 1,389 after automated de-duplication), and all 10 validation studies were retrieved. An LLM assistant produced advisory title/abstract suggestions on these records. Human title/abstract screening, full-text screening, data extraction, and synthesis have not started.

**Start date**: 2026-11-03　**Planned end date**: 【待填】

**Background**
Clinical information is largely recorded as free text. Proprietary LLMs can extract structured information from such text but require sending patient records to external servers, raising privacy, cost, and reproducibility concerns. Open-weight LLMs can be deployed on-premises. Existing reviews of LLM-based clinical information extraction have not focused on open-weight models or on the adaptation strategies specific to locally deployed models.

**Primary research question**
How are open-weight LLMs used for information extraction from clinical free text, and how well do they perform?

**Secondary research questions**
RQ1 landscape (models, tasks, text types, note languages, trends); RQ2 adaptation strategies (zero-/few-shot, LoRA/QLoRA, full fine-tuning, RAG, quantisation) and their performance; RQ3 within-study performance relative to proprietary LLMs, BERT-type models, and rule-based methods; RQ4 deployment and reproducibility (local deployment, hardware, availability of code, prompts, weights, data).

**Expectations / hypotheses**: None (descriptive review).

**Inclusion criteria**
I1 at least one open-weight LLM: transformer-based generative pre-trained model (decoder-only or encoder–decoder), ≥1 billion parameters, weights publicly downloadable regardless of licence type; I2 real clinical free text (including de-identified public datasets; synthetic-only excluded); I3 information extraction (NER, relation extraction, attribute/negation detection, structured field extraction; outputs that are values explicitly documented in the text count as extraction even when framed as classification); I4 quantitative evaluation against a reference standard; I5 published 2022-01-01 to final search date; I6 journal articles, full conference papers, preprints (arXiv, medRxiv); I7 English-language articles (any note language).

**Exclusion criteria (in order)**
X1 publication type (reviews, editorials, commentaries, abstracts only, proceedings front matter, no full text); X2 non-English article; X3 no LLM; X4 proprietary LLMs only; X5 not clinical free text (including synthetic only); X6 not an extraction task (summarisation, QA, automated ICD/SNOMED coding, document-level classification or prediction requiring inference beyond the text, note generation, dialogue); X7 no quantitative evaluation; X8 duplicate report.

**Information sources**
PubMed/MEDLINE, Scopus, IEEE Xplore, ACM Digital Library, arXiv (API), medRxiv (via Europe PMC). All searched on the same day. Backward and forward citation searching of included studies via the OpenAlex API (one round each).

**Search strategy**
Three concept blocks (LLM terms including named open-weight model families; clinical text types; information extraction terms) combined with AND, in title/abstract/keywords (IEEE: All Metadata), from 2022. Full strings for each source are attached (protocol Section 3.4; `scripts/queries/`).

**Search validation procedure**
A set of 10 known eligible studies (`data/validation_set.csv`) must all be retrieved by the searches of the databases that index them. Formal search (14 Nov 2026): all 10 validation studies were retrieved; the formal results also contain all records of the exploratory PubMed (242), Scopus (10), and IEEE (23) searches.

**Procedures to contact authors**: One email for unclear or missing data; recorded as not reported after two weeks.

**Selection procedure**
De-duplication by script (normalised DOI, PMID, normalised title + year). Calibration on 50 random records (repeat if κ < 0.6). Two reviewers independently screen titles/abstracts (include if either says include/unsure) and full texts; disagreements resolved by discussion, then a third reviewer. Cohen's κ reported for both stages. An LLM assistant may provide suggestions with rationales but is not a reviewer.

**Software for selection**: Python scripts (version-controlled), Microsoft Excel screening forms.

**Data extraction**
Piloted form (3 studies); one reviewer extracts, a second verifies every field; each value recorded with page/table location. Fields: study, data, task, models (name, size, domain, licence), adaptation strategy, deployment, comparators, results (metric, value, evaluation level, matching), reproducibility, stated limitations and reasons for open models.

**Missing data**: Not imputed; recorded as not reported.

**Risk of bias**
Adapted QUADAS-2 (data and sample; reference standard; model and evaluation flow, including contamination and test-set separation; analysis), informed by TRIPOD-LLM; low/high/unclear per domain; two independent reviewers.

**Synthesis**
Narrative synthesis following SWiM; no pooling expected. Grouping by task, text type, adaptation strategy, model size. Within-study difference in F1 between the best open-weight model and the best comparator of each class, summarised by median, range, and direction of effect. Side-by-side display for ≥3 studies on the same public dataset and metric. Sensitivity analyses excluding preprints and high risk-of-bias studies.

**Effect size**: Reported metrics (F1 preferred; then accuracy, precision/recall); within-study F1 differences.

**Heterogeneity**: Explored descriptively by grouping variables.

**Publication bias**: Selective-reporting assessment per study; publication bias discussed narratively (no funnel plots).

**Software for synthesis**: Python (matplotlib), scripts shared on OSF.

**Certainty of evidence**: Adapted GRADE or justified non-applicability, decided before synthesis.

**Deviations already known at registration**
Exploratory searches (3 Nov 2026) used non-harmonised strings and are not used as formal results. Formal searches were completed on 14 November 2026, before this registration; screening begins after registration. The arXiv search used a run earlier the same day with the identical query because later re-runs were rate-limited by the arXiv API.

**Conflicts of interest / Funding**: 【待填】
