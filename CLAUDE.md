# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A **Gemma skill creator**: a repeatable toolkit for authoring [AI Edge Gallery](https://github.com/google-ai-edge/gallery)
Agent Skills. These skills extend small on-device LLMs (Gemma running locally on phones/edge
devices) with new capabilities — APIs, computation, interactive UIs — that the limited local
model cannot do on its own.

Each skill is a self-contained folder (validated, then loaded into the Gallery app via URL,
featured list, or `adb push`). This repo holds the authored skills plus the tooling to scaffold
and validate them.

## Commands

```bash
# Scaffold a new skill (creates skills/<name>/ with boilerplate)
python3 scripts/new_skill.py <skill-name> --type <text|js|js-webview|native> --description "..."

# Validate one skill or all skills (run before sharing/shipping)
python3 scripts/validate_skill.py skills/<skill-name>
python3 scripts/validate_skill.py --all

# Serve skills locally over HTTP with correct MIME types (for in-app "Load from URL" testing).
# raw.githubusercontent.com serves text/plain and will NOT execute JS skills — use a real host.
python3 -m http.server 8000   # then point the app at http://<your-ip>:8000/skills/<name>
```

There is no build step, package manager, or test framework. Skills are static files
(Markdown + HTML/JS) executed inside the app's webview.

## How skills execute (the key constraint)

On-device LLMs run sandboxed — **no terminal, no Python, no arbitrary commands**. The Gallery
app exposes exactly two execution paths, and every skill must route through one of them:

1. **`run_js`** — loads `scripts/index.html` into a hidden webview and calls a global function.
2. **`run_intent`** — invokes a native Android/iOS intent (only `send_email` / `send_sms`
   ship by default; new intents require modifying the app's `IntentHandler.kt`).

The LLM decides to invoke a skill purely from its `name` + `description`. It then follows the
`## Instructions` prose to call `run_js`/`run_intent` with the exact JSON `data` shape you
document. **The instructions are a contract between the model and your code** — the field names
in `SKILL.md` must match what `index.html` reads from the parsed `data`.

## Skill types and their anatomy

| Type | Files | Mechanism |
|------|-------|-----------|
| `text` | `SKILL.md` | Persona/knowledge only; no tool call. Instructions shape model behavior. |
| `js` | `SKILL.md`, `scripts/index.html` (+ optional `.js`) | `run_js`; logic in webview, can `fetch()`/CDN/WASM. |
| `js-webview` | `+ assets/webview.html` | `run_js` returns a `webview` object the app renders in chat. |
| `native` | `SKILL.md` | `run_intent` maps to OS capability. |

### The JS contract (`scripts/index.html`)

```js
window['ai_edge_gallery_get_result'] = async (data, secret) => {
  try {
    const input = JSON.parse(data);           // fields come from SKILL.md instructions
    const out = await doWork(input.someField, secret);
    return JSON.stringify({ result: out });    // success
  } catch (e) {
    return JSON.stringify({ error: e.message }); // failure
  }
};
```

The return is **always a stringified JSON** with either `result` or `error`. Optional extras:
- `image: { base64: "..." }` — renders an image in chat.
- `webview: { url: "webview.html", aspectRatio: 1.0 }` — `url` is relative to `assets/`;
  default aspect ratio is `1.333`. Pass dynamic data to the webview via URL query params
  (`webview.html?foo=bar`) and read it with `URLSearchParams` on the page.

### Secrets

Never route API keys through the prompt. Set `metadata: { require-secret: true }` (and optional
`require-secret-description`) in frontmatter — the app shows a native input dialog and passes the
value as the **second argument** (`secret`) to `ai_edge_gallery_get_result`.

## Authoring conventions for this repo

- **Folder name == frontmatter `name`**, both kebab-case. The validator enforces this.
- Keep `description` short and trigger-oriented — it is the model's only signal for relevance.
  Include a `## Examples` section with sample user phrasings to sharpen matching.
- In `## Instructions`, spell out **every** `data` field with type and whether it's required,
  and tell the model how to extract/normalize it (see `skills` examples for the level of detail,
  e.g. "extract ONLY the primary entity, remove question words").
- Keep results compact — on-device context windows are small. Truncate long API responses and
  say so in the returned text.
- A skill's `index.html` must be self-contained or pull deps from CDN; there is no bundler.
- For hosting: JS skills must be served from a real host (GitHub Pages with a `.nojekyll` file,
  Cloudflare, etc.), not `raw.githubusercontent.com`.

## Reference

Full upstream spec: https://github.com/google-ai-edge/gallery/tree/main/skills
Native intent source: `Android/.../customtasks/agentchat/IntentHandler.kt` in that repo.
