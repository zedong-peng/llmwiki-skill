#!/usr/bin/env python3
"""Restore untracked caches from metadata.yaml.

Downloads missing assets (TeX archives, PDFs, supplementary files) from their
recorded URL, verifies the recorded SHA-256, and clones missing official
repositories at the recorded commit. A missing TeX archive URL is derived from
paper.arxiv_id and selected_version.

Dry run by default; --apply performs the work. Existing files are never
overwritten and metadata.yaml is never modified. Downloaded repository code is
not executed.

Usage: fetch_assets.py <wiki-root> [--apply] [--kinds tex_source,pdf,supplementary,repo] [--topic T] [--slug S]
"""
import argparse
import glob
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required: pip install pyyaml")

UA = "llmwiki-fetch/1 (personal paper archive)"
ARXIV_DELAY = 3.0  # arXiv asks automated clients to pause between requests
_last_arxiv = [0.0]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def asset_url(asset, paper):
    if asset.get("url"):
        return asset["url"]
    if asset.get("kind") == "tex_source" and paper.get("arxiv_id"):
        return f"https://arxiv.org/src/{paper['arxiv_id']}{paper.get('selected_version') or asset.get('version') or ''}"
    return None


def download(url, dest, expected):
    if "arxiv.org" in url:
        wait = ARXIV_DELAY - (time.time() - _last_arxiv[0])
        if wait > 0:
            time.sleep(wait)
        _last_arxiv[0] = time.time()
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(dest), prefix=".fetch-")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=120) as r, os.fdopen(fd, "wb") as f:
            shutil.copyfileobj(r, f)
        got = sha256(tmp)
        if expected and got != expected:
            return f"sha256 mismatch (got {got[:12]}, recorded {expected[:12]}); not saved"
        if os.path.exists(dest):
            return "destination appeared meanwhile; not overwritten"
        os.rename(tmp, dest)
        return None
    except Exception as e:  # network errors are reported, not fatal
        return f"{type(e).__name__}: {e}"
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def clone(url, dest, commit):
    tmp = tempfile.mkdtemp(dir=os.path.dirname(dest), prefix=".fetch-")
    try:
        if commit:
            subprocess.run(["git", "clone", "--quiet", "--filter=blob:none", "--no-checkout", url, tmp], check=True)
            subprocess.run(["git", "-C", tmp, "checkout", "--quiet", commit], check=True)
        else:
            subprocess.run(["git", "clone", "--quiet", "--depth", "1", url, tmp], check=True)
        head = subprocess.run(["git", "-C", tmp, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        os.rename(tmp, dest)
        return None, head
    except subprocess.CalledProcessError as e:
        shutil.rmtree(tmp, ignore_errors=True)
        return f"git failed: {e}", None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--kinds", default="tex_source,pdf,supplementary,repo")
    ap.add_argument("--topic")
    ap.add_argument("--slug")
    args = ap.parse_args()
    kinds = set(args.kinds.split(","))
    pattern = os.path.join(args.root, "wiki", "research", args.topic or "*", "assets", args.slug or "*", "metadata.yaml")
    todo = done = failed = 0
    for meta_path in sorted(glob.glob(pattern)):
        ref = os.path.dirname(meta_path)
        name = os.path.relpath(ref, os.path.join(args.root, "wiki", "research"))
        meta = yaml.safe_load(open(meta_path)) or {}
        paper = meta.get("paper") or meta.get("reference") or {}
        for a in meta.get("assets") or []:
            path = a.get("path")
            if a.get("kind") not in kinds or not path or path.endswith("/") or os.path.exists(os.path.join(ref, path)):
                continue
            url = asset_url(a, paper)
            todo += 1
            if not url:
                print(f"skip   {name}/{path}: no URL recorded")
                failed += 1
                continue
            if not args.apply:
                print(f"fetch  {name}/{path} <- {url}")
                continue
            problem = download(url, os.path.join(ref, path), a.get("sha256"))
            print(f"{'FAIL ' if problem else 'ok   '}  {name}/{path}" + (f": {problem}" if problem else ""))
            failed += bool(problem)
            done += not problem
        if "repo" not in kinds:
            continue
        for r in meta.get("repositories") or []:
            url = r.get("url")
            if not url:
                continue
            path = r.get("path") or "github-repo/" + url.rstrip("/").split("/")[-1].removesuffix(".git")
            dest = os.path.join(ref, path)
            if os.path.exists(dest):
                continue
            todo += 1
            pin = r.get("commit")
            if not args.apply:
                print(f"clone  {name}/{path} <- {url} @ {pin or 'default branch (unpinned)'}")
                continue
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            problem, head = clone(url, dest, pin)
            if problem:
                print(f"FAIL   {name}/{path}: {problem}")
                failed += 1
            else:
                note = "" if pin else f" (unpinned; HEAD {head[:12]}, record it in metadata if you inspect this code)"
                print(f"ok     {name}/{path}{note}")
                done += 1
    verb = "restored" if args.apply else "to restore"
    print(f"{todo} missing, {done if args.apply else todo} {verb}, {failed} failed or skipped")


if __name__ == "__main__":
    main()
