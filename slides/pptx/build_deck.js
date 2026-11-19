// Classroom PPTX for the systematic review (32 slides; structure follows the team's v5 edit of 2026-11-16, v10 layout fixes).
// Statistics are read at build time from analysis/*.json, screening/*, extraction/*; nothing is typed in by hand,
// except the adapted QUADAS-2 results, which come verbatim from the v5 deck (slides/pptx/quadas_v5.json, no source table in repo).
// Speaker notes: slides/pptx/speaker_notes.json (team's v5 script, wording on screening/verification corrected to the decision log).
// Usage (repo root): node slides/pptx/build_deck.js [out.pptx]  ->  slides/pptx/open_llm_clinical_ie_review.pptx
// After writing, the file is post-processed: East Asian font on chart text, ZIP folder entries dropped.
const fs = require('fs');
const path = require('path');
const pptxgen = require('pptxgenjs');
const JSZip = require('jszip');

const ROOT = path.resolve(__dirname, '..', '..');
const readJSON = (p) => JSON.parse(fs.readFileSync(path.join(ROOT, p), 'utf8').replace(/^﻿/, ''));
function readCSV(p) {
  const text = fs.readFileSync(path.join(ROOT, p), 'utf8').replace(/^﻿/, '');
  const rows = []; let row = [], cell = '', q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) { if (c === '"') { if (text[i + 1] === '"') { cell += '"'; i++; } else q = false; } else cell += c; }
    else if (c === '"') q = true;
    else if (c === ',') { row.push(cell); cell = ''; }
    else if (c === '\n' || c === '\r') { if (c === '\r' && text[i + 1] === '\n') i++; row.push(cell); rows.push(row); row = []; cell = ''; }
    else cell += c;
  }
  if (cell || row.length) { row.push(cell); rows.push(row); }
  const head = rows.shift();
  return rows.filter((r) => r.length > 1).map((r) => Object.fromEntries(head.map((h, i) => [h, r[i] ?? ''])));
}
const must = (cond, msg) => { if (!cond) throw new Error('Data no longer supports slide wording: ' + msg); };

// ---------- data ----------
const N = readJSON('analysis/slide_numbers.json');
const C = readJSON('analysis/prisma_counts.json');
const K = readJSON('analysis/sonnet_vs_opus.json');
const VR = readCSV('extraction/review/verify_report.csv');
const SID = Object.fromEntries(readCSV('extraction/study_ids.csv').map((r) => [r.study_id, r]));
const Q = readJSON('slides/pptx/quadas_v5.json');
const NOTES = readJSON('slides/pptx/speaker_notes.json');
const count = (arr, f) => arr.reduce((m, x) => { const k = f(x); m[k] = (m[k] || 0) + 1; return m; }, {});
const TA = count(readCSV('screening/title_abstract_final.csv').filter((r) => r.final_decision === 'exclude'), (r) => r.final_code);
const codexDir = path.join(ROOT, 'extraction/codex');
const STUDIES = fs.readdirSync(codexDir).filter((f) => /^batch_\d+_studies\.csv$/.test(f))
  .flatMap((f) => readCSV('extraction/codex/' + f)).filter((r) => N.study_ids.includes(r.study_id));
must(STUDIES.length === N.n_studies, 'codex studies cover the 39 included studies');
const langs = STUDIES.map((r) => r.note_language.split(';').map((x) => x.trim()).filter(Boolean));
const langNR = langs.filter((l) => l.length === 0 || (l.length === 1 && l[0] === 'NR')).length;
const langNonEn = langs.filter((l) => l.some((x) => x !== 'English' && x !== 'NR')).length;
const langEnOnly = langs.filter((l) => l.length === 1 && l[0] === 'English').length;
must(langEnOnly + langNonEn + langNR === N.n_studies, 'language groups add up');
const verdict = count(VR, (r) => r.verdict);
const dbTotal = Object.values(C.database_counts).reduce((a, b) => a + b, 0);
const sought = C.screened - C.title_abstract_excluded;
const ftExcluded = Object.values(C.full_text_excluded_by_code).reduce((a, b) => a + b, 0);
const scopeExcluded = C.included - N.n_studies;
must(Object.values(TA).reduce((a, b) => a + b, 0) === C.title_abstract_excluded, 'title/abstract exclusion codes add up');
const f3 = (x) => Number(x).toFixed(3);
const pct = (a, b) => Math.round((100 * a) / b);
const byStudy = (id) => N.comparisons.filter((p) => p.study_id === id);
const REC = Object.fromEntries(readCSV('data/records_dedup.csv').map((r) => [r.record_id, r]));
// "Du X.; Zhou Z.; ..." -> "Du X, Zhou Z, Wang Y, et al"
const authors = (rid) => {
  must(REC[rid] && REC[rid].authors, 'record ' + rid + ' has authors');
  const a = REC[rid].authors.split(';').map((x) => x.trim().replace(/\./g, '')).filter(Boolean);
  return a.length > 3 ? a.slice(0, 3).join(', ') + ', et al' : a.join(', ');
};
const surname = (rid) => REC[rid].authors.split(';')[0].trim().replace(/\s+\S+$/, '');
const strat = (r) => r.strategies.split(';').map((x) => x.trim());
const FT = ['LoRA', 'QLoRA', 'full FT'];
const nFT = STUDIES.filter((r) => strat(r).some((x) => FT.includes(x))).length;
must(pct(nFT, N.n_studies) === N.pct_finetune, 'fine-tuning study count matches pct_finetune');
// Every instruction-tuning study also used LoRA / QLoRA / full FT, so it is already inside the fine-tuning share.
const nIT = STUDIES.filter((r) => strat(r).includes('instruction tuning')).length;
must(STUDIES.filter((r) => strat(r).includes('instruction tuning')).every((r) => strat(r).some((x) => FT.includes(x))), 'instruction tuning implies fine-tuning');
// Rank by count, "other" last.
const ranked = (o) => Object.entries(o).sort((a, b) => (a[0] === 'other') - (b[0] === 'other') || b[1] - a[1]);

// QUADAS-2 (v5): the per-study table must reproduce the summary counts.
Q.domains.slice(0, 4).forEach((d, j) => {
  const col = Q.rows.map((r) => r[j + 1]);
  must(col.filter((v) => v === '+').length === Q.low[j] && col.filter((v) => v === '?').length === Q.unclear[j] && col.filter((v) => v === '−').length === Q.high[j], 'QUADAS domain ' + d);
});
const overall = Q.rows.map((r) => r[7]);
must(overall.filter((v) => v === '−').length === Q.high[4] && overall.filter((v) => v === '?').length === Q.unclear[4] && Q.rows.length === N.n_studies, 'QUADAS overall');

// ---------- design ----------
const FONT = 'Microsoft JhengHei';
const COL = { navy: '1F4E79', blue: '2E75B6', orange: 'C55A11', body: '262626', muted: '6B6B6B', rule: 'D9D9D9',
  tint: 'EAF1F8', gray: 'F3F4F6', grid: 'E5E5E5', white: 'FFFFFF', lightBlue: 'A9C4E2', paleNavy: 'C9D9EE', bar: '8EB1D8',
  low: '4E9A5B', unclear: 'E3B341', high: 'C0392B' };
const W = 13.333, H = 7.5, M = 0.5;
const CT = 1.5, CB = 6.85, CH = CB - CT;          // content band
const RX = 8.75, RW = W - M - RX;                  // right column next to a chart
const SECTIONS = ['背景', '方法', '結果概覽', 'RQ1 模型', 'RQ2 策略', 'RQ3 效能', '品質評估', '討論'];
const ZH = {
  'clinical note (mixed)': '臨床紀錄（混合）', 'radiology report': '放射報告', 'pathology report': '病理報告',
  'discharge summary': '出院摘要', 'progress note': '病程紀錄', other: '其他',
  'field extraction': '欄位抽取', NER: '命名實體辨識', attribute: '屬性抽取', RE: '關係抽取',
  'zero-shot': 'Zero-shot', 'few-shot': 'Few-shot', CoT: '思維鏈 CoT', LoRA: 'LoRA', RAG: 'RAG',
  'full FT': '全參數微調', 'instruction tuning': '指令微調', quantization: '量化', ensemble: '集成', QLoRA: 'QLoRA',
  local: '本地', mixed: '混合', 'private cloud': '私有雲', 'public API': '公開 API', NR: '未報告',
};
const zh = (k) => ZH[k] || k;

const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE';
pres.title = '開源大型語言模型用於臨床病歷資訊抽取：系統性回顧';
pres.author = '王閎立、羅泓勛、顏丞瑋';
pres.theme = { headFontFace: FONT, bodyFontFace: FONT };
pres.defineSlideMaster({
  title: 'CONTENT', background: { color: COL.white },
  slideNumber: { x: W - M - 0.6, y: H - 0.42, w: 0.6, h: 0.3, fontFace: FONT, fontSize: 12, color: COL.muted, align: 'right' },
});
pres.defineSlideMaster({ title: 'DARK', background: { color: COL.navy } });

const T = (slide, text, o) => slide.addText(text, { fontFace: FONT, isTextBox: true, margin: 0, ...o });
const note = (s, key) => { must(NOTES[key], 'speaker note ' + key); s.addNotes(NOTES[key]); };

function content(section, title, noteKey, { appendix } = {}) {
  const s = pres.addSlide({ masterName: 'CONTENT' });
  if (appendix) {
    T(s, appendix, { x: M, y: 0.22, w: 8, h: 0.3, fontSize: 13, color: COL.muted });
  } else {
    const runs = [];
    SECTIONS.forEach((sec, i) => {
      const active = sec === section;
      runs.push({ text: sec, options: { color: active ? COL.blue : '9A9A9A', bold: active } });
      if (i < SECTIONS.length - 1) runs.push({ text: '  ·  ', options: { color: 'C8C8C8' } });
    });
    T(s, runs, { x: M, y: 0.2, w: W - 2 * M, h: 0.3, fontSize: 13 });
  }
  // One-line titles: shrink the font with the title's visual length (CJK ≈ 1 em, Latin/digits ≈ 0.55 em).
  const em = [...title].reduce((a, ch) => a + (/[⺀-￯]/.test(ch) ? 1 : 0.55), 0);
  const size = Math.max(22, Math.min(30, Math.floor(((W - 2 * M) * 72 * 0.97) / em)));
  T(s, title, { x: M, y: 0.56, w: W - 2 * M, h: 0.8, fontSize: size, bold: true, color: COL.navy, valign: 'middle' });
  if (noteKey) note(s, noteKey);
  return s;
}
const source = (s, text) => T(s, text, { x: M, y: H - 0.45, w: W - 2 * M - 1.0, h: 0.3, fontSize: 12, color: COL.muted, valign: 'middle' });
const card = (s, x, y, w, h, fill = COL.tint) => s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: fill, width: 0 }, rectRadius: 0.1 });
function bullets(s, items, o) {
  const runs = [];
  items.forEach((it, i) => {
    const last = i === items.length - 1;
    const parts = typeof it === 'string' ? [{ t: it }] : it.b ? [{ t: it.b, bold: true }, { t: it.t }] : [{ t: it.t }];
    if (typeof it === 'object' && it.sub) parts.push({ t: it.sub, sub: true });
    parts.forEach((p, j) => runs.push({ text: p.t, options: {
      bold: !!p.bold, bullet: j === 0 ? (o.numbered ? { type: 'number' } : { indent: 20 }) : undefined,
      ...(p.sub ? { softBreakBefore: true, fontSize: (o.fontSize || 20) - 4, color: COL.muted } : {}),
      breakLine: j === parts.length - 1 && !last } }));
  });
  T(s, runs, { fontSize: 20, color: COL.body, paraSpaceAfter: 12, valign: 'top', ...o, margin: [0, 0, 0, 2] });
}
// Tinted card with a heading and bullets.
function panel(s, x, y, w, h, head, items, o = {}) {
  card(s, x, y, w, h, o.fill || COL.tint);
  T(s, head, { x: x + 0.3, y: y + 0.22, w: w - 0.6, h: 0.45, fontSize: 22, bold: true, color: o.headColor || COL.blue });
  bullets(s, items, { x: x + 0.3, y: y + 0.85, w: w - 0.55, h: h - 1.0, fontSize: o.fontSize || 20, paraSpaceAfter: o.space || 16 });
}
// Stack of stat cards: big value + label. `hi` fills the card navy.
function stats(s, list, x = RX, y = CT, w = RW, h = CH) {
  const gap = 0.22, ch = (h - gap * (list.length - 1)) / list.length;
  list.forEach((st, i) => {
    const cy = y + i * (ch + gap);
    card(s, x, cy, w, ch, st.hi ? COL.navy : COL.tint);
    const size = st.size || 40, vh = Math.max(0.72, (size * 1.22) / 72);
    const lh = Math.min(ch - 0.3 - vh, 0.72), top = cy + Math.max(0.12, (ch - vh - lh - 0.04) / 2);
    T(s, String(st.v), { x: x + 0.3, y: top, w: w - 0.5, h: vh, fontSize: size, bold: true, color: st.hi ? COL.white : COL.navy, valign: 'bottom' });
    T(s, st.l, { x: x + 0.3, y: top + vh + 0.04, w: w - 0.45, h: lh, fontSize: 18, color: st.hi ? COL.paleNavy : COL.body, valign: 'top' });
  });
}
const axis = { catAxisLabelFontFace: FONT, valAxisLabelFontFace: FONT, dataLabelFontFace: FONT, catAxisLabelColor: COL.body,
  valAxisLabelColor: COL.muted, catAxisLabelFontSize: 16, valAxisLabelFontSize: 13, dataLabelFontSize: 16, dataLabelColor: COL.body,
  valGridLine: { style: 'none' }, catGridLine: { style: 'none' }, showLegend: false, showValue: true,
  valAxisLineShow: false, catAxisLineShow: true, catAxisLineColor: 'BFBFBF' };
function bar(s, labels, values, o = {}) {
  const hi = o.highlight || [];
  s.addChart(pres.charts.BAR, [{ name: o.name || '研究數', labels, values }], {
    x: o.x ?? M, y: o.y ?? CT, w: o.w ?? 7.95, h: o.h ?? CH, barDir: o.dir || 'bar', barGapWidthPct: 35,
    chartColors: labels.map((l) => (hi.includes(l) ? COL.navy : COL.bar)), dataLabelPosition: 'outEnd',
    catAxisOrientation: o.dir === 'col' ? 'minMax' : 'maxMin', valAxisHidden: true, ...axis, ...(o.extra || {}),
  });
}
function table(s, rows, o) {
  const head = rows[0].map((h) => ({ text: h, options: { bold: true, color: COL.white, fill: { color: COL.navy } } }));
  const body = rows.slice(1).map((r, i) => r.map((c) => (typeof c === 'object' ? { ...c, options: { fill: { color: i % 2 ? 'F5F8FC' : COL.white }, ...c.options } } : { text: String(c), options: { fill: { color: i % 2 ? 'F5F8FC' : COL.white } } })));
  s.addTable([head, ...body], { fontFace: FONT, fontSize: 18, color: COL.body, border: { type: 'solid', pt: 0.5, color: COL.rule },
    valign: 'middle', margin: [3, 8, 3, 8], autoPage: false, ...o });
}
const arrowR = (s, x, y, w) => s.addShape(pres.shapes.LINE, { x, y, w, h: 0, line: { color: COL.muted, width: 1.5, endArrowType: 'triangle' } });

// ---------- 1 cover ----------
{
  const s = pres.addSlide({ masterName: 'DARK' });
  T(s, '系統性回顧 · PRISMA 2020', { x: 0.9, y: 1.0, w: 11, h: 0.45, fontSize: 18, color: COL.lightBlue });
  T(s, '開源大型語言模型用於臨床病歷資訊抽取', { x: 0.9, y: 1.55, w: 11.8, h: 1.0, fontSize: 44, bold: true, color: COL.white });
  T(s, '使用方式、效能，以及與閉源模型的差距', { x: 0.9, y: 2.6, w: 11.5, h: 0.6, fontSize: 26, color: COL.paleNavy });
  T(s, '115423080 王閎立 · 115423074 羅泓勛 · 顏丞瑋', { x: 0.9, y: 5.7, w: 11, h: 0.45, fontSize: 20, color: COL.white });
  T(s, '2026/11/18', { x: 0.9, y: 6.2, w: 11, h: 0.4, fontSize: 18, color: COL.lightBlue });
  note(s, 'cover');
}

// ---------- 2–3 background ----------
{
  const s = content('背景', '病歷資訊多寫在自由文本；開源 LLM 可在院內做抽取，病歷不必離院', 'why');
  const ie = [['NER', '藥名、症狀、檢查值'], ['關係抽取', '藥物—劑量、病灶—位置'], ['欄位抽取', '病灶大小、TNM 分期']];
  ie.forEach(([h, d], i) => {
    const w = (W - 2 * M - 0.5) / 3, x = M + i * (w + 0.25);
    card(s, x, CT, w, 1.15);
    T(s, h, { x: x + 0.3, y: CT + 0.12, w: w - 0.6, h: 0.45, fontSize: 22, bold: true, color: COL.blue });
    T(s, d, { x: x + 0.3, y: CT + 0.6, w: w - 0.6, h: 0.42, fontSize: 18, color: COL.body });
  });
  table(s, [['面向', '閉源 LLM（GPT、Gemini、Claude）', '開源 LLM（Llama、Qwen、Gemma…）'],
    ['病歷是否離院', '需送至外部 API（或特約雲端）', '可在院內伺服器執行'],
    ['成本', '依用量計價', '硬體與維運成本'],
    ['版本與重現性', '供應商可更新或下架模型', '權重固定，可重現'],
    ['客製化', '多數只能提示', '可用院內資料微調']],
  { x: M, y: 2.9, w: W - 2 * M, colW: [2.1, 5.1, 5.13], fontSize: 18, rowH: 0.58 });
  card(s, M, 6.1, W - 2 * M, 0.72, COL.navy);
  T(s, '本回顧的「開源」= 權重可公開下載，且參數量 ≥ 1B', { x: M + 0.3, y: 6.1, w: W - 2 * M - 0.6, h: 0.72, fontSize: 20, bold: true, color: COL.white, valign: 'middle' });
}
{
  const s = content('背景', '既有回顧已涵蓋生成式 AI 抽取；本回顧聚焦同一研究內的開源 vs 閉源比較', 'reviews_rq');
  const lw = 5.6;
  card(s, M, CT, lw, CH, COL.gray);
  T(s, '既有回顧', { x: M + 0.3, y: CT + 0.22, w: lw - 0.6, h: 0.45, fontSize: 22, bold: true, color: COL.blue });
  const refs = [['Abdellaoui 等，2025', '生成式 AI 從臨床筆記抽取資訊（範疇回顧）'], [`${surname('R0543')} 等，${REC.R0543.year}`, '生成式 LLM 在電子病歷應用的測試與評估（JAMIA 系統性回顧）'],
    ['Sugihara 等，2026', '開源與商用 LLM 在臨床資訊抽取的取捨']];
  refs.forEach(([a, b], i) => {
    const y = CT + 0.95 + i * 1.42;
    T(s, a, { x: M + 0.3, y, w: lw - 0.6, h: 0.42, fontSize: 20, bold: true, color: COL.navy });
    T(s, b, { x: M + 0.3, y: y + 0.45, w: lw - 0.6, h: 0.8, fontSize: 18, color: COL.body, valign: 'top' });
  });
  const rx = M + lw + 0.35, rw = W - M - rx;
  card(s, rx, CT, rw, CH, COL.tint);
  T(s, '研究問題', { x: rx + 0.3, y: CT + 0.22, w: rw - 0.6, h: 0.45, fontSize: 22, bold: true, color: COL.blue });
  const rq = [['RQ1', '用了哪些開源 LLM？規模多大？'], ['RQ2', '怎麼用：提示、微調、RAG？部署在哪？'], ['RQ3', '同一研究內，與閉源 LLM 差多少？'], ['品質', '納入研究的偏倚風險如何？']];
  rq.forEach(([k, q], i) => {
    const y = CT + 0.95 + i * 1.07;
    T(s, k, { x: rx + 0.3, y, w: 1.2, h: 0.8, fontSize: 28, bold: true, color: COL.blue, valign: 'middle' });
    T(s, q, { x: rx + 1.55, y, w: rw - 1.85, h: 0.8, fontSize: 21, color: COL.navy, valign: 'middle' });
  });
}

// ---------- 4–7 methods ----------
{
  const s = content('方法', '納入：≥ 1B 開源 LLM、真實臨床文本、有量化評估的資訊抽取研究', 'criteria');
  const w = (W - 2 * M - 0.35) / 2;
  panel(s, M, CT, w, CH, '納入（全部符合）', [{ b: 'P　', t: '真實臨床自由文本', sub: '病歷、出院摘要、影像與病理報告' }, { b: 'I　', t: '至少一個開源 LLM', sub: '權重可公開下載，參數量 ≥ 1B' },
    { b: 'O　', t: '資訊抽取任務，有量化評估', sub: 'F1、precision、recall 等' }, { b: '期間　', t: '2022–2026 年英文論文', sub: '病歷語言不限' }], { fontSize: 22, space: 14 });
  panel(s, M + w + 0.35, CT, w, CH, '排除（代碼 X1–X8）', [{ b: 'X4　', t: '只用閉源 LLM' }, { b: 'X5　', t: '非臨床文本', sub: '含只用合成病歷' },
    { b: 'X6　', t: '非抽取任務', sub: '摘要、問答、ICD 自動編碼、文件層級分類' }, { b: 'X1／X7　', t: '發表類型不符；無量化評估', sub: '回顧、社論、無全文' }], { fill: COL.gray, fontSize: 22, space: 14 });
  source(s, '完整定義：protocol 3.1–3.2；排除代碼見附錄 A');
}
{
  const nVer = VR.length;
  const s = content('方法', `篩選與萃取以 AI 為主：兩個 AI 獨立判斷，分歧由作者裁定`, 'workflow');
  const steps = [
    ['1 標題／摘要', C.screened.toLocaleString(), `兩個 AI 獨立判斷\n分歧由作者裁定\n排除 ${C.title_abstract_excluded}`],
    ['2 全文', String(C.full_text_assessed), `AI 讀重點段落\n未取得 ${C.full_text_not_retrieved}、排除 ${ftExcluded}\n${C.included} 篇符合原始條件`],
    ['3 萃取', String(N.n_studies), `收緊後 ${C.included} → ${N.n_studies}\nAI 預填並附頁碼\n腳本驗證數值在該頁\n對原文核對 ${nVer} 列`],
    ['4 品質評估', String(Q.rows.length), '改編 QUADAS-2\n四領域、18 題'],
  ];
  const gap = 0.35, w = (W - 2 * M - 3 * gap) / 4, h = 3.75;
  steps.forEach(([hd, n, d], i) => {
    const x = M + i * (w + gap);
    card(s, x, CT, w, h, i === 3 ? COL.gray : COL.tint);
    T(s, hd, { x: x + 0.25, y: CT + 0.2, w: w - 0.5, h: 0.45, fontSize: 21, bold: true, color: COL.blue });
    T(s, n, { x: x + 0.25, y: CT + 0.72, w: w - 0.5, h: 0.95, fontSize: 48, bold: true, color: COL.navy });
    T(s, d, { x: x + 0.25, y: CT + 1.8, w: w - 0.4, h: 1.8, fontSize: 18, color: COL.body, valign: 'top', paraSpaceAfter: 4 });
    if (i < 3) arrowR(s, x + w + 0.04, CT + 1.2, gap - 0.08);
  });
  card(s, M, CT + h + 0.3, W - 2 * M, CH - h - 0.3, COL.navy);
  T(s, [{ text: '揭露　', options: { bold: true } },
    { text: `κ = ${K.binary.kappa.toFixed(2)} 是兩個 AI 間的一致性，非人工 κ；萃取核對由 AI Agent 依作者授權完成，非作者逐篇核對。指標與資料集異質，採敘述性綜合，不做統合分析` }],
  { x: M + 0.3, y: CT + h + 0.3, w: W - 2 * M - 0.6, h: CH - h - 0.3, fontSize: 19, color: COL.white, valign: 'middle' });
}
{
  const s = content('方法', `PRISMA 2020 流程：${C.included} 篇符合原始條件，課堂版最終納入 ${N.n_studies} 篇`, 'prisma');
  const CODE = { X1: '發表類型', X2: '非英文', X3: '未用合格 LLM', X4: '只用閉源', X5: '非臨床文本', X6: '非抽取任務', X7: '無量化評估', X8: '其他版本' };
  const codes = (o) => Object.entries(o).sort((a, b) => b[1] - a[1]).map(([k, v]) => `${CODE[k] || k} ${v}`).join('、');
  const dbs = Object.entries(C.database_counts).sort((a, b) => b[1] - a[1]).map(([k, v]) => `${k} ${v}`).join('、');
  const left = [`資料庫檢索 n = ${dbTotal.toLocaleString()}`, `標題／摘要篩選 n = ${C.screened.toLocaleString()}`, `尋求全文 n = ${sought}`,
    `全文評估 n = ${C.full_text_assessed}`, `符合原始納入條件 n = ${C.included}`, `課堂版最終納入 n = ${N.n_studies}`];
  const right = [[`移除重複 n = ${C.duplicates_removed}`, ''], [`排除 n = ${C.title_abstract_excluded}`, codes(TA)], [`未取得全文 n = ${C.full_text_not_retrieved}`, '無開放取用版本，未以學校權限補取'],
    [`全文排除 n = ${ftExcluded}`, codes(C.full_text_excluded_by_code)],
    [`課堂版收緊條件排除 n = ${scopeExcluded}`, `預印本 ${N.scope_excluded_r1_preprint}、無閉源直接比較 ${N.scope_excluded_r2_no_closed}、核對發現不符 ${N.scope_excluded_other}`]];
  const step = CH / 6, bh = 0.7, px = M, lx = M + 0.6, bw = 3.2, rx = lx + bw + 0.45, rw = W - M - rx, rbh = 0.84;
  [['識別', 0, 1], ['篩選', 1, 4], ['納入', 5, 1]].forEach(([t, i0, n]) => {
    card(s, px, CT + i0 * step, 0.45, n * step - (step - bh), COL.tint);
    T(s, t, { x: px, y: CT + i0 * step, w: 0.45, h: n * step - (step - bh), fontSize: 16, bold: true, color: COL.navy, align: 'center', valign: 'middle', vert: 'eaVert' });
  });
  left.forEach((t, i) => {
    const y = CT + i * step, last = i === left.length - 1;
    s.addShape(pres.shapes.RECTANGLE, { x: lx, y, w: bw, h: bh, fill: { color: last ? COL.navy : COL.white }, line: { color: last ? COL.navy : COL.blue, width: 1.25 } });
    T(s, t, { x: lx + 0.08, y, w: bw - 0.16, h: bh, fontSize: 18, bold: last, color: last ? COL.white : COL.navy, align: 'center', valign: 'middle' });
    if (!last) s.addShape(pres.shapes.LINE, { x: lx + bw / 2, y: y + bh, w: 0, h: step - bh, line: { color: COL.muted, width: 1.25, endArrowType: 'triangle' } });
  });
  T(s, dbs, { x: rx, y: CT, w: rw, h: 0.34, fontSize: 14, color: COL.muted, valign: 'middle' });
  right.forEach(([hd, detail], i) => {
    const cy = CT + i * step + bh + (step - bh) / 2, y = cy - rbh / 2;
    arrowR(s, lx + bw / 2, cy, rx - lx - bw / 2);
    s.addShape(pres.shapes.RECTANGLE, { x: rx, y, w: rw, h: rbh, fill: { color: COL.gray }, line: { color: COL.rule, width: 0.75 } });
    const runs = [{ text: hd, options: { bold: true, fontSize: 18, color: COL.navy, breakLine: !!detail } }];
    if (detail) runs.push({ text: detail, options: { fontSize: 15, color: COL.body } });
    T(s, runs, { x: rx + 0.18, y, w: rw - 0.32, h: rbh, valign: 'middle', paraSpaceAfter: 2 });
  });
  source(s, '依 PRISMA 2020 流程圖（僅資料庫檢索）改編；課堂版收緊條件為事後設定，排除代碼定義見附錄 A');
}
{
  const s = content('方法', `效能只在同一研究內比較：差距 = 閉源 − 開源，≤ ${N.tie_threshold} 視為追平`, 'compare_def');
  const items = [['配對', '每個任務與資料集：最佳開源 LLM vs 最佳閉源 LLM，且指標相同'],
    ['差距', `閉源 − 開源（0–1 尺度）；≤ ${N.tie_threshold} 視為開源追平或較好`],
    ['研究層級', '每篇取各組差距的中位數，避免多任務研究主導（主要結果）'],
    ['分組', '依開源模型使用方式分為「微調」（LoRA、QLoRA、全參數）與「提示」']];
  const gap = 0.3, w = (W - 2 * M - gap) / 2, h = (CH - gap) / 2;
  items.forEach(([hd, d], i) => {
    const x = M + (i % 2) * (w + gap), y = CT + Math.floor(i / 2) * (h + gap);
    card(s, x, y, w, h, i === 2 ? COL.navy : COL.tint);
    T(s, hd, { x: x + 0.35, y: y + 0.3, w: w - 0.7, h: 0.55, fontSize: 26, bold: true, color: i === 2 ? COL.white : COL.blue });
    T(s, d, { x: x + 0.35, y: y + 1.0, w: w - 0.7, h: h - 1.2, fontSize: 21, color: i === 2 ? COL.white : COL.body, valign: 'top' });
    if (i === 1) T(s, '例：閉源 0.90、開源 0.89 → 差距 0.01，視為追平', { x: x + 0.35, y: y + h - 0.6, w: w - 0.7, h: 0.4, fontSize: 17, color: COL.muted });
  });
  source(s, '敘述性綜合（SWiM）：指標與資料集異質，不做統合分析');
}

// ---------- 8–9 overview ----------
{
  const yrs = Object.keys(N.years).sort();
  const recent = (N.years['2025'] || 0) + (N.years['2026'] || 0);
  const s = content('結果概覽', `${N.n_studies} 篇中 ${pct(recent, N.n_studies)}% 發表於 2025–2026 年；英語病歷為主，${langNR} 篇未報告語言`, 'overview');
  bar(s, yrs, yrs.map((y) => N.years[y]), { dir: 'col', w: 6.3, h: CH, highlight: ['2026'], name: '研究數' });
  const cards = [[N.n_studies, '納入研究'], [N.n_pair_studies, '有開源 vs 閉源配對'], [langEnOnly, '只有英語病歷'], [langNonEn, '含非英語病歷']];
  const x0 = 7.1, gap = 0.25, cw = (W - M - x0 - gap) / 2, chh = 2.05;
  cards.forEach(([v, l], i) => {
    const x = x0 + (i % 2) * (cw + gap), y = CT + Math.floor(i / 2) * (chh + gap);
    card(s, x, y, cw, chh, i === 0 ? COL.navy : COL.tint);
    T(s, String(v), { x, y: y + 0.2, w: cw, h: 1.05, fontSize: 54, bold: true, color: i === 0 ? COL.white : COL.navy, align: 'center' });
    T(s, l, { x, y: y + 1.3, w: cw, h: 0.5, fontSize: 19, color: i === 0 ? COL.paleNavy : COL.body, align: 'center' });
  });
  T(s, `另有 ${langNR} 篇未報告病歷語言`, { x: x0, y: CT + 2 * chh + 2 * gap + 0.05, w: W - M - x0, h: 0.5, fontSize: 17, color: COL.body });
  source(s, `n = ${N.n_studies}；2027 年 1 篇為期刊標示的出版年份`);
}
{
  const tt = ranked(N.text_types);
  must(tt[0][0] === 'clinical note (mixed)' && tt[1][0] === 'radiology report', 'text type ranking');
  const tk = ranked(N.task_types);
  must(tk[0][0] === 'field extraction', 'task ranking');
  const s = content('結果概覽', '混合型臨床紀錄最常見，其次是放射與病理報告；任務以欄位抽取為主', 'text_task');
  T(s, '文本類型（篇）', { x: M, y: CT, w: 6, h: 0.45, fontSize: 22, bold: true, color: COL.blue });
  bar(s, tt.map(([k]) => zh(k)), tt.map(([, v]) => v), { y: CT + 0.5, w: 7.95, h: CH - 0.5 });
  card(s, RX, CT, RW, CH, COL.tint);
  T(s, '任務類型（篇）', { x: RX + 0.3, y: CT + 0.22, w: RW - 0.6, h: 0.45, fontSize: 22, bold: true, color: COL.blue });
  table(s, [['任務', '篇數'], ...tk.map(([k, v]) => [zh(k), { text: String(v), options: { align: 'right' } }])],
    { x: RX + 0.3, y: CT + 0.9, w: RW - 0.6, colW: [RW - 1.85, 1.25], fontSize: 19, rowH: 0.62 });
  source(s, `n = ${N.n_studies}；一篇可計入多類`);
}

// ---------- 10–11 RQ1 ----------
{
  const fam = ranked(N.model_family);
  must(fam[0][0] === 'Llama', 'Llama most common');
  const s = content('RQ1 模型', `Llama 家族最常用：${N.n_studies} 篇中 ${N.model_family.Llama} 篇使用`, 'family');
  bar(s, fam.map(([k]) => zh(k)), fam.map(([, v]) => v), { highlight: ['Llama'] });
  stats(s, [{ v: `${N.model_family.Llama} 篇`, l: `使用 Llama 家族（${pct(N.model_family.Llama, N.n_studies)}%）`, hi: true },
    { v: `${N.model_family.Qwen} · ${N.model_family.Gemma} · ${N.model_family.DeepSeek} 篇`, l: 'Qwen、Gemma、DeepSeek' },
    { v: N.n_distinct_open_models, l: '不同開源模型' }]);
  source(s, `n = ${N.n_studies} 篇；一篇可用多個家族`);
}
{
  const pb = N.params_bins, labs = Object.keys(pb), small = pb[labs[0]];
  must(/^1.10B$/.test(labs[0]) && labs[labs.length - 1] === '> 100B', 'params bins order');
  const s = content('RQ1 模型', `${pct(small, N.n_params_reported)}% 的模型在 10B 以下；${N.n_medical_model_studies} 篇（${N.pct_medical_model}%）用了醫療領域模型`, 'params');
  bar(s, labs, labs.map((k) => pb[k]), { dir: 'col', highlight: [labs[0]], name: '模型數' });
  stats(s, [{ v: `${pct(small, N.n_params_reported)}%`, l: `模型在 10B 以下（${small}/${N.n_params_reported}）`, hi: true },
    { v: pb['> 100B'], l: '模型超過 100B' }, { v: `${N.n_medical_model_studies}/${N.n_studies}`, l: '篇用了醫療領域模型' }]);
  source(s, `參數量以研究 × 模型計，n = ${N.n_params_reported}（原文有報告者）`);
}

// ---------- 12–13 RQ2 ----------
{
  const st = ranked(N.strategies);
  must(st[0][0] === 'zero-shot', 'zero-shot most common');
  const s = content('RQ2 策略', `提示工程仍是主流（zero-shot ${N.strategies['zero-shot']} 篇），${N.pct_finetune}% 的研究有做微調`, 'strategy');
  bar(s, st.map(([k]) => zh(k)), st.map(([, v]) => v), { highlight: ['LoRA', '全參數微調', 'QLoRA', '指令微調'], extra: { catAxisLabelFontSize: 15, dataLabelFontSize: 15 } });
  stats(s, [{ v: `${N.strategies['zero-shot']} · ${N.strategies['few-shot']}`, l: 'Zero-shot · Few-shot（篇）' },
    { v: `${N.pct_finetune}%`, l: `研究有做微調（${nFT} 篇，圖中深色）`, hi: true }, { v: `${N.strategies.RAG} · ${N.strategies.CoT}`, l: 'RAG · CoT（篇）' }]);
  source(s, `n = ${N.n_studies}；一篇可計入多類。微調 = LoRA、QLoRA 或全參數；指令微調 ${nIT} 篇皆同時使用其一，已計入`);
}
{
  const dp = Object.entries(N.deployment).sort((a, b) => b[1] - a[1]);
  const s = content('RQ2 策略', `${N.deployment.NR} 篇（${pct(N.deployment.NR, N.n_studies)}%）未報告部署方式；明確只在本地執行的有 ${N.deployment.local} 篇`, 'deploy');
  bar(s, dp.map(([k]) => zh(k)), dp.map(([, v]) => v), { highlight: ['未報告'] });
  stats(s, [{ v: `${N.pct_local}%`, l: `明確只在本地執行（${N.deployment.local} 篇）` }, { v: N.deployment.mixed, l: '篇混合：開源本地＋閉源 API' },
    { v: N.deployment.NR, l: '篇未報告部署方式', hi: true }]);
  source(s, `n = ${N.n_studies}；每篇一類`);
}

// ---------- 14–18 RQ3 ----------
function dumbbell(s, rows, o) {
  const x0 = o.x + 2.9, x1 = o.x + o.w - 0.15, y0 = o.y + 0.45, rowH = Math.min(0.36, (o.h - 0.95) / rows.length);
  const X = (v) => x0 + (x1 - x0) * v;
  [0, 0.2, 0.4, 0.6, 0.8, 1.0].forEach((t) => {
    s.addShape(pres.shapes.LINE, { x: X(t), y: y0 - 0.1, w: 0, h: rowH * rows.length + 0.1, line: { color: COL.grid, width: 0.75 } });
    T(s, t.toFixed(1), { x: X(t) - 0.3, y: y0 + rowH * rows.length + 0.04, w: 0.6, h: 0.28, fontSize: 13, color: COL.muted, align: 'center' });
  });
  T(s, [{ text: '● 最佳開源 LLM', options: { color: COL.blue } }, { text: '　　● 最佳閉源 LLM', options: { color: COL.orange } }],
    { x: x0, y: o.y, w: x1 - x0, h: 0.32, fontSize: 16, bold: true });
  rows.forEach((d, i) => {
    const cy = y0 + i * rowH + rowH / 2, a = Math.min(d.open_median, d.closed_median), b = Math.max(d.open_median, d.closed_median);
    T(s, `${d.label}（${d.n}）`, { x: o.x, y: cy - rowH / 2, w: 2.8, h: rowH, fontSize: 15, color: COL.body, align: 'right', valign: 'middle' });
    if (b - a > 0.003) s.addShape(pres.shapes.LINE, { x: X(a), y: cy, w: X(b) - X(a), h: 0, line: { color: 'BFBFBF', width: 3 } });
    const near = X(b) - X(a) < 0.14, rc = near ? 0.115 : 0.09, ro = near ? 0.065 : 0.09;
    s.addShape(pres.shapes.OVAL, { x: X(d.closed_median) - rc, y: cy - rc, w: 2 * rc, h: 2 * rc, fill: { color: COL.orange }, line: { color: COL.white, width: 0.75 } });
    s.addShape(pres.shapes.OVAL, { x: X(d.open_median) - ro, y: cy - ro, w: 2 * ro, h: 2 * ro, fill: { color: COL.blue }, line: { color: COL.white, width: 0.75 } });
  });
  T(s, '效能（0–1）；括號 = 比較數；兩點重疊時外圈為閉源', { x: x0, y: y0 + rowH * rows.length + 0.34, w: x1 - x0, h: 0.28, fontSize: 13, color: COL.muted, align: 'center' });
}
{
  const ahead = N.study_level.filter((d) => d.gap_median > N.tie_threshold).sort((a, b) => b.gap_median - a.gap_median);
  must(ahead.length === N.n_studies_closed_ahead, 'closed-ahead count');
  const within15 = ahead.filter((d) => d.gap_median <= 0.15).length;
  const s = content('RQ3 效能', `${N.n_pair_studies} 篇可配對研究中，${N.n_studies_closed_ahead} 篇閉源領先，但多數差距在 0.15 以內`, 'closed_ahead');
  dumbbell(s, ahead, { x: M, y: CT, w: 8.1, h: CH });
  stats(s, [{ v: ahead.length, l: '篇閉源領先（差距 > 0.02）' }, { v: within15, l: '篇差距 ≤ 0.15' },
    { v: f3(N.median_study_gap), l: `全部 ${N.n_pair_studies} 篇差距中位數`, hi: true }]);
  source(s, '研究層級：點 = 各組數值的中位數；差距 = 各組差距的中位數（不一定等於兩點相減）');
}
{
  const tie = N.study_level.filter((d) => d.gap_median <= N.tie_threshold).sort((a, b) => a.gap_median - b.gap_median);
  must(tie.length === N.n_studies_open_comparable_or_better, 'open-comparable count');
  const better = tie.filter((d) => d.gap_median < 0).length;
  const s = content('RQ3 效能', `${N.n_studies_open_comparable_or_better} 篇研究中開源追平或優於閉源，其中 ${better} 篇開源較好`, 'open_tie');
  dumbbell(s, tie, { x: M, y: CT, w: 8.1, h: CH });
  stats(s, [{ v: `${pct(tie.length, N.n_pair_studies)}%`, l: '可配對研究中開源追平或較好', hi: true },
    { v: better, l: '篇開源較好（差距 < 0）' }, { v: tie.filter((d) => Math.abs(d.gap_median) <= 0.05).length, l: '篇差距在 ±0.05 以內' }]);
  source(s, '研究層級：點 = 各組數值的中位數；分類依各組差距的中位數（不一定等於兩點相減）；逐篇見附錄 C');
}
{
  const s = content('RQ3 效能', `微調後的開源模型與閉源差距較小：中位數 ${f3(N.median_gap_finetuned)} vs 提示 ${f3(N.median_gap_prompting)}`, 'finetune');
  s.addChart(pres.charts.BAR, [{ name: '差距中位數', labels: [`微調（n = ${N.n_finetuned_comparisons}）`, `提示（n = ${N.n_prompting_comparisons}）`], values: [N.median_gap_finetuned, N.median_gap_prompting] }], {
    x: M, y: CT, w: 7.95, h: CH, barDir: 'col', barGapWidthPct: 70, chartColors: [COL.blue, 'A6A6A6'], ...axis,
    catAxisLabelFontSize: 18, dataLabelFontSize: 20, dataLabelFormatCode: '0.000', dataLabelPosition: 'outEnd', valAxisHidden: true, valAxisMinVal: 0,
    showCatAxisTitle: true, catAxisTitle: '差距中位數（閉源 − 開源，任務層級）', catAxisTitleFontFace: FONT, catAxisTitleFontSize: 14, catAxisTitleColor: COL.muted,
  });
  must(N.median_gap_finetuned <= N.tie_threshold, 'fine-tuned median gap within tie threshold');
  stats(s, [{ v: f3(N.median_gap_finetuned), l: `微調組差距中位數，在追平門檻 ${N.tie_threshold} 以內`, hi: true },
    { v: f3(N.median_gap_prompting), l: '提示組差距中位數' }, { v: '非因果', l: `微調僅 ${N.n_finetuned_comparisons} 組，屬觀察性比較`, size: 34 }]);
  source(s, '任務層級比較；觀察性分組，非因果');
}
{
  const p = byStudy('S033')[0];
  must(p && p.open_model === 'Med42-8B', 'S033 pair');
  const s = content('RQ3 效能', '代表研究一：小型醫療模型經任務微調，可超過通用閉源模型', 'case1');
  must(/distillation/i.test(SID.S033.title), 'S033 is a distillation study');
  stats(s, [{ v: p.open_value, l: 'macro F1｜Med42-8B（開源，微調）', hi: true, size: 54 }, { v: p.closed_value, l: 'macro F1｜Gemini 2.0 Flash（閉源）', size: 54 }], M, CT, 5.0, CH);
  panel(s, M + 5.35, CT, W - 2 * M - 5.35, CH, '研究設定', [{ b: '文本：', t: '病理報告，肺癌組織型四分類' }, { b: '模型：', t: '8B 醫療領域模型，本地部署' },
    { b: '訓練：', t: 'LoRA 微調，標註由 Gemini 蒸餾而來' }, { b: '解讀：', t: '小模型＋任務微調可追上通用閉源模型' }, { b: '限制：', t: '測試集僅 33 份報告，屬概念驗證' }], { fontSize: 21 });
  source(s, `Wiyanti et al. (2026), ${SID.S033.venue}；數值出處 ${p.open_src}、${p.closed_src}`);
}
{
  const ps = byStudy('S052').sort((a, b) => b.gap - a.gap);
  const main = ps.find((p) => p.task === 'Main');
  must(main && ps.every((p) => p.gap > 0), 'S052 all closed ahead');
  const s = content('RQ3 效能', `代表研究二：荷蘭語心血管報告的 ${ps.length} 項任務，閉源全面領先`, 'case2');
  const top = ps.slice(0, 7);
  const TASK = { 'Tricuspid Sten. grade': '三尖瓣狹窄分級', 'Pulmonary Sten. grade': '肺動脈瓣狹窄分級', 'Pulmonary Reg. grade': '肺動脈瓣逆流分級',
    'Aortic Sten. grade': '主動脈瓣狹窄分級', 'Tricuspid Reg. grade': '三尖瓣逆流分級', 'Aortic Reg. grade': '主動脈瓣逆流分級',
    'Mitral Reg. grade': '二尖瓣逆流分級', Main: '主要任務（冠狀動脈）' };
  top.forEach((p) => must(TASK[p.task], 'Chinese label for S052 task ' + p.task));
  const tl = top.map((p) => TASK[p.task]);
  s.addChart(pres.charts.BAR, [
    { name: 'Phi-4（開源）', labels: tl, values: top.map((p) => p.open_value) },
    { name: 'GPT-4o（閉源）', labels: tl, values: top.map((p) => p.closed_value) }], {
    x: M, y: CT, w: 7.95, h: CH, barDir: 'bar', barGapWidthPct: 35, chartColors: [COL.blue, COL.orange], ...axis,
    showLegend: true, legendPos: 't', legendFontFace: FONT, legendFontSize: 16, catAxisOrientation: 'maxMin', catAxisLabelFontSize: 14,
    dataLabelFontSize: 13, dataLabelFormatCode: '0.00', dataLabelPosition: 'outEnd', valAxisHidden: true, valAxisMaxVal: 1.15,
  });
  stats(s, [{ v: `${ps.length}/${ps.length}`, l: '項任務閉源領先', hi: true }, { v: `${main.open_value} vs ${main.closed_value}`, l: '主要任務 F1（開源 vs 閉源）', size: 34 },
    { v: '瓣膜分級', l: '落差最大；圖為差距最大 7 項', size: 34 }]);
  source(s, `van der Loo et al. (2026), ${SID.S052.venue}；p.5 Table 2、p.6 Table 3`);
}

// ---------- 19 quality (adapted QUADAS-2, verbatim from v5) ----------
{
  const s = content('品質評估', `改編 QUADAS-2：${Q.n_high}/${Q.rows.length} 篇整體為高偏倚風險，主要在評估流程與分析`, 'quadas');
  s.addChart(pres.charts.BAR, [
    { name: '低風險', labels: Q.domains, values: Q.low }, { name: '不明', labels: Q.domains, values: Q.unclear }, { name: '高風險', labels: Q.domains, values: Q.high }], {
    x: M, y: CT, w: 7.6, h: CH, barDir: 'bar', barGrouping: 'stacked', barGapWidthPct: 40, chartColors: [COL.low, COL.unclear, COL.high], ...axis,
    catAxisOrientation: 'maxMin', showLegend: true, legendPos: 't', legendFontFace: FONT, legendFontSize: 16, dataLabelPosition: 'ctr',
    dataLabelColor: COL.white, dataLabelFontSize: 15, dataLabelFontBold: true, dataLabelFormatCode: '0;-0;', valAxisHidden: true, valAxisMaxVal: Q.rows.length,
  });
  const rx = 8.4, rw = W - M - rx;
  card(s, rx, CT, rw, CH, COL.tint);
  T(s, '重點', { x: rx + 0.3, y: CT + 0.2, w: rw - 0.6, h: 0.45, fontSize: 22, bold: true, color: COL.blue });
  // v5 phrased these as 「signal question」為否; say the same thing without the double negative.
  const NO = { 討論預訓練資料污染: '未討論預訓練資料污染', 未不當排除文件: '有不當排除文件', 開源與閉源比較公平: '開源與閉源比較條件不公平' };
  const points = Q.points.map((t) => { const m = t.match(/^「(.+)」為否：(.+)$/); if (!m) return t; must(NO[m[1]], 'plain wording for ' + m[1]); return `${NO[m[1]]}：${m[2]}`; });
  bullets(s, points, { x: rx + 0.3, y: CT + 0.8, w: rw - 0.5, h: 3.0, fontSize: 18, paraSpaceAfter: 10 });
  card(s, rx + 0.2, CT + 3.85, rw - 0.4, CH - 4.05, COL.white);
  T(s, [{ text: '與結果的關係：', options: { bold: true, color: COL.navy } }, { text: Q.relation }],
    { x: rx + 0.4, y: CT + 3.95, w: rw - 0.8, h: CH - 4.25, fontSize: 17, color: COL.body, valign: 'middle' });
  source(s, `改編 QUADAS-2（四領域、18 個信號問題）；n = ${Q.rows.length}；未因品質排除研究；逐篇見附錄 E`);
}

// ---------- 20–21 discussion ----------
{
  const s = content('討論', '限制：證據異質且品質有限；本回顧事後收緊範圍，半數全文未取得', 'limits');
  const w = (W - 2 * M - 0.35) / 2;
  panel(s, M, CT, w, CH, '證據本身', ['指標、資料集與標註方式各異，不做統合分析', `${N.unpaired.length} 篇數值只在圖或補充資料，無法配對`,
    `${Q.n_single_site} 篇只用單一機構資料評估`, `${Q.n_no_annotation_agreement} 篇未報告標註一致性或雙人標註`, `${Q.n_high} 篇整體為高偏倚風險（改編 QUADAS-2）`], { fontSize: 21 });
  panel(s, M + w + 0.35, CT, w, CH, '本回顧', ['未事先註冊 protocol', `${sought} 篇中 ${C.full_text_not_retrieved} 篇無開放全文，可能遺漏研究`,
    `事後限同儕審查且有閉源比較（${C.included} → ${N.n_studies}）`, '篩選以兩個 AI 為主、作者裁定分歧；萃取核對由 Agent 依授權完成', '未做引用追蹤與 GRADE 確信度評估'], { fill: COL.gray, fontSize: 21 });
}
{
  const s = content('討論', '對醫院：可先試院內微調小模型；對研究者：需同條件比較並報告部署', 'implications');
  const w = (W - 2 * M - 0.35) / 2, ph = 2.7;
  panel(s, M, CT, w, ph, '醫院與臨床資訊團隊', ['資料不能離院時，開源模型是可行選項', '可先以院內資料微調 10B 以下模型', '上線前在院內測試集與閉源基準比較'], { fontSize: 20, space: 8 });
  panel(s, M + w + 0.35, CT, w, ph, '研究者', ['同一測試集同時評估開源與閉源模型', '統一指標，報告於正文而非只在圖中', `報告部署方式（${N.deployment.NR}/${N.n_studies} 篇未報告）`], { fill: COL.gray, fontSize: 20, space: 8 });
  T(s, '建議的依據', { x: M, y: CT + ph + 0.12, w: 5, h: 0.4, fontSize: 18, bold: true, color: COL.muted });
  const basis = [[`${N.n_studies_open_comparable_or_better}/${N.n_pair_studies}`, '篇研究開源追平或較好'], [f3(N.median_gap_finetuned), '微調組差距中位數'],
    [`${N.deployment.NR}/${N.n_studies}`, '篇未報告部署方式'], [String(N.unpaired.length), '篇數值只在圖或補充資料']];
  const bw = (W - 2 * M - 3 * 0.25) / 4;
  basis.forEach(([v, l], i) => {
    const x = M + i * (bw + 0.25), y = CT + ph + 0.56;
    card(s, x, y, bw, 1.2, COL.tint);
    T(s, v, { x: x + 0.25, y: y + 0.08, w: bw - 0.5, h: 0.66, fontSize: 32, bold: true, color: COL.navy });
    T(s, l, { x: x + 0.25, y: y + 0.76, w: bw - 0.4, h: 0.36, fontSize: 16, color: COL.body });
  });
  card(s, M, CB - 0.62, W - 2 * M, 0.62, COL.navy);
  T(s, '建議依據本回顧的觀察性結果，非因果結論', { x: M + 0.3, y: CB - 0.62, w: W - 2 * M - 0.6, h: 0.62, fontSize: 19, color: COL.white, valign: 'middle' });
}

// ---------- 22 conclusions ----------
{
  const s = pres.addSlide({ masterName: 'DARK' });
  T(s, '結論：開源尚未全面追上閉源，但差距小，微調後常可追平', { x: M + 0.4, y: 0.5, w: W - 2 * M - 0.8, h: 0.7, fontSize: 30, bold: true, color: COL.white, valign: 'middle' });
  const small = pct(N.params_bins[Object.keys(N.params_bins)[0]], N.n_params_reported);
  const pts = [
    ['開源模型以 Llama 家族為主，', `${small}% 的模型在 10B 以下；${N.n_medical_model_studies}/${N.n_studies} 篇用了醫療領域模型。`],
    ['提示工程仍是主流，', `${nFT}/${N.n_studies} 篇有微調；${N.deployment.NR}/${N.n_studies} 篇未報告部署方式。`],
    ['同一研究內比較，閉源多小幅領先，', `但 ${N.n_studies_open_comparable_or_better}/${N.n_pair_studies} 篇開源追平或較好；微調組差距中位數僅 ${f3(N.median_gap_finetuned)}。`],
    ['證據品質有限，', `改編 QUADAS-2 評估 ${Q.n_high}/${Q.rows.length} 篇整體為高偏倚風險。`],
  ];
  pts.forEach(([a, b], i) => {
    const y = 1.45 + i * 1.22;
    s.addShape(pres.shapes.OVAL, { x: M + 0.4, y: y + 0.08, w: 0.7, h: 0.7, fill: { color: COL.blue }, line: { color: COL.blue, width: 0 } });
    T(s, String(i + 1), { x: M + 0.4, y: y + 0.08, w: 0.7, h: 0.7, fontSize: 24, bold: true, color: COL.white, align: 'center', valign: 'middle' });
    T(s, [{ text: a, options: { bold: true, color: COL.white } }, { text: b, options: { color: COL.paleNavy } }],
      { x: M + 1.4, y, w: W - 2 * M - 1.8, h: 0.95, fontSize: 24, valign: 'middle' });
  });
  T(s, '檢索紀錄、篩選結果、萃取表與分析腳本皆保存於專案資料夾，可重現', { x: M + 0.4, y: 6.55, w: 9.4, h: 0.4, fontSize: 15, color: COL.lightBlue, valign: 'middle' });
  T(s, '敬請指教', { x: W - M - 2.9, y: 6.5, w: 2.5, h: 0.5, fontSize: 22, bold: true, color: COL.white, align: 'right', valign: 'middle' });
  // Q&A happens on this slide, so the prepared answers travel with it.
  must(NOTES.conclusion && NOTES.thanks, 'speaker notes conclusion + thanks');
  s.addNotes(NOTES.conclusion + '\n\n' + NOTES.thanks);
}

// ---------- 23 references ----------
{
  const s = content(null, '參考文獻', 'refs', { appendix: ' ' });
  const ref = (id) => `${authors(SID[id].record_id)}. ${SID[id].title.replace(/\.$/, '')}. ${SID[id].venue}. ${SID[id].year}. doi:${SID[id].doi}`;
  const refs = [
    'Abdellaoui C, Redjdal A, Seroussi B. Generative-AI-Based Approaches for Information Extraction from Clinical Notes: A Scoping Review. Stud Health Technol Inform. 2025;328:193–197. doi:10.3233/SHTI250700',
    `${authors('R0543')}. ${REC.R0543.title.replace(/\.$/, '')}. J Am Med Inform Assoc. ${REC.R0543.year}. doi:${REC.R0543.doi}`,
    'Page MJ, McKenzie JE, Bossuyt PM, et al. The PRISMA 2020 statement: an updated guideline for reporting systematic reviews. BMJ. 2021;372:n71',
    'Sugihara Y, Milosavljevic A, Jankovskaja S, Falk M. A review for navigating the trade-offs: evaluating open-source and proprietary large language models for clinical and biomedical information extraction. Front Digit Health. 2026. doi:10.3389/fdgth.2026.1778786',
    ref('S052'),
    ref('S033'),
  ];
  must(REC.R0543.pmid === '41528313', 'JAMIA review record');
  T(s, refs.map((r, i) => ({ text: r, options: { breakLine: i < refs.length - 1 } })), { x: M, y: CT, w: W - 2 * M, h: CH, fontSize: 16, color: COL.body, paraSpaceAfter: 14, valign: 'top' });
}

// ---------- appendix ----------
{
  const CODE = { X1: '發表類型不符（回顧、社論、無全文）', X2: '非英文論文', X3: '未使用符合定義的 LLM', X4: '只使用閉源 LLM',
    X5: '非臨床自由文本（含只用合成文本）', X6: '非資訊抽取任務', X7: '無量化評估', X8: '同一研究的其他版本' };
  const ft = Object.entries(C.full_text_excluded_by_code).sort((a, b) => b[1] - a[1]);
  const s = content(null, `全文排除 ${ftExcluded} 篇，最常見原因是只用閉源 LLM 與重複版本`, 'appx_codes', { appendix: '附錄 A　排除代碼' });
  bar(s, ft.map(([k]) => k), ft.map(([, v]) => v), { w: 5.2, name: '篇數' });
  table(s, [['代碼', '定義'], ...Object.entries(CODE).map(([k, v]) => [k, v])], { x: 6.0, y: CT, w: W - M - 6.0, colW: [1.0, W - M - 7.0], fontSize: 17, rowH: 0.58 });
  source(s, '排除代碼依序判斷，取第一個符合者');
}
{
  const s = content(null, `六個來源以統一檢索式檢索，共 ${dbTotal.toLocaleString()} 筆，去重後 ${C.screened.toLocaleString()} 筆`, 'appx_sources', { appendix: '附錄 B1　檢索來源' });
  const field = { PubMed: '[tiab] + MeSH', arXiv: '摘要', medRxiv: '標題／摘要（經 Europe PMC）', Scopus: 'TITLE-ABS-KEY', 'IEEE Xplore': 'All Metadata', ACM: '標題／摘要／關鍵字' };
  const rows = Object.entries(C.database_counts).sort((a, b) => b[1] - a[1]).map(([k, v]) => [k, field[k] || '', { text: v.toLocaleString(), options: { align: 'right' } }]);
  table(s, [['來源', '檢索欄位', '筆數'], ...rows, [{ text: '合計', options: { bold: true } }, '', { text: dbTotal.toLocaleString(), options: { bold: true, align: 'right' } }]],
    { x: M, y: CT, w: 7.95, colW: [2.2, 4.25, 1.5], fontSize: 19, rowH: 0.64 });
  stats(s, [{ v: '6', l: '個來源，2026-11-14 同日完成' }, { v: '10/10', l: '預先選定的驗證集全部檢出', hi: true }, { v: C.duplicates_removed, l: '筆自動去重移除' }]);
  source(s, '概念區塊：LLM × 臨床文本 × 資訊抽取；PubMed 完整檢索式見附錄 B2');
}
{
  const s = content(null, 'PubMed 檢索式：三個概念區塊以 AND 結合，限 2022 年以後', 'appx_query', { appendix: '附錄 B2　檢索式' });
  const q = [
    '("large language model*"[tiab] OR LLM[tiab] OR LLMs[tiab] OR "foundation model*"[tiab] OR "open-source"[tiab] OR "open-weight*"[tiab] OR Llama[tiab] OR Mistral[tiab] OR Mixtral[tiab] OR Qwen*[tiab] OR Gemma[tiab] OR DeepSeek[tiab] OR "Phi-3"[tiab] OR "Phi-4"[tiab] OR Vicuna[tiab] OR Falcon[tiab] OR BioMistral[tiab] OR Meditron[tiab] OR … OR "Large Language Models"[Mesh])',
    'AND ("clinical note*"[tiab] OR "clinical text*"[tiab] OR "medical record*"[tiab] OR "health record*"[tiab] OR EHR[tiab] OR EMR[tiab] OR "discharge summar*"[tiab] OR "progress note*"[tiab] OR "radiology report*"[tiab] OR "pathology report*"[tiab] OR … OR "Electronic Health Records"[Mesh])',
    'AND ("information extraction"[tiab] OR "named entity recognition"[tiab] OR NER[tiab] OR "relation extraction"[tiab] OR "entity extraction"[tiab] OR "data extraction"[tiab] OR "chart abstraction"[tiab] OR "structured data"[tiab] OR … OR "text mining"[tiab])',
    'AND ("2022/01/01"[dp] : "2026/12/31"[dp])',
  ];
  card(s, M, CT, W - 2 * M, CH, COL.gray);
  T(s, q.map((t, i) => ({ text: t, options: { breakLine: i < q.length - 1 } })), { x: M + 0.3, y: CT + 0.25, w: W - 2 * M - 0.6, h: CH - 0.5, fontSize: 16, color: COL.body, paraSpaceAfter: 14, valign: 'top', fontFace: 'Consolas' });
  source(s, '「…」為節錄；其他來源依各自語法改寫同一組詞彙');
}
{
  const rows = [...N.study_level].sort((a, b) => a.gap_median - b.gap_median);
  const half = Math.ceil(rows.length / 2);
  [rows.slice(0, half), rows.slice(half)].forEach((part, k) => {
    const s = content(null, `${N.n_pair_studies} 篇配對研究逐篇數值（依差距排序，${k + 1}/2）`, 'appx_pairs', { appendix: `附錄 C${k + 1}　逐篇配對` });
    table(s, [['研究', '比較數', '開源中位數', '閉源中位數', '差距中位數'], ...part.map((d) => [d.label, String(d.n), f3(d.open_median), f3(d.closed_median),
      { text: f3(d.gap_median), options: { bold: d.gap_median <= N.tie_threshold, color: d.gap_median <= N.tie_threshold ? COL.blue : COL.body } }])],
    { x: M, y: CT, w: W - 2 * M, colW: [4.33, 1.7, 2.1, 2.1, 2.1], fontSize: 15, rowH: CH / (half + 1), margin: [1, 8, 1, 8] });
    source(s, `藍色粗體 = 開源追平或較好（差距 ≤ ${N.tie_threshold}）；差距中位數取自各組差距，不一定等於前兩欄相減`);
  });
}
{
  const gaps = N.comparisons.map((p) => p.gap);
  const bins = [['< −0.05', (g) => g < -0.05], ['−0.05～0.02', (g) => g >= -0.05 && g <= N.tie_threshold],
    ['0.02～0.10', (g) => g > N.tie_threshold && g <= 0.1], ['0.10～0.20', (g) => g > 0.1 && g <= 0.2], ['> 0.20', (g) => g > 0.2]];
  const counts = bins.map(([, f]) => gaps.filter(f).length);
  must(counts.reduce((a, b) => a + b, 0) === N.n_comparisons && counts[0] + counts[1] === N.n_open_comparable_or_better, 'gap bins');
  const s = content(null, `任務層級 ${N.n_comparisons} 組比較：差距中位數 ${f3(N.median_gap)}，${N.n_open_comparable_or_better} 組開源追平或較好`, 'appx_tasks', { appendix: '附錄 C3　任務層級比較' });
  s.addChart(pres.charts.BAR, [{ name: '比較數', labels: bins.map(([l]) => l), values: counts }], {
    x: M, y: CT, w: 7.95, h: CH, barDir: 'col', barGapWidthPct: 35, chartColors: [COL.blue, COL.blue, 'C9C9C9', 'A6A6A6', '7F7F7F'],
    ...axis, dataLabelPosition: 'outEnd', valAxisHidden: true,
    showCatAxisTitle: true, catAxisTitle: '差距（閉源 − 開源）；藍色 = 開源追平或較好', catAxisTitleFontFace: FONT, catAxisTitleFontSize: 14, catAxisTitleColor: COL.muted,
  });
  stats(s, [{ v: N.n_open_comparable_or_better, l: `組開源追平或較好（${pct(N.n_open_comparable_or_better, N.n_comparisons)}%）`, hi: true },
    { v: N.n_closed_ahead, l: '組閉源領先' }, { v: f3(N.median_gap), l: '差距中位數（任務層級）' }]);
  source(s, '任務層級：一篇研究可貢獻多組比較；右尾（差距 > 0.20）多來自少數多任務研究');
}
{
  const why = { S001: '閉源 Gemini 3 Flash 數值只在 PDF 附錄（p.25），萃取文字未收錄', S022: '開源與閉源的直接比較只畫在 Figure 3，正文無數值',
    S030: '閉源結果只在圖與補充表；指標為 RMSE', S102: '原文同一條件前後報告兩組不同數值，無法確定',
    S118: '開源模型數值只在補充表', S119: '開源數值只在補充表，正文僅給範圍', S164: '開源數值只在 Figure 3 與補充表' };
  N.unpaired.forEach((u) => must(why[u.study_id], 'unpaired reason for ' + u.study_id));
  const s = content(null, `${N.unpaired.length} 篇有閉源實測但無法配對：數值多只在圖或補充資料`, 'appx_unpaired', { appendix: '附錄 D　無法配對的研究' });
  table(s, [['研究', '無法配對的原因'], ...N.unpaired.map((u) => [u.label, why[u.study_id]])], { x: M, y: CT, w: W - 2 * M, colW: [3.0, 9.33], fontSize: 19, rowH: CH / (N.unpaired.length + 1) });
  source(s, '萃取規則：數值只取正文與 PDF 內表格，不從圖讀值、不萃取外部補充資料');
}
{
  const half = Math.ceil(Q.rows.length / 2);
  const mark = { '+': COL.low, '?': 'B7871A', '−': COL.high };
  [Q.rows.slice(0, half), Q.rows.slice(half)].forEach((part, k) => {
    const s = content(null, `改編 QUADAS-2 逐篇結果（${k + 1}/2）`, 'appx_quadas', { appendix: `附錄 E${k + 1}　品質評估` });
    table(s, [Q.header, ...part.map((r) => [r[0], ...r.slice(1).map((v) => ({ text: v, options: { align: 'center', bold: true, color: mark[v] } }))])],
      { x: M, y: CT, w: W - 2 * M, colW: [3.33, 1.3, 1.45, 1.45, 1.2, 1.2, 1.2, 1.2], fontSize: 14, rowH: CH / (half + 1), margin: [1, 6, 1, 6] });
    source(s, '+ 低風險　? 不明　− 高風險（偏倚風險與適用性疑慮）；適用性只評 D1、D2');
  });
}

const out = process.argv[2] ? path.resolve(process.argv[2]) : path.join(__dirname, 'open_llm_clinical_ie_review.pptx');
// pptxgenjs sets only the Latin typeface on chart text, so CJK labels fall back to PMingLiU: add the East Asian font.
// Folder entries in the ZIP break cloud co-editing: copy files only.
async function postprocess(file) {
  const zin = await JSZip.loadAsync(fs.readFileSync(file));
  const zout = new JSZip();
  let patched = 0;
  for (const name of Object.keys(zin.files)) {
    const f = zin.files[name];
    if (f.dir) continue;
    if (/^ppt\/charts\/chart\d+\.xml$/.test(name)) {
      let xml = await f.async('string');
      xml = xml.replace(/<a:latin typeface="([^"]+)"\/>(?!<a:ea)/g, (m, face) => { patched++; return `${m}<a:ea typeface="${face}"/>`; });
      zout.file(name, xml, { createFolders: false });
    } else zout.file(name, await f.async('nodebuffer'), { createFolders: false });
  }
  must(patched > 0, 'chart text got the East Asian font');
  fs.writeFileSync(file, await zout.generateAsync({ type: 'nodebuffer', compression: 'DEFLATE' }));
  return patched;
}
pres.writeFile({ fileName: out }).then(() => postprocess(out)).then((n) => console.log('wrote', out, pres.slides.length, 'slides;', n, 'chart font runs patched'));
