"""Build a source-aware inventory for the Aeneid integration review.

This script only reads the original packages. Its output is a decision queue,
not an approved translation or an instruction to replace whole books.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = Path("E:/埃涅阿斯纪_第4_9_10_11卷逐行复核_二次复审交接包_2026-09-27/埃涅阿斯纪_第4_9_10_11卷逐行复核_二次复审交接包_2026-09-27")
REVIEW = ROOT / "00_下一轮AI复核意见_请先读_2026-09-27"
RECENT = ROOT / "00_00_最新续接任务_请先读_2026-09-27"
FOUR = ROOT / "00_00_00_第四九十十一卷逐行复核_2026-09-27"
FINAL = ROOT / "00_00_00_00_四卷二次复审_最新裁决_2026-09-27"
V17 = HERE / "v17_制版基底" / "正文与注释权威源" / "埃涅阿斯纪_v17_审校推进定本_2026-09-21.txt"
V20 = HERE / "v20_正式基准.txt"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def parse_full_text(path: Path):
    verses = {}
    notes = {}
    book = 0
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if re.fullmatch(r"第[一二三四五六七八九十]+卷", line):
            book += 1
            continue
        verse = re.match(r"^\s*(\d+)  (.+)$", line)
        if verse and 1 <= book <= 12:
            key = f"{book}.{verse.group(1)}"
            if key in verses:
                raise ValueError(f"Duplicate verse {key}: {path}")
            verses[key] = verse.group(2)
        note = re.match(r"^\[注(\d+)\]（第([一二三四五六七八九十]+)卷 (\d+)）(.*)$", line)
        if note:
            number = int(note.group(1))
            if number in notes:
                raise ValueError(f"Duplicate note {number}: {path}")
            notes[number] = {"book": book, "line": int(note.group(3)), "text": note.group(4)}
    return verses, notes


def parse_candidate_books(path: Path):
    verses = {}
    for book_file in path.glob("第*卷_当前建议合成文本.txt"):
        for line in book_file.read_text(encoding="utf-8-sig").splitlines():
            match = re.fullmatch(r"(\d+\.\d+)\t(.*)", line)
            if not match:
                raise ValueError(f"Malformed candidate line: {book_file}: {line[:80]}")
            verses[match.group(1)] = match.group(2)
    return verses


def expand_range(text: str):
    roman = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6,
             "VII": 7, "VIII": 8, "IX": 9, "X": 10, "XI": 11, "XII": 12}
    text = re.sub(r"\b(XII|XI|X|IX|VIII|VII|VI|V|IV|III|II|I)\.",
                  lambda match: f"{roman[match.group(1)]}.", text)
    result = []
    for part in re.split(r"[、,，]", text):
        part = part.strip()
        match = re.fullmatch(r"(\d+)\.(\d+)(?:[—–-](?:(\d+)\.)?(\d+))?", part)
        if not match:
            raise ValueError(f"Unrecognized verse location: {part}")
        book, start = int(match.group(1)), int(match.group(2))
        end_book = int(match.group(3) or book)
        end = int(match.group(4) or start)
        if book != end_book or end < start:
            raise ValueError(f"Unexpected range: {part}")
        result.extend(f"{book}.{line}" for line in range(start, end + 1))
    return result


def main():
    v17, v17_notes = parse_full_text(V17)
    v20, v20_notes = parse_full_text(V20)
    candidate = parse_candidate_books(REVIEW / "05_候选合成正文_未批准")
    assert len(v17) == len(v20) == len(candidate) == 9888
    assert len(v17_notes) == len(v20_notes) == 527
    assert set(v17) == set(v20) == set(candidate)

    sources = defaultdict(list)
    for key in v20:
        if v17[key] != v20[key]:
            sources[key].append("v17→v20正式基准差异")
        if v20[key] != candidate[key]:
            sources[key].append("9月27日未批准合成正文差异")

    # The local structured data generated the packaged 124-place report.
    review_data = read_json(HERE.parent / "final_review_data.json")
    assert len(review_data["rows"]) == 124
    for entry in review_data["rows"]:
        key = entry["id"]
        assert entry["v20"] == re.sub(r"\[注\d+\]", "", v20[key]) or entry["v20"] == v20[key], key
        sources[key].append(f"124处复核:{entry['kind']}")
    for entry in review_data["extra"]:
        sources[entry["id"]].append(f"124处联动补充:{entry['kind']}")

    quick_early = read_json(REVIEW / "02_各卷新增候选" / "第一至六卷_候选登记.json")
    for entry in quick_early:
        for key in expand_range(entry["lines"]):
            sources[key].append(f"一至六卷快速登记:{entry['number']:03d}")

    quick_late_text = (REVIEW / "02_各卷新增候选" / "第七至十二卷_候选登记.md").read_text(encoding="utf-8")
    quick_late = re.findall(r"^## (\d+)｜([^｜]+)｜", quick_late_text, re.M)
    assert len(quick_late) == 11
    for number, location in quick_late:
        for key in expand_range(location):
            sources[key].append(f"七至十二卷快速登记:{int(number):03d}")

    close_read = read_json(REVIEW / "03_第一二六卷逐行复核" / "候选明细.json")
    assert len(close_read) == 19
    for number, entry in enumerate(close_read, 1):
        for key in entry["ids"]:
            sources[key].append(f"一二六卷逐行复核:{number:02d}:{entry['level']}")

    four_audit = read_json(FOUR / "06_本轮新增修正_6组.json")
    for key, entry in four_audit["line_items"].items():
        sources[key].append(f"四卷逐行审计:{entry['group']}")
    latest = read_json(FINAL / "03_最新续接状态.json")["latest_decisions"]
    for location, decision in latest.items():
        for key in expand_range(location):
            sources[key].append(f"四卷二次复审:{decision['level']}")

    for key in ["3.484", "6.188", "6.189", "10.791", "10.547", "10.548", "1.192", "11.538", "12.950"]:
        sources[key].append("最新续接再裁决/作者口径")
    for key in ["12.943", "12.944", "12.945", "12.946", "12.947", "12.948", "12.949", "12.950"]:
        sources[key].append("第十二卷结尾专题")

    decisions_path = HERE / "body_overrides.json"
    if decisions_path.exists():
        for key in read_json(decisions_path).get("confirmed_decisions", {}):
            if key not in v20:
                raise ValueError(f"Unknown confirmed verse: {key}")
            sources.setdefault(key, [])
    note_status = read_json(REVIEW / "04_全书注释复核" / "注释逐条检查状态.json")
    note_rows = note_status["逐条"]
    assert len(note_rows) == 527
    output = {
        "source_roots": {"v17": str(V17), "v20": str(V20), "review": str(ROOT)},
        "summary": {
            "verse_lines": len(v20),
            "v17_to_v20_changed_lines": sum(v17[key] != v20[key] for key in v20),
            "v20_to_unapproved_candidate_changed_lines": sum(v20[key] != candidate[key] for key in v20),
            "close_read_groups": len(close_read),
            "close_read_unique_lines": len({key for entry in close_read for key in entry["ids"]}),
            "nonoverlapping_124_plus_close_read_lines": len({entry["id"] for entry in review_data["rows"]}
                                                        | {key for entry in close_read for key in entry["ids"]}),
            "body_work_pool_lines": len(sources),
            "existing_notes": len(v20_notes),
            "nondefault_note_states": sum("通读保留/本轮无行动建议" not in row["本轮状态"] for row in note_rows),
        },
        "body_rows": [
            {"id": key, "v17": v17[key], "v20": v20[key], "unapproved_candidate": candidate[key],
             "sources": sources[key], "decision": "待逐项定稿", "final_text": None}
            for key in sorted(sources, key=lambda value: tuple(map(int, value.split("."))))
        ],
        "note_rows": [
            {"old_number": row["注号"], "book": row["卷"], "old_anchor": row["行"],
             "status": row["本轮状态"], "v20_text": v20_notes[row["注号"]]["text"],
             "final_anchor": None, "final_text": None}
            for row in note_rows if "通读保留/本轮无行动建议" not in row["本轮状态"]
        ],
        "new_note_candidates": ["1.509-511", "4.681", "7.119", "11.172", "11.565"],
    }
    decisions_path = HERE / "body_overrides.json"
    if decisions_path.exists():
        decisions = read_json(decisions_path)
        for row in output["body_rows"]:
            confirmation = decisions.get("confirmed_decisions", {}).get(row["id"])
            if confirmation:
                row["decision"] = confirmation["status"]
                row["final_text"] = decisions["overrides"][row["id"]]
                row["sources"].append(confirmation["date"] + ":" + confirmation["source"])
    (HERE / "写回研究矩阵.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (HERE / "正文工作池.tsv").open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["id", "v17", "v20", "unapproved_candidate", "sources", "decision"], delimiter="\t")
        writer.writeheader()
        for row in output["body_rows"]:
            writer.writerow({
                key: "；".join(row["sources"]) if key == "sources" else row[key]
                for key in writer.fieldnames
            })
    print(json.dumps(output["summary"], ensure_ascii=False, indent=2))
    print("source categories:", dict(Counter(part.split(":")[0] for values in sources.values() for part in values)))


if __name__ == "__main__":
    main()
