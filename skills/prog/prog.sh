#!/usr/bin/env bash
# prog.sh · 项目进度块。数字全部由 PLAN.md + git + gh 现算，不依赖任何会话记忆。
# 用法：prog.sh [PLAN.md 路径]      （默认 ./PLAN.md，从仓库根跑）
#       prog.sh --selftest          （自检：构造夹具并断言输出）
#       PROG_NO_GH=1 prog.sh        （跳过 gh 查询：离线 / 无 gh 时）
set -u

plan_block() { # $1 = PLAN.md
  awk '
  function trim(s){ sub(/^[ \t]+/,"",s); sub(/[ \t\r]+$/,"",s); return s }
  /当前里程碑(:|：)/ { if (match($0,/当前里程碑(:|：) *M[-A-Za-z0-9.]*/)) { s=substr($0,RSTART,RLENGTH); sub(/^.*(:|：) */,"",s); decl=s } }
  /已完成里程碑(:|：)/ { arch=trim($0); gsub(/\*\*/,"",arch) }
  /^## / {
    ms=""; task=""
    if (match($0,/^## M[-A-Za-z0-9.]*/)) {
      ms=substr($0,RSTART+3,RLENGTH-3); order[++nms]=ms
      nm=substr($0,RSTART+RLENGTH); sub(/^ *· */,"",nm); name[ms]=trim(nm)
    }
    next
  }
  ms!="" && /^- \[( |x|X)\] / {            # 顶格复选框才是任务；缩进的子复选框不计
    isdone = ($0 ~ /^- \[(x|X)\]/)
    t=$0; sub(/^- \[.\] /,"",t); gsub(/\*\*/,"",t); t=trim(t)
    id=""; if (match(t,/M[-A-Za-z0-9.]*-T[0-9]+[a-z]?/)) id=substr(t,RSTART,RLENGTH)
    task=(id!=""?id:t); sub(/^.*-T/,"T",task)
    total[ms]++; n++; tms[n]=ms; ttitle[n]=t; tshort[n]=task; tdone[n]=isdone
    if (isdone) done[ms]++
    next
  }
  ms!="" && task!="" {                      # 任务块内以「待拍板：」「偏差：」开头的行 = 待你处理
    l=trim($0); sub(/^- */,"",l); sub(/^Evidence(:|：) */,"",l)
    if (l ~ /^(待拍板|偏差)(:|：)/) { nf++; fms[nf]=ms; ftxt[nf]=task " " l }
  }
  END {
    cur=""
    if (decl!="" && total[decl]>0) cur=decl
    if (cur=="") for (i=1;i<=nms;i++) if (total[order[i]]>done[order[i]]+0) { cur=order[i]; break }
    if (cur=="") for (i=nms;i>=1;i--) if (total[order[i]]>0) { cur=order[i]; break }
    if (cur=="") { print "PLAN 里没有找到带任务的里程碑（需要 `## M… ·` 标题 + 顶格 `- [ ]` 任务行）"; exit 1 }
    d=done[cur]+0; tt=total[cur]; W=16; fill=int(d*W/tt); bar=""
    for (i=1;i<=W;i++) bar=bar (i<=fill?"█":"░")
    pos=0; for (i=1;i<=nms;i++) if (order[i]==cur) pos=i
    printf "━━ %s「%s」━━━━━━━━━━━━\n", cur, name[cur]
    printf "里程碑   %s %d/%d（%d%%）   PLAN 内第 %d/%d 个里程碑\n", bar, d, tt, int(d*100/tt), pos, nms
    if (arch!="") printf "         %s\n", arch
    last=""; nxt=""; rest=""
    for (i=1;i<=n;i++) if (tms[i]==cur) {
      if (tdone[i]) last=ttitle[i]
      else { if (nxt=="") nxt=ttitle[i]; rest=rest (rest==""?"":" → ") tshort[i] }
    }
    if (last!="") printf "最近勾选 %s\n", last
    if (nxt=="") print "下一个   无——本里程碑任务已全勾：待收口 / 立项下一里程碑"
    else {
      hint="（可连续跑，不需要你）"
      if (nxt ~ /单独\+确认|命门/) hint="← 命门：做完会停下等你核验"
      else if (nxt ~ /重型/) hint="← 重型：先出计划等你确认"
      printf "下一个   %s  %s\n", nxt, hint
    }
    split("① ② ③ ④ ⑤ ⑥ ⑦ ⑧ ⑨",c," "); k=0
    for (i=1;i<=nf;i++) if (fms[i]==cur) { k++; printf "%s %s %s\n", (k==1?"待你处理":"        "), (k<=9?c[k]:"·"), ftxt[i] }
    if (k==0) print "待你处理 无"
    if (rest!="") printf "距收口   %s\n", rest
  }' "$1"
}

health_line() {
  git rev-parse --git-dir >/dev/null 2>&1 || { echo "健康     （不在 git 仓库内）"; return; }
  br=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
  dirty=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
  if ahead=$(git rev-list --count '@{u}..HEAD' 2>/dev/null); then push="未推送 $ahead 个提交"; else push="分支尚未推送"; fi
  line="分支 $br · 未提交 $dirty 个文件 · $push"
  if [ "${PROG_NO_GH:-0}" != "1" ] && command -v gh >/dev/null 2>&1; then
    ci=$(gh run list --branch main --limit 1 --json status,conclusion --jq '.[0] | (if .conclusion and .conclusion != "" then .conclusion else .status end)' 2>/dev/null)
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

## M3 · 用户可导入 CSV 并看到点位
> 说明里出现 待拍板： 字样不应被计入
- [x] **M3-T1 · 契约冻结** —【重型】【单独+确认】（命门）
  Evidence：commit abc
- [x] **M3-T2 · 解析器** —【常规】【可批量】
  - [ ] 缩进的子复选框不计入任务
  偏差（已处理）：改用流式解析
- [x] M3-T3 · 预览端点 —【常规】【可批量】
  偏差：>50MB 文件未测
- [ ] **M3-T4 · 确认写库** —【重型】【单独+确认】（命门）
  待拍板：重复点合并策略
- [ ] **M3-T5 · 收口验收门** —【常规】【单独+确认】

## M4 · 下一里程碑（占位）
EOF
  out=$(PROG_NO_GH=1 "$0" "$tmp/PLAN.md") || { echo "selftest FAIL: 非零退出"; echo "$out"; exit 1; }
  fail=0
  for want in "M3「用户可导入 CSV 并看到点位」" "3/5（60%）" "PLAN 内第 1/2 个里程碑" "最近勾选 M3-T3" "下一个   M3-T4" "命门：做完会停下等你核验" "① T3 偏差：>50MB 文件未测" "② T4 待拍板：重复点合并策略" "距收口   T4 → T5"; do
    printf '%s' "$out" | grep -qF -- "$want" || { echo "selftest FAIL: 缺少「$want」"; fail=1; }
  done
  for bad in "已处理" "③"; do
    printf '%s' "$out" | grep -qF -- "$bad" && { echo "selftest FAIL: 不应出现「$bad」"; fail=1; }
  done
  [ $fail = 0 ] && echo "selftest ok" || { echo "-----"; echo "$out"; exit 1; }
}

case "${1:-}" in
  --selftest) selftest ;;
  *) plan="${1:-PLAN.md}"
     [ -f "$plan" ] || { echo "找不到 $plan（从仓库根运行，或把 PLAN.md 路径作为参数传入）"; exit 1; }
     plan_block "$plan" || exit 1
     health_line ;;
esac
