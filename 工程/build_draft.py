"""Generate a traceable integration draft from v20 and the v17 layout.

The source packages and the copied v17 baseline are read-only inputs. This
script writes only into the sibling 拼合工程_工作稿 directory.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path

from build_matrix import HERE, REVIEW, V20, parse_candidate_books, parse_full_text
from citation_format import render_note_citations


BOOK_NAMES = ["", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二"]
MARKER_RE = re.compile(r"\[注(\d+)\]")
VERSE_RE = re.compile(r"^(\s*\d+  )(.*)$")
NOTE_RE = re.compile(r"^\[注(\d+)\]（第[一二三四五六七八九十]+卷 \d+）")
TEX_LINE_RE = re.compile(r"^\\verseline\{([^}]*)\}\{.*\}$")


def read_json(name: str):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def verse_order(path: Path):
    order = defaultdict(list)
    book = 0
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if re.fullmatch(r"第[一二三四五六七八九十]+卷", line):
            book += 1
        elif match := VERSE_RE.match(line):
            if 1 <= book <= 12:
                number = int(match.group(1).strip())
                order[book].append(f"{book}.{number}")
    return order


def tex_escape(text: str):
    substitutions = {
        "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
        "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
        "^": r"\textasciicircum{}", "~": r"\textasciitilde{}",
    }
    return "".join(substitutions.get(char, char) for char in text)


def poem_to_tex(text: str, notes_by_number: dict[int, dict]):
    chunks = []
    last = 0
    for match in MARKER_RE.finditer(text):
        chunks.append(tex_escape(text[last:match.start()]))
        number = int(match.group(1))
        note = render_note_citations(notes_by_number[number]["text"], tex_escape)
        if notes_by_number[number].get("old_number") == 160:
            note = note.replace("lumina morte resignat", r"\textit{lumina morte resignat}")
        chunks.append(r"\footnote{" + note + "}")
        last = match.end()
    chunks.append(tex_escape(text[last:]))
    return "".join(chunks)


def main():
    base, old_notes = parse_full_text(V20)
    order = verse_order(V20)
    candidate = parse_candidate_books(REVIEW / "05_候选合成正文_未批准")
    body_decisions = read_json("body_overrides.json")
    note_decisions = read_json("note_decisions.json")
    matrix = read_json("写回研究矩阵.json")
    source_by_key = {row["id"]: row["sources"] for row in matrix["body_rows"]}

    body = dict(candidate)
    for key, text in body_decisions["overrides"].items():
        if key not in base:
            raise ValueError(f"Unknown verse override: {key}")
        body[key] = text
    assert set(body) == set(base)

    # Keep original note identities until final reading order is known.
    notes = []
    for old_number, source in old_notes.items():
        if old_number in note_decisions.get("removed_old_notes", []):
            continue
        move = note_decisions["moved_old_notes"].get(str(old_number), {})
        notes.append({
            "id": f"old:{old_number}", "old_number": old_number,
            "book": move.get("book", source["book"]),
            "line": move.get("line", source["line"]),
            "text": note_decisions["updated_old_notes"].get(str(old_number), source["text"]),
        })
    for entry in note_decisions["new_notes"]:
        notes.append({**entry, "old_number": None})
    assert len(notes) == 532

    position = {key: index for book in range(1, 13) for index, key in enumerate(order[book])}
    for note in notes:
        key = f"{note['book']}.{note['line']}"
        if key not in base:
            raise ValueError(f"Missing note anchor: {note['id']} at {key}")
        note["anchor"] = key
    notes.sort(key=lambda item: (
        item["book"], position[item["anchor"]],
        0 if item["old_number"] is not None else 1,
        item["old_number"] if item["old_number"] is not None else 0,
    ))
    for number, note in enumerate(notes, 1):
        note["number"] = number
    notes_by_number = {note["number"]: note for note in notes}
    old_to_new = {note["old_number"]: note["number"] for note in notes if note["old_number"] is not None}
    anchor_to_notes = defaultdict(list)
    for note in notes:
        anchor_to_notes[note["anchor"]].append(note)

    rendered = {}
    seen_markers = Counter()
    for key in base:
        verse = body[key]
        existing = []
        def replace_marker(match):
            old_number = int(match.group(1))
            note = next((item for item in anchor_to_notes[key] if item["old_number"] == old_number), None)
            if note is None:
                return ""
            existing.append(note["number"])
            return f"[注{note['number']}]"
        verse = MARKER_RE.sub(replace_marker, verse)
        for note in anchor_to_notes[key]:
            if note["number"] not in existing:
                verse += f"[注{note['number']}]"
            seen_markers[note["number"]] += 1
        rendered[key] = verse
    assert len(seen_markers) == len(notes)
    assert all(count == 1 for count in seen_markers.values())

    draft = HERE / "拼合工程_工作稿"
    if not draft.exists():
        shutil.copytree(HERE / "v17_制版基底", draft)
    txt_name = "埃涅阿斯纪_复核拼合工作稿_2026-09-27.txt"
    txt_path = draft / "正文与注释权威源" / txt_name
    notes_by_book = defaultdict(list)
    for note in notes:
        notes_by_book[note["book"]].append(note)

    output_lines = []
    book = 0
    in_notes = False
    for line in V20.read_text(encoding="utf-8-sig").splitlines():
        if re.fullmatch(r"第[一二三四五六七八九十]+卷", line):
            book += 1
            in_notes = False
            output_lines.append(line)
            continue
        if in_notes:
            if line == "========================================================================":
                output_lines.extend(["", line])
                in_notes = False
            continue
        if NOTE_RE.match(line):
            for index, note in enumerate(notes_by_book[book]):
                if index:
                    output_lines.append("")
                output_lines.append(
                    f"[注{note['number']}]（第{BOOK_NAMES[book]}卷 {note['line']}）{note['text']}"
                )
            in_notes = True
            continue
        if match := VERSE_RE.match(line):
            if 1 <= book <= 12:
                key = f"{book}.{int(match.group(1).strip())}"
                output_lines.append(match.group(1) + rendered[key])
                continue
        output_lines.append(line)
    text = "\n".join(output_lines) + "\n"
    text = text.replace("v20 审校推进定本 · 2026-09-22", "复核拼合工作稿 · 2026-09-27", 1)
    text = text.replace("全书 527 条注释按 1 至 527", "全书 532 条注释按 1 至 532", 1)
    text = text.replace(
        "诗行编号依 Conte 2019 底本对应关系；正文中的 [注N] 与各卷末注释一一对应。",
        "诗行编号依 Conte 2019 底本对应关系；正文中的 [注N] 与各卷末注释一一对应。\n"
        "注释中“Conte 2019”指 Gian Biagio Conte 编订的2019年《埃涅阿斯纪》（Aeneis）第二版拉丁校勘本；"
        "未另署出处的“校勘记”指该版拉丁正文页下记录传本异文、学者校订及删疑意见的部分。",
        1,
    )
    txt_path.write_text(text, encoding="utf-8")

    tex_count = 0
    for book in range(1, 13):
        path = draft / "制版源文件" / "content" / f"book{book:02d}_current.tex"
        input_lines = path.read_text(encoding="utf-8-sig").splitlines()
        output = []
        index = 0
        for line in input_lines:
            match = TEX_LINE_RE.match(line)
            if not match:
                output.append(line)
                continue
            key = order[book][index]
            mark = match.group(1)
            if mark and int(mark) != int(key.split(".")[1]):
                raise ValueError(f"TeX verse label mismatch: {path}: {mark} vs {key}")
            output.append(r"\verseline{" + mark + "}{" + poem_to_tex(rendered[key], notes_by_number) + "}")
            index += 1
        if index != len(order[book]):
            raise ValueError(f"TeX verse count mismatch: book {book}: {index} vs {len(order[book])}")
        path.write_text("\n".join(output) + "\n", encoding="utf-8")
        tex_count += index

    authority_path = draft / "制版源文件" / "CONTENT_AUTHORITY.json"
    authority = json.loads(authority_path.read_text(encoding="utf-8"))
    authority.update({
        "authority_txt": txt_name, "notes": len(notes), "note_sequence_ok": True,
        "per_book_notes": {str(book): len(notes_by_book[book]) for book in range(1, 13)},
        "release": "2026-09-27-integration-draft", "release_date": "2026-09-27",
    })
    authority_path.write_text(json.dumps(authority, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    with (HERE / "注释新旧编号.tsv").open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file, delimiter="\t")
        writer.writerow(["新注号", "旧注号或新注ID", "卷", "旧锚点", "新锚点", "内容是否改变"])
        for note in notes:
            old = note["old_number"]
            writer.writerow([
                note["number"], old if old is not None else note["id"], note["book"],
                old_notes[old]["line"] if old is not None else "", note["line"],
                "是" if old is None or str(old) in note_decisions["updated_old_notes"] else "否",
            ])
    with (HERE / "工作稿相对v20正文差异.tsv").open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file, delimiter="\t")
        writer.writerow(["卷.行", "v20", "工作稿", "来源索引"])
        for key in base:
            if MARKER_RE.sub("", base[key]) != MARKER_RE.sub("", rendered[key]):
                writer.writerow([key, base[key], rendered[key], "；".join(source_by_key.get(key, []))])

    manifest = draft / "MANIFEST_SHA256_拼合工作稿.txt"
    manifest_lines = []
    for path in sorted(draft.rglob("*")):
        if path.is_file() and path != manifest:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            manifest_lines.append(f"{digest}  ./{path.relative_to(draft).as_posix()}")
    manifest.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")

    print(json.dumps({
        "verses": len(rendered), "tex_verses": tex_count, "notes": len(notes),
        "notes_per_book": {str(book): len(notes_by_book[book]) for book in range(1, 13)},
        "body_diff_from_v20_including_note_renumbering": sum(base[key] != rendered[key] for key in base),
        "body_text_diff_from_v20": sum(MARKER_RE.sub("", base[key]) != MARKER_RE.sub("", rendered[key]) for key in base),
        "manifest_entries": len(manifest_lines),
        "draft": str(draft),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    raise SystemExit("本脚本主流程属于历史合成阶段，会重建旧稿。当前更新请运行 sync_current_sources.py；辅助函数仍可导入。")
