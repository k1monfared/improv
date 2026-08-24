#!/usr/bin/env python3
import re, sys

MINOR = {"a","an","the","and","or","but","nor","for","of","on","at","to",
         "in","by","as","with","from"}

def smart_title(name):
    out = []
    for i, tok in enumerate(name.split()):
        fixed = []
        for j, sub in enumerate(tok.split("-")):
            letters = re.search(r"[A-Za-z]", sub)
            if not letters:
                fixed.append(sub)
                continue
            k = letters.start()
            low = sub.lower()
            if i > 0 and j > 0 and low in MINOR:
                fixed.append(sub)
            else:
                fixed.append(sub[:k] + sub[k].upper() + sub[k+1:].lower())
        out.append("-".join(fixed))
    return " ".join(out)

LABEL_RE = re.compile(r"^\*\*([^*]+?):\*\*\s*(.*)$")
PLAIN_SET = {"players","setup","goal","rules","variations","variants",
             "coaching","notes","source","format","context"}
PLAIN_RE = re.compile(r"^([A-Za-z][A-Za-z' -]{0,28}):\s*(.*)$")
H_PART = re.compile(r"^#\s+(.+)$")
H_NUM = re.compile(r"^#{2,3}\s+\d+\.\s+(.+)$")
H_PLAIN = re.compile(r"^#{2,3}\s+(.+)$")
CAPS = re.compile(r"^[A-Z][A-Z0-9 ,''&()/\u2019-]{5,}$")
STEP_LINE = re.compile(r"^(\d{1,2})\.\s+(.*)$")
STEP_INLINE = re.compile(r"(?:^|(?<=\s))(\d{1,2})\.(?=\s)")

def clean_name(n):
    n = re.sub(r"\s*\((?:ll?|lines?)\.[^)]*\)", " ", n, flags=re.I)
    n = re.sub(r"\s+", " ", n).strip(" .")
    if len(n) > 1 and n[0] == '"' and n[-1] == '"':
        n = n[1:-1]
    if n.isupper():
        n = smart_title(n)
    return n

def split_steps(text):
    cands = [(m.start(), m.end(), int(m.group(1)))
             for m in STEP_INLINE.finditer(text)]
    pos, expected = [], 1
    for start, end, num in cands:
        if num == expected:
            pos.append((start, end))
            expected += 1
        elif num < expected:
            continue
        else:
            break
    if len(pos) < 2:
        return None
    parts = []
    for i, (_, end) in enumerate(pos):
        nxt = pos[i + 1][0] if i + 1 < len(pos) else len(text)
        parts.append(re.sub(r"\s+", " ", text[end:nxt]).strip())
    return parts

def parse(path):
    entries, cur, field, part = [], None, None, None
    with open(path) as f:
        for raw in f:
            s = raw.strip()
            if not s or re.fullmatch(r"-{3,}", s) or s.startswith("# Keith"):
                continue
            m = LABEL_RE.match(s)
            pm = None
            if not m:
                cand = PLAIN_RE.match(s)
                if cand and cand.group(1).strip().lower() in PLAIN_SET \
                        and cur is not None:
                    m, pm = cand, cand
            if m and cur is not None:
                label = m.group(1).strip()
                text = m.group(2).strip()
                if re.match(r"extracted exercis", label + " " + text, re.I):
                    break
                field = [label, text]
                cur["fields"].append(field)
                continue
            m = H_PART.match(s)
            if m:
                part = m.group(1).strip().upper()
                continue
            m = H_NUM.match(s) or H_PLAIN.match(s)
            if m:
                name = clean_name(m.group(1))
                if re.match(r"extracted exercis", name, re.I):
                    break
                cur = {"name": name, "fields": [], "part": part}
                entries.append(cur)
                field = None
                continue
            if CAPS.match(s) and sum(c.isalpha() for c in s) >= 4:
                cur = {"name": smart_title(s), "fields": [], "part": part}
                entries.append(cur)
                field = None
                continue
            if cur is not None and field is not None:
                sm = STEP_LINE.match(s)
                if sm and field[0].lower().startswith("rule"):
                    if len(field) == 2:
                        field.extend(["steps", [sm.group(2)]])
                    else:
                        field[3].append(sm.group(2))
                    continue
                if len(field) == 4:
                    if sm:
                        field[3].append(sm.group(2))
                    else:
                        field[3][-1] = (field[3][-1] + " " + s).strip()
                    continue
                if re.match(r"extracted exercis", s, re.I):
                    break
                field[1] = (field[1] + " " + s).strip()
                continue
    return [e for e in entries if e["fields"]]

def emit(entries, indent=8):
    pad, deep = " " * indent, " " * (indent + 4)
    for e in entries:
        print(f"{pad}- {e['name']}")
        for field in e["fields"]:
            label, text = field[0], field[1]
            if text.strip().lower().rstrip(".") in ("none given", "none", "n/a"):
                continue
            is_rule = label.lower().startswith("rule")
            steps = (field[3] if len(field) == 4 else
                     (split_steps(text) if is_rule else None))
            if steps:
                print(f"{deep}- {label}")
                for st in steps:
                    st = re.sub(r"\s+", " ", st)
                    print(f"{deep}    - {st}")
            else:
                print(f"{deep}- {label}: {re.sub(r'[ \t]+', ' ', text)}")

GROUPS = [
    ("impro_status.md", [
        ("- Impro 1979, Status chapter #book:impro #status", None)]),
    ("impro_spont_narrative.md", [
        ("- Impro 1979, Spontaneity chapter #book:impro #spontaneity", "SPONTANEITY"),
        ("- Impro 1979, Narrative Skills chapter #book:impro #narrative", "NARRATIVE SKILLS")]),
    ("st_ch4_spontaneity.md", [
        ("- Impro for Storytellers 1999, ch 4 Spontaneity #book:storytellers #spontaneity", None)]),
    ("st_ch7_storygames.md", [
        ("- Impro for Storytellers 1999, ch 7 Story Games #book:storytellers #narrative", None)]),
    ("st_ch8_beingthere.md", [
        ("- Impro for Storytellers 1999, ch 8 Being There #book:storytellers #presence", None)]),
    ("st_ch9_filler.md", [
        ("- Impro for Storytellers 1999, ch 9 Filler Games #book:storytellers #warmup", None)]),
    ("st_ch10a_procedures.md", [
        ("- Impro for Storytellers 1999, ch 10 Procedures, offers and focus #book:storytellers #scene", None)]),
    ("st_ch10_procedures.md", [
        ("- Impro for Storytellers 1999, ch 10 Procedures, gibberish and status #book:storytellers #gibberish #status", None)]),
    ("st_ch10b_balloons.md", [
        ("- Impro for Storytellers 1999, ch 10 Procedures, balloons and audiences #book:storytellers #audience", None)]),
    ("st_ch12_14.md", [
        ("- Impro for Storytellers 1999, ch 12 to 14 Character work #book:storytellers #character", None)]),
]

BASE = __import__("os").path.join(
    __import__("os").path.dirname(__import__("os").path.abspath(__file__)),
    "extractions", "extract_")

def main():
    print("- FROM THE JOHNSTONE BOOKS #johnstone #books")
    total = 0
    for fname, groups in GROUPS:
        entries = parse(BASE + fname)
        total += len(entries)
        for header, marker in groups:
            subset = ([e for e in entries if e["part"] == marker]
                      if marker else entries)
            print()
            print("    " + header)
            emit(subset)
    print(f"\nTOTAL ENTRIES: {total}", file=sys.stderr)

if __name__ == "__main__":
    main()
