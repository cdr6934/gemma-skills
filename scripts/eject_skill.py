#!/usr/bin/env python3
"""Eject a skill from this toolkit into its own standalone, deployable repo.

A skill authored under skills/<name>/ is nested (its Pages URL would be
.../skills/<name>). Ejecting copies the skill's files to the ROOT of a new
directory so the whole repo *is* the skill folder, giving a clean Pages URL like
https://<user>.github.io/<name>/ . Adds .nojekyll (so GitHub Pages serves
SKILL.md raw) and .gitignore, then git-inits and commits.

Usage:
    python3 scripts/eject_skill.py <skill-name> [--out DIR] [--force] [--no-git]

After it runs, publish with the gh commands it prints (create public repo,
push, enable Pages). Run validate_skill.py on the output dir to confirm it is
still well-formed (the validator is folder-based, so it works on the eject too).
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
GITIGNORE = ".DS_Store\n__pycache__/\n*.pyc\n"


def main():
    p = argparse.ArgumentParser(description="Eject a skill into its own standalone repo.")
    p.add_argument("name", help="Skill folder under skills/ to eject.")
    p.add_argument("--out", help="Output directory (default: ../<name> next to this repo).")
    p.add_argument("--force", action="store_true", help="Overwrite the output dir if present.")
    p.add_argument("--no-git", action="store_true", help="Skip git init/commit.")
    args = p.parse_args()

    src = SKILLS_DIR / args.name
    if not (src / "SKILL.md").exists():
        sys.exit(f"error: {src}/SKILL.md not found — is '{args.name}' a skill under skills/?")

    out = Path(args.out).resolve() if args.out else (REPO_ROOT.parent / args.name)
    # Re-ejecting over an already-published repo must keep its .git (history + remote), so a
    # re-eject becomes a safe "publish an update" rather than a fresh, divergent history.
    stashed_git = None
    if out.exists():
        if not args.force:
            sys.exit(f"error: {out} already exists (use --force to overwrite).")
        git_dir = out / ".git"
        if git_dir.exists():
            stashed_git = out.parent / f".{args.name}.gitstash"
            if stashed_git.exists():
                shutil.rmtree(stashed_git)
            shutil.move(str(git_dir), str(stashed_git))
        shutil.rmtree(out)
    preserve_git = stashed_git is not None

    # Copy the skill's files to the ROOT of the new repo (SKILL.md, scripts/, assets/, README).
    shutil.copytree(src, out)
    if stashed_git:
        shutil.move(str(stashed_git), str(out / ".git"))
    (out / ".nojekyll").write_text("")          # GitHub Pages: serve SKILL.md raw, no Jekyll
    (out / ".gitignore").write_text(GITIGNORE)

    if not args.no_git and preserve_git:
        subprocess.run(["git", "add", "-A"], cwd=out, check=True)
        clean = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=out).returncode == 0
        if clean:
            print("Existing repo already matches the skill — nothing to commit.")
        else:
            subprocess.run(["git", "-c", "commit.gpgsign=false", "commit", "-q", "-m",
                            f"{args.name}: update skill files"], cwd=out, check=True)
            print("Updated existing repo (committed) — `git -C %s push` to deploy." % out)
    elif not args.no_git:
        subprocess.run(["git", "init", "-q"], cwd=out, check=True)
        subprocess.run(["git", "add", "-A"], cwd=out, check=True)
        subprocess.run(
            ["git", "-c", "commit.gpgsign=false", "commit", "-q", "-m",
             f"{args.name}: standalone AI Edge Gallery skill"],
            cwd=out, check=True,
        )

    print(f"Ejected '{args.name}' -> {out}")
    print(f"Validate:  python3 {REPO_ROOT}/scripts/validate_skill.py {out}")
    if preserve_git:
        print(f"Publish update:  git -C {out} push")
    else:
        print("Publish (creates a PUBLIC repo + GitHub Pages):")
        print(f"  gh repo create {args.name} --public --source={out} --remote=origin --push")
        print(f"  gh api -X POST repos/<owner>/{args.name}/pages -f 'source[branch]=main' -f 'source[path]=/'")
    print(f"  # Skill URL for the app: https://<owner>.github.io/{args.name}")


if __name__ == "__main__":
    main()
