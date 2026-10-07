#!/usr/bin/env python3
"""Migrate legacy paper archives to the canonical layout.

Legacy:    wiki/research/<topic>/papers/<slug>/{*.pdf, source/, repo/, ...}
Canonical: wiki/research/<topic>/assets/<slug>/{paper-pdf/, paper-tex/, github-repo/, ...}

Dry run by default. --apply moves files, rewrites metadata.yaml to schema v1
(legacy fields kept verbatim under `legacy:`), maps note status to the page
vocabulary, and rewrites links that point into moved paths.

--caches-only is for a second clone after pulling a migrated commit: it only
moves leftover untracked files (for example ignored repository caches) from
papers/<slug>/ into the already migrated assets/<slug>/, without touching
metadata or links.

Deletes only loose source/ files whose SHA-256 equals a file in source/archives/. A destination that already exists is reported and the
source is left in place.
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import sys

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required: pip install pyyaml")

TODAY = datetime.date.today().isoformat()
INGEST_STATES = ["queued", "downloaded", "extracted", "read", "processed"]
NOTE_STATUS = {"processed": "active", "read": "active", "stub": "seed", "queued": "seed",
               "downloaded": "seed", "extracted": "seed"}
LEGACY_EXTRACTION_ID = "legacy"
LOG_FILES = {"log.md"}


# ---------------------------------------------------------------- planning

def legacy_refs(wiki):
    research = os.path.join(wiki, "research")
    for topic in sorted(os.listdir(research)):
        papers = os.path.join(research, topic, "papers")
        if not os.path.isdir(papers):
            continue
        for slug in sorted(os.listdir(papers)):
            src = os.path.join(papers, slug)
            if os.path.isdir(src) and ({"index.md", "metadata.yaml"} & set(os.listdir(src))):
                yield topic, slug, src, os.path.join(research, topic, "assets", slug)


class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


def load_yaml(path):
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, yaml.YAMLError):
        return {}


def supplementary_names(meta):
    names = set()
    for key in ("supplementary",):
        for v in meta.get(key) or []:
            if isinstance(v, str):
                names.add(os.path.basename(v))
            elif isinstance(v, dict):
                for k in ("file", "path"):
                    if isinstance(v.get(k), str):
                        names.add(os.path.basename(v[k]))
    files = meta.get("files")
    if isinstance(files, dict):
        for v in files.get("supplementary") or []:
            if isinstance(v, str):
                names.add(os.path.basename(v))
    return names


def plan_ref(src):
    """Return [(relative source, relative destination)] inside one reference."""
    meta = load_yaml(os.path.join(src, "metadata.yaml"))
    supp = supplementary_names(meta)
    moves = []
    for name in sorted(os.listdir(src)):
        p = os.path.join(src, name)
        if name == "source" and os.path.isdir(p):
            arch = os.path.join(p, "archives")
            digests = {sha256(os.path.join(arch, x)) for x in os.listdir(arch)
                       if os.path.isfile(os.path.join(arch, x))} if os.path.isdir(arch) else set()
            archive_hashes = {os.path.join(p, x) for x in os.listdir(p)
                              if os.path.isfile(os.path.join(p, x)) and sha256(os.path.join(p, x)) in digests}
            for sub in sorted(os.listdir(p)):
                sp = os.path.join(p, sub)
                rel = f"source/{sub}"
                if sub == "archives" and os.path.isdir(sp):
                    moves += [(f"{rel}/{x}", f"paper-tex/archives/{x}") for x in sorted(os.listdir(sp))]
                elif sub == "extracted" and os.path.isdir(sp):
                    if os.listdir(sp):
                        moves.append((rel, f"paper-tex/extracted/{LEGACY_EXTRACTION_ID}"))
                elif os.path.isdir(sp) and sub != "code-audit":
                    moves.append((rel, f"paper-tex/extracted/{sub}"))
                elif sub.endswith((".json", ".md")) or sub == "code-audit":
                    moves.append((rel, sub))
                elif os.path.isfile(sp) and sp in archive_hashes:
                    moves.append((rel, None))  # byte-identical copy of a file in archives/
                else:
                    moves.append((rel, f"paper-tex/archives/{sub}"))
        elif name == "repo" and os.path.isdir(p):
            moves += [(f"repo/{x}", f"github-repo/{x}") for x in sorted(os.listdir(p))]
        elif name.lower().endswith(".pdf") and os.path.isfile(p):
            moves.append((name, f"supplementary/{name}" if name in supp else f"paper-pdf/{name}"))
        elif name in ("paper-pdf", "paper-tex", "supplementary", "github-repo") and os.path.isdir(p):
            for dp, _, fs in os.walk(p):
                for f in fs:
                    r = os.path.relpath(os.path.join(dp, f), src)
                    moves.append((r, r))
        else:
            moves.append((name, name))
    return moves


# ---------------------------------------------------------------- moving

def move(src, dst, report):
    if os.path.lexists(dst):
        if os.path.isdir(src) and os.path.isdir(dst) and not os.path.islink(src):
            for x in sorted(os.listdir(src)):
                move(os.path.join(src, x), os.path.join(dst, x), report)
            return
        report.append(f"conflict: {dst} exists; left {src}")
        return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    os.rename(src, dst)


def prune_empty(path, stop):
    for dp, ds, fs in os.walk(path, topdown=False):
        if not os.listdir(dp):
            os.rmdir(dp)
    while path != stop and os.path.isdir(path) and not os.listdir(path):
        os.rmdir(path)
        path = os.path.dirname(path)


# ---------------------------------------------------------------- metadata

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def detect_format(path):
    with open(path, "rb") as f:
        head = f.read(512)
    if head.startswith(b"%PDF"):
        return "pdf"
    if head.startswith(b"\x1f\x8b"):
        return "gzip"
    if head.startswith(b"PK\x03\x04"):
        return "zip"
    if len(head) > 262 and head[257:262] == b"ustar":
        return "tar"
    if head.lstrip().lower().startswith((b"<!doctype html", b"<html")):
        return "html"
    if b"\\documentclass" in head or b"\\begin{" in head or head.lstrip().startswith(b"%"):
        return "tex"
    return "unknown"


def first(*vals):
    for v in vals:
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def dig(d, *keys):
    for k in keys:
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d


def note_frontmatter(path):
    try:
        text = open(path).read()
    except OSError:
        return {}
    m = re.match(r"---\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    try:
        fm = yaml.safe_load(m.group(1))
        return fm if isinstance(fm, dict) else {}
    except yaml.YAMLError:
        return {}


def norm_state(v):
    if not isinstance(v, str):
        return None
    v = v.strip().lower()
    if v in INGEST_STATES:
        return v
    if v in ("stub", "seed", "pending", "metadata_only"):
        return "queued"
    return None


def build_v1(ref, topic, slug, legacy, fm):
    links = legacy.get("links") if isinstance(legacy.get("links"), dict) else {}
    download = legacy.get("download") if isinstance(legacy.get("download"), dict) else {}
    retrieved = first(download.get("checked_at"), legacy.get("ingested_at"), legacy.get("date_ingested"))
    pdf_url = first(legacy.get("arxiv_pdf_url"), legacy.get("pdf_url"), links.get("arxiv_pdf"), legacy.get("arxiv_pdf"))
    tex_url = first(legacy.get("arxiv_source_url"), download.get("source_url") if download.get("source_type") != "pdf" else None,
                    legacy.get("arxiv_source"))
    arxiv = first(str(legacy.get("arxiv_id") or "") or None, str(fm.get("arxiv") or "") or None)

    extracted_root = os.path.join(ref, "paper-tex", "extracted")
    trees = sorted(os.listdir(extracted_root)) if os.path.isdir(extracted_root) else []

    assets = []
    for sub, kind in (("paper-pdf", "pdf"), ("paper-tex/archives", "tex_source"), ("supplementary", "supplementary")):
        root = os.path.join(ref, sub)
        if not os.path.isdir(root):
            continue
        for dp, _, fs in os.walk(root):
            for f in sorted(fs):
                p = os.path.join(dp, f)
                rel = os.path.relpath(p, ref)
                fmt = detect_format(p)
                a = {"kind": kind, "url": pdf_url if kind == "pdf" else tex_url if kind == "tex_source" else None,
                     "resolved_url": None, "version": first(legacy.get("arxiv_version")), "path": rel,
                     "original_filename": f, "filename_provenance": None, "format": fmt,
                     "retrieved_at": retrieved, "bytes": os.path.getsize(p), "sha256": sha256(p),
                     "status": "downloaded", "error": None,
                     "extraction": {"status": "not_applicable", "path": None, "error": None}}
                if kind == "tex_source" and fmt in ("gzip", "tar", "zip", "tex", "unknown") and trees:
                    a["extraction"] = {"status": "extracted",
                                       "path": f"paper-tex/extracted/{trees[0]}" if len(trees) == 1 else "paper-tex/extracted/",
                                       "error": None}
                assets.append(a)
        # Legacy archives/ sometimes hold already extracted directories.
        if kind == "tex_source":
            for x in sorted(os.listdir(root)):
                if os.path.isdir(os.path.join(root, x)):
                    assets.append({"kind": "tex_source", "url": tex_url, "path": f"paper-tex/archives/{x}/",
                                   "format": "directory", "status": "downloaded",
                                   "error": "legacy directory stored under archives/; original bytes not separated",
                                   "extraction": {"status": "not_applicable", "path": None, "error": None}})
    # Avoid counting files inside such directories twice.
    dir_assets = [a["path"] for a in assets if a.get("format") == "directory"]
    assets = [a for a in assets if a.get("format") == "directory" or not any(a["path"].startswith(d) for d in dir_assets)]

    repos = []
    urls = [first(legacy.get("repo_url")), first(links.get("code")), first(legacy.get("github_url")),
            first(legacy.get("github"))]
    for r in legacy.get("repositories") or []:
        if isinstance(r, dict):
            urls.append(first(r.get("url")))
        elif isinstance(r, str):
            urls.append(first(r))
    seen = set()
    audit = legacy.get("code_audit") if isinstance(legacy.get("code_audit"), dict) else {}
    local = first(legacy.get("repo_local_path"), dig(legacy, "files", "code_repository"), legacy.get("repo_path"))
    for url in [u for u in urls if u]:
        if url in seen or "github.com" not in url and "gitlab" not in url:
            continue
        seen.add(url)
        name = url.rstrip("/").split("/")[-1].removesuffix(".git")
        path = f"github-repo/{name}"
        cached = os.path.isdir(os.path.join(ref, path)) or (local and local.strip("/") not in ("repo", ""))
        inspected = bool(legacy.get("repo_read")) or bool(audit.get("read_scope")) or bool(legacy.get("repo_inspection_scope"))
        repos.append({"url": url, "path": path if cached else None,
                      "commit": first(audit.get("commit"), legacy.get("repo_commit")),
                      "branch": None, "retrieved_at": first(audit.get("checked_at")),
                      "submodules": None, "inspection_scope": first(audit.get("read_scope"), legacy.get("repo_inspection_scope")),
                      "status": "inspected" if inspected else "cached" if cached else "pending",
                      "execution": first(audit.get("board_reproduction"), legacy.get("repo_execution")) or "not_run"})

    ingest_raw = legacy.get("ingest")
    state = None
    for v in (legacy.get("ingest_status"), dig(legacy, "ingest", "note_status"),
              ingest_raw if isinstance(ingest_raw, str) else None, legacy.get("ingest_stage"),
              legacy.get("status"), fm.get("status")):
        state = norm_state(v)
        if state:
            break
    if state is None or (state in ("queued", "downloaded") and assets):
        state = "extracted" if trees else "downloaded" if assets else "queued"

    read_src = " ".join(str(legacy.get(k) or "") for k in ("reading_source", "read_source", "source_read_from", "read_from")).lower()
    pdf_fallback = bool(legacy.get("used_pdf_fallback")) or "pdf" in read_src and "tex" not in read_src
    read_done = state in ("read", "processed")
    source = "pdf" if pdf_fallback else "tex" if (legacy.get("source_read") or "tex" in read_src or "source" in read_src) else None
    reading = {"status": "read" if read_done else "not_started", "source": source if read_done else None,
               "paths": [], "scope": [],
               "fallback_reason": "TeX unavailable, used PDF fallback." if read_done and pdf_fallback else None,
               "note": "index.md" if os.path.exists(os.path.join(ref, "index.md")) else None}
    if read_done and source is None:
        reading["scope"] = ["legacy record: reading source not recorded"]

    paper = {"title": first(legacy.get("title"), fm.get("title")), "slug": slug, "topic": topic,
             "arxiv_id": arxiv, "doi": first(legacy.get("doi")), "selected_version": first(legacy.get("arxiv_version"))}
    for k in ("authors", "year", "venue"):
        v = legacy.get(k, fm.get(k))
        if v not in (None, "", []):
            paper[k] = v
    return {"schema_version": 1, "paper": paper, "assets": assets, "repositories": repos, "reading": reading,
            "ingest": {"status": state, "updated_at": TODAY,
                       "exceptions": [f"migrated from legacy papers/ layout on {TODAY}; original fields kept under legacy"]},
            **({"legacy": legacy} if legacy else {})}


def set_note_status(path):
    try:
        text = open(path).read()
    except OSError:
        return False
    m = re.match(r"(---\n)(.*?)(\n---)", text, re.S)
    if not m:
        return False
    def repl(mm):
        v = mm.group(2).strip().strip("'\"")
        return f"{mm.group(1)}{NOTE_STATUS[v]}" if v in NOTE_STATUS else mm.group(0)
    body = re.sub(r"(?m)^(status:\s*)(\S.*)$", repl, m.group(2), count=1)
    if body != m.group(2):
        open(path, "w").write(m.group(1) + body + m.group(3) + text[m.end():])
        return True
    return False


# ---------------------------------------------------------------- links

class Mapper:
    def __init__(self, repo, pairs):
        self.repo = repo
        self.pairs = sorted(((os.path.normpath(a), os.path.normpath(b)) for a, b in pairs), key=lambda x: -len(x[0]))

    def new(self, old):
        for a, b in self.pairs:
            if old == a or old.startswith(a + "/"):
                return b + old[len(a):]
        return None

    def old(self, new):
        for a, b in self.pairs:
            if new == b or new.startswith(b + "/"):
                return a + new[len(b):]
        return None


LINK_RE = re.compile(r"(\[\[)([^\]|#]+)|(\]\()([^)\s]+)|(`)([^`\n]+)(`)")


def rewrite_file(path, mapper, wiki, is_log):
    repo = mapper.repo
    rel_new = os.path.relpath(path, repo)
    rel_old = mapper.old(rel_new) or rel_new
    old_dir, new_dir = os.path.dirname(rel_old), os.path.dirname(rel_new)
    wiki_rel = os.path.relpath(wiki, repo)

    def resolve(target, wikilink):
        t = target.strip()
        if "://" in t or t.startswith(("#", "mailto:")):
            return None
        anchor = ""
        if not wikilink and "#" in t:
            t, anchor = t.split("#", 1)
            anchor = "#" + anchor
        trail = "/" if t.endswith("/") else ""
        core = t.rstrip("/")
        cands = [("file", os.path.normpath(os.path.join(old_dir, core)))]
        cands += [("wiki", os.path.normpath(os.path.join(wiki_rel, core))), ("repo", os.path.normpath(core))]
        for style, c in cands:
            for ext in ("", ".md"):
                n = mapper.new(c + ext)
                if n and not (os.path.exists(os.path.join(repo, n)) or os.path.exists(os.path.join(repo, n + ".md"))):
                    n = None  # accidental prefix match; the moved target must exist
                if n:
                    n = n[: len(n) - len(ext)] if ext else n
                    if style == "file":
                        out = os.path.relpath(n, new_dir)
                    elif style == "wiki":
                        out = os.path.relpath(n, wiki_rel)
                    else:
                        out = n
                    return out + trail + anchor
        # Relative link from a moved file to an unmoved target.
        if old_dir != new_dir and not wikilink:
            c = os.path.normpath(os.path.join(old_dir, core))
            if os.path.exists(os.path.join(repo, c)):
                return os.path.relpath(c, new_dir) + trail + anchor
        return None

    text = open(path, errors="surrogateescape").read()
    def sub(m):
        if m.group(1):
            r = resolve(m.group(2), True)
            return m.group(1) + r if r else m.group(0)
        if m.group(3):
            r = resolve(m.group(4), False)
            return m.group(3) + r if r else m.group(0)
        if is_log or " " in m.group(6) or "/" not in m.group(6) and "." not in m.group(6):
            return m.group(0)
        r = resolve(m.group(6), False)
        return m.group(5) + r + m.group(7) if r else m.group(0)
    new = LINK_RE.sub(sub, text)
    if new != text:
        open(path, "w", errors="surrogateescape").write(new)
        return True
    return False


ASSET_DIRS = ("paper-tex", "paper-pdf", "github-repo", "supplementary", "source", "repo")


def text_files(wiki):
    for dp, ds, fs in os.walk(wiki):
        ds[:] = [d for d in ds if d not in ASSET_DIRS and d != ".git"
                 and not os.path.exists(os.path.join(dp, d, ".git"))]
        for f in fs:
            if f.endswith((".md", ".yaml", ".yml")):
                yield os.path.join(dp, f)


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", help="wiki repository root (contains wiki/)")
    ap.add_argument("--apply", action="store_true", help="perform the migration")
    ap.add_argument("--caches-only", action="store_true", help="only move leftover files into migrated references")
    ap.add_argument("--map-out", help="write the old->new path map as JSON")
    args = ap.parse_args()
    repo = os.path.abspath(args.root)
    wiki = os.path.join(repo, "wiki")
    report, pairs = [], []

    refs = list(legacy_refs(wiki))
    if args.caches_only:
        refs += [(t, s, p, d) for t, s, p, d in _leftovers(wiki) if (t, s, p, d) not in refs]
    for topic, slug, src, dst in refs:
        if os.path.exists(dst) and not args.caches_only:
            report.append(f"skip: {os.path.relpath(dst, repo)} already exists")
            continue
        moves = plan_ref(src)
        dsts = [d for _, d in moves if d]
        dup = {d for d in dsts if dsts.count(d) > 1}
        if dup:
            report.append(f"skip: {os.path.relpath(src, repo)} maps several files to {sorted(dup)}")
            continue
        r_src, r_dst = os.path.relpath(src, repo), os.path.relpath(dst, repo)
        pairs.append((r_src, r_dst))
        pairs += [(f"{r_src}/{a}", f"{r_dst}/{b}") for a, b in moves if b and a != b]
        if not args.apply:
            print(f"{r_src} -> {r_dst}")
            for a, b in moves:
                if a != b:
                    print(f"    {a} -> {b or '(duplicate of archives/, removed)'}")
            continue
        legacy = load_yaml(os.path.join(src, "metadata.yaml"))
        fm = note_frontmatter(os.path.join(src, "index.md"))
        for a, b in moves:
            if b is None:
                os.remove(os.path.join(src, a))  # hash-verified duplicate in plan_ref
            else:
                move(os.path.join(src, a), os.path.join(dst, b), report)
        prune_empty(src, os.path.dirname(src))
        if args.caches_only:
            continue
        meta = build_v1(dst, topic, slug, legacy, fm)
        with open(os.path.join(dst, "metadata.yaml"), "w") as f:
            yaml.dump(meta, f, Dumper=NoAliasDumper, sort_keys=False, allow_unicode=True, width=1000)
        set_note_status(os.path.join(dst, "index.md"))

    if args.map_out:
        with open(args.map_out, "w") as f:
            json.dump(pairs, f, indent=1)
    if args.apply and not args.caches_only and pairs:
        mapper = Mapper(repo, pairs)
        changed = 0
        for p in text_files(wiki):
            if os.path.basename(p) == "metadata.yaml":
                continue
            changed += rewrite_file(p, mapper, wiki, os.path.basename(p) in LOG_FILES)
        print(f"rewrote links in {changed} files")
    for line in report:
        print(line)
    print(f"{len([p for p in pairs if p[0].count('/') == 4])} references {'migrated' if args.apply else 'planned'}")


def _leftovers(wiki):
    """papers/<slug> directories left behind after pulling a migrated commit."""
    research = os.path.join(wiki, "research")
    for topic in sorted(os.listdir(research)):
        papers = os.path.join(research, topic, "papers")
        if not os.path.isdir(papers):
            continue
        for slug in sorted(os.listdir(papers)):
            src = os.path.join(papers, slug)
            dst = os.path.join(research, topic, "assets", slug)
            if os.path.isdir(src) and os.path.isdir(dst):
                yield topic, slug, src, dst


if __name__ == "__main__":
    main()
