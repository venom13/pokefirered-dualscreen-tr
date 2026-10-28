#!/usr/bin/env python3
"""Turkish translation workflow for the FireRed dual-screen port.

Translations are keyed to the English sources at BASE_COMMIT, never to the
working tree, so `apply` is idempotent: it always starts from the pristine
English file and substitutes every translated unit.

A unit is one message: a run of `.string` lines under a label in data/*.inc
and data/*.s, one `_("...")` expression in C, or one text field in the item
and region-map JSON files. Its id is the 1-based line of the unit in the
English file (plus `.k` for the k-th `_(` on a C line), stable because the
English file never changes.

Translation files live in tools/turkish/translations/<source path>.json as
{"<id>": "<Turkish text>"}. Turkish text uses the game's escapes: `\\p` starts a
new box, `\\n` forces a line break; `apply` re-wraps every unit whose English
text had line breaks to the pixel width of its group, choosing `\\n`/`\\l` the
way the original does. Units without breaks are copied as written.

Commands:
  status                 progress per source group
  pending [PATH] [-n N]  print untranslated units of the first pending file(s)
  import FILE            merge a batch file ("### <path>#<id>" headers)
  import-list PATH FILE  one translation per line for a name table
  keep PATH [--label R]  leave pending units deliberately in English
  apply                  write Turkish sources into the working tree
  check                  validate every translation without writing
"""
import argparse
import collections
import glob
import json
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TOOLDIR = os.path.join(ROOT, "tools", "turkish")
TRDIR = os.path.join(TOOLDIR, "translations")
# Source edits Turkish grammar needs beyond swapping text units (word order of
# composed messages, strings without letters): [{"path", "old", "new", "why"}].
RAW_PATCHES = os.path.join(TOOLDIR, "raw_patches.json")
BASE_COMMIT = "0ce39a18d"

# C files whose strings stay English: proper names, Japanese-only tables,
# word lists whose order is alphabetical, and LeafGreen-only Pokédex text.
SKIP_C = {
    "src/data/text/species_names.h",
    "src/data/trainers.h",
    "src/data/ingame_trades.h",
    "src/data/pokemon/pokedex_text_lg.h",
    "src/data/union_room.h",
    "src/keyboard_text.c",
}
SKIP_C_DIRS = ("src/data/easy_chat/", "src/data/decoration/")
JSON_FIELDS = {
    "src/data/items.json": ("english", "description_english"),
    "src/data/region_map/region_map_sections.json": ("name",),
}
NAME_LIMITS = {  # fixed-size name buffers, in bytes before the terminator
    "src/battle_main.c": 6,
    "src/data/text/move_names.h": 12,
    "src/data/text/nature_names.h": 12,
    "src/data/text/trainer_class_names.h": 12,
    "src/data/pokemon/pokedex_entries.h": 11,
    "src/data/text/abilities.h:name": 12,
    "src/data/text/abilities.h:desc": None,  # width only
    "src/data/items.json:english": 13,
    "src/data/region_map/region_map_sections.json:name": 16,
}
# Groups printed into one fixed-size box, where any unit may use as many
# lines as the longest English one; elsewhere a unit keeps its own count.
FIXED_BOXES = {
    "src/data/items.json:description_english",
    "src/move_descriptions.c",
    "src/data/pokemon/pokedex_text_fr.h",
}
# data/*.inc files printed into their own windows rather than the field box.
OWN_WINDOW_INC = {"data/text/help_system.inc", "data/text/fame_checker.inc"}
# strings.c label prefixes whose text goes to one dedicated window.
STRINGS_WINDOWS = (
    "gText_RegionMap_AreaDesc_",
    "gText_PokeSum_",
    "gStartMenuDesc_",
    "gCreditsString_",
)
# Widest likely expansion of a placeholder, in pixels: 7-letter player
# names, 10-letter Pokémon names behind a "Vahşi "/"Rakip " prefix, 12-letter
# move/ability names, 13-letter item names.
PLACEHOLDER_WIDTH = {"PLAYER": 42, "RIVAL": 42, "B_PLAYER_NAME": 42, "B_TRAINER1_NAME": 60,
                     "B_TRAINER2_NAME": 60, "B_TRAINER1_CLASS": 72, "B_TRAINER2_CLASS": 72,
                     "B_CURRENT_MOVE": 72, "B_LAST_ITEM": 78}
DEFAULT_PLACEHOLDER_WIDTH = 60
PREFIXED_NAME_WIDTH = 90   # B_..._NAME_WITH_PREFIX
ABILITY_WIDTH = 72         # B_..._ABILITY
# Message windows whose real width is known: 28 tiles minus the margins.
GROUP_LIMITS = {"field": 216, "src/battle_message.c": 216}

STRING_LINE = re.compile(r'^(\s*)\.string\s+"((?:[^"\\]|\\.)*)"\s*$')
LABEL = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)::?")
C_UNIT = re.compile(r'_\(\s*((?:"(?:[^"\\]|\\.)*"\s*)+)\)', re.S)
C_LITERAL = re.compile(r'"((?:[^"\\]|\\.)*)"')
KANA = re.compile(r"[぀-ヿ]")
CODE = re.compile(r"\{[^}]*\}|\\[nlp]|\\.|.", re.S)


# ---------------------------------------------------------------------------
# English sources
# ---------------------------------------------------------------------------

def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True).stdout


def base_files():
    names = git("ls-tree", "-r", "--name-only", BASE_COMMIT).decode().splitlines()
    out = []
    for n in names:
        if n.startswith("data/") and n.endswith((".inc", ".s")):
            out.append(n)
        elif n.startswith("src/") and n.endswith((".c", ".h")) and not n.startswith("src/platform/"):
            if n in SKIP_C or n.startswith(SKIP_C_DIRS):
                continue
            out.append(n)
        elif n in JSON_FIELDS:
            out.append(n)
    return out


_cache = {}


def preload(paths):
    """Read many English files with one `git cat-file --batch`."""
    want = [p for p in paths if p not in _cache]
    if not want:
        return
    query = "".join("%s:%s\n" % (BASE_COMMIT, p) for p in want).encode()
    out = subprocess.run(["git", "cat-file", "--batch"], cwd=ROOT, input=query,
                         check=True, capture_output=True).stdout
    pos = 0
    for p in want:
        nl = out.index(b"\n", pos)
        size = int(out[pos:nl].split()[2])
        _cache[p] = out[nl + 1:nl + 1 + size].decode("utf8")
        pos = nl + 1 + size + 1


def base_text(path):
    if path not in _cache:
        preload([path])
    return _cache[path]


def translatable(text):
    return re.search(r"[A-Za-z]{2}", re.sub(r"\{[^}]*\}", "", text)) and not KANA.search(text)


class Unit:
    __slots__ = ("path", "id", "en", "start", "end", "kind", "label", "indent")

    def __init__(self, path, uid, en, start, end, kind, label, indent=""):
        self.path, self.id, self.en = path, uid, en
        self.start, self.end = start, end  # character span in the English file
        self.kind, self.label, self.indent = kind, label, indent


def units_inc(path, text):
    units, label, run = [], None, []
    pos = 0
    lines = text.split("\n")
    offsets = []
    for line in lines:
        offsets.append(pos)
        pos += len(line) + 1

    def flush():
        if run:
            first, last = run[0], run[-1]
            en = "".join(STRING_LINE.match(lines[i]).group(2) for i in run)
            if translatable(en):
                indent = STRING_LINE.match(lines[first]).group(1)
                units.append(Unit(path, str(first + 1), en, offsets[first],
                                  offsets[last] + len(lines[last]), "inc", label or "", indent))
            run.clear()

    for i, line in enumerate(lines):
        if STRING_LINE.match(line):
            run.append(i)
            continue
        flush()
        m = LABEL.match(line)
        if m:
            label = m.group(1)
    flush()
    return units


def units_c(path, text):
    units, per_line = [], collections.Counter()
    for m in C_UNIT.finditer(text):
        en = "".join(C_LITERAL.findall(m.group(1)))
        line = text.count("\n", 0, m.start()) + 1
        per_line[line] += 1
        if not translatable(en):
            continue
        uid = str(line) if per_line[line] == 1 else "%d.%d" % (line, per_line[line])
        head = text[text.rfind("\n", 0, m.start()) + 1:m.start()]
        lab = re.findall(r"[A-Za-z_][A-Za-z0-9_]*|\[[A-Z0-9_]+\]", head)
        units.append(Unit(path, uid, en, m.start(), m.end(), "c", lab[-1] if lab else ""))
    return units


def units_json(path, text):
    units = []
    fields = JSON_FIELDS[path]
    for m in re.finditer(r'"(%s)":\s*"((?:[^"\\]|\\.)*)"' % "|".join(fields), text):
        en = json.loads('"%s"' % m.group(2))
        if not translatable(en) or en.startswith("?"):
            continue
        line = text.count("\n", 0, m.start()) + 1
        units.append(Unit(path, str(line), en, m.start(2), m.end(2), "json", m.group(1)))
    return units


def units_of(path):
    text = base_text(path)
    if path in JSON_FIELDS:
        return units_json(path, text)
    if path.endswith((".inc", ".s")):
        return units_inc(path, text)
    return units_c(path, text)


def all_units():
    out = collections.OrderedDict()
    paths = base_files()
    preload(paths)
    for path in paths:
        us = units_of(path)
        if us:
            out[path] = us
    return out


# ---------------------------------------------------------------------------
# Widths
# ---------------------------------------------------------------------------

class Metrics:
    def __init__(self):
        self.chars, self.names = {}, {}
        for line in open(os.path.join(ROOT, "charmap.txt"), encoding="utf8"):
            line = line.split("@")[0].strip() if not line.startswith("'@'") else line.strip()
            m = re.match(r"^'(\\?.)'\s*=\s*([0-9A-Fa-f]{2})", line)
            if m:
                ch = m.group(1)[-1] if m.group(1) != "\\'" else "'"
                self.chars.setdefault(ch, int(m.group(2), 16))
                continue
            m = re.match(r"^([A-Z_0-9]+)\s*=\s*((?:[0-9A-Fa-f]{2}\s*)+)$", line)
            if m:
                self.names.setdefault(m.group(1), [int(b, 16) for b in m.group(2).split()])
        src = open(os.path.join(ROOT, "src", "text.c"), encoding="utf8").read()
        body = re.search(r"sFontNormalLatinGlyphWidths\[\]\s*=\s*\{([^}]*)\}", src).group(1)
        self.width = [int(n) for n in re.findall(r"\d+", body)]

    def encodable(self, ch):
        return ch in self.chars

    def byte_len(self, s):
        n = 0
        for tok in CODE.findall(s.rstrip("$")):
            if tok.startswith("{"):
                n += len(self.names.get(tok[1:-1].split()[0], [0])) if tok[1:-1].split() else 0
            else:
                n += 1
        return n

    def code_width(self, code):
        name = code[1:-1].split()[0] if code[1:-1].split() else ""
        bytes_ = self.names.get(name)
        if bytes_ is None:
            return 0
        if bytes_[0] == 0xFD:
            if name in PLACEHOLDER_WIDTH:
                return PLACEHOLDER_WIDTH[name]
            if name.endswith("WITH_PREFIX"):
                return PREFIXED_NAME_WIDTH
            if name.endswith("ABILITY"):
                return ABILITY_WIDTH
            return DEFAULT_PLACEHOLDER_WIDTH
        if bytes_[0] >= 0xF7:
            return 0
        return sum(self.width[b] for b in bytes_)

    def is_placeholder(self, code):
        name = code[1:-1].split()[0] if code[1:-1].split() else ""
        return self.names.get(name, [0])[0] in (0xF7, 0xFD)

    def text_width(self, s):
        w = 0
        for tok in CODE.findall(s):
            if tok.startswith("{"):
                w += self.code_width(tok)
            elif tok.startswith("\\"):
                continue
            elif tok in self.chars:
                w += self.width[self.chars[tok]]
        return w


def split_lines(s):
    """English text -> paragraphs -> lines (codes \\n \\l separate lines)."""
    s = s.rstrip("$")
    return [re.split(r"\\[nl]", p) for p in s.split("\\p")]


def group_of(unit):
    """Units printed into the same kind of window. strings.c holds text for
    many screens; a label prefix from STRINGS_WINDOWS tells those apart."""
    if unit.kind == "inc":
        return unit.path if unit.path in OWN_WINDOW_INC else "field"
    if unit.kind == "json":
        return unit.path + ":" + unit.label
    if unit.path == "src/strings.c":
        for prefix in STRINGS_WINDOWS:
            if unit.label.startswith(prefix):
                return unit.path + ":" + prefix
    return unit.path


def name_table(unit):
    """The NAME_LIMITS key of a name-table unit, else None."""
    key = unit.path + (":" + unit.label if unit.kind == "json" else "")
    if unit.path == "src/data/text/abilities.h":
        key = unit.path + (":name" if unit.label.startswith("[") else ":desc")
    return key if key in NAME_LIMITS else None


def has_breaks(s):
    return bool(re.search(r"\\[nlp]", s))


def group_widths(units_by_path, metrics):
    """Pixel width per group, plus "<group>#lines": the most lines one box of
    that group holds in English."""
    widths = collections.defaultdict(list)
    lines = {}
    for us in units_by_path.values():
        for u in us:
            if has_breaks(u.en):
                paras = split_lines(u.en)
                for para in paras:
                    for line in para:
                        widths[group_of(u)].append(metrics.text_width(line))
                lines[group_of(u)] = max(lines.get(group_of(u), 0), max(len(p) for p in paras))
            elif name_table(u):
                widths["names:" + name_table(u)].append(metrics.text_width(u.en))
    limits = {}
    for g, ws in widths.items():
        ws.sort()
        # the box width: the widest line the English text already uses,
        # ignoring a stray outlier above the 99.5th percentile
        limits[g] = GROUP_LIMITS.get(g) or ws[min(len(ws) - 1, int(len(ws) * 0.995))]
    for g, n in lines.items():
        if g in FIXED_BOXES:
            limits[g + "#lines"] = n
    return limits


# ---------------------------------------------------------------------------
# Wrapping and validation
# ---------------------------------------------------------------------------

def wrap(tr, unit, limit, metrics, group_lines=0):
    """Re-wrap Turkish text to `limit` pixels in the English unit's style.

    Field text (data/*.inc messages of up to two lines per box) goes to a
    box that scrolls: the first break of a box is \\n, later ones \\l. Other
    text, multi-line pages included, keeps \\n breaks and at most as many
    lines per box as the English used; when the English already spans
    several boxes, overflow continues in a new box.
    """
    en = unit.en
    end = "$" if en.endswith("$") else ""
    body = tr[:-1] if tr.endswith("$") else tr
    en_lines = max(len(p) for p in split_lines(en))
    field_style = "\\l" in en or (unit.kind == "inc" and en_lines <= 2)
    max_lines = max(en_lines, group_lines)
    out_paras, problems = [], []
    for para in body.split("\\p"):
        lines = []
        for hard in re.split(r"\\[nl]", para):
            # keep a hard line's indent; help steps ("{CIRCLE_n} ...") hang
            # their continuation lines under the text, three spaces in
            indent = hard[:len(hard) - len(hard.lstrip(" "))]
            hang = "   " if hard.startswith("{CIRCLE_") else indent
            cur = ""
            for w in hard.lstrip(" ").split(" "):
                cand = w if not cur else cur + " " + w
                if cur and metrics.text_width(cand) > limit:
                    lines.append(cur)
                    cur = hang + w
                else:
                    cur = cand if cur else indent + cand
            lines.append(cur)
        for ln in lines:
            if metrics.text_width(ln) > limit:
                problems.append("line wider than %dpx: %s" % (limit, ln))
        if field_style:
            joined = lines[0]
            for i, ln in enumerate(lines[1:]):
                joined += ("\\n" if i == 0 else "\\l") + ln
            out_paras.append(joined)
        elif len(lines) <= max_lines:
            out_paras.append("\\n".join(lines))
        elif "\\p" in en:
            for i in range(0, len(lines), max_lines):
                out_paras.append("\\n".join(lines[i:i + max_lines]))
        else:
            problems.append("%d lines, box holds %d: %s" % (len(lines), max_lines, para))
            out_paras.append("\\n".join(lines))
    return "\\p".join(out_paras) + end, problems


def codes(s, metrics=None):
    """Control codes and placeholders of s; glyph codes like {PKMN} may be
    dropped or added freely, so they are left out when metrics is given."""
    found = re.findall(r"\{[^}]*\}", s)
    if metrics is not None:
        found = [c for c in found if metrics.code_width(c) == 0 or metrics.is_placeholder(c)]
    return sorted(found)


def validate(unit, tr, metrics, limits):
    if tr == unit.en:  # kept in English on purpose: written back untouched
        return tr, []
    problems = []
    if codes(unit.en, metrics) != codes(tr, metrics):
        problems.append("control codes differ: %s vs %s" % (codes(unit.en, metrics), codes(tr, metrics)))
    if unit.en.endswith("$") != tr.endswith("$"):
        problems.append("terminator $ mismatch")
    bad = sorted({ch for ch in re.sub(r"\{[^}]*\}|\\.", "", tr) if not metrics.encodable(ch)})
    if bad:
        problems.append("characters missing from charmap: %s" % "".join(bad))
    limit = NAME_LIMITS.get(name_table(unit))
    if limit and metrics.byte_len(tr) > limit:
        problems.append("longer than %d characters" % limit)
    if has_breaks(unit.en):
        wrapped, wrap_problems = wrap(tr, unit, limits[group_of(unit)], metrics,
                                       limits.get(group_of(unit) + "#lines", 0))
        problems += wrap_problems
    else:
        wrapped = tr
        if "\\p" in tr or "\\n" in tr:
            problems.append("English has no line breaks; keep it on one line")
        ew, tw = metrics.text_width(unit.en), metrics.text_width(tr)
        if name_table(unit):
            ew = limits["names:" + name_table(unit)]  # the table's window fits its widest name
        if unit.kind != "inc" and tw > max(ew, 1) and tw > ew + 6:
            problems.append("WARN wider than English (%d > %dpx)" % (tw, ew))
    return wrapped, problems


# ---------------------------------------------------------------------------
# Translation storage
# ---------------------------------------------------------------------------

def tr_path(path):
    return os.path.join(TRDIR, path + ".json")


def load_tr(path):
    p = tr_path(path)
    if not os.path.exists(p):
        return {}
    return json.load(open(p, encoding="utf8"))


def save_tr(path, data, units):
    order = {u.id: i for i, u in enumerate(units)}
    data = dict(sorted(data.items(), key=lambda kv: order.get(kv[0], 1 << 30)))
    p = tr_path(path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_status(args):
    units = all_units()
    groups = collections.OrderedDict()
    for path, us in units.items():
        g = "/".join(path.split("/")[:2]) if path.startswith("data/") else path
        done = load_tr(path)
        t = groups.setdefault(g, [0, 0, 0, 0])
        t[0] += len(us)
        t[1] += sum(1 for u in us if u.id in done)
        t[2] += sum(len(u.en) for u in us)
        t[3] += sum(len(u.en) for u in us if u.id in done)
    tot = [0, 0, 0, 0]
    for g, t in groups.items():
        if args.all or t[1] < t[0]:
            print("%-48s %5d/%5d units %7d/%7d chars" % (g, t[1], t[0], t[3], t[2]))
        tot = [a + b for a, b in zip(tot, t)]
    print("%-48s %5d/%5d units %7d/%7d chars  (%.1f%%)" % ("TOTAL", tot[1], tot[0], tot[3], tot[2],
                                                            100.0 * tot[3] / max(tot[2], 1)))


def cmd_pending(args):
    units = all_units()
    paths = [p for p in units if not args.path or p.startswith(args.path)]
    shown = 0
    for path in paths:
        done = load_tr(path)
        for u in units[path]:
            if u.id in done:
                continue
            if shown == 0 or (shown and last_path != path):
                print("## %s" % path)
            last_path = path
            ctx = (" [%s]" % u.label) if u.label else ""
            print("### %s#%s%s\n%s" % (path, u.id, ctx, u.en))
            shown += 1
            if shown >= args.n:
                return


def cmd_import(args):
    units = all_units()
    metrics = Metrics()
    limits = group_widths(units, metrics)
    entries, cur = collections.OrderedDict(), None
    for raw in open(args.file, encoding="utf8").read().split("\n"):
        m = re.match(r"^### (\S+?)#([0-9.]+)", raw)
        if m:
            cur = (m.group(1), m.group(2))
            entries[cur] = []
        elif raw.startswith("## ") or cur is None:
            continue
        else:
            entries[cur].append(raw)
    by_path = collections.defaultdict(dict)
    for (path, uid), lines in entries.items():
        by_path[path][uid] = "".join(l.strip() if i == 0 else " " + l.strip() if l.strip() else ""
                                     for i, l in enumerate(lines)).strip()
    failures = 0
    for path, new in by_path.items():
        if path not in units:
            print("unknown file:", path)
            failures += 1
            continue
        index = {u.id: u for u in units[path]}
        data = load_tr(path)
        for uid, tr in new.items():
            u = index.get(uid)
            if u is None:
                print("unknown unit: %s#%s" % (path, uid))
                failures += 1
                continue
            if tr == "":
                continue
            _, problems = validate(u, tr, metrics, limits)
            hard = [p for p in problems if not p.startswith("WARN")]
            for p in problems:
                print("%s %s#%s: %s" % ("ERROR" if not p.startswith("WARN") else "warn ", path, uid, p))
            if hard:
                failures += 1
                if not args.force:
                    continue
            data[uid] = tr
        save_tr(path, data, units[path])
    print("imported %d units, %d with errors" % (sum(len(v) for v in by_path.values()), failures))
    return 1 if failures else 0


def cmd_import_list(args):
    """One translation per line, in unit order, for the units of PATH whose
    context label matches --label (for name tables)."""
    units = all_units()[args.path]
    if args.label:
        units = [u for u in units if re.search(args.label, u.label)]
    if args.field:
        units = [u for u in units if u.kind == "json" and u.label == args.field]
    lines = [l.rstrip("\n") for l in open(args.file, encoding="utf8") if l.strip()]
    if len(lines) != len(units):
        print("%d lines for %d units" % (len(lines), len(units)))
        for u, l in zip(units, lines):
            print("  %s -> %s" % (u.en, l))
        return 1
    tmp = args.file + ".batch"
    with open(tmp, "w", encoding="utf8", newline="\n") as f:
        for u, l in zip(units, lines):
            f.write("### %s#%s\n%s\n" % (u.path, u.id, l))
    args.file = tmp
    return cmd_import(args)


def cmd_keep(args):
    """Mark the pending units of PATH (optionally only those whose label
    matches --label) as deliberately left in English: proper names, staff
    credits, Pokémon names."""
    units = all_units()[args.path]
    data = load_tr(args.path)
    kept = 0
    for u in units:
        if u.id in data or (args.label and not re.search(args.label, u.label)):
            continue
        data[u.id] = u.en
        kept += 1
    save_tr(args.path, data, units)
    print("kept %d units of %s in English" % (kept, args.path))
    return 0


def raw_patches():
    if not os.path.exists(RAW_PATCHES):
        return []
    return json.load(open(RAW_PATCHES, encoding="utf8"))


def patch_raw(path, text, patches):
    """Apply the raw patches of path; each `old` must occur exactly once."""
    problems = []
    for p in patches:
        if p["path"] != path:
            continue
        n = text.count(p["old"])
        if n != 1:
            problems.append("%s: raw patch matches %d times: %s" % (path, n, p["old"][:60]))
            continue
        text = text.replace(p["old"], p["new"])
    return text, problems


def apply_units(path, units, data, metrics, limits):
    text = base_text(path)
    out, last, problems = [], 0, []
    for u in units:
        tr = data.get(u.id)
        if tr is None:
            continue
        wrapped, probs = validate(u, tr, metrics, limits)
        problems += ["%s#%s: %s" % (path, u.id, p) for p in probs]
        out.append(text[last:u.start])
        if u.kind == "inc":
            out.append(render_inc(wrapped, u.indent))
        elif u.kind == "c":
            out.append('_("%s")' % wrapped)
        else:
            out.append(json.dumps(wrapped, ensure_ascii=False)[1:-1])
        last = u.end
    out.append(text[last:])
    return "".join(out), problems


def render_inc(s, indent):
    parts = re.split(r"(\\[nlp])", s)
    lines, cur = [], ""
    for p in parts:
        cur += p
        if p in ("\\n", "\\l", "\\p"):
            lines.append(cur)
            cur = ""
    if cur:
        lines.append(cur)
    return "\n".join('%s.string "%s"' % (indent, ln) for ln in lines)


def cmd_apply(args, write=True):
    units = all_units()
    metrics = Metrics()
    limits = group_widths(units, metrics)
    count, problems = 0, []
    patches = raw_patches()
    patched = {p["path"] for p in patches}
    for path in sorted(patched - set(units)):
        new, probs = patch_raw(path, base_text(path), patches)
        problems += probs
        if write:
            with open(os.path.join(ROOT, path), "w", encoding="utf8", newline="\n") as f:
                f.write(new)
    for path, us in units.items():
        data = load_tr(path)
        if not data and path not in patched:
            if write:
                restore(path)
            continue
        new, probs = apply_units(path, us, data, metrics, limits)
        new, raw_probs = patch_raw(path, new, patches)
        problems += probs + raw_probs
        count += len(data)
        if write:
            with open(os.path.join(ROOT, path), "w", encoding="utf8", newline="\n") as f:
                f.write(new)
    errors = [p for p in problems if "WARN" not in p]
    for p in problems:
        print(p)
    print("%s %d translated units; %d errors, %d warnings" % ("applied" if write else "checked", count,
                                                             len(errors), len(problems) - len(errors)))
    return 1 if errors else 0


def restore(path):
    target = os.path.join(ROOT, path)
    text = base_text(path)
    if os.path.exists(target) and open(target, encoding="utf8").read() == text:
        return
    with open(target, "w", encoding="utf8", newline="\n") as f:
        f.write(text)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("status")
    s.add_argument("--all", action="store_true")
    s = sub.add_parser("pending")
    s.add_argument("path", nargs="?")
    s.add_argument("-n", type=int, default=60)
    s = sub.add_parser("import")
    s.add_argument("file")
    s.add_argument("--force", action="store_true", help="store units that fail validation")
    s = sub.add_parser("import-list")
    s.add_argument("path")
    s.add_argument("file")
    s.add_argument("--label", help="regex on the unit's context label")
    s.add_argument("--field", help="JSON field name")
    s.add_argument("--force", action="store_true")
    s = sub.add_parser("keep")
    s.add_argument("path")
    s.add_argument("--label", help="regex on the unit's context label")
    sub.add_parser("apply")
    sub.add_parser("check")
    sub.add_parser("limits")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf8")
    if args.cmd == "status":
        return cmd_status(args)
    if args.cmd == "pending":
        return cmd_pending(args)
    if args.cmd == "import":
        return cmd_import(args)
    if args.cmd == "import-list":
        return cmd_import_list(args)
    if args.cmd == "keep":
        return cmd_keep(args)
    if args.cmd == "apply":
        return cmd_apply(args)
    if args.cmd == "check":
        return cmd_apply(args, write=False)
    if args.cmd == "limits":
        units = all_units()
        for g, w in sorted(group_widths(units, Metrics()).items()):
            print("%4d %s" % (w, g))
    return 0


if __name__ == "__main__":
    sys.exit(main())
