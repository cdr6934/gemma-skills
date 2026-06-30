#!/usr/bin/env python3
"""Validate AI Edge Gallery (Gemma) skill folders.

Checks the structural contract the Gallery app relies on:
  - SKILL.md exists with a frontmatter block containing `name` and `description`
  - frontmatter `name` matches the folder name and is kebab-case
  - JS skills expose `window['ai_edge_gallery_get_result']` in scripts/index.html
  - js-webview skills referencing assets/*.html actually ship those files
  - require-secret skills accept a second (secret) argument

Usage:
    python3 scripts/validate_skill.py skills/<name>
    python3 scripts/validate_skill.py --all
Exit code is non-zero if any skill fails.
"""
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
ENTRY = "ai_edge_gallery_get_result"


def parse_frontmatter(text):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not m:
        return None
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    # crude nested metadata scan
    if "require-secret" in m.group(1):
        fm["_require_secret"] = "true" in m.group(1).split("require-secret", 1)[1][:8]
    return fm


def validate(folder: Path):
    errors, warnings = [], []
    name = folder.name

    if not KEBAB.match(name):
        errors.append(f"folder name '{name}' is not kebab-case")

    skill_md = folder / "SKILL.md"
    if not skill_md.exists():
        errors.append("missing SKILL.md")
        return errors, warnings

    text = skill_md.read_text()
    fm = parse_frontmatter(text)
    if fm is None:
        errors.append("SKILL.md has no '---' frontmatter block")
        return errors, warnings

    if "name" not in fm:
        errors.append("frontmatter missing 'name'")
    elif fm["name"] != name:
        errors.append(f"frontmatter name '{fm['name']}' != folder '{name}'")
    if not fm.get("description"):
        errors.append("frontmatter missing/empty 'description'")
    elif len(fm["description"]) > 200:
        warnings.append("description is long (>200 chars); keep it tight for model matching")

    index = folder / "scripts" / "index.html"
    is_js = index.exists()
    mentions_run_js = "run_js" in text
    mentions_run_intent = "run_intent" in text

    if is_js:
        idx = index.read_text()
        if ENTRY not in idx:
            # may be in a referenced .js file
            js_files = list((folder / "scripts").glob("*.js"))
            if not any(ENTRY in f.read_text() for f in js_files):
                errors.append(f"scripts/index.html (or its .js) must define window['{ENTRY}']")
        if not mentions_run_js:
            warnings.append("SKILL.md does not mention the `run_js` tool")
        if fm.get("_require_secret"):
            blob = idx + "".join(f.read_text() for f in (folder / "scripts").glob("*.js"))
            if re.search(rf"{ENTRY}['\"]\]\s*=\s*async\s*\(\s*\w+\s*,\s*\w+", blob) is None:
                warnings.append("require-secret set but entry fn takes no 2nd (secret) arg")
        # webview asset existence
        for ref in re.findall(r"url:\s*[`'\"]([^`'\"?]+)", idx):
            if ref.endswith(".html") and not (folder / "assets" / ref).exists():
                errors.append(f"webview references assets/{ref} which is missing")
    else:
        if mentions_run_js:
            errors.append("SKILL.md references run_js but scripts/index.html is missing")
        if not mentions_run_intent and not mentions_run_js:
            pass  # text-only skill: fine

    return errors, warnings


def main():
    args = sys.argv[1:]
    if args == ["--all"]:
        targets = sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir()) if SKILLS_DIR.exists() else []
        if not targets:
            print("no skills found in skills/")
            return
    elif len(args) == 1:
        targets = [Path(args[0]).resolve()]
    else:
        sys.exit(__doc__)

    failed = False
    for folder in targets:
        errors, warnings = validate(folder)
        status = "FAIL" if errors else "OK"
        if errors:
            failed = True
        print(f"[{status}] {folder.name}")
        for e in errors:
            print(f"    error:   {e}")
        for w in warnings:
            print(f"    warning: {w}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
