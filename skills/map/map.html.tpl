<!-- vibe-map-page -->
<title>__TITLE__</title>
<style>
:root{
  --ground:#F3F5F6; --surface:#FFFFFF; --sunk:#E9EDEF; --ink:#15202B; --muted:#5A6772; --faint:#8995A0; --rule:#D3DADF;
  --accent:#0E6F8C; --accent-soft:#DCEEF4; --on-accent:#FFFFFF;
  --crit:#B83227; --crit-soft:#F8E1DE; --warn:#9A6212; --warn-soft:#F7EBD3; --ok:#2F7D55; --ext:#56657A; --ext-soft:#E4E9EF;
  --sans:"PingFang SC","Hiragino Sans GB","Microsoft YaHei","Noto Sans CJK SC",system-ui,-apple-system,"Segoe UI",sans-serif;
  --mono:ui-monospace,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;   /* 不从外网拉字体：私有页面不向第三方发请求，大陆访问 Google Fonts 会卡住渲染 */
  --r:10px;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    color-scheme:dark;
    --ground:#0E1418; --surface:#162026; --sunk:#1D2930; --ink:#E3E9ED; --muted:#9AA8B2; --faint:#6F7E89; --rule:#2B3942;
    --accent:#4DB4D2; --accent-soft:#16333E; --on-accent:#0B1418;
    --crit:#F07B6F; --crit-soft:#3A1E1C; --warn:#E3AE55; --warn-soft:#352914; --ok:#62C08F; --ext:#A4B2C4; --ext-soft:#243039;
  }
}
:root[data-theme="dark"]{
  color-scheme:dark;
  --ground:#0E1418; --surface:#162026; --sunk:#1D2930; --ink:#E3E9ED; --muted:#9AA8B2; --faint:#6F7E89; --rule:#2B3942;
  --accent:#4DB4D2; --accent-soft:#16333E; --on-accent:#0B1418;
  --crit:#F07B6F; --crit-soft:#3A1E1C; --warn:#E3AE55; --warn-soft:#352914; --ok:#62C08F; --ext:#A4B2C4; --ext-soft:#243039;
}
*{box-sizing:border-box}
body{background:var(--ground);color:var(--ink);font:14px/1.55 var(--sans);margin:0}
.wrap{max-width:1240px;margin:0 auto;padding-inline:20px;padding-block:22px 48px}
.mono,.id,.num{font-family:var(--mono);font-variant-numeric:tabular-nums}
h1,h2,h3{text-wrap:balance;margin:0}
button{font:inherit;color:inherit}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}

/* 顶部：阶段 */
.eyebrow{font-size:12px;color:var(--muted);letter-spacing:.02em;display:flex;flex-wrap:wrap;gap:4px 14px}
.eyebrow .mono{font-size:11.5px}
.eyebrow a{color:var(--accent);text-decoration:none}
h1{font-size:26px;font-weight:650;letter-spacing:.01em;margin:6px 0 16px}
h1 small{font-size:14px;font-weight:500;color:var(--muted);margin-left:10px;letter-spacing:.04em}
.stage{display:grid;grid-template-columns:minmax(0,2.2fr) minmax(0,2fr) minmax(0,1fr) minmax(0,1fr);gap:1px;background:var(--rule);border:1px solid var(--rule);border-radius:var(--r);overflow:hidden}
.stat{background:var(--surface);padding:12px 14px;display:flex;flex-direction:column;gap:4px;min-width:0}
.stat .k{font-size:11.5px;color:var(--muted);letter-spacing:.08em}
.stat .v{font-weight:600;overflow-wrap:anywhere}
.stat .v .id{font-weight:600;margin-right:6px;color:var(--accent)}
.stat .sub{font-size:12px;color:var(--muted);display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.big{font-family:var(--mono);font-size:22px;font-weight:600;line-height:1.2}
.big.alert{color:var(--crit)}
.meter{display:inline-block;width:88px;height:6px;border-radius:3px;background:var(--sunk);overflow:hidden;vertical-align:middle}
.meter i{display:block;height:100%;background:var(--accent)}
.tag{display:inline-flex;align-items:center;gap:4px;font-size:11.5px;padding:1px 7px;border-radius:999px;border:1px solid currentColor;white-space:nowrap}
.tag.gate{color:var(--crit)}

/* 页签 */
.tabs{display:flex;gap:4px;margin:22px 0 14px;border-bottom:1px solid var(--rule)}
.tabs button{background:none;border:0;padding:8px 12px 9px;cursor:pointer;color:var(--muted);border-bottom:2px solid transparent;margin-bottom:-1px}
.tabs button[aria-selected="true"]{color:var(--ink);border-bottom-color:var(--accent);font-weight:600}
.tabs .n{font-family:var(--mono);font-size:12px;color:var(--faint);margin-left:4px}
.legend{display:flex;flex-wrap:wrap;gap:6px 16px;font-size:12px;color:var(--muted);margin-bottom:14px}
.legend b{font-weight:600;color:var(--ink)}

/* 线路图 */
.lane{margin-bottom:18px}
.lane-name{font-size:12px;font-weight:600;color:var(--muted);letter-spacing:.12em;margin:0 0 8px 2px}
.track-scroll{overflow-x:auto;padding-bottom:4px}
.track{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(var(--cols,5),minmax(186px,1fr));gap:14px;position:relative}
.station{position:relative;display:flex;flex-direction:column;align-items:stretch;padding-top:18px}
.station:not(:last-child)::after{content:"";position:absolute;top:25px;left:11px;width:calc(100% + 14px);height:4px;background:var(--accent)}
.station:not(:last-child)::before{content:"";position:absolute;top:21px;right:-9px;border:6px solid transparent;border-left:7px solid var(--accent);z-index:1}
.flag{position:absolute;top:0;left:0;font-size:11px;font-weight:600;color:var(--accent);letter-spacing:.06em;white-space:nowrap}
.dot{width:18px;height:18px;border-radius:50%;background:var(--surface);border:4px solid var(--accent);margin:0 0 10px 2px;position:relative;z-index:1}
.station.is-ext .dot{border-color:var(--ext)}
.station.is-now .dot{background:var(--accent)}
.station.is-focus .dot{box-shadow:0 0 0 5px var(--accent-soft)}
.card{display:flex;flex-direction:column;gap:7px;text-align:left;background:var(--surface);border:1px solid var(--rule);border-radius:var(--r);padding:11px 12px 10px;cursor:pointer;width:100%;height:100%}
.card:hover{border-color:var(--faint)}
.card[aria-pressed="true"]{border-color:var(--accent);box-shadow:0 0 0 1px var(--accent)}
.station.is-ext .card{border-style:dashed;background:transparent}
.card-head{display:flex;align-items:center;justify-content:space-between;gap:8px}
.card-head .name{font-weight:650;font-size:15px}
.cnt{font-family:var(--mono);font-size:12px;font-weight:600;min-width:22px;text-align:center;padding:0 6px;border-radius:999px;line-height:20px}
.cnt.crit{background:var(--crit);color:var(--surface)} .cnt.warn{background:var(--warn-soft);color:var(--warn)} .cnt.ext{background:var(--ext-soft);color:var(--ext)}
.cnt.none{color:var(--ok);font-family:var(--sans);font-weight:500;padding:0}
.layer{display:grid;grid-template-columns:30px 1fr;gap:2px 6px;align-items:baseline;font-size:12.5px}
.layer .lk{color:var(--muted);font-size:12px}
.layer .lv{display:flex;flex-wrap:wrap;gap:3px 6px;align-items:baseline;min-width:0}
.layer .files{color:var(--faint);font-family:var(--mono);font-size:11.5px}
.layer .here{color:var(--accent);font-size:11.5px;font-weight:600}
.chip{font-family:var(--mono);font-size:11px;font-weight:500;padding:0 5px;border-radius:4px;line-height:18px;white-space:nowrap}
.chip.crit{background:var(--crit-soft);color:var(--crit)} .chip.warn{background:var(--warn-soft);color:var(--warn)} .chip.ext{background:var(--ext-soft);color:var(--ext)}
.foot{margin-top:auto;display:flex;flex-direction:column;gap:5px;padding-top:6px;border-top:1px solid var(--sunk)}
.effort{display:flex;align-items:center;gap:8px;font-size:11.5px;color:var(--muted)}
.effort .bar{flex:1;height:5px;background:var(--sunk);border-radius:3px;overflow:hidden}
.effort .bar i{display:block;height:100%;background:var(--muted);opacity:.7}
.effort .pct{font-family:var(--mono);min-width:44px;text-align:right}
.nowline{font-size:11.5px;color:var(--accent);font-weight:600}
.nowline .dirty{color:var(--warn);font-weight:500;margin-left:6px}
.cross .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(186px,1fr));gap:12px}
.cross .card{background:var(--surface)}
.note{font-size:12.5px;color:var(--muted);background:var(--sunk);border-radius:8px;padding:9px 12px;margin:0 0 16px}

/* 进展 */
.focus{background:var(--surface);border:1px solid var(--rule);border-radius:var(--r);padding:18px 20px;display:flex;flex-direction:column;gap:10px;max-width:980px}
.f-kicker{font-size:12px;color:var(--muted);letter-spacing:.08em}
.f-title{font-size:20px;font-weight:650;line-height:1.35}
.f-title .id,.ns-title .id{color:var(--accent);font-family:var(--mono);font-weight:600;margin-right:8px}
.f-meta{font-size:12.5px;color:var(--muted)}
.steps{list-style:none;margin:4px 0 0;padding:0;display:flex;flex-wrap:wrap;gap:6px}
.steps li{font-family:var(--mono);font-size:12px;padding:3px 8px;border-radius:6px;background:var(--sunk);color:var(--faint);white-space:nowrap}
.steps li.done{color:var(--ok);background:transparent;border:1px solid var(--rule)}
.steps li.cur{background:var(--accent);color:var(--on-accent);font-weight:600}
.steps li.ext{border:1px dashed var(--ext);background:transparent;color:var(--ext)}
.now-step{border-left:4px solid var(--accent);padding:8px 12px;background:var(--accent-soft);border-radius:0 8px 8px 0;margin-top:6px}
.ns-label{font-size:12px;color:var(--muted);letter-spacing:.06em}
.ns-title{font-size:16px;font-weight:600;margin-top:2px;display:flex;flex-wrap:wrap;align-items:center;gap:6px 8px}
.focus h3{font-size:13px;color:var(--muted);font-weight:600;letter-spacing:.06em;margin-top:8px}
.probs,.progress{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:6px}
.prob{display:grid;grid-template-columns:4.2em 1fr;gap:8px;align-items:start;font-size:13px}
.prob .chip{justify-self:start}
.rest{font-size:12.5px;color:var(--muted)}
.rest summary{cursor:pointer;color:var(--accent);margin:2px 0 8px}
.prob .pt{display:flex;flex-wrap:wrap;gap:4px 8px;min-width:0}
.prob .px{flex-basis:100%;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow-wrap:anywhere}
.prob .id{font-family:var(--mono);font-size:12px;color:var(--muted)}
.here-tag{font-size:11px;color:var(--accent);border:1px solid currentColor;border-radius:999px;padding:0 6px}
.prob.none{color:var(--ok)}
.progress li{display:grid;grid-template-columns:auto auto 1fr;gap:8px;font-size:12.5px;align-items:baseline}
.progress .id{font-family:var(--mono);color:var(--muted)}
.progress .when{color:var(--faint);white-space:nowrap}
.progress .subj{overflow-wrap:anywhere}
.status{font-size:12.5px;color:var(--muted);margin:2px 0 0}
.status span{color:var(--faint)}

/* 详情 */
iframe.archify{display:block;width:100%;height:min(82vh,960px);border:1px solid var(--rule);border-radius:var(--r);background:var(--surface)}
.legend a{color:var(--accent);margin-left:auto}
#detail{margin-top:8px;background:var(--surface);border:1px solid var(--rule);border-radius:var(--r);padding:16px 18px}
#detail h3{font-size:17px;margin-bottom:4px}
#detail .meta{font-size:12.5px;color:var(--muted);display:flex;flex-wrap:wrap;gap:4px 16px;margin-bottom:12px}
.issue{display:grid;grid-template-columns:auto 1fr;gap:2px 10px;padding:10px 0;border-top:1px solid var(--sunk)}
.issue:first-of-type{border-top:0}
.issue .id{font-size:12px;font-weight:600;padding-top:2px}
.issue .t{font-weight:600}
.issue .why{font-size:12px;color:var(--muted);grid-column:2}
.issue details{grid-column:2;font-size:12.5px;color:var(--muted)}
.issue summary{cursor:pointer;color:var(--accent);font-size:12px;width:max-content}
.issue pre{white-space:pre-wrap;overflow-wrap:anywhere;font:12px/1.6 var(--sans);margin:6px 0 0;color:var(--ink);background:var(--sunk);padding:8px 10px;border-radius:6px}
.group{margin-bottom:18px}
.group h3{font-size:14px;display:flex;align-items:center;gap:8px;margin-bottom:2px}
.group h3 .lane-tag{font-size:11px;color:var(--faint);font-weight:500;letter-spacing:.06em}
.summary{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:12.5px;color:var(--muted);margin-bottom:14px}

/* 投入分布 */
.heat-scroll{overflow-x:auto;border:1px solid var(--rule);border-radius:var(--r);background:var(--surface)}
table.heat{border-collapse:collapse;font-size:12px;min-width:100%}
.heat th,.heat td{padding:6px 8px;text-align:right;white-space:nowrap}
.heat thead th{font-family:var(--mono);font-weight:500;color:var(--muted);border-bottom:1px solid var(--rule);position:sticky;top:0;background:var(--surface)}
.heat thead th.cur{color:var(--accent);font-weight:600}
.heat tbody th{text-align:left;font-weight:600;position:sticky;left:0;background:var(--surface);border-right:1px solid var(--rule)}
.heat tbody th small{display:block;font-weight:400;color:var(--faint);font-size:10.5px;letter-spacing:.06em}
.heat td.v{font-family:var(--mono);color:var(--ink);min-width:44px}
.heat td.v.hot{color:var(--on-accent)}
.heat td.tot,.heat tfoot td{font-family:var(--mono);color:var(--muted);border-left:1px solid var(--rule)}
.heat tfoot td,.heat tfoot th{border-top:1px solid var(--rule);color:var(--muted);font-weight:500;background:var(--surface)}
.heat tfoot th{text-align:left;position:sticky;left:0}
.lead{font-size:13.5px;margin:0 0 12px;max-width:72ch}
.lead b{font-weight:650}
.fine{font-size:12px;color:var(--muted);margin-top:10px;max-width:80ch}

@media (max-width:980px){ .stage{grid-template-columns:1fr 1fr} }
@media (max-width:640px){
  .wrap{padding-inline:16px}
  .stage{grid-template-columns:1fr}
  .track{grid-template-columns:1fr;gap:10px;padding-left:26px}
  .station:not(:last-child)::after{left:-19px;top:20px;width:4px;height:calc(100% + 10px)}
  .station:not(:last-child)::before{display:none}
  .station{padding-top:0}
  .station .dot{position:absolute;left:-26px;top:12px;margin:0}
  .flag{position:static;margin-bottom:4px}
}
@media (prefers-reduced-motion:no-preference){ .card{transition:border-color .15s} }
</style>

<div class="wrap">
  <header>
    <div class="eyebrow" id="eyebrow"></div>
    <h1 id="h1"></h1>
  </header>
  <nav class="tabs" role="tablist" aria-label="视图">
    <button role="tab" id="tab-now" aria-selected="true" aria-controls="view-now">进展</button>
    <button role="tab" id="tab-map" aria-selected="false" aria-controls="view-map">模块图</button>
    <button role="tab" id="tab-cards" aria-selected="false" aria-controls="view-cards" hidden>模块</button>
    <button role="tab" id="tab-issues" aria-selected="false" aria-controls="view-issues">问题<span class="n" id="n-issues"></span></button>
    <button role="tab" id="tab-effort" aria-selected="false" aria-controls="view-effort">投入分布</button>
  </nav>
  <section id="view-now" role="tabpanel" aria-labelledby="tab-now"></section>
  <section id="view-map" role="tabpanel" aria-labelledby="tab-map" hidden></section>
  <section id="view-cards" role="tabpanel" aria-labelledby="tab-cards" hidden></section>
  <section id="view-issues" role="tabpanel" aria-labelledby="tab-issues" hidden></section>
  <section id="view-effort" role="tabpanel" aria-labelledby="tab-effort" hidden></section>
</div>

<script>
const D = __DATA__;
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const fmt = n => Number(n).toLocaleString("en-US");
const sum = o => Object.values(o || {}).reduce((a, b) => a + b, 0);
const pct = n => (100 * n / D.total).toFixed(n / D.total < 0.1 ? 1 : 0) + "%";
const LAYERS = ["页面", "接口", "数据", "逻辑"];
const RANK = {"待拍板": 4, "安全": 3, "偏差": 2, "欠账": 2, "外部依赖": 1};
const TONE = k => RANK[k] >= 4 ? "crit" : RANK[k] >= 2 ? "warn" : "ext";
const MOD = Object.fromEntries(D.modules.map(m => [m.name, m]));
const inFlow = new Set(D.lanes.flatMap(l => l.mods));
const isFocus = m => m.name === D.focus;
const effMax = Math.max(1, ...D.modules.map(m => m.effort));
const cur = D.current ? D.current.id : null;
const maxLane = Math.max(1, ...D.lanes.map(l => l.mods.length));
let selected = null;

function header() {
  document.getElementById("eyebrow").innerHTML =
    `<a href="../index.html">← 全部项目</a><span>生成于 ${esc(D.generated)}</span><span class="mono">${esc(D.branch)} @ ${esc(D.head)}</span>`;
  document.getElementById("h1").innerHTML = `${esc(D.project)}<small>${D.mapped ? "" : "未配模块地图 · 按目录分组"}</small>`;
  document.getElementById("n-issues").textContent = D.issues.length;
}

const ago = t => { const s = Date.now() / 1000 - t; return s < 90 ? "刚刚" : s < 3600 ? Math.round(s / 60) + " 分钟前" : s < 86400 ? Math.round(s / 3600) + " 小时前" : Math.round(s / 86400) + " 天前"; };
const PTONE = k => k === "待拍板" || k === "CI" ? "crit" : k === "偏差" || k === "安全" || k === "欠账" ? "warn" : "ext";
function viewNow() {
  const N = D.now, m = N.milestone, st = N.step;
  const short = id => m && id.startsWith(m.id + "-") ? id.slice(m.id.length + 1) : id;
  // 先看会卡住下一步的：这一步的问题、所有待拍板、CI；其余（别的任务上的偏差、外部等待）折叠
  const main = N.state === "active" ? N.problems.filter(p => p.here || p.kind === "待拍板" || p.kind === "CI") : N.problems;
  const rest = N.state === "active" ? N.problems.filter(p => !main.includes(p)) : [];
  const probs = main.length ? main.map(p => `
      <li class="prob"><span class="chip ${PTONE(p.kind)}">${esc(p.kind)}</span>
        <span class="pt">${p.task ? `<span class="id">${esc(p.task)}</span>` : ""}${p.here ? `<span class="here-tag">这一步</span>` : ""}<span class="px" title="${esc(p.text)}">${esc(p.text)}</span></span></li>`).join("")
    : `<li class="prob none">${N.state === "active" ? "这一步没有卡住的事" : "没有挂着的问题"}</li>`;
  const restHtml = rest.length ? `<details class="rest"><summary>本里程碑其他问题 ${rest.length} 条（别的任务上的偏差到收口裁决；外部等待）</summary><ul class="probs">${rest.map(p => `
      <li class="prob"><span class="chip ${PTONE(p.kind)}">${esc(p.kind)}</span><span class="pt">${p.task ? `<span class="id">${esc(p.task)}</span>` : ""}<span class="px" title="${esc(p.text)}">${esc(p.text)}</span></span></li>`).join("")}</ul></details>` : "";
  const prog = N.progress.map(c => `<li><span class="id">${esc(c.sha)}</span><span class="when">${ago(c.t)}</span><span class="subj">${esc(c.subject)}</span></li>`).join("");
  const head = N.state === "active" ? `
      <div class="f-kicker">正在做</div>
      <h2 class="f-title"><span class="id">${esc(m.id)}</span>${esc(m.name)}</h2>
      <div class="f-meta">完成 <b class="num">${m.done}/${m.total}</b></div>
      <ol class="steps" aria-label="步骤">${N.steps.map(s => `<li class="${s.done ? "done" : ""} ${s.current ? "cur" : ""} ${s.external ? "ext" : ""}" title="${esc(s.id + " " + s.title)}">${s.done ? "✓ " : s.current ? "▶ " : ""}${esc(short(s.id))}</li>`).join("")}</ol>
      <div class="now-step">
        <div class="ns-label">${st ? `当前这一步 · 第 ${st.index}/${st.total} 步` : "当前这一步"}</div>
        <div class="ns-title">${st ? `<span class="id">${esc(st.id)}</span>${esc(st.title)}${st.gate ? `<span class="tag gate">需要你到场</span>` : ""}` : "任务都勾完了，等收口（走 close）"}</div>
      </div>` : `
      <div class="f-kicker">当前没有正在开发的功能</div>
      <h2 class="f-title">${m ? `上一个：<span class="id">${esc(m.id)}</span>${esc(m.name)}` : "还没有里程碑"}</h2>
      ${m && m.note ? `<div class="f-meta">${esc(m.note)}</div>` : ""}
      <div class="now-step"><div class="ns-label">下一步</div><div class="ns-title">立项下一个里程碑<span class="tag gate">要你拍板方向</span></div></div>
      ${N.status ? `<p class="status"><span>PLAN 里的当前状态：</span>${esc(N.status)}</p>` : ""}`;
  document.getElementById("view-now").innerHTML = `
    <section class="focus">${head}
      <h3>${N.state === "active" ? "这一步的问题" : "还挂着"}</h3><ul class="probs">${probs}</ul>${restHtml}
      <h3>最近进展</h3><ul class="progress">${prog || "<li>还没有提交</li>"}</ul>
    </section>`;
}

function issuesOf(m) {
  const byLayer = {}, modLevel = [];
  for (const x of m.issues) {
    const it = {...D.issues[x.idx], idx: x.idx};
    if (x.layers.length) x.layers.forEach(l => (byLayer[l] = byLayer[l] || []).push(it)); else modLevel.push(it);
  }
  return {byLayer, modLevel, all: m.issues.map(x => D.issues[x.idx])};
}
const chip = it => `<span class="chip ${TONE(it.kind)}" title="${esc(it.kind + " · " + it.title)}">${esc(it.id)}</span>`;

function card(m, opts = {}) {
  const {byLayer, modLevel, all} = issuesOf(m);
  const worst = all.reduce((a, it) => Math.max(a, RANK[it.kind] || 0), 0);
  const tone = worst >= 4 ? "crit" : worst >= 2 ? "warn" : worst ? "ext" : "none";
  const ext = (m.files["外部"] || 0) > 0 && !LAYERS.some(l => m.files[l]);
  const rows = LAYERS.filter(l => m.files[l] || byLayer[l]).map(l => `
      <div class="layer"><span class="lk">${l}</span><span class="lv">
        ${m.files[l] ? `<span class="files">${m.files[l]} 个文件</span>` : ""}
        ${(m.now[l] || 0) ? `<span class="here" title="${esc(cur)} 改动 ${fmt(m.now[l])} 行">▶ ${fmt(m.now[l])}</span>` : ""}
        ${(byLayer[l] || []).map(chip).join("")}</span></div>`).join("");
  const modRow = modLevel.length ? `<div class="layer"><span class="lk">${ext ? "对接" : "整体"}</span><span class="lv">${modLevel.map(chip).join("")}</span></div>` : "";
  const now = sum(m.now), dirty = sum(m.dirty);
  const cls = ["station", ext ? "is-ext" : "", now ? "is-now" : "", isFocus(m) ? "is-focus" : ""].join(" ");
  const inner = `
    <button class="card" data-mod="${esc(m.name)}" aria-pressed="${selected === m.name}">
      <span class="card-head"><span class="name">${esc(m.name)}</span>
        <span class="cnt ${tone}" title="挂在这里的问题">${all.length || "无问题"}</span></span>
      ${ext ? `<div class="layer"><span class="lk">性质</span><span class="lv"><span class="files">跨仓库 · ${m.files["外部"]} 份对接文档</span></span></div>` : ""}
      ${rows}${modRow}
      <span class="foot">
        ${now || dirty ? `<span class="nowline">${now ? `▶ ${esc(cur)} 动了 ${fmt(now)} 行` : ""}${dirty ? `<span class="dirty">● 未提交 ${dirty} 个文件</span>` : ""}</span>` : ""}
        <span class="effort" title="全部历史改动行数的 ${pct(m.effort)}"><span>投入</span><span class="bar"><i style="width:${100 * m.effort / effMax}%"></i></span><span class="pct">${pct(m.effort)}</span></span>
      </span>
    </button>`;
  return opts.station ? `<li class="${cls}">${isFocus(m) ? `<span class="flag">你在这里</span>` : ""}<span class="dot" aria-hidden="true"></span>${inner}</li>` : inner;
}

const CARDS = D.archify ? "view-cards" : "view-map";
function viewArchify() {
  document.getElementById("view-map").innerHTML = `
    <div class="legend"><span>交互架构图（archify）：点上方章节看「你在这里 / 问题在哪 / 投入最多」，点节点看页面 · 接口 · 数据的代表文件</span>
      <a href="${esc(D.archify)}#view=here" target="_blank" rel="noopener">新窗口打开</a></div>
    <iframe class="archify" src="${esc(D.archify)}#view=here" title="${esc(D.project)} 交互架构图"></iframe>`;
}
function viewMap() {
  const crossMods = D.modules.filter(m => !inFlow.has(m.name));
  const unplaced = D.unplaced.map(i => D.issues[i]);
  document.getElementById(CARDS).innerHTML = `
    <div class="legend">
      <span><b>▶</b> ${esc(cur || "当前里程碑")} 动过（行数）</span><span><b>●</b> 有未提交改动</span>
      <span><span class="chip crit">待拍板</span></span><span><span class="chip warn">安全 / 偏差 / 欠账</span></span><span><span class="chip ext">外部依赖</span></span>
      <span>投入 = 全部历史改动行数占比</span></div>
    ${D.lanes.length ? "" : `<p class="note">这个项目还没有模块地图，下面按目录自动分组。在 ENGINEERING.md 加一节「模块地图」（一行业务线 + 一张路径表），就能画出业务流程和各模块的页面 / 接口 / 数据。</p>`}
    ${D.lanes.map(l => `
      <section class="lane"><h2 class="lane-name">${esc(l.name)}</h2>
        <div class="track-scroll"><ol class="track" style="--cols:${maxLane}">${l.mods.map(n => MOD[n] ? card(MOD[n], {station: true}) : "").join("")}</ol></div>
      </section>`).join("")}
    ${crossMods.length ? `<section class="lane cross"><h2 class="lane-name">${D.lanes.length ? "横切 · 不在业务线上" : "模块"}</h2>
      <div class="grid">${crossMods.map(m => card(m)).join("")}</div></section>` : ""}
    ${unplaced.length ? `<p class="note">还有 ${unplaced.length} 个问题定位不到模块：${unplaced.map(chip).join(" ")}——在「问题」页查看，给地图补路径或关键词。</p>` : ""}
    <div id="detail" ${selected ? "" : "hidden"}></div>`;
  document.querySelectorAll("#" + CARDS + " .card").forEach(b => b.addEventListener("click", () => {
    selected = selected === b.dataset.mod ? null : b.dataset.mod; viewMap();
    if (selected) document.getElementById("detail").scrollIntoView({block: "nearest", behavior: "smooth"});
  }));
  if (selected) detail(MOD[selected]);
}

function issueRow(it, showMod) {
  const where = it.pins.map(p => p.mod + (p.layers.length ? "·" + p.layers.join("/") : "")).join("、") || "未定位";
  return `<div class="issue"><span class="id chip ${TONE(it.kind)}">${esc(it.id)}</span>
    <span class="t">${esc(it.title)}</span>
    <span class="why">${esc(it.kind)}${it.ms ? " · 记在 " + esc(it.ms) : ""}${showMod ? " · 在 " + esc(where) : ""}${it.how ? " · 定位依据：" + esc(it.how) : ""}</span>
    <details><summary>原文</summary><pre>${esc(it.text)}</pre></details></div>`;
}

function detail(m) {
  const {all} = issuesOf(m);
  const tests = m.files["测试"] || 0;
  const nowParts = Object.entries(m.now).filter(([, v]) => v).sort((a, b) => b[1] - a[1]).map(([k, v]) => `${k} ${fmt(v)}`).join(" · ");
  document.getElementById("detail").innerHTML = `
    <h3>${esc(m.name)}</h3>
    <div class="meta"><span>投入 ${pct(m.effort)}（${fmt(m.effort)} 行）</span>
      <span>文件：${[...LAYERS, "测试", "外部"].filter(l => m.files[l]).map(l => `${l} ${m.files[l]}`).join(" · ") || "—"}</span>
      ${nowParts ? `<span>${esc(cur)} 动到：${nowParts} 行</span>` : ""}</div>
    ${all.length ? all.map(it => issueRow(it, false)).join("") : `<p class="fine">这里没有挂着的问题。</p>`}`;
}

function viewIssues() {
  const kinds = {};
  D.issues.forEach(it => kinds[it.kind] = (kinds[it.kind] || 0) + 1);
  const order = [...D.lanes.flatMap(l => l.mods.map(n => [n, l.name])), ...D.modules.filter(m => !inFlow.has(m.name)).map(m => [m.name, "横切"])];
  const groups = order.map(([n, lane]) => MOD[n] && MOD[n].issues.length ? `
      <div class="group"><h3>${esc(n)}<span class="lane-tag">${esc(lane)}</span></h3>
        ${issuesOf(MOD[n]).all.map(it => issueRow(it, false)).join("")}</div>` : "").join("");
  const un = D.unplaced.map(i => D.issues[i]);
  document.getElementById("view-issues").innerHTML = `
    <div class="summary">${Object.entries(kinds).sort((a, b) => (RANK[b[0]] || 0) - (RANK[a[0]] || 0)).map(([k, v]) => `<span><span class="chip ${TONE(k)}">${esc(k)}</span> ${v}</span>`).join("")}
      <span>来源：PLAN.md 里未勾的非任务条目（SEC- / EXT- …）与进行中里程碑任务下的「待拍板」「偏差」</span></div>
    ${groups || `<p class="fine">PLAN.md 里没有挂着的问题。</p>`}
    ${un.length ? `<div class="group"><h3>未定位<span class="lane-tag">给地图补路径或关键词</span></h3>${un.map(it => issueRow(it, false)).join("")}</div>` : ""}`;
}

function viewEffort() {
  const rows = [...D.lanes.flatMap(l => l.mods.map(n => [n, l.name])), ...D.modules.filter(m => !inFlow.has(m.name)).map(m => [m.name, "横切"])]
    .filter(([n]) => MOD[n] && MOD[n].effort);
  const cols = D.ms_cols;
  const cells = rows.flatMap(([n]) => cols.map(c => MOD[n].heat[c] || 0));
  const max = Math.max(1, ...cells), L = Math.log(max + 1);
  const shade = v => v ? Math.round(8 + 82 * Math.log(v + 1) / L) : 0;
  const colTot = cols.map(c => rows.reduce((a, [n]) => a + (MOD[n].heat[c] || 0), 0));
  const top = [...D.modules].sort((a, b) => b.effort - a.effort).slice(0, 3);
  const topMs = cols.map((c, i) => [c, colTot[i]]).filter(([c]) => c !== "其他").sort((a, b) => b[1] - a[1])[0];
  document.getElementById("view-effort").innerHTML = `
    <p class="lead">投入最多的三块：${top.map(m => `<b>${esc(m.name)}</b> ${pct(m.effort)}`).join("、")}。
      ${topMs ? `最重的里程碑是 <b class="mono">${esc(topMs[0])}</b>${D.ms_names[topMs[0]] ? "（" + esc(D.ms_names[topMs[0]]) + "）" : ""}，${fmt(topMs[1])} 行。` : ""}</p>
    <div class="heat-scroll"><table class="heat">
      <thead><tr><th></th>${cols.map(c => `<th class="${c === cur ? "cur" : ""}" title="${esc(D.ms_names[c] || "")}">${esc(c)}</th>`).join("")}<th>合计</th></tr></thead>
      <tbody>${rows.map(([n, lane]) => `<tr><th>${esc(n)}<small>${esc(lane)}</small></th>${cols.map(c => {
        const v = MOD[n].heat[c] || 0, s = shade(v);
        return `<td class="v ${s > 55 ? "hot" : ""}" style="${v ? `background:color-mix(in oklab, var(--accent) ${s}%, var(--surface))` : ""}" title="${esc(n)} · ${esc(c)} · ${fmt(v)} 行">${v ? fmt(v) : ""}</td>`;
      }).join("")}<td class="tot">${pct(MOD[n].effort)}</td></tr>`).join("")}</tbody>
      <tfoot><tr><th>合计</th>${colTot.map(v => `<td>${fmt(v)}</td>`).join("")}<td>${fmt(D.total)}</td></tr></tfoot>
    </table></div>
    <p class="fine">单位：改动行数（增 + 删，不含合并提交），含测试与文档，只用来比相对大小。按提交说明里的里程碑编号归列，没有编号的记入「其他」；文件按模块地图归行，首条命中为准。</p>`;
}

const TABS = D.archify ? ["now", "map", "cards", "issues", "effort"] : ["now", "map", "issues", "effort"];
document.getElementById("tab-cards").hidden = !D.archify;
function show(t) {
  TABS.forEach(x => {
    document.getElementById("tab-" + x).setAttribute("aria-selected", x === t);
    document.getElementById("view-" + x).hidden = x !== t;
  });
  try { localStorage.setItem("panel-tab", t); } catch (e) {}
}
TABS.forEach(t => document.getElementById("tab-" + t).addEventListener("click", () => { show(t); history.replaceState(null, "", "#" + t); }));
header(); viewNow(); if (D.archify) viewArchify(); viewMap(); viewIssues(); viewEffort();
let start = location.hash.slice(1);
if (!TABS.includes(start)) { try { start = localStorage.getItem("panel-tab"); } catch (e) {} }
show(TABS.includes(start) ? start : "now");
</script>
