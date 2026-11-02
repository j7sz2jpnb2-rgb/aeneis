# 地图中文字体

四份 `.map-subset.otf` 为 Noto Sans CJK SC 与 Noto Serif CJK SC Regular/Bold 的字形子集，用于本次地图标题、标签和说明。它们依据 SIL Open Font License 1.1 随工程分发；两套原许可证分别保存在 `OFL_Sans.txt` 和 `OFL_Serif.txt`。

来源：<https://github.com/notofonts/noto-cjk>，具体为 `Sans/OTF/SimplifiedChinese/` 和 `Serif/OTF/SimplifiedChinese/` 下同名字体。使用 fontTools 子集化，保留中文文案、ASCII 和所需标点。生成地图无需安装 fontTools。

若新增文案超出子集字符范围，绘图核查会报告缺字。可下载上述四份完整 OTF，并设置 `AENEID_CJK_FONT_DIR` 指向其目录；此目录优先于随包字体。

PDF 使用 Type 3 矢量字形，以正确呈现 CFF 轮廓。其中文文字不能保证可搜索或复制；版面与字形保持矢量输出。可编辑文案保留在绘图源代码中。
