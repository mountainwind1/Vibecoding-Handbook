<!-- vibe-map-page -->
<title>项目地图</title>
<style>
:root{
  --ground:#F3F5F6; --surface:#FFFFFF; --sunk:#E9EDEF; --ink:#15202B; --muted:#5A6772; --faint:#8995A0; --rule:#D3DADF;
  --accent:#0E6F8C; --accent-soft:#DCEEF4; --on-accent:#FFFFFF;
  --crit:#B83227; --crit-soft:#F8E1DE; --warn:#9A6212; --warn-soft:#F7EBD3; --ok:#2F7D55; --ext:#56657A; --ext-soft:#E4E9EF;
  --sans:"PingFang SC","Hiragino Sans GB","Microsoft YaHei","Noto Sans CJK SC",system-ui,-apple-system,"Segoe UI",sans-serif;
  --mono:ui-monospace,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;
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
.wrap{max-width:980px;margin:0 auto;padding-inline:20px;padding-block:26px 48px}
h1{font-size:24px;font-weight:650;margin:0}
.sub{color:var(--muted);font-size:13px;margin:4px 0 18px}
.list{display:flex;flex-direction:column;gap:10px}
.proj{display:grid;grid-template-columns:4px 1fr;background:var(--surface);border:1px solid var(--rule);border-radius:10px;color:inherit;text-decoration:none;overflow:hidden}
.proj:hover{border-color:var(--faint)}
.proj:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.bar{background:var(--rule)} .proj.crit .bar{background:var(--crit)} .proj.active .bar{background:var(--accent)}
.body{padding:12px 16px;display:flex;flex-direction:column;gap:4px;min-width:0}
.top{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.name{font-weight:650;font-size:16px;margin-right:auto}
.badge{font-size:12px;padding:0 8px;border-radius:999px;line-height:20px;white-space:nowrap}
.badge.crit{background:var(--crit);color:var(--surface)} .badge.warn{background:var(--warn-soft);color:var(--warn)} .badge.ext{background:var(--ext-soft);color:var(--ext)}
.upd{font-size:12px;color:var(--faint);white-space:nowrap}
.line{font-size:13.5px;overflow-wrap:anywhere}
.line .id{font-family:var(--mono);color:var(--accent);font-weight:600;margin-right:6px}
.line.muted{color:var(--muted);font-size:12.5px}
.meter{display:inline-block;width:72px;height:5px;border-radius:3px;background:var(--sunk);overflow:hidden;vertical-align:middle;margin-left:6px}
.meter i{display:block;height:100%;background:var(--accent)}
.gate{color:var(--crit);font-size:12px;border:1px solid currentColor;border-radius:999px;padding:0 6px;margin-left:6px;white-space:nowrap}
.empty{color:var(--muted)}
@media (max-width:640px){ .wrap{padding-inline:16px} }
</style>

<div class="wrap">
  <h1>项目地图</h1>
  <p class="sub">每个项目：正在做什么、走到哪一步、有没有卡在你这里。点进去看这一步的问题和最近进展。</p>
  <main class="list" id="list"><p class="empty">加载中…</p></main>
</div>

<script>
const EMBED = __SUMMARIES__;   // 本机版把各项目摘要直接嵌进来；服务器版为 null，读 projects.json
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const ago = t => { const s = Date.now() / 1000 - t; return s < 90 ? "刚刚" : s < 3600 ? Math.round(s / 60) + " 分钟前" : s < 86400 ? Math.round(s / 3600) + " 小时前" : Math.round(s / 86400) + " 天前"; };
async function load() {
  if (EMBED) return EMBED;
  const names = await (await fetch("projects.json", {cache: "no-store"})).json();
  const all = await Promise.all(names.map(n => fetch(encodeURIComponent(n) + "/summary.json", {cache: "no-store"}).then(r => r.ok ? r.json() : null).then(j => j && Object.assign(j, {dir: n})).catch(() => null)));
  return all.filter(Boolean);
}
function card(p) {
  const m = p.milestone, st = p.step, active = p.state === "active";
  const badges = [p.waiting ? `<span class="badge crit">等你拍板 ${p.waiting}</span>` : "", p.ci === "fail" ? `<span class="badge crit">CI 失败</span>` : "",
                  p.deviations ? `<span class="badge warn">偏差 ${p.deviations}</span>` : ""].join("");
  const lines = active ? `
      <div class="line"><span class="id">${esc(m.id)}</span>${esc(m.name)}<span class="meter"><i style="width:${m.total ? 100 * m.done / m.total : 0}%"></i></span> ${m.done}/${m.total}</div>
      <div class="line">${st ? `第 ${st.index}/${st.total} 步：<span class="id">${esc(st.id)}</span>${esc(st.title)}${st.gate ? `<span class="gate">需要你到场</span>` : ""}` : "任务都勾完了，等收口"}</div>`
    : `<div class="line">没有正在开发的功能${m ? ` · 上一个 <span class="id">${esc(m.id)}</span>${esc(m.note || "已收口")}` : ""}<span class="gate">下一步：立项</span></div>`;
  const top = p.top ? `<div class="line muted">${esc(p.top.kind)}${p.top.task ? " · " + esc(p.top.task) : ""}：${esc(p.top.text)}</div>` : "";
  const tone = p.waiting || p.ci === "fail" ? "crit" : active ? "active" : "";
  return `<a class="proj ${tone}" href="${encodeURIComponent(p.dir || p.project)}/index.html"><span class="bar"></span><span class="body">
      <span class="top"><span class="name">${esc(p.dir || p.project)}</span>${badges}<span class="upd">${p.last ? "最近提交 " + ago(p.last.t) : ""}</span></span>
      ${lines}${top}</span></a>`;
}
load().then(list => {
  const rank = p => (p.waiting || p.ci === "fail" ? 0 : p.state === "active" ? 1 : 2);
  list.sort((a, b) => rank(a) - rank(b) || (b.last ? b.last.t : 0) - (a.last ? a.last.t : 0));
  document.getElementById("list").innerHTML = list.length ? list.map(card).join("") : `<p class="empty">还没有项目发布过地图。</p>`;
}).catch(e => { document.getElementById("list").innerHTML = `<p class="empty">读不到项目列表：${esc(e.message)}</p>`; });
</script>
