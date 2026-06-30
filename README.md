# gemma-skills

A repeatable toolkit for building **[AI Edge Gallery](https://github.com/google-ai-edge/gallery)
Agent Skills** — modular capabilities that extend small, on-device Gemma models running on phones
and edge devices. Skills let a limited local model do things it otherwise can't: call APIs, run
computation, render interactive UIs, or trigger native device actions.

## Why

On-device LLMs are sandboxed — no terminal, no Python, no arbitrary code. The Gallery app bridges
this with two execution paths a skill can target: **`run_js`** (logic in a hidden webview) and
**`run_intent`** (native OS actions). A skill is just a folder the model can discover from its
`name`/`description` and invoke automatically.

## Workflow

```bash
# 1. Scaffold
python3 scripts/new_skill.py my-skill --type js --description "What it does, in one line."

# 2. Edit skills/my-skill/SKILL.md and scripts/index.html

# 3. Validate the structural contract
python3 scripts/validate_skill.py skills/my-skill      # or --all

# 4. Eject into its own standalone repo (files at root + .nojekyll), then publish to GitHub Pages
python3 scripts/eject_skill.py my-skill                 # creates ../my-skill, prints gh commands
gh repo create my-skill --public --source=../my-skill --remote=origin --push
gh api -X POST repos/<owner>/my-skill/pages -f 'source[branch]=main' -f 'source[path]=/'
# → add in app: https://<owner>.github.io/my-skill
```

JS skills must be served from a real host (GitHub Pages with `.nojekyll`), **not**
`raw.githubusercontent.com` (which serves `text/plain` and won't execute the webview).
Each skill ships as its own repo; this repo stays the creator toolkit.

## Skill types

- `text` — persona/knowledge only (`SKILL.md`).
- `js` — webview logic via `run_js` (`SKILL.md` + `scripts/index.html`); can `fetch()`, use CDN/WASM.
- `js-webview` — JS that also renders an interactive view in chat (`+ assets/webview.html`).
- `native` — maps to an OS intent via `run_intent` (email/SMS ship by default).

See [`CLAUDE.md`](CLAUDE.md) for the full contract (the JS entry function, return shapes,
images/webviews, secrets) and authoring conventions.

## Layout

```
skills/      authored skills (one folder each)
scripts/     new_skill.py (scaffold), validate_skill.py (lint)
templates/   reference notes
```
