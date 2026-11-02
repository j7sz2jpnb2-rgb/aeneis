#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build

command -v xelatex >/dev/null 2>&1 || { echo "缺少 XeLaTeX。" >&2; exit 1; }
command -v kpsewhich >/dev/null 2>&1 || { echo "缺少 kpsewhich。" >&2; exit 1; }
kpsewhich ctexbook.cls >/dev/null 2>&1 || { echo "缺少 ctexbook.cls。" >&2; exit 1; }
python3 -c 'import pypdf' >/dev/null 2>&1 || { echo "缺少 Python 包 pypdf。" >&2; exit 1; }

# 封面是批准版成品基准：默认绝不重渲染、绝不覆盖。
if [[ ! -f cover.pdf ]]; then
  echo "缺少批准版 cover.pdf；为避免封面偏差，默认构建不会自动重建它。" >&2
  exit 1
fi

# 当前地图为确认成书资产；缺失时停止，避免自动恢复旧尺寸版本。
for map in aeneas-voyage latium-tiber strabo-world; do
  if [[ ! -f "assets/maps/${map}.pdf" ]]; then
    echo "缺少当前成书地图：${map}；请恢复当前资产，不要调用旧地图脚本或自动恢复旧尺寸版本。" >&2
    exit 1
  fi
done
kpsewhich xurl.sty >/dev/null 2>&1 || { echo "缺少 xurl 宏包。" >&2; exit 1; }

# 内部校样允许缺少末页；正式发布模式必须已有批准的单页末页 PDF。
if [[ "${AENEIS_RELEASE:-0}" == "1" && ! -f assets/colophon.pdf ]]; then
  echo "发布模式缺少 assets/colophon.pdf；请先填写并输出 Claude 版本记。" >&2
  exit 1
fi
if [[ -f assets/colophon.pdf ]]; then
  python3 - <<'PY'
from pypdf import PdfReader
r = PdfReader('assets/colophon.pdf')
assert len(r.pages) == 1, '版本记必须是单页'
p = r.pages[0]
assert abs(float(p.mediabox.width) * 25.4 / 72 - 185) < .1, '版本记宽度须为185mm'
assert abs(float(p.mediabox.height) * 25.4 / 72 - 260) < .1, '版本记高度须为260mm'
PY
fi

for pass in 1 2 3; do
  echo "[XeLaTeX] 第 ${pass} 遍编译正文"
  xelatex -jobname=main_body -output-directory=build -interaction=nonstopmode -halt-on-error main.tex
 done
python3 merge_cover.py cover.pdf build/main_body.pdf build/main.pdf
python3 - <<'PY'
from pathlib import Path
p = Path('build/main.pdf')
size = p.stat().st_size
print(f'完整 PDF 实际体积：{size:,} 字节')
assert size <= 50_000_000, '完整PDF超过50,000,000字节；须定位大对象后优化'
PY
echo "完成：build/main.pdf（工作/成品 PDF 不应回塞进交接 ZIP）"
