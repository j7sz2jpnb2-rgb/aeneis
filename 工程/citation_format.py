"""Render agreed citation links inside notes; authoritative TXT remains plain text."""
from pathlib import Path
import json
RULES = json.loads((Path(__file__).with_name('footnote_citation_links.json')).read_text(encoding='utf-8'))['rules']
def render_note_citations(text, escape):
    rendered = escape(text)
    for rule in RULES:
        label = rule['label']
        if label not in text:
            continue
        assert text.count(label) == 1, f'Citation label repeated: {label}'
        target = escape(label)
        value = r'\textit{' + target + '}' if rule.get('italic') else target
        if rule.get('url'):
            url = rule['url'].replace('%', r'\%').replace('#', r'\#').replace('&', r'\&')
            value = r'\href{' + url + '}{' + value + '}'
        rendered = rendered.replace(target, value, 1)
    return rendered
