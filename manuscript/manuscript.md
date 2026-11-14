# Open-weight large language models for information extraction from clinical free text: a systematic review

<!--
Drafting rules (from AGENTS.md):
- Every number in this manuscript must come from a file or script output. Placeholders are upper-case keys in double curly braces, filled from `analysis/prisma_counts.json` and `analysis/` outputs; do not type numbers by hand.
- Every claim about an included study must be traceable to `extraction/extraction.xlsx` (with page numbers).
- PRISMA 2020 item numbers are given in [#n] tags to support the checklist (`manuscript/prisma_checklist.md`).
-->

---

## Abstract  [#2; PRISMA 2020 for Abstracts]

**Background**: Clinical information is largely recorded as free text. Proprietary large language models (LLMs) can extract structured information from such text, but sending patient records to external servers raises privacy, cost, and reproducibility concerns. Open-weight LLMs can be deployed on-premises.
**Objective**: To systematically review how open-weight LLMs are used for information extraction from clinical free text, and how well they perform.
**Methods**: We searched PubMed, Scopus, IEEE Xplore, ACM Digital Library, arXiv, and medRxiv (via Europe PMC) on {{SEARCH_DATE}} for studies published from 2022 onward. Eligible studies evaluated at least one open-weight LLM (≥1 billion parameters) on an information extraction task over real clinical free text with a quantitative reference-standard evaluation. A large language model screened records and assessed full texts, with every decision verified by a human reviewer. Risk of bias was assessed with a QUADAS-2–derived tool. Results were synthesised narratively following SWiM.
**Results**: {{ABSTRACT_RESULTS}}
**Conclusions**: {{ABSTRACT_CONCLUSIONS}}
**Funding**: None.

---

## 1. Introduction

### 1.1 Rationale  [#3]

A large share of clinically relevant information — diagnoses, medications, tumour characteristics, social determinants — is recorded only in free-text notes, discharge summaries, and radiology and pathology reports. Converting this text into structured data underpins clinical research, quality monitoring, registry curation, and decision support. Information extraction (IE) has historically relied on rule-based systems and supervised models such as BERT variants, which require task-specific annotation.

Generative LLMs can perform extraction from instructions and a few examples, reducing annotation needs. However, the most widely studied models are proprietary and accessed through vendor APIs, which requires transmitting patient text outside the institution and exposes studies to undocumented model changes. Open-weight models (whose weights can be downloaded and run locally) address these concerns, and their capability has improved rapidly since 2023.

Several reviews have examined LLMs for clinical information extraction. A scoping review of oncology data extraction (MEDLINE, searched June 2024) included 24 studies, 75% of which used BERT-type models and 25% ChatGPT [1]. A scoping review of generative-AI extraction from clinical notes and guidelines included 16 studies and found GPT-4 the best-performing model in 11 of them [2]. A systematic literature review of LLMs for clinical IE synthesised 85 studies across tasks, methods, and datasets [3]. A broader systematic review of generative LLMs applied to EHR data (searched to November 2024) included 196 studies, in which GPT-4 and ChatGPT were used in 60.2% and 57.7% respectively, and most addressed clinical decision support rather than extraction [4]. Domain-specific reviews of registry population [5] and uro-oncology data extraction [6] included 15 and 14 studies, respectively; the former identified only one study using a generative LLM. A narrative review contrasted open-source and proprietary LLMs for clinical and biomedical extraction across performance, reproducibility, cost, transparency, and governance, but did not report a systematic search [11]. None of these reviews systematically identified studies of open-weight models on real clinical text, separated them from proprietary models, or compared adaptation strategies such as parameter-efficient fine-tuning and quantisation that are specific to locally deployed models. Their searches also predate much of the 2025–2026 literature, in which open-weight model families (e.g., Llama 3, Qwen, Gemma) became widely used.
<!-- Statements above are taken from the abstracts of the cited records in the initial search exports; verify against full texts before submission (prior-review list: `manuscript/prior_reviews.md`). -->

### 1.2 Objectives  [#4]

The primary question was: how are open-weight LLMs used for information extraction from clinical free text, and how well do they perform? We addressed four sub-questions:

- **RQ1 (landscape)**: Which open-weight LLMs (family, size, domain adaptation) have been applied to which extraction tasks, text types, and note languages, and how has this changed over time?
- **RQ2 (adaptation strategy)**: Which adaptation strategies (zero-shot, few-shot, parameter-efficient fine-tuning, full fine-tuning, retrieval augmentation, quantisation) are used, and how does performance differ across them?
- **RQ3 (relative performance)**: Within the same study and dataset, how do open-weight LLMs compare with proprietary LLMs, BERT-type models, and rule-based methods?
- **RQ4 (deployment and reproducibility)**: Are models deployed locally, on what hardware, and are code, prompts, and data shared?

---

## 2. Methods

This review is reported according to PRISMA 2020 [7]. Deviations from the review protocol are reported in Section 2.12 [#24c].

### 2.1 Eligibility criteria  [#5]

Studies were included if they met all of the following:

1. **Model (I1)**: evaluated at least one open-weight LLM, defined as a transformer-based generative pre-trained language model (decoder-only or encoder–decoder) with at least 1 billion parameters whose weights are publicly downloadable, irrespective of whether the licence is OSI-approved (e.g., Llama and Gemma community licences qualified). Licence type was extracted.
2. **Text (I2)**: input was clinical free text originating from real patient care, including de-identified public datasets (e.g., MIMIC, n2c2/i2b2). Studies using only synthetic clinical text were excluded; for studies using both, only results on real text were extracted.
3. **Task (I3)**: the task was information extraction — identifying and outputting specific entities, relations, or values of predefined fields from text (named entity recognition, relation extraction, attribute/negation detection, structured field extraction). Tasks whose output is a value explicitly documented in the text were treated as extraction even when framed as classification (e.g., smoking status, tumour stage). Summarisation, question answering, automated ICD/SNOMED coding, document-level classification or prediction requiring inference beyond the text, note generation, and dialogue were excluded.
4. **Evaluation (I4)**: reported at least one quantitative performance metric against a reference standard (manual annotation or existing structured data).
5. **Date (I5)**: published from 1 January 2022 to the final search date.
6. **Publication type (I6)**: journal articles, full conference papers, and preprints (arXiv, medRxiv). Reviews, editorials, commentaries, conference abstracts, and records without full text were excluded.
7. **Language (I7)**: articles in English; the language of the clinical text was not restricted and was extracted.

Excluded reports were assigned the first applicable reason in the order X1 (publication type), X2 (non-English article), X3 (no LLM), X4 (proprietary LLMs only), X5 (not clinical free text, including synthetic-only), X6 (not an extraction task), X7 (no quantitative evaluation), X8 (duplicate report of an included study).

For synthesis, studies (not reports) were the unit of analysis [#5]. Preprint and peer-reviewed versions, or conference and extended journal versions, of the same work were linked as one study; the peer-reviewed version was the primary data source.

### 2.2 Information sources  [#6]

We searched PubMed/MEDLINE, Scopus, IEEE Xplore, ACM Digital Library, arXiv (via the arXiv API), and medRxiv (via Europe PMC). All sources were searched on {{SEARCH_DATE}}. We additionally performed one round each of backward (references) and forward (citing articles) citation searching for all included studies using the OpenAlex API on {{CITATION_SEARCH_DATE}}.

### 2.3 Search strategy  [#7]

The search combined three concept blocks — (A) LLMs, including generic terms and named model families; (B) clinical text types; and (C) information extraction — with AND, restricted to title, abstract, and keywords (All Metadata in IEEE Xplore) and to publication from 2022. Block A did not require the term "open-source" because many studies comparing proprietary and open-weight models describe them only as "LLMs"; open-weight status was assessed during screening. Full search strings for every source, as executed, are provided in Supplementary Appendix S1. The search strategy was validated by confirming retrieval of a set of {{N_VALIDATION}} known eligible studies (Appendix S1). Searches were executed with version-controlled scripts where an API was available (PubMed E-utilities, arXiv API, Europe PMC REST API); queries, execution timestamps, and record counts were logged automatically.

### 2.4 Selection process  [#8]

Records from all sources were merged and de-duplicated with a script (exact match on normalised DOI, PubMed ID, or normalised title with publication year within one year; near-identical titles were flagged for manual review). Titles and abstracts were screened by a large language model (Claude Sonnet) using a fixed instruction set that operationalised the eligibility criteria and exclusion codes; for each record it returned a decision (include, exclude, or unsure), an exclusion code, a rationale, and verbatim evidence phrases from the title or abstract. To validate this step, one reviewer independently screened a random sample of 50 records blind to the model output (agreement: κ = {{KAPPA_AI_HUMAN}}; model sensitivity for records the reviewer judged include or unsure: {{AI_SENSITIVITY}}). The reviewer then verified every model decision, confirming or overriding it ({{N_OVERRIDES}} of {{N_SCREENED}} decisions overridden); the human decision was final, and any record marked include or unsure by either the model or the reviewer proceeded to full-text assessment. Full texts were assessed by the same procedure: the model judged each full text against the eligibility criteria with an exclusion code, rationale, and page reference; the reviewer first assessed a random 20% sample (at least 20 reports) blind to the model output (κ = {{KAPPA_FT}}) and then verified every model decision. Reasons for exclusion were recorded for every excluded report. Because the review had a single author, there was no second reviewer or arbiter; the human decision was final, and uncertain cases were re-checked against the eligibility rules with the reasoning recorded.

Use of automation [#8]: the model, its instructions, and all per-record outputs are provided in Supplementary Appendix S5. Because the human reviewer verified rather than independently duplicated the model's decisions, screening at both stages was not independent dual screening; this is discussed as a limitation.

### 2.5 Data collection process  [#9]

Data were extracted into a piloted form (piloted on three studies). An LLM assistant pre-populated every field with its page, table, or figure location, and the reviewer verified each field against the source and corrected it where needed; the proportion of corrected fields is reported. When data were unclear, study authors were contacted once by email; data not received within two weeks were recorded as not reported.

### 2.6 Data items  [#10a, #10b]

**Outcomes [#10a]**: The primary outcome was extraction performance, with F1 score prioritised; if F1 was not reported we extracted accuracy, then precision and recall. Where multiple evaluation levels were reported, entity-level strict matching was preferred. All tasks within a study were extracted and analysed by task.

**Other variables [#10b]**: study characteristics (first author, year, country, publication type, peer review status); data (note language, text type, dataset, public availability, number of institutions and documents, annotation method and inter-annotator agreement); task (type, extraction targets, clinical domain); models (name, version, parameter count, domain-specific pre-training, licence); adaptation strategy (zero-shot, few-shot and number of examples, chain-of-thought, LoRA/QLoRA, full fine-tuning, retrieval augmentation, quantisation bit-width, output format constraints); deployment (local or cloud, hardware, inference time or cost); comparators (proprietary LLMs, BERT-type models, rule-based systems, humans); results (metric, value, evaluation level, matching criterion, test set size); reproducibility (availability of code, prompts, fine-tuned weights, data); stated limitations and stated reasons for using open-weight models.

### 2.7 Study risk of bias assessment  [#11]

No risk-of-bias tool exists for evaluations of LLM-based information extraction. We adapted the four QUADAS-2 domains [8], informed by TRIPOD-LLM reporting items [10]: (1) data and sample (representativeness, single vs. multiple institutions, sample size); (2) reference standard (number and qualification of annotators, reported agreement, availability of guidelines); (3) model and evaluation flow (separation of test data from prompt development and fine-tuning data; risk of contamination when public datasets may be in pre-training corpora; reporting of only the best prompt); and (4) analysis (metric definitions, reporting of variability across runs or confidence intervals, fairness of comparisons). Each domain was rated low, high, or unclear risk; an LLM assistant proposed a rating with rationale and page references, and the reviewer verified each rating and made the final judgement. The signalling questions are given in Appendix S3.

### 2.8 Effect measures  [#12]

Performance was summarised as reported metric values (F1, precision, recall, accuracy). For within-study comparisons (RQ3), the effect measure was the difference in F1 between the best-performing open-weight LLM and the best-performing comparator of each class, evaluated on the same data and with the same evaluation procedure.

### 2.9 Synthesis methods  [#13a–f]

[#13a] Studies were grouped by task type, text type, adaptation strategy, and model size for each synthesis. [#13b] Metrics were used as reported; no conversion or imputation was performed. [#13c] Results are presented in structured tables and figures (annual trend, model family frequency, task distribution, open-weight vs. comparator differences, fine-tuning vs. prompting). [#13d] Because datasets, tasks, and metrics were expected to be highly heterogeneous, we did not pool results statistically and followed the Synthesis Without Meta-analysis (SWiM) guideline [9]. For RQ3 we summarised within-study differences by median and range and by vote counting based on direction of effect. Where at least three studies used the same public dataset and metric, their results were displayed side by side without pooling. [#13e] Heterogeneity was explored descriptively across the grouping variables above. [#13f] Sensitivity analyses excluded (a) preprints and (b) studies at high risk of bias in any domain.

### 2.10 Reporting bias assessment  [#14]

We assessed selective reporting by comparing evaluations described in methods with those reported in results and by recording whether studies reported only their best configuration. Publication bias was discussed narratively; funnel plots were not used because effect sizes were not comparable across studies.

### 2.11 Certainty assessment  [#15]

{{CERTAINTY_METHOD}}
<!-- Decide at E2: adapted GRADE or justified non-applicability (protocol 3.11). -->

### 2.12 Deviations from the protocol  [#24c]

An exploratory search of PubMed, Scopus, IEEE Xplore, and ACM Digital Library was performed on 3 November 2026 with database-specific search strings before the protocol was finalised. Because the search terms and fields were inconsistent across databases, we harmonised the search strategy, added arXiv and medRxiv, and re-ran all searches; the exploratory search results were retained but not used as the formal results. {{OTHER_DEVIATIONS}}

---

## 3. Results

### 3.1 Study selection  [#16a, #16b]

The searches identified {{N_IDENTIFIED}} records ({{N_BY_SOURCE}}). After removing {{N_DUPLICATES}} duplicates, {{N_SCREENED}} records were screened by title and abstract, of which {{N_EXCLUDED_TA}} were excluded. Of {{N_SOUGHT}} reports sought for retrieval, {{N_NOT_RETRIEVED}} could not be retrieved; {{N_ASSESSED}} were assessed in full text, and {{N_EXCLUDED_FT}} were excluded ({{FT_EXCLUSION_REASONS}}). Citation searching identified {{N_CITATION}} additional records, of which {{N_CITATION_INCLUDED}} were included. In total, {{N_STUDIES}} studies ({{N_REPORTS}} reports) were included (Figure 1). Agreement between the reviewer and the model on the blind samples was κ = {{KAPPA_AI_HUMAN}} at title/abstract screening and κ = {{KAPPA_FT}} at full-text assessment; the reviewer overrode {{N_OVERRIDES}} of {{N_SCREENED}} title/abstract decisions and {{N_OVERRIDES_FT}} of {{N_ASSESSED}} full-text decisions. Studies that appeared to meet the criteria but were excluded are listed with reasons in Appendix S2 [#16b].

### 3.2 Study characteristics  [#17]

{{RESULTS_CHARACTERISTICS}}

### 3.3 Risk of bias  [#18]

{{RESULTS_ROB}}

### 3.4 Results of individual studies  [#19]

{{RESULTS_INDIVIDUAL}}
<!-- Table 2: per-study best open-weight result and comparators; full data in Appendix S4. -->

### 3.5 Results of syntheses  [#20a–d]

#### RQ1 — Models, tasks, and text types
{{RESULTS_RQ1}}

#### RQ2 — Adaptation strategies
{{RESULTS_RQ2}}

#### RQ3 — Open-weight vs. comparators
{{RESULTS_RQ3}}

#### RQ4 — Deployment and reproducibility
{{RESULTS_RQ4}}

#### Sensitivity analyses
{{RESULTS_SENSITIVITY}}

### 3.6 Reporting biases  [#21]

{{RESULTS_REPORTING_BIAS}}

### 3.7 Certainty of evidence  [#22]

{{RESULTS_CERTAINTY}}

---

## 4. Discussion  [#23a–d]

### 4.1 Principal findings  [#23a]
{{DISCUSSION_FINDINGS}}

### 4.2 Limitations of the evidence  [#23b]
{{DISCUSSION_EVIDENCE_LIMITS}}

### 4.3 Limitations of the review process  [#23c]
Limitations include restriction to English-language articles; reliance on title, abstract, and keyword fields, which may miss studies that mention open-weight models only in the full text; the rapid pace of preprint publication, which means relevant studies may have appeared after the search date; the use of an adapted, unvalidated risk-of-bias tool; and screening, data extraction, and risk-of-bias assessment by a language model with single-reviewer verification rather than independent dual human review, which may increase the risk of missed eligible studies despite blind validation on a random sample. {{DISCUSSION_REVIEW_LIMITS}}

### 4.4 Implications  [#23d]
{{DISCUSSION_IMPLICATIONS}}

---

## 5. Other information

- **Amendments** [#24c]: Section 2.12.
- **Support** [#25]: No specific funding was received.
- **Competing interests** [#26]: The author declares no competing interests.
- **Availability of data, code, and other materials** [#27]: Search strings, search logs, screening records, the extraction form and data, and analysis scripts are provided in the supplementary materials.

## References

1. Chen D, Alnassar SA, Avison KE, Huang RS, Raman S. Large language model applications for health information extraction in oncology: scoping review. JMIR Cancer. 2025;11:e65984. doi:10.2196/65984
2. Abdellaoui C, Redjdal A, Seroussi B. Generative-AI-based approaches for information extraction from clinical notes: a scoping review. Stud Health Technol Inform. 2025;328:193-197. doi:10.3233/SHTI250700
3. Rodrigues T, Teixeira Lopes C. Harnessing large language models for clinical information extraction: a systematic literature review. ACM Trans Comput Healthcare. 2025;6(4):47. doi:10.1145/3744660
4. Du X, Zhou Z, Wang Y, et al. Testing and evaluation of generative large language models in electronic health record applications: a systematic review. J Am Med Inform Assoc. 2026;33(3):743-753. doi:10.1093/jamia/ocaf233 (preprint: medRxiv doi:10.1101/2024.08.11.24311828)
5. Liu L, Blake V, Barman M, et al. Using natural language processing to extract information from clinical text in electronic medical records for populating clinical registries: a systematic review. J Am Med Inform Assoc. 2026;33(2):484-499. doi:10.1093/jamia/ocaf176
6. Greß J, Otto G, Sommer S, et al. Artificial intelligence applications for automated data extraction and secondary use of clinical information in uro-oncology: a systematic review. Eur Urol Open Sci. 2026;86:68-78. doi:10.1016/j.euros.2026.02.006
7. Page MJ, McKenzie JE, Bossuyt PM, et al. The PRISMA 2020 statement: an updated guideline for reporting systematic reviews. BMJ. 2021;372:n71. doi:10.1136/bmj.n71
8. Whiting PF, Rutjes AWS, Westwood ME, et al. QUADAS-2: a revised tool for the quality assessment of diagnostic accuracy studies. Ann Intern Med. 2011;155(8):529-536. doi:10.7326/0003-4819-155-8-201110180-00009
9. Campbell M, McKenzie JE, Sowden A, et al. Synthesis without meta-analysis (SWiM) in systematic reviews: reporting guideline. BMJ. 2020;368:l6890. doi:10.1136/bmj.l6890
10. Gallifant J, Afshar M, Ameen S, et al. The TRIPOD-LLM reporting guideline for studies using large language models. Nat Med. 2025;31(1):60-69. doi:10.1038/s41591-024-03425-5
11. Sugihara Y, Milosavljevic A, Jankovskaja S, Falk M. A review for navigating the trade-offs: evaluating open-source and proprietary large language models for clinical and biomedical information extraction. Front Digit Health. 2026;8:1778786. doi:10.3389/fdgth.2026.1778786
<!-- Refs 1–6: details copied from the initial search export records (PubMed/ACM). Refs 7–10: title, journal, volume, pages and first author verified against Crossref on 2026-11-14 (co-author lists for ref 10 to be re-checked). Add further references only with verified DOIs. -->
