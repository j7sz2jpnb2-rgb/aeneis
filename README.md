# 《埃涅阿斯纪》（AENEIS）中文译本与制版源工程

[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.23255498-blue.svg)](https://doi.org/10.5281/zenodo.23255498)
[![License: CC BY-NC-ND 4.0](https://img.shields.io/badge/License-CC%20BY--NC--ND%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-nd/4.0/)
[![Edition: 4th](https://img.shields.io/badge/Edition-Fourth%20(2026.10.9)-green.svg)](#版本信息)

> **原著**：普布利乌斯·维吉尔·马罗（Publius Vergilius Maro）  
> **译编**：ChatGPT & Novelist  
> **版本**：第四版（2026 年 10 月 9 日定稿）  
> **版型**：185 × 260 mm 典藏开本 · XeLaTeX 专业制版  

---

## 📖 项目简介

本项目收录古罗马史诗《埃涅阿斯纪》（*Aeneis*）全十二卷中文无韵自由体诗逐行译本及排版编译源工程。

本译本以 Gian Biagio Conte 编订之 [*Aeneis: Editio altera*](https://doi.org/10.1515/9783110649031)（De Gruyter，2019）第二版为核心底本，正文 9888 行与底本逐行严谨对应，并包含 534 条学术注释、3 幅高精度地理历史地图、12 幅 17 世纪经典蚀刻卷首版画及 115 条专名术语表。

---

## 📑 快速导航

### 1. 纯译文阅读（Markdown 拆分十二卷）
- 📄 [**前言与体例说明**](前言与体例说明.md)
- 📜 [**纯译文目录与导读**](纯译文/README.md)
- 卷一：[第一卷（LIBER I）· 756行](纯译文/01_第一卷.md)
- 卷二：[第二卷（LIBER II）· 803行](纯译文/02_第二卷.md)
- 卷三：[第三卷（LIBER III）· 718行](纯译文/03_第三卷.md)
- 卷四：[第四卷（LIBER IV）· 703行](纯译文/04_第四卷.md)
- 卷五：[第五卷（LIBER V）· 871行](纯译文/05_第五卷.md)
- 卷六：[第六卷（LIBER VI）· 901行](纯译文/06_第六卷.md)
- 卷七：[第七卷（LIBER VII）· 817行](纯译文/07_第七卷.md)
- 卷八：[第八卷（LIBER VIII）· 731行](纯译文/08_第八卷.md)
- 卷九：[第九卷（LIBER IX）· 816行](纯译文/09_第九卷.md)
- 卷十：[第十卷（LIBER X）· 907行](纯译文/10_第十卷.md)
- 卷十一：[第十一卷（LIBER XI）· 915行](纯译文/11_第十一卷.md)
- 卷十二：[第十二卷（LIBER XII）· 950行](纯译文/12_第十二卷.md)
- 📘 [**【全书合订】埃涅阿斯纪·纯译文全文（9888行）**](纯译文/埃涅阿斯纪_纯译文全文.md)

### 2. 权威底本与学术注释（TXT）
- 完整带注底本：[`工程/拼合工程_工作稿/正文与注释权威源/埃涅阿斯纪_最新全文_附注释_20261006.txt`](工程/拼合工程_工作稿/正文与注释权威源/埃涅阿斯纪_最新全文_附注释_20261006.txt)
- 十二卷分卷附注：[`工程/拼合工程_工作稿/正文与注释权威源/当前分卷_20261006/`](工程/拼合工程_工作稿/正文与注释权威源/当前分卷_20261006/)
- 专名术语表：[`工程/专名与术语表_更新版.md`](工程/专名与术语表_更新版.md)

### 3. 视觉与排版资产
- 🗺️ **成书地图**（置于 [`工程/拼合工程_工作稿/制版源文件/assets/maps/`](工程/拼合工程_工作稿/制版源文件/assets/maps/)）：
  - **地图 1**：斯特拉波所述的世界（*Strabo's World*，Bunbury 1883 重构版）
  - **地图 2**：从特洛伊到拉提乌姆（*Aeneas's Voyage*，约 400 ppi 矢量修整与航线）
  - **地图 3**：拉提乌姆与台伯河（*Latium and the Tiber*）
  - 提供 PDF、PNG 及 SVG 三种格式。
- 🖼️ **卷首版画**（置于 [`工程/拼合工程_工作稿/制版源文件/assets/plates/`](工程/拼合工程_工作稿/制版源文件/assets/plates/)）：
  - 12 幅 1654 年 Wenceslaus Hollar 蚀刻版画（全书十二卷每卷一幅，采用自然纸边与灰阶处理）。
- 🎨 **封面油画**：J. M. W. Turner 1815 年名作《狄多建造迦太基》（高清图版见 [`assets/cover/`](工程/拼合工程_工作稿/制版源文件/assets/cover/)）。
- 📑 **版本记与末页**：包含独立 DOI 与豆瓣作者页面二维码的 HTML 权威源及单页资产（见 [`工程/末页设计/`](工程/末页设计/) 及 [`assets/colophon.pdf`](工程/拼合工程_工作稿/制版源文件/assets/colophon.pdf)）。

---

## 🛠️ 编译与排版指南

本工程排版基于 **XeLaTeX**（`ctexbook`），输出 185 × 260 mm 版型，内建完善的目录、书签、脚注对跳与数字无障碍增强流程。

### 环境依赖
- **TeX 排版系统**：TeX Live 2024+（含 `xelatex`, `kpsewhich`, `ctexbook`, `xurl` 等宏包）
- **中英文字体**：
  - 中文正文：思源宋体（Noto Serif CJK SC）
  - 中文无衬线：思源黑体（Noto Sans CJK SC）
  - 西文衬线：EB Garamond
  - 地图内嵌字体：Noto CJK 子集字体（已内置于 `assets/fonts/maps/`）
- **Python 环境**：Python 3.10+，安装依赖：
  ```bash
  pip install -r 工程/拼合工程_工作稿/制版源文件/requirements-assets.txt
  ```

### 编译步骤
进入制版源文件目录执行编译脚本：
```bash
cd 工程/拼合工程_工作稿/制版源文件
bash compile.sh
```
编译脚本将自动进行三遍正文排版，并在验证封面单页尺寸与各依赖后通过 `merge_cover.py` 合并封面，生成 `build/main.pdf`。

### 数字无障碍与元数据增强（PDF/UA）
排版完成后，可通过 [`数字增强/`](数字增强/) 目录下的脚本对输出 PDF 进行后处理：
- 注入完整 PDF 书签、正确的 Page Labels；
- 建立正文与 534 个脚注之间的双向锚点跳转；
- 嵌入结构化标签（Tagged PDF）、图片替代文本（Alt Text）与无边框超链接；
- 校验脚本：`python 数字增强/verify_pdf.py build/main.pdf`。

> 详细编译规范请阅读 [《编译交接与规格说明》](编译交接与规格说明.md)。

---

## 🏛️ 仓库目录结构

```text
├── README.md                          # 本说明文档
├── 前言与体例说明.md                   # 译文体例、底本渊源与注释体例说明
├── 编译交接与规格说明.md               # 排版规格、尺寸定义与数字增强编译交接备忘
├── 纯译文/                            # 9888 行纯诗行拆分十二卷（Markdown）
│   ├── README.md
│   ├── 01_第一卷.md ~ 12_第十二卷.md
│   └── 埃涅阿斯纪_纯译文全文.md
├── 工程/                              # 核心排版源工程与原始文本
│   ├── 专名与术语表_更新版.md
│   ├── 埃涅阿斯纪_最新全文_附注释_20261006.txt
│   ├── 末页设计/                      # 版本记设计与发布元数据
│   └── 拼合工程_工作稿/
│       ├── 正文与注释权威源/          # 权威正文与分卷附注 TXT
│       └── 制版源文件/                # XeLaTeX 制版源码（main.tex、compile.sh、content/、assets/）
└── 数字增强/                          # PDF 可访问性（Tagged PDF / UA）处理脚本
```

---

## ⚖️ 版权与发布信息

- **译本著作权**：普布利乌斯·维吉尔·马罗 著 ｜ ChatGPT & Novelist 译编
- **授权协议**：[知识共享署名-非商业性使用-禁止演绎 4.0 国际许可协议（CC BY-NC-ND 4.0）](https://creativecommons.org/licenses/by-nc-nd/4.0/)
- **数字对象唯一标识符（DOI）**：[10.5281/zenodo.23255498](https://doi.org/10.5281/zenodo.23255498)
- **勘误联系**：Novelist 的[豆瓣主页](https://www.douban.com/people/252994365/)（数字 ID：`252994365`）
