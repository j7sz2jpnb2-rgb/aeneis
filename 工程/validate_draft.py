"""Independently compare the generated TXT, TeX, and authority metadata."""

from __future__ import annotations

import json
import re
from collections import Counter

from build_matrix import HERE, parse_full_text
from build_draft import MARKER_RE, TEX_LINE_RE, verse_order


DRAFT = HERE / "拼合工程_工作稿"
TXT = DRAFT / "正文与注释权威源" / "埃涅阿斯纪_最新全文_附注释_20261006.txt"
TEX = DRAFT / "制版源文件" / "content"


def brace_argument(text: str, opening: int):
    if text[opening] != "{":
        raise ValueError("Expected brace")
    depth = 1
    index = opening + 1
    while depth:
        if index >= len(text):
            raise ValueError("Unbalanced TeX brace")
        if text[index] == "{" and (index == 0 or text[index - 1] != "\\"):
            depth += 1
        elif text[index] == "}" and (index == 0 or text[index - 1] != "\\"):
            depth -= 1
        index += 1
    return text[opening + 1:index - 1], index


def plain_tex(text: str):
    text = re.sub(r"\\textit\{([^{}]*)\}", r"\1", text)
    text = text.replace(r"\textbackslash{}", "\\")
    text = text.replace(r"\textasciicircum{}", "^").replace(r"\textasciitilde{}", "~")
    for char in "&%$#_{}":
        text = text.replace("\\" + char, char)
    if re.search(r"\\[A-Za-z]+", text):
        raise ValueError(f"Unexpected TeX command in text: {text[:120]}")
    return text


def main():
    verses, notes = parse_full_text(TXT)
    order = verse_order(TXT)
    assert len(verses) == 9888
    assert len(notes) == 534
    assert sorted(notes) == list(range(1, 535))

    markers = Counter()
    for book in range(1, 13):
        for key in order[book]:
            for value in MARKER_RE.findall(verses[key]):
                number = int(value)
                markers[number] += 1
                assert (notes[number]["book"], notes[number]["line"]) == (
                    book, int(key.split(".")[1])
                ), (key, number)
    assert markers == Counter({number: 1 for number in notes})

    actual_footnote = 0
    tex_lines = 0
    for book in range(1, 13):
        path = TEX / f"book{book:02d}_current.tex"
        index = 0
        for line in path.read_text(encoding="utf-8").splitlines():
            match = TEX_LINE_RE.match(line)
            if not match:
                continue
            key = order[book][index]
            index += 1
            tex_lines += 1
            if match.group(1):
                assert int(match.group(1)) == int(key.split(".")[1]), key
            body = line.split("}{", 1)[1][:-1]
            rebuilt = []
            cursor = 0
            while True:
                start = body.find(r"\footnote{", cursor)
                if start == -1:
                    rebuilt.append(plain_tex(body[cursor:]))
                    break
                rebuilt.append(plain_tex(body[cursor:start]))
                argument, cursor = brace_argument(body, start + len(r"\footnote"))
                actual_footnote += 1
                assert plain_tex(argument) == notes[actual_footnote]["text"], (
                    key, actual_footnote, argument[:100]
                )
                rebuilt.append(f"[注{actual_footnote}]")
            assert "".join(rebuilt) == verses[key], (key, "".join(rebuilt), verses[key])
        assert index == len(order[book]), (book, index, len(order[book]))
    assert tex_lines == 9888
    assert actual_footnote == 534

    authority = json.loads((DRAFT / "制版源文件" / "CONTENT_AUTHORITY.json").read_text(encoding="utf-8"))
    assert authority["verse_lines"] == tex_lines
    assert authority["notes"] == actual_footnote
    assert authority["authority_txt"] == TXT.name
    for book in range(1, 13):
        assert authority["per_book_verse_lines"][str(book)] == len(order[book])
        assert authority["per_book_notes"][str(book)] == sum(note["book"] == book for note in notes.values())

    print(json.dumps({
        "verse_lines": tex_lines,
        "footnotes": actual_footnote,
        "continuous_numbers": True,
        "each_anchor_matches_note": True,
        "txt_matches_tex": True,
        "authority_matches": True,
        "inline_markers": [key for book in range(1, 13) for key in order[book]
                           if re.search(r"\[注\d+\].", verses[key])],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
