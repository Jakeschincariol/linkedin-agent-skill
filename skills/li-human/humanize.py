#!/usr/bin/env python3
"""
humanize.py - strip the machine fingerprint out of a draft.

Three passes, in this order:

  1. INVISIBLE   delete or normalise the characters a human keyboard never
                 produces: zero-width joiners, word joiners, soft hyphens,
                 BOMs, Unicode tag characters, non-breaking and narrow spaces.
                 These survive copy-paste and are the most mechanical tell in
                 any generated text.
  2. TYPOGRAPHIC em dash -> comma, en dash -> hyphen, curly quotes -> straight,
                 ellipsis -> three dots, bullet -> hyphen.
  3. LEXICAL     replace the slop lexicon in slop.json with plain words,
                 preserving capitalisation and leaving URLs untouched.

Arabic: slop_ar.json is merged in when it sits next to this file. In Arabic
text the em dash becomes the Arabic comma (،), stray Latin commas between
Arabic words are converted, and bidi marks (LRM/RLM/ALM) are kept because
mixed Arabic-English lines need them. Arabic entries whose replace is null are
flagged, not rewritten - agreement makes blind substitution ungrammatical.

Structural tells (rule-of-three, "not just X, it's Y", hashtag walls) are
REPORTED, never auto-rewritten - rewriting a sentence's shape needs judgement,
so that is the model's job, not a regex's.

Usage
  python3 humanize.py draft.txt
  python3 humanize.py draft.txt --report
  pbpaste | python3 humanize.py - --report
  python3 humanize.py draft.txt --json
  python3 humanize.py draft.txt -o clean.txt
"""

import argparse
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
LEX = os.path.join(HERE, "slop.json")
LEX_AR = os.path.join(HERE, "slop_ar.json")

URL_RE = re.compile(r"https?://\S+|www\.\S+|\S+@\S+\.\S+")
SENT_RE = re.compile(r"[^.!?؟\n]+[.!?؟]*")

AR_LETTER = "\u0621-\u064A\u066E-\u06D3"
AR_RE = re.compile(f"[{AR_LETTER}]")
TASHKEEL = "[\u064B-\u0652\u0670\u0640]*"
BIDI_MARKS = {0x200E, 0x200F, 0x061C}


def is_arabic(text):
    return bool(AR_RE.search(text))


def load_lexicon(path=LEX):
    with open(path, encoding="utf-8") as fh:
        lex = json.load(fh)
    if os.path.exists(LEX_AR):
        with open(LEX_AR, encoding="utf-8") as fh:
            ar = json.load(fh)
        for key in ("words", "phrases", "structures"):
            lex[key] = lex[key] + ar.get(key, [])
    return lex


def lex_pattern(find):
    """English: word-bounded, case-insensitive. Arabic: ignores tashkeel and
    alef hamza forms, and captures an optional leading و/ف as group 1."""
    if not is_arabic(find):
        return re.compile(r"()\b" + re.escape(find).replace(r"\ ", r"\s+") + r"\b",
                          re.IGNORECASE)
    parts = []
    for ch in find:
        if ch == " ":
            parts.append(r"\s+")
        elif ch in "اأإآ":
            parts.append("[اأإآ]" + TASHKEEL)
        else:
            parts.append(re.escape(ch) + TASHKEEL)
    return re.compile(r"(?<!\w)([وف]?)" + "".join(parts) + r"(?!\w)")


def _cp(spec):
    """'U+200B' -> '\\u200b';  'U+E0000-U+E007F' -> (start, end)."""
    if "-" in spec:
        a, b = spec.split("-")
        return (int(a[2:], 16), int(b[2:], 16))
    return int(spec[2:], 16)


def protect_urls(text):
    """Swap URLs for placeholders so no pass rewrites inside a link."""
    found = []

    def stash(m):
        found.append(m.group(0))
        return f"\x00URL{len(found) - 1}\x00"

    return URL_RE.sub(stash, text), found


def restore_urls(text, found):
    for i, url in enumerate(found):
        text = text.replace(f"\x00URL{i}\x00", url)
    return text


def pass_invisible(text, lex):
    """Delete or space-normalise invisible characters. Returns (text, hits)."""
    hits = []
    keep = BIDI_MARKS if is_arabic(text) else set()
    for entry in lex["invisible"]:
        cp = _cp(entry["cp"])
        if cp in keep:
            continue
        if isinstance(cp, tuple):
            pattern = "[" + re.escape(chr(cp[0])) + "-" + re.escape(chr(cp[1])) + "]"
        else:
            pattern = re.escape(chr(cp))
        n = len(re.findall(pattern, text))
        if n:
            hits.append({"name": entry["cp"] + " " + entry["name"], "count": n,
                         "action": entry["action"]})
            text = re.sub(pattern, "" if entry["action"] == "delete" else " ", text)
    # Any remaining Cf (format) character is invisible by definition.
    drop = lambda c: unicodedata.category(c) == "Cf" and ord(c) not in keep
    stray = [c for c in text if drop(c)]
    if stray:
        hits.append({"name": "other invisible format chars", "count": len(stray),
                     "action": "delete"})
        text = "".join(c for c in text if not drop(c))
    return text, hits


def _comma_for(text, start, end):
    """Arabic comma if the nearest letter on either side is Arabic, so
    "Claude Code — وهو" still gets ، inside an Arabic sentence."""
    before = next((c for c in reversed(text[max(0, start - 40):start]) if c.isalpha()), "")
    after = next((c for c in text[end:end + 40] if c.isalpha()), "")
    return "، " if AR_RE.match(before) or AR_RE.match(after) else ", "


def pass_typographic(text, lex):
    hits = []
    for entry in lex["typographic"]:
        ch = entry["from"]
        n = text.count(ch)
        if not n:
            continue
        to = "، / ," if ch in "—–" and is_arabic(text) else entry["to"].strip() or "(space)"
        hits.append({"name": f"{ch} {entry['name']}", "count": n, "to": to})
        if ch == "—":
            # " word — word " and "word—word" both collapse to a comma + space.
            text = re.sub(r"\s*—\s*", lambda m: _comma_for(m.string, m.start(), m.end()), text)
        elif ch == "–":
            text = re.sub(r"\s*–\s*(?=\d)", "-", text)      # 5–10  -> 5-10
            text = re.sub(r"\s+–\s+", lambda m: _comma_for(m.string, m.start(), m.end()), text)
            text = text.replace("–", "-")
        else:
            text = text.replace(ch, entry["to"])
    # A Latin comma between Arabic words: Arabic keyboards type ،.
    latin = re.compile(rf"(?<=[{AR_LETTER}])[ \t]*,[ \t]*(?=[{AR_LETTER}])")
    n = len(latin.findall(text))
    if n:
        hits.append({"name": ", LATIN COMMA IN ARABIC", "count": n, "to": "،"})
        text = latin.sub("، ", text)
    # A comma inserted before existing punctuation reads wrong.
    text = re.sub(r"[,،]\s*([,،.;؛:!?؟])", r"\1", text)
    text = re.sub(r"[,،]\s*\n", "\n", text)
    return text, hits


def _match_case(src, repl):
    if not repl:
        return repl
    if src.isupper() and len(src) > 1:
        return repl.upper()
    if src[0].isupper():
        return repl[0].upper() + repl[1:]
    return repl


def _sub_entry(m, replace):
    prefix, word = m.group(1), m.group(0)[len(m.group(1)):]
    if not replace and prefix:
        return prefix + "\x01"          # و/ف re-attaches to the next word
    if not replace and is_arabic(word):
        return "\x02"                   # marks a deletion, see pass_lexical
    return prefix + _match_case(word, replace)


def pass_lexical(text, lex):
    """Replace slop words and phrases. Longest first so phrases win.
    Entries with replace null are flagged, not rewritten. Returns
    (text, hits, flagged)."""
    hits, flagged, taken = [], [], []
    entries = sorted(lex["phrases"] + lex["words"],
                     key=lambda e: len(e["find"]), reverse=True)
    for entry in entries:
        if entry["replace"] is None:
            continue
        pattern = lex_pattern(entry["find"])
        found = pattern.findall(text)
        if not found:
            continue
        hits.append({"find": entry["find"], "replace": entry["replace"] or "(deleted)",
                     "count": len(found), "family": entry["family"]})
        text = pattern.sub(lambda m: _sub_entry(m, entry["replace"]), text)
    text = re.sub("\x01\\s*", "", text)
    text = re.sub("(?m)^\x02[ \t]*", "", text)
    text = text.replace("\x02", "")
    # Flag-only entries, after rewriting so spans are final. No double counts.
    for entry in entries:
        if entry["replace"] is not None:
            continue
        spans = [m.span() for m in lex_pattern(entry["find"]).finditer(text)
                 if not any(a < m.end() and m.start() < b for a, b in taken)]
        if spans:
            taken += spans
            flagged.append({"find": entry["find"], "count": len(spans),
                            "family": entry["family"]})
    # Clean up after deletions.
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"(?m)^[ \t]*([,.;:،؛])\s*", "", text)
    text = re.sub(r"([.!?؟])[ \t]*[,،][ \t]*", r"\1 ", text)
    text = re.sub(r"\s+([,.;:!?،؛؟])", r"\1", text)
    text = re.sub(r"(?m)^[ \t]+$", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # An em dash that became a comma, followed by a sentence connective, leaves
    # a splice ("is important, also, it's proof"). Promote it to a full stop.
    text = re.sub(r",\s*(also|so|still|basically|in the end)\s*,\s*",
                  lambda m: ". " + m.group(1)[0].upper() + m.group(1)[1:] + ", ", text)
    return text, hits, flagged


def scan_structures(text, lex):
    flags = []
    for s in lex["structures"]:
        try:
            pattern = re.compile(s["regex"], re.MULTILINE)
        except re.error:
            continue
        found = pattern.findall(text)
        if found:
            flags.append({"name": s["name"], "count": len(found), "fix": s["fix"]})
    # Sentence-length uniformity is structural too.
    lens = [len(s.split()) for s in SENT_RE.findall(text) if len(s.split()) > 2]
    if len(lens) >= 4:
        mean = sum(lens) / len(lens)
        var = sum((n - mean) ** 2 for n in lens) / len(lens)
        cv = (var ** 0.5) / mean if mean else 0
        if cv < 0.35:
            flags.append({
                "name": f"Uniform sentence length (variation {cv:.2f})",
                "count": len(lens),
                "fix": "Break one sentence in half. Let another run long. Machines write even.",
            })
    return flags


def humanize(text, lex):
    text, urls = protect_urls(text)
    text, inv = pass_invisible(text, lex)
    text, typo = pass_typographic(text, lex)
    text, lexi, flagged = pass_lexical(text, lex)
    text = restore_urls(text, urls)
    return text.strip() + "\n", {
        "invisible": inv,
        "typographic": typo,
        "lexical": lexi,
        "flagged": flagged,
        "structures": scan_structures(text, lex),
    }


def render_report(report, out=sys.stderr):
    def head(title):
        print(f"\n{title}\n" + "-" * len(title), file=out)

    total = sum(h["count"] for h in report["invisible"]) \
        + sum(h["count"] for h in report["typographic"]) \
        + sum(h["count"] for h in report["lexical"])

    head("HUMANIZE REPORT")
    print(f"{total} machine artefacts removed, "
          f"{len(report['structures'])} structural tells and "
          f"{len(report['flagged'])} stock phrases flagged for rewrite", file=out)

    if report["invisible"]:
        head("1. INVISIBLE CHARACTERS")
        for h in report["invisible"]:
            print(f"  {h['count']:>3}x  {h['name']}  -> {h['action']}", file=out)
    if report["typographic"]:
        head("2. TYPOGRAPHY")
        for h in report["typographic"]:
            print(f"  {h['count']:>3}x  {h['name']}  -> {h['to']}", file=out)
    if report["lexical"]:
        head("3. SLOP LEXICON")
        for h in report["lexical"]:
            print(f"  {h['count']:>3}x  {h['find']}  -> {h['replace']}   [{h['family']}]", file=out)
    if report["flagged"]:
        head("4. STOCK PHRASES  (not auto-fixed - rewrite these yourself)")
        for h in report["flagged"]:
            print(f"  {h['count']:>3}x  {h['find']}   [{h['family']}]", file=out)
    if report["structures"]:
        head("5. STRUCTURAL TELLS  (not auto-fixed - rewrite these yourself)")
        for h in report["structures"]:
            print(f"  {h['count']:>3}x  {h['name']}\n        {h['fix']}", file=out)
    if not any(report.values()):
        head("CLEAN")
        print("  Nothing to strip.", file=out)
    print("", file=out)


def main():
    ap = argparse.ArgumentParser(description="Strip the machine fingerprint out of a draft.")
    ap.add_argument("input", nargs="?", default="-", help="file, or - for stdin")
    ap.add_argument("-o", "--out", help="write cleaned text here instead of stdout")
    ap.add_argument("--report", action="store_true", help="print what changed, to stderr")
    ap.add_argument("--json", action="store_true", help="emit {text, report} as JSON")
    ap.add_argument("--lexicon", default=LEX, help="path to slop.json")
    args = ap.parse_args()

    raw = sys.stdin.read() if args.input == "-" else open(args.input, encoding="utf-8").read()
    lex = load_lexicon(args.lexicon)
    clean, report = humanize(raw, lex)

    if args.json:
        print(json.dumps({"text": clean, "report": report}, indent=2, ensure_ascii=False))
        return
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(clean)
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(clean)
    if args.report:
        render_report(report)


if __name__ == "__main__":
    main()
