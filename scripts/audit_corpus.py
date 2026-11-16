import argparse
import re
import unicodedata
from pathlib import Path

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
INDEX_FILE = WORKSPACE_DIR / "39_Expanded_Keyword_Index.md"
TRANSCRIPTIONS_DIR = WORKSPACE_DIR / "transcriptions"


def strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )


def normalize_token(s: str) -> str:
    s = strip_accents(s).lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


class KeywordIndex:
    def __init__(self, index_path: Path):
        self.lines = index_path.read_text(encoding="utf-8").splitlines()
        self.line_entries = []
        self.term_to_lines = {}
        self._parse()

    def _parse(self):
        cur_sec = ""
        cur_sub = ""
        bold_pat = re.compile(r"\*\*(.+?)\*\*")
        italic_pat = re.compile(r"\*([^*]+?)\*")

        for idx, raw in enumerate(self.lines, start=1):
            stripped = raw.strip()
            if stripped.startswith("## "):
                cur_sec = stripped[3:].strip()
                cur_sub = ""
            elif stripped.startswith("### "):
                cur_sub = stripped[4:].strip()

            if not stripped or stripped.startswith("#") or stripped == "---":
                continue

            terms = []
            for m in bold_pat.finditer(stripped):
                t = m.group(1).strip()
                terms.append(t)
                for part in re.split(r"[,/()]", t):
                    p = part.strip()
                    if len(p) > 2:
                        terms.append(p)

            if not terms and (stripped.startswith("*") or stripped.startswith("-") or re.match(r"^\d+\.", stripped)):
                clean = re.sub(r"^(\*|-|\d+\.)\s+", "", stripped)
                clean = re.sub(r"\([^)]*\)", "", clean).strip()
                clean = clean.split(":")[0].strip()
                if len(clean) > 2:
                    terms.append(clean)

            for m in italic_pat.finditer(stripped):
                it = m.group(1).strip()
                if len(it) > 3 and not it.startswith("The Power"):
                    terms.append(it)

            norm_terms = set()
            for t in terms:
                nt = normalize_token(t)
                if len(nt) > 2:
                    norm_terms.add(nt)
                    self.term_to_lines.setdefault(nt, []).append(idx)

            self.line_entries.append((idx, raw, cur_sec, cur_sub, norm_terms))

    def line_matches_term(self, lineno: int, term: str) -> bool:
        if lineno < 1 or lineno > len(self.lines):
            return False
        raw = self.lines[lineno - 1]
        if not raw.strip() or raw.strip().startswith("#"):
            return False
        norm_raw = normalize_token(raw)
        clean_term = re.sub(r"\[.*?\]", "", term)
        clean_term = re.sub(r"\(.*?\)", "", clean_term).strip()
        norm_term = normalize_token(clean_term)

        # Also check parentheticals inside term, e.g. "priests (santri / pradikan / ulama)"
        paren_parts = []
        for pm in re.finditer(r"\(([^)]+)\)", term):
            for p in re.split(r"[,/]", pm.group(1)):
                np = normalize_token(p)
                if len(np) > 2:
                    paren_parts.append(np)

        if norm_term and norm_term in norm_raw:
            return True

        stopwords = {
            "raden", "pangeran", "sultan", "sunan", "kyai", "tumenggung",
            "adipati", "ngabehi", "aria", "mas", "lord", "general", "resident",
            "governor", "captain", "major", "brigadier", "admiral", "colonel",
            "van", "von", "der", "den", "the", "and", "for", "with", "listed",
            "under", "letters", "archival", "papers", "residency", "aliases",
            "commanders", "corps", "cavalry", "royal", "titles", "priests"
        }
        words = [w for w in norm_term.split() if len(w) > 3 and w not in stopwords]
        if not words:
            words = [w for w in norm_term.split() if len(w) > 2 and w not in stopwords]
        if words:
            hits = 0
            for w in words:
                w_stem = w[:-1] if w.endswith("s") and len(w) > 4 else w
                if re.search(r"\b" + re.escape(w_stem) + r"s?\b", norm_raw):
                    hits += 1
            if hits >= max(1, (len(words) + 1) // 2):
                return True

        location_tags = {"surakarta", "yogyakarta", "yogya", "solo", "semarang", "batavia", "java"}
        for pp in paren_parts:
            if pp not in location_tags and re.search(r"\b" + re.escape(pp) + r"\b", norm_raw):
                return True
        return False

    def find_best_line(self, term: str, context: str = "") -> int | None:
        clean_term = re.sub(r"\[.*?\]", "", term)
        clean_term = re.sub(r"\(.*?\)", "", clean_term).strip()
        norm_term = normalize_token(clean_term)

        # 1. Exact normalized match
        if norm_term and norm_term in self.term_to_lines:
            candidates = self.term_to_lines[norm_term]
            for c in candidates:
                if "**" in self.lines[c - 1] and norm_term in normalize_token(self.lines[c - 1].split(":")[0]):
                    return c
            return candidates[0]

        # 2. Check parentheticals in term itself, e.g. (santri / pradikan / ulama)
        for pm in re.finditer(r"\(([^)]+)\)", term):
            for p in re.split(r"[,/]", pm.group(1)):
                np = normalize_token(p)
                if np and np in self.term_to_lines:
                    return self.term_to_lines[np][0]

        # 3. Check aliases / parentheticals in context (backticks or parens)
        for m in re.finditer(r"`([^`]+)`|\(([^)]+)\)", context):
            alias = m.group(1) or m.group(2)
            if alias.lower().startswith("line"):
                continue
            for p in re.split(r"[,/]", alias):
                na = normalize_token(p)
                if na and na in self.term_to_lines:
                    return self.term_to_lines[na][0]

        if not norm_term:
            return None

        # 4. Score all lines by distinctive word overlap
        stopwords = {
            "raden", "pangeran", "sultan", "sunan", "kyai", "tumenggung",
            "adipati", "ngabehi", "aria", "mas", "lord", "general", "resident",
            "governor", "captain", "major", "brigadier", "admiral", "colonel",
            "van", "von", "der", "den", "the", "and", "for", "with", "listed",
            "under", "letters", "archival", "papers", "residency", "aliases",
            "commanders", "corps", "cavalry", "royal", "titles"
        }
        words = [w for w in norm_term.split() if len(w) > 2 and w not in stopwords]
        if not words:
            return None

        best_score = 0
        best_line = None
        for idx, raw, sec, sub, _ in self.line_entries:
            head = raw.split(":")[0]
            norm_head = normalize_token(head)
            norm_full = normalize_token(raw)
            score = 0
            for w in words:
                w_stem = w[:-1] if w.endswith("s") and len(w) > 4 else w
                if re.search(r"\b" + re.escape(w_stem) + r"s?\b", norm_head):
                    score += 3
                elif re.search(r"\b" + re.escape(w_stem) + r"s?\b", norm_full):
                    score += 1
            if score > best_score:
                best_score = score
                best_line = idx

        if best_line is not None and (best_score >= 3 or (len(words) == 1 and best_score >= 1)):
            if self.line_matches_term(best_line, term):
                return best_line
        return None


def normalize_standardized_diacritics(text: str) -> str:
    text = re.sub(r"\bRaden\b", "Radèn", text)
    text = re.sub(r"\bPangeran\b", "Pangéran", text)
    text = re.sub(r"\bRadèn Rangga\b", "Radèn Rongga", text)
    text = re.sub(r"\bRadèn Ronggo\b", "Radèn Rongga", text)
    return text


def audit_and_fix(fix: bool = False):
    index = KeywordIndex(INDEX_FILE)
    md_files = sorted(TRANSCRIPTIONS_DIR.glob("*.md"))

    total_cites = 0
    mismatched_cites = 0
    fixed_cites = 0
    marked_unindexed = 0
    files_modified = 0
    diacritic_fixes = 0
    template_fixes = 0

    cite_pat = re.compile(r"([Ll]ines?\s+)(\d+)")
    bold_pat = re.compile(r"\*\*(.+?)\*\*")

    for mf in md_files:
        orig_text = mf.read_text(encoding="utf-8")
        lines = orig_text.splitlines()
        modified = False

        in_cross_ref = False
        in_metadata = False
        has_two_col_table = any("Original Transcription" in l and "Standardized" in l for l in lines)
        new_lines = []

        for raw_line in lines:
            cur_line = raw_line

            # Normalize IMG_0868-0874 Matched Keywords heading
            if fix and cur_line.strip() == "## Matched Keywords from Index":
                cur_line = "### Cross-Reference with `39_Expanded_Keyword_Index.md`"
                modified = True
                template_fixes += 1

            if "Cross-Reference" in cur_line or "Matched Keywords from Index" in cur_line:
                in_cross_ref = True
                in_metadata = False
            elif cur_line.strip().startswith("## Metadata"):
                in_metadata = True
            elif cur_line.strip().startswith("---") or cur_line.strip().startswith("### "):
                if not ("Cross-Reference" in cur_line):
                    in_metadata = False

            # Diacritic normalization in Metadata, Cross-Reference, or 2nd column of Standardized table
            if fix:
                if in_cross_ref or in_metadata:
                    normed = normalize_standardized_diacritics(cur_line)
                    if normed != cur_line:
                        cur_line = normed
                        modified = True
                        diacritic_fixes += 1
                elif has_two_col_table and cur_line.startswith("|") and cur_line.count("|") >= 3:
                    # Only normalize the 2nd column (Standardized & Expanded), keep 1st column verbatim!
                    parts = cur_line.split("|")
                    if len(parts) >= 4 and "Original Transcription" not in parts[1] and "---" not in parts[1]:
                        norm_col2 = normalize_standardized_diacritics(parts[2])
                        if norm_col2 != parts[2]:
                            parts[2] = norm_col2
                            cur_line = "|".join(parts)
                            modified = True
                            diacritic_fixes += 1

            # Check and fix line citations (and recover any 'not in current index' that ARE in index)
            if in_cross_ref and ("**" in cur_line or "39_Expanded_Keyword_Index" in cur_line):
                bold_terms = [
                    b for b in bold_pat.findall(cur_line)
                    if not re.match(r"^[Ll]ines?\s+\d+$", b.strip()) and b.strip() != "not in current index"
                ]
                if bold_terms:
                    term = bold_terms[0]
                elif ":" in cur_line:
                    term = cur_line.split(":", 1)[1].strip()
                else:
                    term = ""

                if fix and "not in current index" in cur_line and term:
                    best = index.find_best_line(term, cur_line)
                    if best is not None:
                        if "**not in current index**" in cur_line:
                            cur_line = cur_line.replace("**not in current index**", f"**Line {best}**", 1)
                        else:
                            cur_line = cur_line.replace("not in current index", f"line {best}", 1)
                        fixed_cites += 1
                        modified = True

            if in_cross_ref and cite_pat.search(cur_line) and ("**" in cur_line or "39_Expanded_Keyword_Index" in cur_line):

                def replace_cite(m):
                    nonlocal total_cites, mismatched_cites, fixed_cites, marked_unindexed
                    prefix, num_str = m.group(1), m.group(2)
                    lno = int(num_str)
                    total_cites += 1
                    if index.line_matches_term(lno, term):
                        return m.group(0)
                    cat_m = re.search(r"Listed under \*([^*]+)\*", cur_line)
                    if cat_m and index.line_matches_term(lno, cat_m.group(1)):
                        return m.group(0)
                    mismatched_cites += 1
                    best = index.find_best_line(term, cur_line)
                    if best is not None:
                        if fix:
                            fixed_cites += 1
                            return f"{prefix}{best}"
                    else:
                        if fix:
                            marked_unindexed += 1
                            return "not in current index"
                    return m.group(0)

                updated_line = cite_pat.sub(replace_cite, cur_line)
                if updated_line != cur_line:
                    cur_line = updated_line
                    modified = True

            new_lines.append(cur_line)

        if fix and modified:
            mf.write_text("\n".join(new_lines) + ("\n" if orig_text.endswith("\n") else ""), encoding="utf-8")
            files_modified += 1

    print(f"Files scanned: {len(md_files)}")
    print(f"Total line citations checked: {total_cites}")
    print(f"Mismatched line citations: {mismatched_cites}")
    if fix:
        print(f"Fixed line citations: {fixed_cites}")
        print(f"Marked unindexed (not in current 39_Expanded_Keyword_Index.md): {marked_unindexed}")
        print(f"Diacritic/spelling normalizations (Metadata/Standardized/Cross-Ref): {diacritic_fixes}")
        print(f"Template heading normalizations: {template_fixes}")
        print(f"Total files updated: {files_modified}")

    return mismatched_cites


def main():
    parser = argparse.ArgumentParser(description="Audit and fix transcription files against 39_Expanded_Keyword_Index.md")
    parser.add_argument("--fix", action="store_true", help="Apply deterministic fixes")
    parser.add_argument("--check", action="store_true", help="Exit non-zero if any mismatched line citations exist")
    args = parser.parse_args()

    mismatches = audit_and_fix(fix=args.fix)
    if args.check and mismatches > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
