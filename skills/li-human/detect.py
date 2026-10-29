#!/usr/bin/env python3
"""
detect.py - a five-check panel that scores how machine-written a draft looks.

What this is:  five local heuristics modelled on the signals public AI
detectors actually measure - sentence-length variation, concreteness, stock
vocabulary, typographic fingerprint, and voice. Every score is computed on
your machine from the text alone. Nothing is uploaded.

What this is NOT:  GPTZero, Originality, Copyleaks, Winston or Turnitin.
It does not call their APIs and it cannot promise their verdict. It catches
the things they all key on, which is why fixing them tends to move their
numbers too - but the only honest claim is the one on this line.

Arabic: words, sentences (؟), Arabic-Indic digits, a short list of Arabic
pronouns and slop_ar.json are understood. Arabic has no contractions and no
capital letters, so VOICE drops the contraction term and SPECIFICITY counts
only numbers and Latin names, against a lower bar. Treat Arabic scores as a
rougher signal than English ones.

Each check returns a HUMAN score from 0 to 100. Higher is better.

Usage
  python3 detect.py draft.txt
  pbpaste | python3 detect.py -
  python3 detect.py draft.txt --json
  python3 detect.py before.txt after.txt      # compare two drafts
"""

import argparse
import json
import os
import re
import statistics
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
LEX = os.path.join(HERE, "slop.json")
LEX_AR = os.path.join(HERE, "slop_ar.json")

AR_LETTER = "\u0621-\u064A\u066E-\u06D3"
AR_RE = re.compile(f"[{AR_LETTER}]")
TASHKEEL = "[\u064B-\u0652\u0670\u0640]*"
BIDI_MARKS = {0x200E, 0x200F, 0x061C}

SENT_RE = re.compile(r"[^.!?؟\n]+[.!?؟]*")
WORD_RE = re.compile(f"[A-Za-z']+|[{AR_LETTER}\u064B-\u0652\u0670]+")
AR_WORD_RE = re.compile(f"[{AR_LETTER}]+")
CONTRACTIONS = re.compile(r"\b\w+'(?:s|t|re|ve|ll|d|m)\b", re.IGNORECASE)
PRONOUNS = re.compile(r"\b(i|me|my|mine|we|us|our|you|your)\b"
                      r"|(?<!\w)[وف]?(?:أنا|نحن|أنت|أنتم|لي|لنا|عندي|عندنا|معي|معنا|كنت|كنا)(?!\w)",
                      re.IGNORECASE)
NUMBERS = re.compile(r"\b\d[\d,.]*%?\b|\$\d|[\u0660-\u0669\u06F0-\u06F9]+")
LATIN_COMMA_AR = re.compile(f"(?<=[{AR_LETTER}])[ \t]*,[ \t]*(?=[{AR_LETTER}])")
PROPER = re.compile(r"(?<![.!?]\s)(?<!^)\b[A-Z][a-z]{2,}\b", re.MULTILINE)


def load_lexicon(path):
    lex = json.load(open(path, encoding="utf-8"))
    if os.path.exists(LEX_AR):
        ar = json.load(open(LEX_AR, encoding="utf-8"))
        for key in ("words", "phrases", "structures"):
            lex[key] = lex[key] + ar.get(key, [])
    return lex


def lex_pattern(find):
    """Same matching as humanize.py: Arabic ignores tashkeel, alef hamza forms
    and a leading و/ف."""
    if not AR_RE.search(find):
        return re.compile(r"\b" + re.escape(find).replace(r"\ ", r"\s+") + r"\b",
                          re.IGNORECASE)
    parts = []
    for ch in find:
        if ch == " ":
            parts.append(r"\s+")
        elif ch in "اأإآ":
            parts.append("[اأإآ]" + TASHKEEL)
        else:
            parts.append(re.escape(ch) + TASHKEEL)
    return re.compile(r"(?<!\w)[وف]?" + "".join(parts) + r"(?!\w)")


def arabic_dominant(text):
    ar = len(AR_WORD_RE.findall(text))
    return ar > len(re.findall(r"[A-Za-z]+", text))


def clamp(n):
    return max(0.0, min(100.0, n))


def scale(value, human, machine):
    """Map value onto 0-100 where `human` -> 100 and `machine` -> 0."""
    if human == machine:
        return 50.0
    return clamp((value - machine) / (human - machine) * 100)


def sentences(text):
    return [s.strip() for s in SENT_RE.findall(text) if len(s.split()) > 2]


def words(text):
    return WORD_RE.findall(text)


def check_burstiness(text):
    """Humans vary sentence length hard. Models write even."""
    lens = [len(s.split()) for s in sentences(text)]
    if len(lens) < 4:
        return 50.0, "too short to judge"
    mean = statistics.mean(lens)
    cv = statistics.pstdev(lens) / mean if mean else 0
    score = scale(cv, human=0.70, machine=0.22)
    return score, f"variation {cv:.2f} across {len(lens)} sentences (want 0.55+)"


def check_specificity(text):
    """Numbers, names and concrete nouns. Slop is abstract."""
    w = words(text)
    if len(w) < 25:
        return 50.0, "too short to judge"
    per100 = 100 / len(w)
    hits = len(NUMBERS.findall(text)) + len(set(PROPER.findall(text)))
    density = hits * per100
    # No capitals in Arabic, so names go uncounted: lower the bar.
    human = 3.0 if arabic_dominant(text) else 6.0
    score = scale(density, human=human, machine=0.5)
    return score, f"{hits} concrete markers, {density:.1f} per 100 words (want 4+)"


def check_slop(text, lex):
    """Stock vocabulary density against the lexicon."""
    w = words(text)
    if not w:
        return 50.0, "empty"
    hits, found, taken = 0, [], []
    # Longest first, no overlapping spans, so a phrase is not counted twice.
    for entry in sorted(lex["words"] + lex["phrases"], key=lambda e: len(e["find"]), reverse=True):
        spans = [m.span() for m in lex_pattern(entry["find"]).finditer(text)
                 if not any(a < m.end() and m.start() < b for a, b in taken)]
        if spans:
            taken += spans
            hits += len(spans)
            found.append(entry["find"])
    density = hits * 100 / len(w)
    score = scale(density, human=0.0, machine=4.0)
    detail = f"{hits} stock terms, {density:.1f} per 100 words"
    if found:
        detail += " (" + ", ".join(sorted(found)[:4]) + (", ..." if len(found) > 4 else "") + ")"
    return score, detail


def check_fingerprint(text):
    """Characters a phone keyboard does not produce."""
    # Bidi marks are legitimate in mixed Arabic-English text.
    keep = BIDI_MARKS if AR_RE.search(text) else set()
    invisible = sum(1 for c in text if unicodedata.category(c) == "Cf" and ord(c) not in keep)
    em = text.count("—")
    latin = len(LATIN_COMMA_AR.findall(text))
    curly = sum(text.count(c) for c in "‘’“”")
    ellip = text.count("…")
    nbsp = sum(text.count(c) for c in "   ")
    total = invisible * 4 + em * 2 + curly + ellip + nbsp + latin
    per1k = total * 1000 / max(len(text), 1)
    score = scale(per1k, human=0.0, machine=12.0)
    detail = (f"{invisible} invisible, {em} em dash, {curly} curly quote, "
              f"{ellip} ellipsis, {nbsp} hard space")
    if latin:
        detail += f", {latin} Latin comma in Arabic"
    return score, detail


def check_voice(text, lex):
    """Contractions, person, and the shapes models default to."""
    w = words(text)
    if len(w) < 25:
        return 50.0, "too short to judge"
    per100 = 100 / len(w)
    contractions = len(CONTRACTIONS.findall(text)) * per100
    person = len(PRONOUNS.findall(text)) * per100
    tells = 0
    names = []
    for s in lex["structures"]:
        try:
            n = len(re.compile(s["regex"], re.MULTILINE).findall(text))
        except re.error:
            continue
        if n:
            tells += n
            names.append(s["id"])
    bullets = [len(b.split()) for b in re.findall(r"(?m)^\s*[-*•]\s+(.+)$", text)]
    uniform = (len(bullets) >= 3 and statistics.pstdev(bullets) < 1.6)
    if arabic_dominant(text):
        # Arabic has no contractions; person and tells carry the check.
        score = (scale(person, human=6.0, machine=0.5) * 0.6
                 + clamp(100 - tells * 22) * 0.4)
    else:
        score = (scale(contractions, human=3.0, machine=0.0) * 0.35
                 + scale(person, human=8.0, machine=1.0) * 0.35
                 + clamp(100 - tells * 22) * 0.30)
    if uniform:
        score -= 12
        names.append("uniform-bullets")
    detail = (f"{contractions:.1f} contractions, {person:.1f} personal pronouns "
              f"per 100 words, {tells} structural tell(s)")
    if names:
        detail += " [" + ", ".join(names[:4]) + "]"
    return clamp(score), detail


CHECKS = ["BURSTINESS", "SPECIFICITY", "SLOP DENSITY", "FINGERPRINT", "VOICE"]


def run(text, lex):
    results = {}
    results["BURSTINESS"] = check_burstiness(text)
    results["SPECIFICITY"] = check_specificity(text)
    results["SLOP DENSITY"] = check_slop(text, lex)
    results["FINGERPRINT"] = check_fingerprint(text)
    results["VOICE"] = check_voice(text, lex)
    scores = [results[c][0] for c in CHECKS]
    # The weakest check drags the verdict: a detector only needs one signal.
    overall = statistics.mean(scores) * 0.6 + min(scores) * 0.4
    verdict = "PASS" if overall >= 70 and min(scores) >= 55 else (
        "REVIEW" if overall >= 50 else "FLAGGED")
    return results, overall, verdict


def bar(score, width=24):
    filled = round(score / 100 * width)
    return "#" * filled + "." * (width - filled)


def render(results, overall, verdict, label=None, out=sys.stdout):
    title = "AI DETECTION PANEL" + (f"  -  {label}" if label else "")
    print("\n" + title, file=out)
    print("=" * max(len(title), 62), file=out)
    for name in CHECKS:
        score, detail = results[name]
        print(f"  {name:<13} {bar(score)} {score:5.1f}", file=out)
        print(f"  {'':<13} {detail}", file=out)
    print("-" * 62, file=out)
    print(f"  {'HUMAN SCORE':<13} {bar(overall)} {overall:5.1f}   {verdict}", file=out)
    if verdict != "PASS":
        weakest = min(CHECKS, key=lambda c: results[c][0])
        print(f"\n  Weakest signal: {weakest}. Fix that first.", file=out)
    print("", file=out)


def main():
    ap = argparse.ArgumentParser(description="Score how machine-written a draft looks.")
    ap.add_argument("input", nargs="?", default="-", help="file, or - for stdin")
    ap.add_argument("compare", nargs="?", help="second file, to show before/after")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--lexicon", default=LEX)
    args = ap.parse_args()

    lex = load_lexicon(args.lexicon)
    read = lambda p: sys.stdin.read() if p == "-" else open(p, encoding="utf-8").read()

    targets = [(args.input, read(args.input))]
    if args.compare:
        targets.append((args.compare, read(args.compare)))

    payload = []
    for name, text in targets:
        results, overall, verdict = run(text, lex)
        payload.append({
            "source": name,
            "checks": {k: {"score": round(v[0], 1), "detail": v[1]} for k, v in results.items()},
            "human_score": round(overall, 1),
            "verdict": verdict,
        })

    if args.json:
        print(json.dumps(payload if args.compare else payload[0], indent=2, ensure_ascii=False))
        return

    for (name, text), p in zip(targets, payload):
        results, overall, verdict = run(text, lex)
        render(results, overall, verdict, label=os.path.basename(name) if args.compare else None)
    if args.compare:
        a, b = payload
        delta = b["human_score"] - a["human_score"]
        print(f"  {a['human_score']:.1f} {a['verdict']}  ->  "
              f"{b['human_score']:.1f} {b['verdict']}   ({delta:+.1f})\n")

    sys.exit(0 if payload[-1]["verdict"] == "PASS" else 1)


if __name__ == "__main__":
    main()
