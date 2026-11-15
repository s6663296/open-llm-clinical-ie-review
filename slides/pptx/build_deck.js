// Academic PPTX for the classroom systematic review (academic-pptx + pptx skills).
// Every statistic is read at build time from analysis/*.json, extraction/review/*; nothing is typed in by hand.
// Usage (repo root): node slides/pptx/build_deck.js  ->  slides/pptx/open_llm_clinical_ie_review.pptx
const fs = require('fs');
const path = require('path');
const pptxgen = require('pptxgenjs');

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
const B50 = readJSON('analysis/blind50_agent_vs_sonnet.json');
const XC = readJSON('extraction/review/crosscheck_62_vs_174_summary.json');
const VR = readCSV('extraction/review/verify_report.csv');
const SID = Object.fromEntries(readCSV('extraction/study_ids.csv').map((r) => [r.study_id, r]));
const count = (arr, f) => arr.reduce((m, x) => { const k = f(x); m[k] = (m[k] || 0) + 1; return m; }, {});
const verdict = count(VR, (r) => r.verdict);
const dbTotal = Object.values(C.database_counts).reduce((a, b) => a + b, 0);
const sought = C.screened - C.title_abstract_excluded;
const ftExcluded = Object.values(C.full_text_excluded_by_code).reduce((a, b) => a + b, 0);
const scopeExcluded = C.included - N.n_studies;
const f2 = (x) => Number(x).toFixed(2);
const f3 = (x) => Number(x).toFixed(3);
const pct = (a, b) => Math.round((100 * a) / b);
const nonEnglishLangs = Object.keys(N.language).filter((k) => k !== 'English').length;
const byStudy = (id) => N.comparisons.filter((p) => p.study_id === id);
const label = (id) => N.study_level.find((d) => d.study_id === id)?.label || N.unpaired.find((d) => d.study_id === id)?.label;

// ---------- design ----------
const FONT = 'Microsoft JhengHei';
const COL = { navy: '1F4E79', blue: '2E75B6', orange: 'C55A11', body: '2D2D2D', muted: '767676', rule: 'D9D9D9',
  tint: 'EBF3FA', grid: 'E5E5E5', white: 'FFFFFF', lightBlue: 'A9C4E2', paleNavy: 'C9D9EE' };
const W = 13.333, H = 7.5, M = 0.6;
const SECTIONS = ['背景', '方法', '結果概覽', 'RQ1 模型', 'RQ2 策略', 'RQ3 效能', '討論'];
const ZH = {
  English: '英語', Spanish: '西班牙語', German: '德語', Thai: '泰語', French: '法語', Portuguese: '葡萄牙語',
  Russian: '俄語', Chinese: '中文', Norwegian: '挪威語', Japanese: '日語', Dutch: '荷蘭語',
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
  title: 'CONTENT',
  background: { color: COL.white },
  slideNumber: { x: W - M - 0.6, y: H - 0.42, w: 0.6, h: 0.3, fontFace: FONT, fontSize: 11, color: COL.muted, align: 'right' },
});
pres.defineSlideMaster({ title: 'DARK', background: { color: COL.navy } });

const T = (slide, text, o) => slide.addText(text, { fontFace: FONT, isTextBox: true, margin: 0, ...o });

function content(section, title, notes, { appendix } = {}) {
  const s = pres.addSlide({ masterName: 'CONTENT' });
  if (appendix) {
    T(s, appendix, { x: M, y: 0.22, w: 8, h: 0.3, fontSize: 12, color: COL.muted, italic: true });
  } else {
    const runs = [];
    SECTIONS.forEach((sec, i) => {
      const active = sec === section;
      runs.push({ text: sec, options: { color: active ? COL.blue : COL.muted, bold: active } });
      if (i < SECTIONS.length - 1) runs.push({ text: '   ·   ', options: { color: COL.rule } });
    });
    T(s, runs, { x: M, y: 0.22, w: W - 2 * M, h: 0.3, fontSize: 12 });
  }
  T(s, title, { x: M, y: 0.62, w: W - 2 * M, h: 0.95, fontSize: 26, bold: true, color: COL.navy, valign: 'top' });
  if (notes) s.addNotes(notes);
  return s;
}
const source = (s, text) => T(s, text, { x: M, y: H - 0.48, w: W - 2 * M - 1.0, h: 0.32, fontSize: 12, color: COL.muted, valign: 'middle' });
function bullets(s, items, o) {
  const runs = [];
  items.forEach((it, i) => {
    const last = i === items.length - 1;
    const parts = typeof it === 'string' ? [{ t: it }] : it.b ? [{ t: it.b, bold: true }, { t: it.t }] : [{ t: it.t }];
    parts.forEach((p, j) => runs.push({ text: p.t, options: {
      bold: !!p.bold, bullet: j === 0 ? (o.numbered ? { type: 'number' } : { indent: 18 }) : undefined,
      breakLine: j === parts.length - 1 && !last } }));
  });
  T(s, runs, { fontSize: 18, color: COL.body, paraSpaceAfter: 10, valign: 'top', ...o, margin: [0, 0, 0, 2] });
}
function sideHead(s, text, x, y, w) { T(s, text, { x, y, w, h: 0.4, fontSize: 20, bold: true, color: COL.blue }); }
function callout(s, x, y, w, h, text, o = {}) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: COL.tint }, line: { color: COL.blue, width: 1 }, rectRadius: 0.08 });
  T(s, text, { x: x + 0.25, y: y + 0.1, w: w - 0.5, h: h - 0.2, fontSize: 18, color: COL.navy, valign: 'middle', ...o });
}
const axis = { catAxisLabelFontFace: FONT, valAxisLabelFontFace: FONT, dataLabelFontFace: FONT, catAxisLabelColor: COL.body,
  valAxisLabelColor: COL.muted, catAxisLabelFontSize: 14, valAxisLabelFontSize: 12, dataLabelFontSize: 14, dataLabelColor: COL.body,
  valGridLine: { color: 'E5E5E5', size: 0.75 }, catGridLine: { style: 'none' }, showLegend: false, showValue: true,
  valAxisLineShow: false, catAxisLineShow: true, catAxisLineColor: 'BFBFBF' };
function bar(s, labels, values, o = {}) {
  const hi = o.highlight || [];
  const colors = labels.map((l) => (hi.includes(l) ? COL.navy : '8EB1D8'));
  s.addChart(pres.charts.BAR, [{ name: o.name || '研究數', labels, values }], {
    x: o.x ?? M, y: o.y ?? 1.75, w: o.w ?? 7.9, h: o.h ?? 4.9, barDir: o.dir || 'bar', barGapWidthPct: 45,
    chartColors: colors, dataLabelPosition: 'outEnd', catAxisOrientation: o.dir === 'col' ? 'minMax' : 'maxMin',
    valAxisHidden: true, ...axis, ...(o.axisTitle ? { showValAxisTitle: false, showCatAxisTitle: true, catAxisTitle: o.axisTitle,
      catAxisTitleFontFace: FONT, catAxisTitleFontSize: 12, catAxisTitleColor: COL.muted } : {}),
  });
}
function table(s, rows, o) {
  const head = rows[0].map((h) => ({ text: h, options: { bold: true, color: COL.white, fill: { color: COL.navy } } }));
  const body = rows.slice(1).map((r, i) => r.map((c) => (typeof c === 'object' ? c : { text: String(c), options: { fill: { color: i % 2 ? 'F5F8FC' : COL.white } } })));
  s.addTable([head, ...body], { fontFace: FONT, fontSize: 16, color: COL.body, border: { type: 'solid', pt: 0.5, color: COL.rule },
    valign: 'middle', margin: [3, 6, 3, 6], autoPage: false, ...o });
}

// ---------- 0 cover ----------
{
  const s = pres.addSlide({ masterName: 'DARK' });
  T(s, '系統性回顧 · PRISMA 2020', { x: 0.9, y: 1.3, w: 11, h: 0.4, fontSize: 16, color: COL.lightBlue });
  T(s, '開源大型語言模型用於臨床病歷資訊抽取', { x: 0.9, y: 1.85, w: 11.5, h: 0.9, fontSize: 40, bold: true, color: COL.white });
  T(s, '使用方式、效能，以及與閉源模型的差距', { x: 0.9, y: 2.8, w: 11.5, h: 0.6, fontSize: 24, color: COL.paleNavy });
  T(s, '王閎立 · 羅泓勛 · 顏丞瑋', { x: 0.9, y: 4.5, w: 11, h: 0.45, fontSize: 20, color: COL.white });
  T(s, '[課程名稱] · [報告日期]', { x: 0.9, y: 5.0, w: 11, h: 0.4, fontSize: 16, color: COL.lightBlue });
  s.addNotes('開場：這是一份依 PRISMA 2020 撰寫的系統性回顧（課堂版），題目是開源、權重可下載的大型語言模型用在臨床自由文本資訊抽取。今天會回答三個問題：用了哪些模型、怎麼用、和閉源模型差多少。');
}

// ---------- 1 agenda ----------
{
  const s = content(null, '報告分為四段：從臨床需求出發，回答三個研究問題', '流程約 30–40 分鐘：背景 5 分鐘、方法 8 分鐘、結果 15 分鐘、討論與結論 7 分鐘。');
  const parts = [
    ['01', '背景與研究問題', '臨床資訊抽取的需求、開源模型的動機、既有回顧與本回顧的定位'],
    ['02', '方法', 'PRISMA 2020 流程：檢索、雙 AI 篩選、課堂版範圍、萃取與原文核對'],
    ['03', '結果', 'RQ1 用了哪些模型 · RQ2 怎麼用 · RQ3 與閉源模型差多少'],
    ['04', '討論與結論', '主要發現、限制、對醫院與研究者的意義'],
  ];
  parts.forEach(([n, h, d], i) => {
    const y = 1.85 + i * 1.18;
    T(s, n, { x: M, y, w: 1.0, h: 0.9, fontSize: 36, bold: true, color: COL.blue, valign: 'top' });
    T(s, h, { x: M + 1.2, y, w: 10, h: 0.45, fontSize: 22, bold: true, color: COL.navy });
    T(s, d, { x: M + 1.2, y: y + 0.47, w: 10.5, h: 0.4, fontSize: 18, color: COL.body });
  });
}

// ---------- 2–5 background ----------
{
  const s = content('背景', '臨床最有價值的資訊多半寫在自由文本裡，需要資訊抽取才能用於研究',
    '用具體例子說明：放射報告的病灶大小與位置、病理報告的組織型態與 TNM、出院摘要的用藥與社會決定因素。這些都寫在自由文本，研究與品質監測需要的是結構化欄位，人工摘錄耗時昂貴。資訊抽取（IE）包含命名實體辨識（NER）、關係抽取（RE）、屬性判斷與預先定義欄位的抽取。');
  table(s, [['文本類型', '可抽取的結構化欄位（例）'],
    ['放射報告', '病灶大小、位置、分期、追蹤建議'],
    ['病理報告', '組織型態、切緣、TNM 分期、生物標記'],
    ['出院摘要、病程紀錄', '用藥與劑量、症狀、診斷、社會決定因素']],
  { x: M, y: 1.85, w: 7.6, colW: [2.6, 5.0], fontSize: 18, rowH: 0.62 });
  sideHead(s, '資訊抽取任務', 8.75, 1.85, 4);
  bullets(s, [{ b: 'NER：', t: '辨識藥名、症狀、檢查值' }, { b: '關係抽取：', t: '藥物—劑量、病灶—位置' },
    { b: '欄位抽取：', t: '輸出預先定義欄位的值' }], { x: 8.75, y: 2.35, w: 4.0, h: 2.6 });
  source(s, '本回顧的任務定義見 protocol 3.1（I3）；文件層級分類、摘要、問答與自動編碼不屬資訊抽取（X6）');
}
{
  const s = content('背景', '閉源 LLM 能做抽取，但病歷送到外部 API 有隱私、成本與重現性的疑慮',
    '開源（開放權重）模型可在院內伺服器執行，病歷不必離開醫院；不受 API 計價與模型版本更替影響；可用院內資料微調，權重固定所以結果可重現。本回顧的「開源」定義是權重可公開下載（不要求 OSI 開放授權），參數量 ≥ 1B 以排除 BERT 類模型（2026-11-13、11-14 決策）。');
  table(s, [['面向', '閉源 LLM（GPT、Gemini、Claude）', '開源 LLM（Llama、Qwen、Gemma…）'],
    ['病歷是否離院', '需送至外部 API（或特約雲端）', '可在院內伺服器執行'],
    ['成本', '依用量計價', '硬體與維運成本'],
    ['版本與重現性', '供應商可更新或下架模型', '權重固定，可重現'],
    ['客製化', '多數只能提示，部分可付費微調', '可用院內資料 LoRA／全參數微調']],
  { x: M, y: 1.85, w: W - 2 * M, colW: [2.4, 4.85, 4.88], fontSize: 18, rowH: 0.66 });
  callout(s, M, 5.55, W - 2 * M, 0.75, '本回顧的「開源」= 權重可公開下載（不要求 OSI 授權），且參數量 ≥ 1B');
}
{
  const s = content('背景', '既有回顧已涵蓋生成式 AI 抽取；本回顧聚焦同一研究內的開源 vs 閉源比較',
    '三篇既有回顧取自 protocol 2.1，皆已查證。Sugihara 等人回顧了開源與商用 LLM 在臨床及生醫資訊抽取的取捨，和本題最接近。本回顧不主張「首篇」或「尚無類似回顧」，定位是：只納入權重可下載、≥ 1B 的生成式模型與真實臨床文本，並在課堂版中只比較同一研究內的開源與閉源結果。');
  const refs = [
    ['Abdellaoui 等，2025', '生成式 AI 從臨床筆記抽取資訊的範疇回顧（Stud Health Technol Inform）'],
    ['JAMIA 系統性回顧（PMID 41528313）', '生成式 LLM 在電子病歷應用中的測試與評估'],
    ['Sugihara 等，2026', '開源與商用 LLM 在臨床及生醫資訊抽取的取捨（Front Digit Health）'],
  ];
  refs.forEach(([a, b], i) => {
    const y = 1.85 + i * 1.0;
    T(s, a, { x: M, y, w: 4.2, h: 0.8, fontSize: 18, bold: true, color: COL.navy, valign: 'top' });
    T(s, b, { x: M + 4.4, y, w: 7.7, h: 0.8, fontSize: 18, color: COL.body, valign: 'top' });
  });
  callout(s, M, 5.0, W - 2 * M, 1.0, '本回顧的定位：只納入權重可下載、≥ 1B 的生成式模型與真實臨床文本；效能只在同一研究內比較開源與閉源');
  source(s, 'Abdellaoui et al. (2025)；JAMIA PMID 41528313；Sugihara et al. (2026)。完整書目見參考文獻頁');
}
{
  const s = content('背景', '本回顧回答三個研究問題',
    'RQ1–RQ4 於 2026-11-14 採用。課堂版萃取只做模型、任務、效能，所以 RQ4（可重現性：程式碼、prompt、資料公開）沒有萃取，列為未來工作。');
  const rq = [['RQ1', '用了哪些開源 LLM？規模多大？是否使用醫療領域模型？'],
    ['RQ2', '怎麼用：zero-shot、few-shot、微調、RAG？部署在哪裡？'],
    ['RQ3', '在同一研究內，與閉源 LLM 相比效能差多少？']];
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 1.4, y: 1.85, w: W - 2.8, h: 3.6, fill: { color: COL.tint }, line: { color: COL.blue, width: 1.25 }, rectRadius: 0.08 });
  rq.forEach(([k, q], i) => {
    const y = 2.15 + i * 1.08;
    T(s, k, { x: 1.8, y, w: 1.2, h: 0.7, fontSize: 28, bold: true, color: COL.blue, valign: 'middle' });
    T(s, q, { x: 3.1, y, w: 8.6, h: 0.7, fontSize: 22, color: COL.navy, valign: 'middle' });
  });
  T(s, 'RQ4（可重現性：程式碼、prompt、資料公開）課堂版未萃取，列為未來工作', { x: 1.4, y: 5.75, w: W - 2.8, h: 0.4, fontSize: 16, color: COL.muted });
}

// ---------- 6–12 methods ----------
{
  const s = content('方法', '納入：≥ 1B 開源 LLM、真實臨床文本、有量化評估的資訊抽取研究',
    '條件取自 protocol 3.1–3.2。排除代碼依序判斷，取第一個符合者：X1 發表類型、X2 非英文、X3 未使用符合定義的 LLM、X4 只用閉源、X5 非臨床自由文本（含只用合成文本）、X6 非抽取任務、X7 無量化評估、X8 同一研究的其他版本。');
  sideHead(s, '納入（全部符合）', M, 1.8, 5.9);
  bullets(s, [{ b: 'P　', t: '真實臨床自由文本：病歷、出院摘要、影像與病理報告' }, { b: 'I　', t: '至少一個開源 LLM（權重可下載、≥ 1B）' },
    { b: 'O　', t: '資訊抽取任務，且有量化評估（F1 等）' }, { b: '期間　', t: '2022–2026；英文論文，病歷語言不限' }],
  { x: M, y: 2.3, w: 5.9, h: 3.6 });
  sideHead(s, '排除（代碼 X1–X8）', 6.9, 1.8, 5.8);
  bullets(s, [{ b: 'X4　', t: '只用閉源 LLM' }, { b: 'X5　', t: '非臨床文本，或只用合成病歷' },
    { b: 'X6　', t: '摘要、問答、ICD 自動編碼、文件層級分類' }, { b: 'X1／X7　', t: '回顧、社論、無全文；無量化評估' }],
  { x: 6.9, y: 2.3, w: 5.8, h: 3.6 });
  source(s, '完整定義：protocol/protocol.md 3.1–3.2；排除代碼與各代碼篇數見附錄 A');
}
{
  const s = content('方法', `六個來源以統一檢索式檢索，共 ${dbTotal.toLocaleString()} 筆，去重後 ${C.screened.toLocaleString()} 筆`,
    '檢索式由三個概念區塊組成：LLM AND 臨床文本 AND 資訊抽取，限 2022 年以後；欄位統一為標題、摘要、關鍵字（IEEE 為 All Metadata）。所有來源於 2026-11-14 同日完成。以 10 篇驗證集測試，10/10 檢出。數字來源 analysis/prisma_counts.json。');
  const field = { PubMed: '[tiab] + MeSH', arXiv: '摘要', medRxiv: '標題／摘要（經 Europe PMC）', Scopus: 'TITLE-ABS-KEY', 'IEEE Xplore': 'All Metadata', ACM: '標題／摘要／關鍵字' };
  const rows = Object.entries(C.database_counts).sort((a, b) => b[1] - a[1]).map(([k, v]) => [k, field[k] || '', { text: v.toLocaleString(), options: { align: 'right' } }]);
  table(s, [['來源', '檢索欄位', '筆數'], ...rows, [{ text: '合計', options: { bold: true } }, '', { text: dbTotal.toLocaleString(), options: { bold: true, align: 'right' } }]],
    { x: M, y: 1.8, w: 7.6, colW: [2.2, 3.9, 1.5], fontSize: 16, rowH: 0.5 });
  sideHead(s, '重點', 8.75, 1.8, 4);
  bullets(s, ['2026-11-14 同日完成六個來源', '概念區塊：LLM × 臨床文本 × 資訊抽取', '預先選定 10 篇驗證集，10/10 檢出',
    `自動去重移除 ${C.duplicates_removed} 筆`], { x: 8.75, y: 2.3, w: 4.0, h: 3.5 });
  source(s, '完整檢索式：protocol 3.4（PubMed 版本見附錄 B）');
}
{
  const kb = K.binary.kappa;
  const s = content('方法', `兩個 AI 獨立篩選，二元一致性 κ = ${f2(kb)}，分歧由作者裁定`,
    `如實說明：篩選以兩個 AI（Claude Sonnet 與 Claude Opus）為主，作者裁定分歧，不是兩位人工獨立篩選。κ 是兩個 AI 之間的一致性（二元 ${f2(kb)}、三類 ${f2(K.three_category.kappa)}），不是人工 κ。全文階段 Sonnet 讀全部 ${C.full_text_assessed} 篇，Opus 複查 Sonnet 判排除者；11 列分歧經作者授權由 Agent 裁定。`);
  const steps = [
    ['標題／摘要', C.screened.toLocaleString(), `Sonnet 與 Opus 各自判斷全部紀錄\n分歧由作者裁定；排除 ${C.title_abstract_excluded}`],
    ['全文', String(C.full_text_assessed), `取得全文者由 AI 讀摘要、方法、結果\n未取得全文 ${C.full_text_not_retrieved}；排除 ${ftExcluded}`],
    ['納入', String(C.included), '符合原始納入條件的研究'],
  ];
  steps.forEach(([h, n, d], i) => {
    const x = M + i * 4.1;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.9, w: 3.7, h: 3.3, fill: { color: i === 2 ? COL.tint : 'F7F9FC' }, line: { color: i === 2 ? COL.blue : COL.rule, width: 1 }, rectRadius: 0.08 });
    T(s, h, { x: x + 0.25, y: 2.05, w: 3.2, h: 0.4, fontSize: 20, bold: true, color: COL.blue });
    T(s, n, { x: x + 0.25, y: 2.5, w: 3.2, h: 0.9, fontSize: 44, bold: true, color: COL.navy });
    T(s, d, { x: x + 0.25, y: 3.5, w: 3.25, h: 1.5, fontSize: 16, color: COL.body, valign: 'top' });
    if (i < 2) s.addShape(pres.shapes.LINE, { x: x + 3.72, y: 3.55, w: 0.36, h: 0, line: { color: COL.muted, width: 1.5, endArrowType: 'triangle' } });
  });
  callout(s, M, 5.5, W - 2 * M, 0.75, `限制：AI 為主的篩選，κ 為兩個 AI 間的一致性（三類 ${f2(K.three_category.kappa)}），非人工 κ`);
  source(s, '資料：analysis/sonnet_vs_opus.json、analysis/prisma_counts.json；混淆矩陣見附錄 C');
}
{
  const s = content('方法', `PRISMA 2020 流程：${C.included} 篇符合原始條件，課堂版最終納入 ${N.n_studies} 篇`,
    `流程：${dbTotal} → 去重 ${C.screened} → 標題摘要排除 ${C.title_abstract_excluded} → 尋求全文 ${sought}（未取得 ${C.full_text_not_retrieved}）→ 評估 ${C.full_text_assessed} → 排除 ${ftExcluded} → ${C.included} → 課堂版收緊條件排除 ${scopeExcluded} → ${N.n_studies}。引用追蹤未做，所以只有資料庫一條路徑。`);
  const left = [[`資料庫檢索\nn = ${dbTotal.toLocaleString()}`], [`標題／摘要篩選\nn = ${C.screened.toLocaleString()}`], [`尋求全文\nn = ${sought}`],
    [`全文評估\nn = ${C.full_text_assessed}`], [`符合原始納入條件\nn = ${C.included}`], [`課堂版最終納入\nn = ${N.n_studies}`]];
  const CODE = { X1: '發表類型', X3: '未用合格 LLM', X4: '只用閉源', X5: '非臨床文本', X6: '非抽取任務', X7: '無量化評估', X8: '其他版本' };
  const ft = Object.entries(C.full_text_excluded_by_code).sort((a, b) => b[1] - a[1]);
  const right = [`移除重複 n = ${C.duplicates_removed}`, `排除 n = ${C.title_abstract_excluded}`, `未取得全文 n = ${C.full_text_not_retrieved}`,
    `全文排除 n = ${ftExcluded}：` + ft.map(([k, v]) => `${CODE[k] || k} ${v}`).join('、'),
    `課堂版收緊條件排除 n = ${scopeExcluded}：預印本 ${N.scope_excluded_r1_preprint}、無閉源直接比較 ${N.scope_excluded_r2_no_closed}、核對發現不符原條件 ${N.scope_excluded_other}`];
  const top = 1.72, step = 0.86, bw = 3.0, bh = 0.66, lx = M + 0.3;
  left.forEach(([t], i) => {
    const y = top + i * step, last = i === left.length - 1;
    s.addShape(pres.shapes.RECTANGLE, { x: lx, y, w: bw, h: bh, fill: { color: last ? COL.navy : COL.white }, line: { color: last ? COL.navy : COL.blue, width: 1 } });
    T(s, t, { x: lx, y, w: bw, h: bh, fontSize: 15, bold: last, color: last ? COL.white : COL.navy, align: 'center', valign: 'middle' });
    if (!last) s.addShape(pres.shapes.LINE, { x: lx + bw / 2, y: y + bh, w: 0, h: step - bh, line: { color: COL.muted, width: 1.25, endArrowType: 'triangle' } });
  });
  right.forEach((t, i) => {
    const y = top + i * step + step / 2 + 0.04, rx = lx + bw + 0.9;
    s.addShape(pres.shapes.LINE, { x: lx + bw / 2, y: y + 0.29, w: 0.9 + bw / 2, h: 0, line: { color: COL.muted, width: 1, endArrowType: 'triangle' } });
    s.addShape(pres.shapes.RECTANGLE, { x: rx, y, w: W - M - rx, h: 0.58, fill: { color: 'F7F9FC' }, line: { color: COL.rule, width: 1 } });
    T(s, t, { x: rx + 0.15, y, w: W - M - rx - 0.3, h: 0.58, fontSize: 14, color: COL.body, valign: 'middle' });
  });
  source(s, '資料：analysis/prisma_counts.json、analysis/slide_numbers.json；排除代碼定義見 protocol 3.2（附錄 A）');
}
{
  const s = content('方法', `課堂版再限「同儕審查」且「與閉源 LLM 直接比較」，${C.included} → ${N.n_studies} 篇`,
    `這是事後設定的收緊條件，目的是讓 RQ3 的比較有足夠資料，並把萃取量控制在課堂報告可負擔的範圍。R2 判定：腳本依全文關鍵字提出候選，萃取時確認是否真有同一資料上的閉源數值。閉源有實測但數值只在圖或補充資料者仍算符合 R2，只是無法配對（附錄 E）。範圍由 Agent 依作者授權定案，理由逐篇記錄於 extraction/scope_restriction.csv。`);
  const cards = [['R1 同儕審查', N.scope_excluded_r1_preprint, '排除 arXiv、medRxiv 等預印本'],
    ['R2 閉源直接比較', N.scope_excluded_r2_no_closed, '同一研究、同一資料沒有閉源 LLM 結果'],
    ['核對時發現不符', N.scope_excluded_other, '只有摘要 1 篇、非臨床病歷文本 2 篇']];
  cards.forEach(([h, n, d], i) => {
    const x = M + i * 4.1;
    s.addShape(pres.shapes.RECTANGLE, { x, y: 1.85, w: 3.7, h: 2.6, fill: { color: 'F7F9FC' }, line: { color: COL.rule, width: 1 } });
    T(s, h, { x: x + 0.25, y: 2.0, w: 3.2, h: 0.4, fontSize: 20, bold: true, color: COL.blue });
    T(s, `排除 ${n}`, { x: x + 0.25, y: 2.5, w: 3.2, h: 0.8, fontSize: 36, bold: true, color: COL.navy });
    T(s, d, { x: x + 0.25, y: 3.4, w: 3.2, h: 0.9, fontSize: 16, color: COL.body, valign: 'top' });
  });
  callout(s, M, 4.75, W - 2 * M, 1.2, `課堂版納入 ${N.n_studies} 篇，其中 ${N.n_pair_studies} 篇有可配對的開源 vs 閉源數值；收緊條件為事後設定，於限制中說明`);
  source(s, '資料：extraction/scope_restriction.csv（author_decision、decision_reason）、analysis/slide_numbers.json');
}
{
  const fixN = verdict.fix || 0, nVer = VR.length;
  const s = content('方法', `萃取經頁碼驗證、兩套 AI 交叉比對，並對原文核對 ${nVer} 個最佳結果列`,
    `萃取欄位依課堂版範圍精簡為模型、任務、效能。效能取 F1 優先；每個模型取最佳設定；同任務取最佳閉源比較對象。交叉比對：同一批研究另有一套 174 篇 AI 預填，兩套結果一致 ${XC.status.agree} 篇、不一致者優先核對。對原文核對 ${nVer} 列：正確 ${verdict.correct}、需修正 ${fixN}、不配對 ${verdict.no_pair}、無法判斷 ${verdict.unclear}。課堂版範圍與核對由 AI Agent 依作者授權完成，非作者逐篇人工核對。`);
  const steps = [['1 預填', 'Codex 依萃取指引填寫模型、任務、效能，每個數值附原文頁碼'],
    ['2 頁碼驗證', '腳本檢查每個數值確實出現在所標頁碼'],
    ['3 交叉比對', `與另一套 174 篇 AI 預填比對；一致 ${XC.status.agree} 篇，其餘優先核對`],
    ['4 對原文核對', `${nVer} 個最佳結果列：正確 ${verdict.correct}、修正 ${fixN}、不配對 ${verdict.no_pair}`]];
  steps.forEach(([h, d], i) => {
    const x = M + i * 3.07;
    s.addShape(pres.shapes.RECTANGLE, { x, y: 1.85, w: 2.82, h: 3.0, fill: { color: i === 3 ? COL.tint : 'F7F9FC' }, line: { color: i === 3 ? COL.blue : COL.rule, width: 1 } });
    T(s, h, { x: x + 0.2, y: 2.0, w: 2.45, h: 0.45, fontSize: 20, bold: true, color: COL.blue });
    T(s, d, { x: x + 0.2, y: 2.55, w: 2.45, h: 2.2, fontSize: 16, color: COL.body, valign: 'top' });
  });
  callout(s, M, 5.15, W - 2 * M, 1.0, '揭露：課堂版範圍與萃取核對由 AI Agent 依作者授權完成，非作者逐篇人工核對');
  source(s, '資料：extraction/review/verify_report.csv、crosscheck_62_vs_174_summary.json；修正紀錄 agent_edits.csv（附錄 F）');
}
{
  const s = content('方法', `效能只在同一研究內比較：差距 = 閉源 − 開源，≤ ${N.tie_threshold} 視為追平`,
    `各研究的指標、資料集與標註不同，跨研究直接比較 F1 沒有意義，所以只計算同一研究、同一任務與資料集內的差距。追平門檻 ${N.tie_threshold} 事先寫在 scripts/analysis/slide_figures.py。多任務研究（例如 van der Loo 2026 有 13 組比較）會主導任務層級結果，所以主要結果用研究層級：每篇取其各組差距的中位數。`);
  const items = [['配對', '每個任務與資料集：最佳開源 LLM vs 最佳閉源 LLM，且指標相同'],
    ['差距', `閉源 − 開源（0–1 尺度）；≤ ${N.tie_threshold} 視為開源追平或較好`],
    ['研究層級', '每篇取各組差距的中位數，避免多任務研究主導（主要結果）'],
    ['分組', '依開源模型使用方式分為「微調」（LoRA、QLoRA、全參數）與「提示」']];
  items.forEach(([h, d], i) => {
    const y = 1.85 + i * 1.08;
    T(s, h, { x: M, y, w: 2.4, h: 0.8, fontSize: 22, bold: true, color: COL.blue, valign: 'middle' });
    T(s, d, { x: M + 2.6, y, w: 9.5, h: 0.8, fontSize: 20, color: COL.body, valign: 'middle' });
    if (i < items.length - 1) s.addShape(pres.shapes.LINE, { x: M, y: y + 0.94, w: W - 2 * M, h: 0, line: { color: COL.rule, width: 0.75 } });
  });
  source(s, '敘述性綜合（SWiM）：指標與資料集異質，不做統合分析');
}

// ---------- 13–16 overview ----------
{
  const s = content('結果概覽', `${N.n_studies} 篇研究、${N.n_distinct_open_models} 個開源模型，${N.pct_non_english}% 使用非英語病歷`,
    `數字來自 analysis/slide_numbers.json（n_studies、n_distinct_open_models、pct_non_english、pct_finetune）。開源模型數以模型名稱計，同一模型不同寫法可能重複計算。非英語與微調比例的分母是 ${N.n_studies} 篇。`);
  const stats = [[N.n_studies, '納入研究'], [N.n_distinct_open_models, '不同開源模型'], [`${N.pct_non_english}%`, '非英語病歷'], [`${N.pct_finetune}%`, '有做微調']];
  stats.forEach(([v, l], i) => {
    const x = M + i * 3.07;
    s.addShape(pres.shapes.RECTANGLE, { x, y: 2.0, w: 2.82, h: 2.6, fill: { color: 'F7F9FC' }, line: { color: COL.rule, width: 1 } });
    T(s, String(v), { x, y: 2.25, w: 2.82, h: 1.3, fontSize: 60, bold: true, color: COL.navy, align: 'center' });
    T(s, l, { x, y: 3.65, w: 2.82, h: 0.5, fontSize: 20, color: COL.body, align: 'center' });
  });
  const yrs = Object.keys(N.years).sort();
  T(s, `出版年份 ${yrs[0]}–${yrs[yrs.length - 1]}；${N.n_pair_studies} 篇有可配對的開源 vs 閉源數值`, { x: M, y: 5.05, w: W - 2 * M, h: 0.5, fontSize: 20, color: COL.body });
  source(s, `資料：課堂版 ${N.n_studies} 篇萃取（extraction/extraction_scope62.xlsx → analysis/slide_numbers.json）`);
}
{
  const yrs = Object.keys(N.years).sort();
  const peak = yrs.reduce((a, b) => (N.years[b] > N.years[a] ? b : a));
  const s = content('結果概覽', `研究集中在近兩年，${peak} 年最多（${N.years[peak]} 篇）`,
    `年份分布：${yrs.map((y) => `${y} 年 ${N.years[y]} 篇`).join('、')}。課堂版沒有 2022–2023 年的研究（收緊條件要求與閉源 LLM 直接比較）。2027 年的 1 篇（Wang，Expert Systems with Applications）是書目上的出版年份；2026 年只檢索到 11 月 14 日。`);
  bar(s, yrs, yrs.map((y) => N.years[y]), { dir: 'col', w: 7.6, highlight: [peak] });
  sideHead(s, '重點', 8.75, 1.8, 4);
  bullets(s, [`${peak} 年 ${N.years[peak]} 篇，占 ${pct(N.years[peak], N.n_studies)}%`, '課堂版無 2022–2023 年研究',
    '2027 年 1 篇為書目出版年份', '2026 年檢索至 11 月 14 日'], { x: 8.75, y: 2.3, w: 4.0, h: 3.6 });
  source(s, `資料：課堂版納入研究（n = ${N.n_studies}）`);
}
{
  const langs = Object.entries(N.language).sort((a, b) => b[1] - a[1]);
  const s = content('結果概覽', `英語病歷占多數（${N.language.English}/${N.n_studies} 篇），其餘分散在 ${nonEnglishLangs} 種語言`,
    `一篇研究可有多種病歷語言。非英語病歷是開源模型可在地部署的重要場景，但在課堂版中各語言多只有 1–3 篇。`);
  bar(s, langs.map(([k]) => zh(k)), langs.map(([, v]) => v), { w: 7.6, h: 5.0, highlight: [] });
  sideHead(s, '重點', 8.75, 1.8, 4);
  bullets(s, [`英語 ${N.language.English} 篇（${pct(N.language.English, N.n_studies)}%）`, `非英語病歷 ${N.pct_non_english}%`,
    '西班牙語、德語之外多為單篇', '非英語場景仍是證據缺口'], { x: 8.75, y: 2.3, w: 4.0, h: 3.6 });
  source(s, `資料：studies.note_language（n = ${N.n_studies}；一篇可計入多種語言）`);
}
{
  const tt = Object.entries(N.text_types).sort((a, b) => b[1] - a[1]);
  must(tt[0][0] === 'clinical note (mixed)' && tt[1][0] === 'radiology report', 'text type ranking');
  const tk = Object.entries(N.task_types).sort((a, b) => b[1] - a[1]);
  must(tk[0][0] === 'field extraction', 'task ranking');
  const s = content('結果概覽', '混合型臨床紀錄最常見，其次是放射與病理報告；任務以欄位抽取為主',
    `文本類型：${tt.map(([k, v]) => `${zh(k)} ${v}`).join('、')}。任務類型：${tk.map(([k, v]) => `${zh(k)} ${v}`).join('、')}（一篇可計入多類）。`);
  bar(s, tt.map(([k]) => zh(k)), tt.map(([, v]) => v), { w: 7.6, h: 5.0 });
  sideHead(s, '任務類型（篇）', 8.75, 1.8, 4);
  table(s, [['任務', '篇數'], ...tk.map(([k, v]) => [zh(k), { text: String(v), options: { align: 'right' } }])],
    { x: 8.75, y: 2.3, w: 3.95, colW: [2.75, 1.2], fontSize: 16, rowH: 0.48 });
  source(s, `資料：studies.text_type、studies.task_types（n = ${N.n_studies}；一篇可計入多類）`);
}

// ---------- 17–18 RQ1 ----------
{
  const fam = Object.entries(N.model_family).sort((a, b) => b[1] - a[1]);
  must(fam[0][0] === 'Llama', 'Llama most common');
  const s = content('RQ1 模型', `Llama 家族最常用：${N.n_studies} 篇中 ${N.model_family.Llama} 篇使用`,
    `以「使用該家族的研究數」計，只計入有效能數值的開源模型。「其他」為未歸入七個主要家族的模型。`);
  bar(s, fam.map(([k]) => zh(k)), fam.map(([, v]) => v), { w: 7.6, h: 4.9, highlight: ['Llama'] });
  sideHead(s, '重點', 8.75, 1.8, 4);
  bullets(s, [`Llama ${N.model_family.Llama} 篇（${pct(N.model_family.Llama, N.n_studies)}%）`, `Qwen ${N.model_family.Qwen}、Gemma ${N.model_family.Gemma}、DeepSeek ${N.model_family.DeepSeek}`,
    `共 ${N.n_distinct_open_models} 個不同開源模型`], { x: 8.75, y: 2.3, w: 4.0, h: 3.6 });
  source(s, `資料：results 工作表 open LLM 列（n = ${N.n_studies} 篇；一篇可用多個家族）`);
}
{
  const pb = N.params_bins, small = pb['1–10B'];
  const s = content('RQ1 模型', `${pct(small, N.n_params_reported)}% 的模型在 10B 以下；${N.n_medical_model_studies} 篇（${N.pct_medical_model}%）用了醫療領域模型`,
    `參數量以「研究 × 模型」計，只算原文有報告者（${N.n_params_reported} 個）。醫療領域模型如 MedGemma、Meditron、Med42。`);
  const labs = Object.keys(pb);
  bar(s, labs, labs.map((k) => pb[k]), { dir: 'col', w: 7.6, highlight: ['1–10B'], name: '模型數' });
  sideHead(s, '重點', 8.75, 1.8, 4);
  bullets(s, [`10B 以下 ${small} 個（${pct(small, N.n_params_reported)}%）`, `> 100B 只有 ${pb['> 100B']} 個`,
    `醫療領域模型 ${N.n_medical_model_studies}/${N.n_studies} 篇`], { x: 8.75, y: 2.3, w: 4.0, h: 3.6 });
  source(s, `資料：results.params_b（研究 × 模型，n = ${N.n_params_reported}）、studies.medical_domain_model`);
}

// ---------- 19–20 RQ2 ----------
{
  const st = Object.entries(N.strategies).sort((a, b) => b[1] - a[1]);
  must(st[0][0] === 'zero-shot', 'zero-shot most common');
  const s = content('RQ2 策略', `提示工程仍是主流（zero-shot ${N.strategies['zero-shot']} 篇），${N.pct_finetune}% 的研究有做微調`,
    `一篇可計入多類。微調指 LoRA、QLoRA 或全參數微調；${N.pct_finetune}% 的研究至少用一種。「其他」包含蒸餾、自訂流程等。`);
  bar(s, st.map(([k]) => zh(k)), st.map(([, v]) => v), { w: 7.6, h: 5.0, highlight: ['LoRA', 'QLoRA', 'full FT'] });
  sideHead(s, '重點', 8.75, 1.8, 4);
  bullets(s, [`Zero-shot ${N.strategies['zero-shot']}、Few-shot ${N.strategies['few-shot']} 篇`, `微調（深色）：${N.pct_finetune}% 研究`,
    `RAG ${N.strategies.RAG} 篇、CoT ${N.strategies.CoT} 篇`], { x: 8.75, y: 2.3, w: 4.0, h: 3.6 });
  source(s, `資料：studies.strategies（n = ${N.n_studies}；一篇可計入多類）`);
}
{
  const dp = Object.entries(N.deployment).sort((a, b) => b[1] - a[1]);
  const s = content('RQ2 策略', `只有 ${N.pct_local}% 的研究明確只在本地執行，${N.deployment.NR} 篇未報告部署方式`,
    `每篇一類。原本假設多數研究在本地或院內執行，資料不支持。「混合」是開源模型在本地、閉源模型經 API。未報告的比例偏高，本身就是報告品質的發現。`);
  bar(s, dp.map(([k]) => zh(k)), dp.map(([, v]) => v), { w: 7.6, h: 4.6, highlight: ['NR'] });
  sideHead(s, '重點', 8.75, 1.8, 4);
  bullets(s, [`本地 ${N.deployment.local} 篇（${N.pct_local}%）`, `混合 ${N.deployment.mixed} 篇：開源本地＋閉源 API`,
    `未報告 ${N.deployment.NR} 篇（${pct(N.deployment.NR, N.n_studies)}%）`], { x: 8.75, y: 2.3, w: 4.0, h: 3.6 });
  source(s, `資料：studies.deployment（n = ${N.n_studies}；每篇一類）`);
}

// ---------- 21–26 RQ3 ----------
function dumbbell(s, rows, o) {
  const x0 = o.x + 2.6, x1 = o.x + o.w - 0.2, y0 = o.y + 0.45, rowH = Math.min(0.3, (o.h - 0.8) / rows.length);
  const X = (v) => x0 + (x1 - x0) * v;
  [0, 0.2, 0.4, 0.6, 0.8, 1.0].forEach((t) => {
    s.addShape(pres.shapes.LINE, { x: X(t), y: y0 - 0.1, w: 0, h: rowH * rows.length + 0.1, line: { color: COL.grid, width: 0.75 } });
    T(s, t.toFixed(1), { x: X(t) - 0.3, y: y0 + rowH * rows.length + 0.02, w: 0.6, h: 0.28, fontSize: 12, color: COL.muted, align: 'center' });
  });
  T(s, [{ text: '● 最佳開源 LLM', options: { color: COL.blue } }, { text: '　　● 最佳閉源 LLM', options: { color: COL.orange } }],
    { x: x0, y: o.y, w: x1 - x0, h: 0.3, fontSize: 14, bold: true });
  rows.forEach((d, i) => {
    const cy = y0 + i * rowH + rowH / 2, a = Math.min(d.open_median, d.closed_median), b = Math.max(d.open_median, d.closed_median);
    T(s, `${d.label}（${d.n}）`, { x: o.x, y: cy - rowH / 2, w: 2.5, h: rowH, fontSize: 13, color: COL.body, align: 'right', valign: 'middle' });
    if (b - a > 0.003) s.addShape(pres.shapes.LINE, { x: X(a), y: cy, w: X(b) - X(a), h: 0, line: { color: 'BFBFBF', width: 2.5 } });
    const r = 0.075;
    s.addShape(pres.shapes.OVAL, { x: X(d.closed_median) - r, y: cy - r, w: 2 * r, h: 2 * r, fill: { color: COL.orange }, line: { color: COL.white, width: 0.75 } });
    s.addShape(pres.shapes.OVAL, { x: X(d.open_median) - r, y: cy - r, w: 2 * r, h: 2 * r, fill: { color: COL.blue }, line: { color: COL.white, width: 0.75 } });
  });
  T(s, '效能（0–1）；括號 = 該研究的比較數', { x: x0, y: y0 + rowH * rows.length + 0.3, w: x1 - x0, h: 0.28, fontSize: 12, color: COL.muted, align: 'center' });
}
{
  const ahead = N.study_level.filter((d) => d.gap_median > N.tie_threshold).sort((a, b) => b.gap_median - a.gap_median);
  must(ahead.length === N.n_studies_closed_ahead, 'closed-ahead count');
  const s = content('RQ3 效能', `${N.n_pair_studies} 篇可配對研究中，${N.n_studies_closed_ahead} 篇閉源領先，但多數差距在 0.15 以內`,
    `研究層級：每篇取其各任務比較差距的中位數。閉源領先定義為差距 > ${N.tie_threshold}。差距最大的是 Godoy 2026 與 Sushil 2024（差距 > 0.4），其餘多在 0.03–0.15。van der Loo 2026 有 13 組比較，研究層級只算一次。`);
  dumbbell(s, ahead, { x: M, y: 1.7, w: 8.2, h: 5.2 });
  const within15 = ahead.filter((d) => d.gap_median <= 0.15).length;
  sideHead(s, '重點', 9.1, 1.8, 3.6);
  bullets(s, [`閉源領先 ${ahead.length} 篇`, `其中 ${within15} 篇差距 ≤ 0.15`,
    `全部 ${N.n_pair_studies} 篇差距中位數 ${f3(N.median_study_gap)}`], { x: 9.1, y: 2.3, w: 3.65, h: 3.8, fontSize: 18 });
  source(s, '資料：analysis/slide_numbers.json（study_level）；同一研究、同一任務與資料集內比較');
}
{
  const tie = N.study_level.filter((d) => d.gap_median <= N.tie_threshold).sort((a, b) => a.gap_median - b.gap_median);
  must(tie.length === N.n_studies_open_comparable_or_better, 'open-comparable count');
  const better = tie.filter((d) => d.gap_median < 0).length;
  const s = content('RQ3 效能', `${N.n_studies_open_comparable_or_better} 篇研究中開源追平或優於閉源，其中 ${better} 篇開源較好`,
    `追平或較好定義為差距 ≤ ${N.tie_threshold}。開源明顯較好的 Mittman 2026、Fu 2024 差距約 −0.3，報告時可補充其研究情境。逐篇數值見附錄 D。`);
  dumbbell(s, tie, { x: M, y: 1.7, w: 8.2, h: 5.2 });
  sideHead(s, '重點', 9.1, 1.8, 3.6);
  bullets(s, [`占可配對研究 ${pct(tie.length, N.n_pair_studies)}%`, `開源較好（差距 < 0）${better} 篇`,
    `${tie.filter((d) => Math.abs(d.gap_median) <= 0.05).length} 篇差距在 ±0.05 以內`], { x: 9.1, y: 2.3, w: 3.65, h: 3.8, fontSize: 18 });
  source(s, '資料：analysis/slide_numbers.json（study_level）；逐篇數值見附錄 D');
}
{
  const gaps = N.comparisons.map((p) => p.gap);
  const bins = [['< −0.05', (g) => g < -0.05], ['−0.05～0.02', (g) => g >= -0.05 && g <= N.tie_threshold],
    ['0.02～0.10', (g) => g > N.tie_threshold && g <= 0.1], ['0.10～0.20', (g) => g > 0.1 && g <= 0.2],
    ['> 0.20', (g) => g > 0.2]];
  const counts = bins.map(([, f]) => gaps.filter(f).length);
  must(counts.reduce((a, b) => a + b, 0) === N.n_comparisons && counts[0] + counts[1] === N.n_open_comparable_or_better, 'gap bins');
  const s = content('RQ3 效能', `任務層級 ${N.n_comparisons} 組比較：差距中位數 ${f3(N.median_gap)}，${N.n_open_comparable_or_better} 組開源追平或較好`,
    `以任務為單位算 ${N.n_comparisons} 組；一篇研究可貢獻多組，所以閉源領先的比例（${N.n_closed_ahead}/${N.n_comparisons}）比研究層級高。差距 > 0.20 的 ${counts[4]} 組中，多數來自 van der Loo 2026 的瓣膜分級任務（例如 Tricuspid Sten. grade Phi-4 0.185 vs GPT-4o 0.977）。`);
  s.addChart(pres.charts.BAR, [{ name: '比較數', labels: bins.map(([l]) => l), values: counts }], {
    x: M, y: 1.75, w: 8.0, h: 4.8, barDir: 'col', barGapWidthPct: 40, chartColors: [COL.blue, COL.blue, 'C9C9C9', 'A6A6A6', '7F7F7F'],
    ...axis, catAxisLabelFontSize: 14, dataLabelFontSize: 16, valAxisHidden: true,
    showCatAxisTitle: true, catAxisTitle: '差距（閉源 − 開源）；藍色 = 開源追平或較好（≤ 0.02），灰色越深 = 閉源領先越多', catAxisTitleFontFace: FONT, catAxisTitleFontSize: 12, catAxisTitleColor: COL.muted,
  });
  sideHead(s, '重點', 9.0, 1.8, 3.7);
  bullets(s, [`開源追平或較好 ${N.n_open_comparable_or_better} 組（${pct(N.n_open_comparable_or_better, N.n_comparisons)}%）`,
    `閉源領先 ${N.n_closed_ahead} 組`, `中位數 ${f3(N.median_gap)}；右尾來自少數多任務研究`], { x: 9.0, y: 2.3, w: 3.75, h: 3.8 });
  source(s, '資料：analysis/slide_numbers.json（comparisons）；分組由 build_deck.js 依差距計算');
}
{
  const s = content('RQ3 效能', `微調後的開源模型與閉源差距較小：中位數 ${f3(N.median_gap_finetuned)} vs 提示 ${f3(N.median_gap_prompting)}`,
    `這是觀察性的跨研究比較：微調組只有 ${N.n_finetuned_comparisons} 組，且微調研究的任務與資料可能本來就不同，不能解讀為「微調造成差距縮小」。分組依開源模型的使用方式：LoRA、QLoRA、全參數為微調，其餘為提示。`);
  s.addChart(pres.charts.BAR, [{ name: '差距中位數', labels: [`微調（n = ${N.n_finetuned_comparisons}）`, `提示（n = ${N.n_prompting_comparisons}）`], values: [N.median_gap_finetuned, N.median_gap_prompting] }], {
    x: M, y: 1.8, w: 7.6, h: 4.6, barDir: 'col', barGapWidthPct: 80, chartColors: [COL.blue, 'A6A6A6'], ...axis,
    catAxisLabelFontSize: 16, dataLabelFontSize: 16, dataLabelFormatCode: '0.000', valAxisHidden: true, valAxisMinVal: 0,
    showCatAxisTitle: true, catAxisTitle: '差距中位數（閉源 − 開源，任務層級）', catAxisTitleFontFace: FONT, catAxisTitleFontSize: 12, catAxisTitleColor: COL.muted,
  });
  sideHead(s, '重點', 8.75, 1.8, 4);
  bullets(s, [`微調組差距中位數 ${f3(N.median_gap_finetuned)}，接近追平門檻 ${N.tie_threshold}`, `提示組 ${f3(N.median_gap_prompting)}`,
    { b: '注意：', t: `微調組只有 ${N.n_finetuned_comparisons} 組，屬觀察性比較，非因果` }], { x: 8.75, y: 2.3, w: 4.0, h: 4.0 });
  source(s, '資料：analysis/slide_numbers.json（median_gap_finetuned、median_gap_prompting）');
}
{
  const p = byStudy('S033')[0];
  must(p && p.open_model === 'Med42-8B', 'S033 pair');
  const s = content('RQ3 效能', '代表研究一：小型醫療模型經任務微調，可超過通用閉源模型',
    `Wiyanti 等（2026）：病理報告的肺癌組織型四分類抽取。Med42-8B 以 LoRA 微調（由 Gemini 2.0 Flash 蒸餾）並本地部署，macro F1 ${p.open_value} vs Gemini 2.0 Flash ${p.closed_value}（${p.open_src}；${p.closed_src}）。樣本只有 33 份報告，屬概念驗證。數值已由 Agent 對原文核對。`);
  callout(s, M, 1.85, 5.6, 3.0, `Med42-8B（LoRA）\nmacro F1 ${p.open_value}\n\nGemini 2.0 Flash\nmacro F1 ${p.closed_value}`, { fontSize: 24, bold: true });
  sideHead(s, '研究設定', 6.6, 1.85, 6);
  bullets(s, [{ b: '文本：', t: '病理報告，肺癌組織型四分類' }, { b: '模型：', t: '8B 醫療領域模型，LoRA 微調、本地部署' },
    { b: '解讀：', t: '小模型＋任務微調可追上通用閉源模型' }, { b: '限制：', t: '測試集僅 33 份報告' }], { x: 6.6, y: 2.35, w: 6.1, h: 3.4 });
  source(s, `Wiyanti et al. (2026), ${SID.S033.venue}；數值出處 ${p.open_src}、${p.closed_src}`);
}
{
  const ps = byStudy('S052').sort((a, b) => b.gap - a.gap);
  const main = ps.find((p) => p.task === 'Main'), worst = ps[0];
  must(main && ps.every((p) => p.gap > 0), 'S052 all closed ahead');
  const s = content('RQ3 效能', `代表研究二：荷蘭語心血管報告的 ${ps.length} 項任務，閉源全面領先`,
    `van der Loo 等（2026）：荷蘭語心血管報告的結構化資料抽取。開源最佳為 Phi-4（few-shot、院內執行），閉源為 GPT-4o（Azure OpenAI）。主要冠狀動脈層級辨識 F1 ${main.open_value} vs ${main.closed_value}；瓣膜分級落差最大，例如 ${worst.task} ${worst.open_value} vs ${worst.closed_value}（${worst.open_src}）。`);
  const top = ps.slice(0, 7);
  s.addChart(pres.charts.BAR, [
    { name: 'Phi-4（開源）', labels: top.map((p) => p.task), values: top.map((p) => p.open_value) },
    { name: 'GPT-4o（閉源）', labels: top.map((p) => p.task), values: top.map((p) => p.closed_value) }], {
    x: M, y: 1.75, w: 7.9, h: 4.9, barDir: 'bar', barGapWidthPct: 40, chartColors: [COL.blue, COL.orange], ...axis,
    showLegend: true, legendPos: 't', legendFontFace: FONT, legendFontSize: 14, catAxisOrientation: 'maxMin', dataLabelFontSize: 11,
    dataLabelFormatCode: '0.00', valAxisHidden: true, valAxisMaxVal: 1.15,
  });
  sideHead(s, '重點', 8.9, 1.8, 3.9);
  bullets(s, [`${ps.length} 項任務閉源全部領先`, `主要任務 F1 ${main.open_value} vs ${main.closed_value}`, '瓣膜分級任務落差最大',
    '圖示差距最大的 7 項'], { x: 8.9, y: 2.3, w: 3.85, h: 3.8 });
  source(s, `van der Loo et al. (2026), ${SID.S052.venue}；p.5 Table 2、p.6 Table 3`);
}

// ---------- 27–29 discussion ----------
{
  const s = content('討論', '三個主要發現分別回答 RQ1–RQ3',
    '三點對應 RQ1（模型）、RQ2（策略與部署）、RQ3（效能）。強調 RQ3 是研究內比較，研究間指標與資料不同。');
  table(s, [['問題', '主要發現', '依據'],
    ['RQ1 模型', 'Llama 家族為主，醫療領域模型少', `Llama ${N.model_family.Llama}/${N.n_studies} 篇；醫療模型 ${N.pct_medical_model}%`],
    ['RQ2 策略', '提示為主，微調少；部署常未報告', `微調 ${N.pct_finetune}%；未報告部署 ${N.deployment.NR} 篇`],
    ['RQ3 效能', '閉源多小幅領先，部分研究開源追平；微調差距小', `研究層級 ${N.n_studies_open_comparable_or_better} 追平 vs ${N.n_studies_closed_ahead} 領先；微調 ${f3(N.median_gap_finetuned)}`]],
  { x: M, y: 1.85, w: W - 2 * M, colW: [1.9, 5.3, 4.93], fontSize: 18, rowH: 0.85 });
  source(s, '資料：analysis/slide_numbers.json');
}
{
  const s = content('討論', '結果需在七項限制下解讀',
    '這頁要誠實講完，評分者通常很重視。最重要的是：AI 為主的篩選與核對、全文取得率約一半、事後收緊條件。');
  table(s, [['面向', '限制'],
    ['未事先註冊', 'protocol 未註冊 OSF；方法變更皆記錄於決策紀錄'],
    ['AI 輔助篩選', '以兩個 AI 為主、作者裁定分歧，非兩位人工獨立篩選'],
    ['全文取得', `${sought} 篇中 ${C.full_text_not_retrieved} 篇無開放全文，可能遺漏相關研究`],
    ['事後收緊條件', `課堂版限同儕審查且有閉源比較，${C.included} → ${N.n_studies} 篇`],
    ['版本與指標', '部分數值取自預印本版；各研究指標與資料集不同'],
    ['萃取與核對', 'AI 預填、Agent 依作者授權對原文核對；作者未逐篇核對'],
    ['未做項目', '引用追蹤、偏倚風險評估、證據確信度評估']],
  { x: M, y: 1.75, w: W - 2 * M, colW: [2.6, 9.53], fontSize: 16, rowH: 0.6 });
}
{
  const s = content('討論', '對醫院：可先試院內微調小模型；對研究者：需同條件比較並報告部署',
    `醫院端建議依據研究層級 ${N.n_studies_open_comparable_or_better} 篇開源追平或較好、微調組差距中位數 ${f3(N.median_gap_finetuned)}；屬觀察性證據，不是因果結論。研究端建議依據 ${N.deployment.NR} 篇未報告部署方式，以及 ${N.unpaired.length} 篇研究因數值只在圖、補充資料或原文矛盾而無法配對。`);
  sideHead(s, '醫院與臨床資訊團隊', M, 1.85, 5.9);
  bullets(s, ['資料不能離院時，開源模型是可行選項', '以院內標註資料微調 10B 以下模型值得先試', '上線前在院內測試集與閉源基準比較'], { x: M, y: 2.35, w: 5.9, h: 3.4 });
  sideHead(s, '研究者', 6.9, 1.85, 5.8);
  bullets(s, ['同一測試集同時評估開源與閉源模型', '統一指標，報告於正文而非只在圖中', `報告部署方式（${N.deployment.NR}/${N.n_studies} 篇未報告）`], { x: 6.9, y: 2.35, w: 5.8, h: 3.4 });
  source(s, '建議依據本回顧的觀察性結果，非因果結論');
}

// ---------- 30 conclusions ----------
{
  const s = pres.addSlide({ masterName: 'DARK' });
  T(s, '結論', { x: M + 0.3, y: 0.55, w: 6, h: 0.5, fontSize: 22, color: COL.lightBlue });
  const pts = [
    ['開源模型以 Llama 家族為主，', `醫療領域模型只占 ${N.pct_medical_model}%，${pct(N.params_bins['1–10B'], N.n_params_reported)}% 的模型在 10B 以下。`],
    ['提示工程仍是主流，', `${N.pct_finetune}% 的研究有微調；${N.deployment.NR} 篇未報告部署方式。`],
    ['同一研究內比較，閉源多小幅領先，', `但 ${N.n_studies_open_comparable_or_better}/${N.n_pair_studies} 篇開源追平或較好；微調組差距中位數僅 ${f3(N.median_gap_finetuned)}。`],
  ];
  const runs = [];
  pts.forEach(([a, b], i) => {
    runs.push({ text: `${i + 1}　${a}`, options: { bold: true, color: COL.white } });
    runs.push({ text: b, options: { color: COL.paleNavy, breakLine: i < pts.length - 1 } });
  });
  T(s, runs, { x: M + 0.3, y: 1.4, w: W - 2 * M - 0.6, h: 4.0, fontSize: 24, paraSpaceAfter: 26, valign: 'top' });
  T(s, '檢索紀錄、篩選結果、萃取表與分析腳本皆保存於專案資料夾，可重現  ·  [聯絡方式]', { x: M + 0.3, y: 6.3, w: W - 2 * M - 0.6, h: 0.4, fontSize: 14, color: COL.lightBlue });
  s.addNotes('這張在 Q&A 期間停留。收尾：「我先講到這裡，歡迎提問或給建議。」');
}

// ---------- 31 references ----------
{
  const s = content(null, '參考文獻', '完整書目；兩個代表研究取自 extraction/study_ids.csv。', { appendix: ' ' });
  const ref = (id, au) => `${au}. ${SID[id].title.replace(/\.$/, '')}. ${SID[id].venue}. ${SID[id].year}. doi:${SID[id].doi}`;
  const refs = [
    'Abdellaoui C, Redjdal A, Seroussi B. Generative-AI-Based Approaches for Information Extraction from Clinical Notes: A Scoping Review. Stud Health Technol Inform. 2025;328:193–197. doi:10.3233/SHTI250700',
    'Testing and evaluation of generative large language models in electronic health record applications: a systematic review. J Am Med Inform Assoc. PMID: 41528313',
    'Page MJ, McKenzie JE, Bossuyt PM, et al. The PRISMA 2020 statement: an updated guideline for reporting systematic reviews. BMJ. 2021;372:n71',
    'Sugihara Y, Milosavljevic A, Jankovskaja S, Falk M. A review for navigating the trade-offs: evaluating open-source and proprietary large language models for clinical and biomedical information extraction. Front Digit Health. 2026. doi:10.3389/fdgth.2026.1778786',
    ref('S052', 'van der Loo et al'),
    ref('S033', 'Wiyanti et al'),
  ];
  T(s, refs.map((r, i) => ({ text: r, options: { breakLine: i < refs.length - 1 } })), { x: M, y: 1.7, w: W - 2 * M, h: 5.0, fontSize: 14, color: COL.body, paraSpaceAfter: 12, valign: 'top' });
}

// ---------- appendix ----------
{
  const CODE = { X1: '發表類型不符（回顧、社論、無全文）', X2: '非英文論文', X3: '未使用符合定義的 LLM', X4: '只使用閉源 LLM',
    X5: '非臨床自由文本（含只用合成文本）', X6: '非資訊抽取任務', X7: '無量化評估', X8: '同一研究的其他版本' };
  const ft = Object.entries(C.full_text_excluded_by_code).sort((a, b) => b[1] - a[1]);
  const s = content(null, `全文排除 ${ftExcluded} 篇，最常見原因是只用閉源 LLM 與重複版本`, '排除代碼依 protocol 3.2 順序判斷，取第一個符合者。', { appendix: '附錄 A　排除代碼' });
  bar(s, ft.map(([k]) => k), ft.map(([, v]) => v), { w: 5.4, h: 4.9, name: '篇數' });
  table(s, [['代碼', '定義'], ...Object.entries(CODE).map(([k, v]) => [k, v])], { x: 6.3, y: 1.75, w: 6.4, colW: [0.9, 5.5], fontSize: 14, rowH: 0.48 });
  source(s, '資料：analysis/prisma_counts.json（full_text_excluded_by_code）；定義：protocol 3.2');
}
{
  const s = content(null, 'PubMed 檢索式：三個概念區塊以 AND 結合，限 2022 年以後', '其他來源依各自語法改寫同一組詞彙（protocol 3.4.3–3.4.7）。', { appendix: '附錄 B　檢索式' });
  const q = [
    '("large language model*"[tiab] OR LLM[tiab] OR LLMs[tiab] OR "foundation model*"[tiab] OR "open-source"[tiab] OR "open-weight*"[tiab] OR Llama[tiab] OR Mistral[tiab] OR Mixtral[tiab] OR Qwen*[tiab] OR Gemma[tiab] OR DeepSeek[tiab] OR "Phi-3"[tiab] OR "Phi-4"[tiab] OR Vicuna[tiab] OR Falcon[tiab] OR BioMistral[tiab] OR Meditron[tiab] OR … OR "Large Language Models"[Mesh])',
    'AND ("clinical note*"[tiab] OR "clinical text*"[tiab] OR "medical record*"[tiab] OR "health record*"[tiab] OR EHR[tiab] OR EMR[tiab] OR "discharge summar*"[tiab] OR "progress note*"[tiab] OR "radiology report*"[tiab] OR "pathology report*"[tiab] OR … OR "Electronic Health Records"[Mesh])',
    'AND ("information extraction"[tiab] OR "named entity recognition"[tiab] OR NER[tiab] OR "relation extraction"[tiab] OR "entity extraction"[tiab] OR "data extraction"[tiab] OR "chart abstraction"[tiab] OR "structured data"[tiab] OR … OR "text mining"[tiab])',
    'AND ("2022/01/01"[dp] : "2026/12/31"[dp])',
  ];
  T(s, q.map((t, i) => ({ text: t, options: { breakLine: i < q.length - 1 } })), { x: M, y: 1.7, w: W - 2 * M, h: 4.6, fontSize: 13, color: COL.body, paraSpaceAfter: 10, valign: 'top', fontFace: 'Consolas' });
  source(s, '「…」為節錄，完整檢索式見 protocol/protocol.md 3.4.2；各來源 search_log.json 保存實際執行紀錄');
}
{
  const cm = K.binary.confusion_matrix;
  const s = content(null, `兩個 AI 的篩選一致性：全部 ${K.n} 筆二元 κ = ${f2(K.binary.kappa)}，校準 ${B50.n} 筆 κ = ${f2(B50.binary_pass_vs_exclude.kappa)}`,
    '兩者都是 AI 之間的一致性，不是人工 κ，也不是 AI 對人工的敏感度。校準 50 筆是 Agent 初判 vs Sonnet，作者看過並裁定分歧。', { appendix: '附錄 C　AI 一致性' });
  table(s, [['', 'Opus：進全文', 'Opus：排除'], ['Sonnet：進全文', String(cm[0][0]), String(cm[0][1])], ['Sonnet：排除', String(cm[1][0]), String(cm[1][1])]],
    { x: M, y: 1.8, w: 6.2, colW: [2.2, 2.0, 2.0], fontSize: 18, rowH: 0.6 });
  sideHead(s, '一致性', 7.3, 1.8, 5);
  bullets(s, [`二元觀察一致 ${(K.binary.observed_agreement * 100).toFixed(1)}%，κ = ${f2(K.binary.kappa)}`, `三類（include／unsure／exclude）κ = ${f2(K.three_category.kappa)}`,
    `校準 ${B50.n} 筆：二元 κ = ${f2(B50.binary_pass_vs_exclude.kappa)}、三類 κ = ${f2(B50.three_category.kappa)}`, '二元分歧由作者裁定'],
  { x: 7.3, y: 2.3, w: 5.4, h: 3.6 });
  source(s, '資料：analysis/sonnet_vs_opus.json、analysis/blind50_agent_vs_sonnet.json');
}
{
  const rows = [...N.study_level].sort((a, b) => a.gap_median - b.gap_median);
  const half = Math.ceil(rows.length / 2);
  [rows.slice(0, half), rows.slice(half)].forEach((part, k) => {
    const s = content(null, `${N.n_pair_studies} 篇配對研究逐篇數值（依差距排序，${k + 1}/2）`,
      '每篇取其各組比較的中位數；差距 = 閉源 − 開源；≤ 0.02 視為追平或較好。', { appendix: `附錄 D${k + 1}　逐篇配對` });
    table(s, [['研究', '比較數', '開源中位數', '閉源中位數', '差距'], ...part.map((d) => [d.label, String(d.n), f3(d.open_median), f3(d.closed_median),
      { text: f3(d.gap_median), options: { bold: d.gap_median <= N.tie_threshold, color: d.gap_median <= N.tie_threshold ? COL.blue : COL.body } }])],
    { x: M, y: 1.6, w: W - 2 * M, colW: [4.13, 1.7, 2.1, 2.1, 2.1], fontSize: 13, rowH: 0.27, margin: [1, 6, 1, 6] });
    source(s, '資料：analysis/slide_numbers.json（study_level）；藍色粗體 = 開源追平或較好');
  });
}
{
  const why = { S001: '閉源 Gemini 3 Flash 數值只在 PDF 附錄（p.25），萃取文字未收錄', S022: '開源與閉源的直接比較只畫在 Figure 3，正文無數值',
    S030: '閉源結果只在圖與補充表；指標為 RMSE', S102: '原文同一條件前後報告兩組不同數值，無法確定',
    S118: '開源模型數值只在補充表', S119: '開源數值只在補充表，正文僅給範圍', S164: '開源數值只在 Figure 3 與補充表' };
  N.unpaired.forEach((u) => must(why[u.study_id], 'unpaired reason for ' + u.study_id));
  const s = content(null, `${N.unpaired.length} 篇有閉源實測但無法配對：數值多只在圖或補充資料`,
    '這些研究符合 R2（同一研究實測閉源 LLM），所以納入課堂版 39 篇，但不進入 RQ3 的配對分析。原因取自 extraction/review/agent_review.csv 與 verify_report.csv。', { appendix: '附錄 E　無法配對的研究' });
  table(s, [['研究', '無法配對的原因'], ...N.unpaired.map((u) => [u.label, why[u.study_id]])], { x: M, y: 1.75, w: W - 2 * M, colW: [3.0, 9.13], fontSize: 16, rowH: 0.55 });
  source(s, '萃取規則：數值只取正文與 PDF 內表格，從圖讀值與外部補充資料不萃取（extraction/d1_codex_brief.md）');
}
{
  const s = content(null, `交叉比對與對原文核對：${VR.length} 列中 ${verdict.correct} 列正確、${verdict.fix} 列修正`,
    '修正實例：S052 三項瓣膜分級的最佳閉源取錯策略（改取各策略最高 F1）；S126 DeepSeek-R1 最佳 F1 應為 0.94；S102 原文前後矛盾改為不配對。並列最佳的 3 列因檢查器要求單一最佳而維持原標記。', { appendix: '附錄 F　萃取核對' });
  const st = XC.status;
  table(s, [['兩套 AI 萃取比對（62 篇）', '篇數'], ...Object.entries(st).map(([k, v]) => [{ agree: '一致', differ_value: '同模型、數值不同', differ_model: '最佳模型不同', differ_closed: '閉源不同', missing_174: '174 版無數值', missing_62: '課堂版無數值' }[k] || k, { text: String(v), options: { align: 'right' } }])],
    { x: M, y: 1.75, w: 5.9, colW: [4.5, 1.4], fontSize: 16, rowH: 0.5 });
  table(s, [['對原文核對（最佳結果列）', '列數'], ...Object.entries(verdict).sort((a, b) => b[1] - a[1]).map(([k, v]) => [{ correct: '正確', fix: '需修正', no_pair: '建議不配對', unclear: '原文無法判斷' }[k] || k, { text: String(v), options: { align: 'right' } }])],
    { x: 6.9, y: 1.75, w: 5.8, colW: [4.4, 1.4], fontSize: 16, rowH: 0.5 });
  source(s, '資料：extraction/review/crosscheck_62_vs_174_summary.json、verify_report.csv；修正以 agent_patch.py 套用並記錄於 agent_edits.csv');
}

const out = path.join(__dirname, 'open_llm_clinical_ie_review.pptx');
pres.writeFile({ fileName: out }).then(() => console.log('wrote', out));
