#!/usr/bin/env bash
# prog.sh · 项目进度块。数字全部由 PLAN.md + git + gh 现算，不依赖任何会话记忆。
# 用法：prog.sh [--full] [PLAN.md 路径]   （默认 ./PLAN.md，从仓库根跑）
#         默认只出三段：进度（项目总体 + 当前里程碑）/ 下一步 / 待处理；main CI 异常时多一行警告
#         --full 追加：全局状态计数、最近勾选、距收口、其他在途、挂账、git/CI 健康（收口时用）
#       prog.sh --selftest          （自检：构造夹具并断言输出）
#       PROG_NO_GH=1 prog.sh        （跳过 gh 查询：离线 / 无 gh 时）
set -u

plan_block() { # $1 = PLAN.md  $2 = full(0/1)
  awk -v full="$2" '
  function trim(s){ sub(/^[ \t]+/,"",s); sub(/[ \t\r]+$/,"",s); return s }
  function utrunc(s,n,  c){            # 按字节截断但不切坏 UTF-8 字符
    if (length(s)<=n) return s
    while (n>0) { c=substr(s,n+1,1); if (c>="\200" && c<="\277") n--; else break }
    return substr(s,1,n) "…"
  }
  function tags(s,  out,a,b){          # 取出标题里全部【…】标注
    out=""
    while ((a=index(s,"【"))>0) { s=substr(s,a); b=index(s,"】"); if (b==0) break
      out=out substr(s,1,b+length("】")-1); s=substr(s,b+length("】")) }
    return out
  }
  function tshow(t,n,  a,d){           # 标题过长：截描述、保标注
    if (length(t)<=n) return t
    a=index(t,"【"); d=(a>0?substr(t,1,a-1):t); sub(/[ —–-]+$/,"",d)
    return utrunc(d,n) " " tags(t)
  }
  function addtask(id,title,isdone){
    total[ms]++; n++; tms[n]=ms; tdone[n]=isdone; ttitle[n]=title
    short=id; if (id!="" && index(id, ms "-")==1) short=substr(id,length(ms)+2)
    tshort[n]=(short!=""?short:title); task=tshort[n]
    if (isdone) done[ms]++
  }
  /当前里程碑(:|：)/ { if (match($0,/当前里程碑(:|：) *M[-A-Za-z0-9.]*/)) { s=substr($0,RSTART,RLENGTH); sub(/^.*(:|：) */,"",s); decl=s } }
  /已完成里程碑(:|：)/ { arch=trim($0); gsub(/\*\*/,"",arch)
    t=$0; sub(/^.*已完成里程碑(:|：)/,"",t); a=index(t,"（"); if (a>0) t=substr(t,1,a-1); a=index(t,"("); if (a>0) t=substr(t,1,a-1)
    prev=-1
    while (match(t,/M[0-9]+/)) {
      num=substr(t,RSTART+1,RLENGTH-1)+0; sep=trim(substr(t,1,RSTART-1)); t=substr(t,RSTART+RLENGTH)
      if (prev>=0 && (sep=="–" || sep=="-" || sep=="—" || sep=="~" || sep=="～" || sep=="至" || sep=="到")) { for (x=prev+1;x<=num;x++) archived["M" x]=1 }
      else archived["M" num]=1
      prev=num
    }
  }
  /^## / {
    ms=""; task=""
    # 里程碑标题：`## M3 · 名称`；容忍"前缀：M-PROD1 · 名称"；标题含 已收口 / ✅ = 已收口
    if (match($0,/^## ([^M]*(:|：) *)?M[-A-Za-z0-9.]*/)) {
      s=substr($0,RSTART,RLENGTH); rest=substr($0,RSTART+RLENGTH)
      if (match(s,/M[-A-Za-z0-9.]*$/)) id=substr(s,RSTART,RLENGTH)
      if (id ~ /[0-9]/ || rest ~ /^ *·/) {
        ms=id; if (!(ms in seen)) { seen[ms]=1; order[++nms]=ms }
        nm=rest; sub(/^ *· */,"",nm); name[ms]=trim(nm); head[ms]=$0
        if ($0 ~ /已收口|✅/) closed[ms]=1
      }
    }
    next
  }
  ms!="" && /^- \[( |x|X)\] / {            # 写法一：顶格复选框（缩进的子复选框不计）
    isdone = ($0 ~ /^- \[(x|X)\]/)
    t=$0; sub(/^- \[.\] /,"",t); gsub(/\*\*/,"",t); t=trim(t)
    id=""; if (match(t,/^[A-Za-z][-A-Za-z0-9.]*[0-9][A-Za-z0-9]*/)) id=substr(t,RSTART,RLENGTH)
    addtask(id,t,isdone); next
  }
  ms!="" && /^\| *[A-Za-z][-A-Za-z0-9.]*-[A-Za-z]+[0-9]+[A-Za-z0-9]* *\|/ {   # 写法二：表格行 | M30-T1 | 内容 | ✅ |
    nc=split($0,cell,"|"); id=trim(cell[2]); st=""
    for (i=nc;i>2;i--) { st=trim(cell[i]); if (st!="") break }
    addtask(id, id " · " trim(cell[3]), (index(st,"✅")>0)); task=""; next
  }
  ms!="" && task!="" {                      # 任务块内以「待拍板：」「偏差：」开头的行 = 待你处理
    l=trim($0); sub(/^- */,"",l); sub(/^Evidence(:|：) */,"",l)
    if (l ~ /^(待拍板|偏差)(:|：)/) { nf++; fms[nf]=ms; ftxt[nf]=task " " l; if (l ~ /^待拍板/) blocked[n]=1 }
  }
  END {
    for (i=1;i<=nms;i++) { m=order[i]; d=done[m]+0; t=total[m]+0
      if (closed[m]) { nclosed++ } else if (t>d) { nactive++ } else if (t>0) { nready++ } else { nidle++ } }
    cur=""
    if (decl!="" && (decl in seen) && !closed[decl] && total[decl]>0) cur=decl
    if (cur=="") for (i=1;i<=nms;i++) { m=order[i]; if (!closed[m] && total[m]>done[m]+0) { cur=m; break } }
    if (cur=="") for (i=1;i<=nms;i++) { m=order[i]; if (!closed[m] && total[m]>0) { cur=m; break } }
    if (nms==0) { print "PLAN 里没有找到里程碑标题（需要 `## M… · 名称`）"; exit 1 }
    # 项目总体进度：已收口里程碑 =（标题标了已收口/✅ 的）∪（「已完成里程碑：」里列的，PLAN 可能已不留其标题）
    for (i=1;i<=nms;i++) if (closed[order[i]]) archived[order[i]]=1
    ndone=0; for (k in archived) ndone++
    nopen=0; for (i=1;i<=nms;i++) if (!closed[order[i]]) nopen++
    ntot=ndone+nopen
    frac=(cur!="" && total[cur]>0) ? (done[cur]+0)/total[cur] : 0
    pct=(ntot>0) ? int((ndone+frac)*100/ntot) : 0
    W=16; fill=(ntot>0)?int((ndone+frac)*W/ntot):0; bar=""
    for (i=1;i<=W;i++) bar=bar (i<=fill?"█":"░")
    printf "项目     %s %d/%d 个里程碑已收口（总体 %d%%）\n", bar, ndone, ntot, pct
    if (cur=="") print "当前     没有进行中的里程碑（全部已收口或未开）"
    else {
      nm=name[cur]; a=index(nm,"（"); if (a>1) nm=substr(nm,1,a-1); nm=trim(nm)
      printf "当前     %s「%s」 %d/%d 个任务\n", cur, utrunc(nm,72), done[cur]+0, total[cur]
    }
    if (full) {
      printf "全局     已收口 %d · 进行中 %d · 任务全勾待收口 %d · 未开 %d\n", ndone, nactive, nready, nidle
      if (arch!="") printf "         %s\n", arch
      if (cur!="" && head[cur] ~ /涉敏/) print "         【涉敏】里程碑：收口必须过独立 A5 审计"
    }
    last=""; nxt=""; rest=""; nxti=0
    if (cur!="") for (i=1;i<=n;i++) if (tms[i]==cur) {
      if (tdone[i]) last=ttitle[i]
      else { if (nxt=="") { nxt=ttitle[i]; nxti=i }; rest=rest (rest==""?"":" → ") tshort[i] }
    }
    if (full && last!="") printf "最近勾选 %s\n", tshow(last,110)
    if (cur=="") print "下一步   立项下一个里程碑（`/kof c`）"
    else if (nxt=="") print "下一步   本里程碑任务已全勾 → 收口（`close`）"
    else {
      hint="（不需要你）"
      if (blocked[nxti]) hint="← 卡在你这里：先处理下面的「待拍板」"
      else if (nxt ~ /收口/) hint="← 收口门：走 close，需要你到场"
      else if (nxt ~ /单独|命门/) hint="← 命门：做完会停下等你核验"
      else if (nxt ~ /重型/) hint="← 重型：先出计划等你确认"
      printf "下一步   %s  %s\n", tshow(nxt,110), hint
    }
    split("① ② ③ ④ ⑤ ⑥ ⑦ ⑧ ⑨",c," "); k=0
    for (i=1;i<=nf;i++) if (fms[i]==cur) { k++
      txt=ftxt[i]; if (!full && txt !~ /待拍板(:|：)/) txt=utrunc(txt,150)     # 待拍板要马上决定→全文；偏差到收口才裁决→精简模式只给一行
      printf "%s %s %s\n", (k==1?"待处理  ":"        "), (k<=9?c[k]:"·"), txt }
    if (k==0) print "待处理   无"
    if (!full) exit 0
    if (rest!="") printf "距收口   %s\n", utrunc(rest,160)
    other=""
    for (i=1;i<=nms;i++) { m=order[i]; if (m!=cur && !closed[m] && total[m]>done[m]+0) other=other (other==""?"":" · ") m " " (done[m]+0) "/" total[m] }
    if (other!="") printf "其他在途 %s\n", other
    debt=""; nd=0
    for (i=1;i<=n;i++) if (closed[tms[i]] && !tdone[i]) { nd++; debt=debt (debt==""?"":"、") tshort[i] "（" tms[i] "）" }
    if (nd>0) printf "挂账     已收口里程碑下还有 %d 项未勾：%s\n", nd, utrunc(debt,160)
  }' "$1"
}

ci_status() { gh run list --branch main --limit 1 --json status,conclusion --jq '.[0] | (if .conclusion and .conclusion != "" then .conclusion else .status end)' 2>/dev/null; }

ci_warning() { # 精简模式：只有 main CI 异常才出声
  [ "${PROG_NO_GH:-0}" = "1" ] && return; command -v gh >/dev/null 2>&1 || return
  git rev-parse --git-dir >/dev/null 2>&1 || return
  ci=$(ci_status)
  case "$ci" in ""|success|in_progress|queued|pending|waiting|requested) ;; *) echo "⚠ 警告   main CI：$ci——红着不准开新任务，先修" ;; esac
}

health_line() {
  git rev-parse --git-dir >/dev/null 2>&1 || { echo "健康     （不在 git 仓库内）"; return; }
  br=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
  dirty=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
  if ahead=$(git rev-list --count '@{u}..HEAD' 2>/dev/null); then push="未推送 $ahead 个提交"; else push="分支尚未推送"; fi
  line="分支 $br · 未提交 $dirty 个文件 · $push"
  if [ "${PROG_NO_GH:-0}" != "1" ] && command -v gh >/dev/null 2>&1; then
    ci=$(ci_status)
    prs=$(gh pr list --state open --json number --jq 'length' 2>/dev/null)
    line="$line · main CI ${ci:-无记录} · 开放 PR ${prs:-?}"
  fi
  echo "健康     $line"
  echo "最近提交 $(git log -1 --format='%h %s' 2>/dev/null)"
}

selftest() {
  tmp=$(mktemp -d) || exit 1; trap 'rm -rf "$tmp"' EXIT
  cat > "$tmp/PLAN.md" <<'EOF'
**当前里程碑：M3**
已完成里程碑：M0–M2，任务见 PLAN-ARCHIVE.md

## 工作方式（速记）
- [ ] 这不是任务（不在里程碑节内）

## M1 · 旧里程碑 —— 已收口（0.2.0），任务见 PLAN-ARCHIVE.md
### 安全欠账（已收口里程碑下的挂账，编号不是 M 开头）
- [x] **SEC-1 · 限流分桶**
- [ ] **EXT-1 · 外部依赖欠账**

## M2 · 表格写法的里程碑 ✅（0.3.0）
| 任务 | 内容 | 状态 |
|---|---|---|
| M2-T1 | 做完了 | ✅ |

## M3 · 用户可导入 CSV 并看到点位【涉敏】
> 说明里出现 待拍板： 字样不应被计入
- [x] **M3-T1 · 契约冻结** —【重型】【单独+确认】（命门）
  Evidence：commit abc
- [x] **M3-T2 · 解析器** —【常规】【可批量】
  - [ ] 缩进的子复选框不计入任务
  偏差（已处理）：改用流式解析
- [x] M3-T3 · 预览端点 —【常规】【可批量】
  偏差：>50MB 文件未测
- [ ] **M3-T4a1 · 确认写库** —【重型】【单独+确认】（命门）
  待拍板：重复点合并策略
- [ ] **M3-T5 · 收口验收门** —【常规】【单独+确认】

## 尚未关闭的前置里程碑：M-PRE1 · 标题带前缀、任务在表格里
| 任务 | 内容 | 状态 |
|---|---|---|
| M-PRE1-T1 | 还没做 | ⬜ |
| M-PRE1-T2 | 做了 | ✅ |

## M4 · 下一里程碑（占位）
## Multi-agent notes
- [ ] 不是里程碑，不计入
EOF
  out=$(PROG_NO_GH=1 "$0" --full "$tmp/PLAN.md") || { echo "selftest FAIL: 非零退出"; echo "$out"; exit 1; }
  fail=0
  # 默认精简输出：只有 项目 / 当前 / 下一步 / 待处理
  outc=$(PROG_NO_GH=1 "$0" "$tmp/PLAN.md")
  for want in "3/6 个里程碑已收口（总体 60%）" "当前     M3「用户可导入 CSV 并看到点位【涉敏】」 3/5 个任务" "下一步   M3-T4a1" "① T3 偏差：>50MB 文件未测" "② T4a1 待拍板：重复点合并策略"; do
    printf '%s' "$outc" | grep -qF -- "$want" || { echo "selftest FAIL(精简): 缺少「$want」"; fail=1; }
  done
  for bad in "距收口" "全局" "挂账" "最近勾选" "其他在途" "健康"; do
    printf '%s' "$outc" | grep -qF -- "$bad" && { echo "selftest FAIL(精简): 不应出现「$bad」"; fail=1; }
  done
  [ "$(printf '%s\n' "$outc" | wc -l | tr -d ' ')" -le 5 ] || { echo "selftest FAIL(精简): 行数超过 5"; fail=1; }
  # 归档后 PLAN 不再留已完成里程碑的标题：总体进度要从「已完成里程碑：」一行里数
  printf '已完成里程碑：M0、M1（见 ARCHIVE）\n## M2 · 戊\n- [x] **M2-T1 · a**\n- [ ] **M2-T2 · b**\n## M3 · 己（占位）\n' > "$tmp/P6.md"
  PROG_NO_GH=1 "$0" "$tmp/P6.md" | grep -qF -- "2/4 个里程碑已收口（总体 62%）" || { echo "selftest FAIL(总体进度·列表写法)"; fail=1; }
  printf '已完成里程碑：M0–M3（任务见 PLAN-ARCHIVE.md）。\n## M4 · 庚\n- [ ] **M4-T1 · a**\n' > "$tmp/P7.md"
  PROG_NO_GH=1 "$0" "$tmp/P7.md" | grep -qF -- "4/5 个里程碑已收口（总体 80%）" || { echo "selftest FAIL(总体进度·范围写法)"; fail=1; }
  for want in "M3「用户可导入 CSV 并看到点位【涉敏】」" "3/5 个任务" "已收口 3 · 进行中 2 · 任务全勾待收口 0 · 未开 1" "收口必须过独立 A5 审计" "最近勾选 M3-T3" "下一步   M3-T4a1" "卡在你这里：先处理下面的「待拍板」" "① T3 偏差：>50MB 文件未测" "② T4a1 待拍板：重复点合并策略" "距收口   T4a1 → T5" "其他在途 M-PRE1 1/2" "已收口里程碑下还有 1 项未勾：EXT-1（M1）"; do
    printf '%s' "$out" | grep -qF -- "$want" || { echo "selftest FAIL: 缺少「$want」"; fail=1; }
  done
  for bad in "已处理" "③" "Multi" "SEC-1"; do
    printf '%s' "$out" | grep -qF -- "$bad" && { echo "selftest FAIL: 不应出现「$bad」"; fail=1; }
  done
  # 试用反馈（TideAnywhere M12）：长「待拍板」不许截断；长标题截描述保标注；卡在待拍板时提示要准
  long="D55 五项（a 低-2 做法：设界 A / 逐站流式 B；b 三个上限数值 64 KiB / 16 MiB / 1 GiB；c 批次内符号链接一律拒；d 规则版本升 v5；e 旧批次不重判）结尾标记ZZ"
  printf '## M9 · 长文本\n- [ ] **M9-T1 · 批次读取设界 + 先判目录后读 + 符号链接一律拒 + 规则版本升级以及其他很长很长的描述文字用来触发截断** —【常规】【单独+确认】（动受保护文件）状态：todo\n  待拍板：%s\n' "$long" > "$tmp/P4.md"
  out4=$(PROG_NO_GH=1 "$0" "$tmp/P4.md")
  printf '  偏差：%s\n' "$long" >> "$tmp/P4.md"
  out4=$(PROG_NO_GH=1 "$0" "$tmp/P4.md")
  [ "$(printf '%s' "$out4" | grep -c '结尾标记ZZ')" = "1" ] || { echo "selftest FAIL(试用反馈): 精简模式下长「偏差」应截成一行、长「待拍板」应保留全文"; fail=1; }
  [ "$(PROG_NO_GH=1 "$0" --full "$tmp/P4.md" | grep -c '结尾标记ZZ')" = "2" ] || { echo "selftest FAIL(试用反馈): --full 下偏差应为全文"; fail=1; }
  for want in "结尾标记ZZ" "【常规】【单独+确认】" "卡在你这里：先处理下面的「待拍板」"; do
    printf '%s' "$out4" | grep -qF -- "$want" || { echo "selftest FAIL(试用反馈): 缺少「$want」"; fail=1; }
  done
  # 下一个任务是命门、且没有待拍板 → 命门提示
  printf '## M6 · 丁\n- [ ] **M6-T1 · 鉴权** —【重型】【单独+确认】（命门）\n' > "$tmp/P5.md"
  PROG_NO_GH=1 "$0" "$tmp/P5.md" | grep -qF -- "命门：做完会停下等你核验" || { echo "selftest FAIL(命门提示)"; fail=1; }
  # 下一个任务是收口任务 → 提示需要用户到场
  printf '## M5 · 丙\n- [x] **M5-T1 · 做了**\n- [ ] **M5-T2 · 收口：部署与实机走查**\n' > "$tmp/P3.md"
  PROG_NO_GH=1 "$0" "$tmp/P3.md" | grep -qF -- "收口门：走 close，需要你到场" || { echo "selftest FAIL(收口提示)"; fail=1; }
  # 全部收口的 PLAN：不应把已收口里程碑当成当前里程碑
  printf '## M1 · 甲 ✅\n- [ ] **EXT-9 · 欠账**\n## M2 · 乙 —— 已收口\n' > "$tmp/P2.md"
  out2=$(PROG_NO_GH=1 "$0" --full "$tmp/P2.md")
  for want in "2/2 个里程碑已收口（总体 100%）" "没有进行中的里程碑" "已收口 2 · 进行中 0" "还有 1 项未勾：EXT-9（M1）"; do
    printf '%s' "$out2" | grep -qF -- "$want" || { echo "selftest FAIL(全收口): 缺少「$want」"; fail=1; }
  done
  [ $fail = 0 ] && echo "selftest ok" || { echo "-----"; echo "$out"; exit 1; }
}

full=0; [ "${1:-}" = "--full" ] && { full=1; shift; }
case "${1:-}" in
  --selftest) selftest ;;
  *) plan="${1:-PLAN.md}"
     [ -f "$plan" ] || { echo "找不到 $plan（从仓库根运行，或把 PLAN.md 路径作为参数传入）"; exit 1; }
     plan_block "$plan" "$full" || exit 1
     if [ $full = 1 ]; then health_line; else ci_warning; fi ;;
esac
