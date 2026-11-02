#!/usr/bin/env python3
"""Prepend cover.pdf to a XeLaTeX body PDF without rendering either PDF.

The body PDF's metadata, outlines/bookmarks, links, and page objects are cloned;
the supplied cover page is inserted as the first PDF page. No header, page number,
line, scaling, or other LaTeX page style can be overlaid on the cover.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from pypdf import PdfReader, PdfWriter


def merge(cover_path: Path, body_path: Path, output_path: Path) -> None:
    cover = PdfReader(str(cover_path))
    body = PdfReader(str(body_path))
    if len(cover.pages) < 1:
        raise ValueError(f"封面 PDF 没有页面：{cover_path}")

    writer = PdfWriter()
    writer.clone_document_from_reader(body)
    writer.insert_page(cover.pages[0], 0)

    # Inserting a cover shifts every body page by one. pypdf updates page objects,
    # links and outline destinations, but the PDF /PageLabels number tree must be
    # shifted explicitly or viewers label the cover as roman page i and the last
    # body page one number too high. Preserve the body label rules and give the
    # cover a nonnumeric label.
    from pypdf.generic import ArrayObject, DictionaryObject, NameObject, NumberObject, TextStringObject
    page_labels = writer._root_object.get('/PageLabels')
    if page_labels is not None:
        page_labels = page_labels.get_object()
        nums = page_labels.get('/Nums')
        if nums is not None:
            shifted = ArrayObject()
            cover_label = DictionaryObject()
            cover_label[NameObject('/P')] = TextStringObject('封面')
            shifted.extend([NumberObject(0), cover_label])
            for i in range(0, len(nums), 2):
                shifted.extend([NumberObject(int(nums[i]) + 1), nums[i + 1]])
            page_labels[NameObject('/Nums')] = shifted

    # Imported HTML links and pypdf.add_uri defaults can carry a visible 2pt border.
    # Preserve destinations and clickable areas, and explicitly make every Link borderless.
    for page in writer.pages:
        for ref in page.get('/Annots', []):
            annotation = ref.get_object()
            if annotation.get('/Subtype') == '/Link':
                annotation[NameObject('/Border')] = ArrayObject([NumberObject(0)] * 3)
                annotation[NameObject('/BS')] = DictionaryObject({
                    NameObject('/W'): NumberObject(0), NameObject('/S'): NameObject('/S')})

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as fh:
        writer.write(fh)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="原样拼接封面 PDF 与正文 PDF")
    parser.add_argument("cover", nargs="?", default="cover.pdf")
    parser.add_argument("body", nargs="?", default="main_body.pdf")
    parser.add_argument("output", nargs="?", default="main.pdf")
    args = parser.parse_args()
    merge(Path(args.cover), Path(args.body), Path(args.output))
    print(f"完成：{Path(args.output).resolve()}")
