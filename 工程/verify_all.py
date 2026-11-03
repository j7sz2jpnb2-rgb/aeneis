"""Comprehensive verification test suite for all modifications."""
import io
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
DRAFT = ROOT / "拼合工程_工作稿"
TXT_DRAFT = DRAFT / "正文与注释权威源" / "埃涅阿斯纪_最新全文_附注释_20261006.txt"
TXT_ROOT = ROOT / "埃涅阿斯纪_最新全文_附注释_20261006.txt"
CHAPTERS_DIR = DRAFT / "正文与注释权威源" / "当前分卷_20261006"
CONTENT_DIR = DRAFT / "制版源文件" / "content"
GLOSSARY_TEX = CONTENT_DIR / "glossary_current.tex"
GLOSSARY_MD = ROOT / "专名与术语表_更新版.md"
MAP_SVG = DRAFT / "制版源文件" / "assets" / "maps" / "aeneas-voyage.svg"
MAP_PDF = DRAFT / "制版源文件" / "assets" / "maps" / "aeneas-voyage.pdf"

sys.path.append(str(ROOT))
from build_matrix import parse_full_text
from build_draft import TEX_LINE_RE, verse_order, BOOK_NAMES

def main():
    print("Running comprehensive test suite...")

    # 0. Check TXT files identity
    assert TXT_DRAFT.read_bytes() == TXT_ROOT.read_bytes(), "Authoritative TXT files mismatch!"
    print("[PASS] Both authoritative TXT files are byte-for-byte identical.")

    verses, notes = parse_full_text(TXT_DRAFT)
    order = verse_order(TXT_DRAFT)
    assert len(verses) == 9888, f"Expected 9888 verses, got {len(verses)}"
    assert len(notes) == 534, f"Expected 534 notes, got {len(notes)}"
    print("[PASS] Verse count (9888) and note count (534) correct.")

    # 1. Poetic Text Polish Verification
    assert verses["1.402"] == "她说完转过身去，玫瑰色的颈项闪耀光辉，"
    assert verses["1.403"] == "不死的长发从头顶吐出神圣的"
    assert verses["1.404"] == "芬芳；长袍一直垂落到脚底，"
    assert verses["1.405"] == "步态间显出真正的女神。当他"
    assert verses["2.376"] == "他说完，因给出的回答并不够可信，"
    assert verses["2.377"] == "便立刻察觉自己已落入敌人中央。"
    assert verses["2.378"] == "他惊住，话音和脚步一同收回："
    assert verses["3.45"] == "因为我是波吕多鲁斯；铁矛的庄稼在这里覆盖了"
    assert verses["3.46"] == "被刺穿的我，长成尖利的投枪。’"
    assert verses["3.47"] == "这时，我的心才被双重的恐惧压住，"
    assert verses["3.48"] == "我惊住，头发直立而声音哽在喉中。"
    assert verses["11.550"] == "为亲爱的负担担忧；他在心中反复权衡一切，"
    assert verses["11.551"] == "才勉强定下这突如其来的主意："
    print("[PASS] 1. Poetic Text Polish: 1.402-405, 2.376-378, 3.45-48, 11.550-551 verified.")

    # 2. Line-end Comma Removal Verification
    b2_comma_lines = [98, 118, 158, 213, 218, 242, 266, 316, 326, 355, 356, 359, 370, 417, 435, 438, 446, 455, 464, 501, 504, 519, 542, 548, 598, 630, 652, 710, 723, 731, 756, 765, 781, 797]
    for num in b2_comma_lines:
        v = verses[f"2.{num}"]
        clean = re.sub(r"\[注\d+\]", "", v)
        assert not clean.endswith("，"), f"Book 2 line {num} still ends with comma: {v}"

    b3_comma_lines = [29, 91, 107, 177, 234, 239, 266, 366, 372, 382, 385, 390, 443, 445, 480, 487, 673, 675, 693]
    for num in b3_comma_lines:
        v = verses[f"3.{num}"]
        clean = re.sub(r"\[注\d+\]", "", v)
        assert not clean.endswith("，"), f"Book 3 line {num} still ends with comma: {v}"

    other_comma_lines = ["1.459", "4.544", "5.100", "5.260", "6.791", "7.100"]
    for k in other_comma_lines:
        v = verses[k]
        clean = re.sub(r"\[注\d+\]", "", v)
        assert not clean.endswith("，"), f"{k} still ends with comma: {v}"
    print(f"[PASS] 2. Line-end Comma Removal: all {len(b2_comma_lines) + len(b3_comma_lines) + len(other_comma_lines)} lines verified clean.")

    # 3. Added Sentence Punctuation Verification
    assert verses["12.69"] == "少女的面庞上便流露出这般交织的色彩。[注505]"
    assert verses["2.173"].endswith("；")
    assert verses["2.325"].endswith("；")
    assert verses["2.433"].endswith("；")
    assert verses["2.440"].endswith("；")
    assert verses["2.454"].endswith("；")
    assert verses["2.486"].endswith("，")
    assert verses["2.487"].endswith("，")
    assert verses["2.521"].endswith("；")
    assert verses["2.761"].endswith("；")
    assert verses["2.780"].endswith("；")
    assert verses["3.85"].endswith("；")
    assert verses["3.170"].endswith("；")
    assert verses["3.400"].endswith("；")
    assert verses["5.719"].endswith("；")
    assert "妻子克瑞乌萨、" in verses["2.651"]
    assert "有福的人们，" in verses["1.94"]
    assert "看她的气息、" in verses["5.648"]
    print("[PASS] 2b. Missing punctuation and collision repairs verified.")

    # 4. Proper Names Verification
    for k, v in verses.items():
        assert "特乌克洛斯" not in v, f"特乌克洛斯 in verse {k}"
    for n, d in notes.items():
        assert "特乌克洛斯" not in d["text"], f"特乌克洛斯 in note {n}"
    assert "伊阿索斯之子" in verses["5.843"]
    assert "罗厄图斯" in verses["10.399"] and "罗厄图斯" in verses["10.402"]
    assert "俄耳提癸乌斯" in verses["9.573"] and "俄耳提癸乌斯" in notes[420]["text"]
    assert "廷布里斯" in verses["10.124"]
    assert "拉里得斯" in verses["10.391"] and "廷贝尔" in verses["10.391"]
    assert "廷贝尔" in verses["10.394"] and "拉里得斯" in verses["10.395"]
    assert "库莫多刻亚" in verses["10.225"] and "库莫多刻亚" in notes[445]["text"]
    assert "珀琉斯" in notes[532]["text"]
    assert "奥伦库斯军队" in verses["10.353"]
    assert "奥伦库斯人" in verses["11.318"]
    assert "奥伦库斯人阿克托耳" in verses["12.94"] and "奥伦库斯人阿克托耳" in notes[506]["text"]
    assert "提布尔人雷穆卢斯" in verses["9.360"] and "提布尔" in verses["11.518"] and "提布尔" in verses["11.757"] and "提布尔" in notes[408]["text"]
    assert "西坎尼亚人" in verses["11.317"]
    assert "叙耳提斯" in verses["10.678"] and "叙耳提斯" in notes[466]["text"]
    assert "迈俄尼亚人" in verses["11.758"]
    assert "马尔西人" in verses["10.544"]
    assert "卡庇托利乌姆" in verses["6.837"]
    assert "库克拉得斯群岛" in verses["3.127"]
    assert "优波亚人" in verses["9.710"]
    assert "罗埃特翁的主帅" in verses["12.456"]
    assert "吕耳涅索斯" in verses["10.127"] and "吕耳涅索斯" in verses["12.547"]
    assert "伊阿庇癸风" in verses["8.710"] and "伊阿皮克斯" in verses["12.391"]
    assert "帕提亚人" in verses["12.857"]
    assert "普里韦耳努姆" in verses["11.540"]
    assert "佛里吉亚" in notes[275]["text"]
    assert "基尼鲁斯" in verses["10.186"]
    assert "阿克提乌姆战役（即亚克兴战役）" in notes[25]["text"]
    assert "伊菲革涅亚" in notes[66]["text"]
    print("[PASS] 3. All 25 Proper Name Unifications verified.")

    # 5. Footnotes & Specific Items Verification
    assert "“更大、远更可怖的怪事”" in notes[70]["text"]
    assert verses["3.78"] == "我被带到那里；这最安宁的岛在安全港中"
    assert "指提洛岛（Delos）" in notes[99]["text"]
    assert "大角星位于牧夫座" in notes[56]["text"] and "并记录 Ribbeck 的删疑意见" in notes[56]["text"]
    
    expected_note_94 = "“战神的土地”（terra Mauortia）指色雷斯，传统神话中战神玛尔斯的崇拜中心与居所；吕库尔戈斯（见第 14 行）为曾驱逐酒神并遭严惩的色雷斯暴君。后文（3.49—56）揭示，普里阿摩斯曾秘密将幼子波吕多鲁斯托付给色雷斯国王波吕墨斯托耳与黄金；特洛伊败亡后，国王杀人夺金。欧里庇得斯悲剧《赫卡柏》亦以此事为背景。"
    assert notes[94]["text"] == expected_note_94
    assert notes[95]["text"].startswith("“父神格拉狄乌斯”（Gradivus pater）")
    assert "统译为“三岔路女神”（其他卷音译为“特里维亚”）" in notes[235]["text"]
    assert "柏尔萨建城传说称，" in notes[31]["text"]
    assert "，见塞尔维乌斯（6.211）。" in notes[244]["text"]
    assert "（塞尔维乌斯（6.211））。" not in notes[244]["text"]
    assert "，见塞尔维乌斯（12.120）。" in notes[507]["text"]
    assert "（塞尔维乌斯（12.120））。" not in notes[507]["text"]

    # Verify NO nested parentheses across all 534 notes
    for nid, ndata in notes.items():
        ntext = ndata["text"]
        assert not re.search(r"（[^）]*（[^）]*）", ntext), f"Nested Chinese parens found in note {nid}: {ntext}"
        assert not re.search(r"\([^)]*\([^)]*\)", ntext), f"Nested ASCII parens found in note {nid}: {ntext}"
        assert not re.search(r"（[^）]*\([^)]*\)[^）]*）", ntext), f"Nested mixed parens found in note {nid}: {ntext}"

    # Verify TeX footnote texts directly
    b03_tex = (CONTENT_DIR / "book03_current.tex").read_text(encoding="utf-8")
    b06_tex = (CONTENT_DIR / "book06_current.tex").read_text(encoding="utf-8")
    b12_tex = (CONTENT_DIR / "book12_current.tex").read_text(encoding="utf-8")

    assert ("\\footnote{" + expected_note_94 + "}") in b03_tex, "Note 94 footnote missing in book03_current.tex"
    assert "，见塞尔维乌斯（6.211）。" in b06_tex, "Note 244 clean Servius citation missing in book06_current.tex"
    assert "（塞尔维乌斯（6.211））。" not in b06_tex, "Note 244 nested parens found in book06_current.tex"
    assert "，见塞尔维乌斯（12.120）。" in b12_tex, "Note 507 clean Servius citation missing in book12_current.tex"
    assert "（塞尔维乌斯（12.120））。" not in b12_tex, "Note 507 nested parens found in book12_current.tex"

    print("[PASS] 4. Footnotes & Specific Items verified (authoritative TXT & TeX sources).")

    # 6. Glossary Verification
    g_tex = GLOSSARY_TEX.read_text(encoding="utf-8")
    assert r"\readerglossentry{tropaeum}{纪功标志；胜利纪念物}" in g_tex
    assert r"\readerglossentry{Iuturna / Juturna}{尤图耳娜}" in g_tex
    assert r"\readerglossentry{Palladium}{帕拉斯神像；帕拉狄乌姆}" in g_tex
    assert "帕拉狄乌姆则是与她相连的特洛伊神像。" in g_tex

    g_md = GLOSSARY_MD.read_text(encoding="utf-8")
    assert "**tropaeum　纪功标志；胜利纪念物**" in g_md
    assert "**尤图耳娜 Iuturna / Juturna**" in g_md
    assert "**Palladium　帕拉斯神像；帕拉狄乌姆**" in g_md
    assert "帕拉狄乌姆则是与她相连的特洛伊神像。" in g_md
    print("[PASS] 4b. Glossary (TeX and Markdown) verified.")

    # 7. Map 2 Verification
    svg = MAP_SVG.read_text(encoding="utf-8")
    assert "伊奥尼亚海" in svg
    assert "爱奥尼亚海" not in svg

    pdf_bytes = MAP_PDF.read_bytes()
    assert b"(\x03\x96\x17\x18\x97) Tj" in pdf_bytes or b"(\\003\\226\\027\\030\\227) Tj" in pdf_bytes, "Expected target glyph in MAP_PDF"
    try:
        import pypdf
        pdf_r = pypdf.PdfReader(MAP_PDF)
        pdf_text = pdf_r.pages[0].extract_text()
        assert "伊奥尼亚海" in pdf_text
        assert "爱奥尼亚海" not in pdf_text
    except ImportError:
        pass
    print("[PASS] 4c. Map 2 (SVG and PDF) verified.")

    # 8. All 12 Chapter Files Verification (Full body match)
    full_text = TXT_DRAFT.read_text(encoding="utf-8")
    book_positions = []
    book_names = [BOOK_NAMES[i] for i in range(1, 13)]
    for b_name in book_names:
        header = f"第{b_name}卷\n------------------------------------------------------------------------\n"
        pos = full_text.find(header)
        assert pos != -1, f"Book {b_name} header not found in full text"
        book_positions.append(pos)
    book_positions.append(len(full_text))

    for idx, b_name in enumerate(book_names, 1):
        start = book_positions[idx - 1]
        end = book_positions[idx]
        expected_body = full_text[start:end].rstrip()

        c_path = CHAPTERS_DIR / f"埃涅阿斯纪_第{b_name}卷_附注释.txt"
        assert c_path.exists(), f"Chapter file missing: {c_path}"
        c_text = c_path.read_text(encoding="utf-8")
        assert f"《埃涅阿斯纪》第{b_name}卷" in c_text.splitlines()[0]
        actual_body = "\n".join(c_text.splitlines()[4:])
        assert actual_body == expected_body, f"Book {b_name} body mismatch with authoritative TXT"

    # Specific note checks in chapter files
    c3_text = (CHAPTERS_DIR / "埃涅阿斯纪_第三卷_附注释.txt").read_text(encoding="utf-8")
    assert expected_note_94 in c3_text, "Note 94 missing in Book 3 chapter file"

    c6_text = (CHAPTERS_DIR / "埃涅阿斯纪_第六卷_附注释.txt").read_text(encoding="utf-8")
    assert "，见塞尔维乌斯（6.211）。" in c6_text, "Note 244 clean Servius citation missing in Book 6 chapter file"
    assert "（塞尔维乌斯（6.211））。" not in c6_text, "Note 244 nested parens found in Book 6 chapter file"

    c12_text = (CHAPTERS_DIR / "埃涅阿斯纪_第十二卷_附注释.txt").read_text(encoding="utf-8")
    assert "，见塞尔维乌斯（12.120）。" in c12_text, "Note 507 clean Servius citation missing in Book 12 chapter file"
    assert "（塞尔维乌斯（12.120））。" not in c12_text, "Note 507 nested parens found in Book 12 chapter file"

    print("[PASS] All 12 chapter files deeply verified (exact body match with full authoritative TXT).")

    print("\nALL VERIFICATIONS PASSED CLEANLY!")

if __name__ == "__main__":
    main()
