#!/usr/bin/env python3
"""Scaffold a new AI Edge Gallery (Gemma) skill.

Usage:
    python3 scripts/new_skill.py <skill-name> --type <text|js|js-webview|native> \
        --description "One-line description the model uses to pick this skill."

Creates skills/<skill-name>/ with the right files for the chosen type. Run
validate_skill.py afterward to confirm the result is well-formed.
"""
import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"

KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def skill_md(name, description, kind):
    fm = [f"name: {name}", f"description: {description}"]
    if kind == "native":
        body = f"""# {name}

## Examples

- "..."

## Instructions

Call the `run_intent` tool with the following exact parameters:

- intent: send_email
- parameters: A JSON string with the following fields:
  - extra_email: String. The recipient email address.
  - extra_subject: String. The email subject.
  - extra_text: String. The email body.
"""
    elif kind == "text":
        body = f"""# {name}

## Persona

You are <describe the persona / role>.

## Instructions

When the user <describes trigger condition>:
1. ...
2. ...
"""
    else:  # js / js-webview
        webview_note = ""
        if kind == "js-webview":
            webview_note = (
                "\nThis skill renders an interactive view in chat after running.\n"
            )
        body = f"""# {name}
{webview_note}
## Examples

- "..."

## Instructions

Call the `run_js` tool with the following exact parameters:

- data: A JSON string with the following field(s):
  - input: String. Required. <Describe exactly what to extract and how to normalize it.>
"""
    return "---\n" + "\n".join(fm) + "\n---\n\n" + body


INDEX_HTML_JS = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{title}</title>
  </head>
  <body>
    <script>
      // The app calls this with `data` = the stringified JSON from SKILL.md instructions.
      // Return a STRINGIFIED JSON with `result` (success) or `error` (failure).
      window["ai_edge_gallery_get_result"] = async (data) => {{
        try {{
          const input = JSON.parse(data);
          if (!input.input) return JSON.stringify({{ error: "Missing required field: input" }});

          const output = await run(input.input);

          return JSON.stringify({{ result: output }});
        }} catch (e) {{
          console.error(e);
          return JSON.stringify({{ error: `Failed: ${{e.message}}` }});
        }}
      }};

      async function run(input) {{
        // TODO: implement. You can fetch() APIs, import CDN libs, use WebCrypto/WASM, etc.
        return `Processed: ${{input}}`;
      }}
    </script>
  </body>
</html>
"""

INDEX_HTML_WEBVIEW = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{title}</title>
  </head>
  <body>
    <script>
      window["ai_edge_gallery_get_result"] = async (data) => {{
        try {{
          const input = JSON.parse(data);
          if (!input.input) return JSON.stringify({{ error: "Missing required field: input" }});

          // Pass dynamic data to the rendered page via URL query params.
          const params = new URLSearchParams({{ value: String(input.input) }});

          return JSON.stringify({{
            result: "Rendered interactive view.",
            webview: {{ url: `webview.html?${{params.toString()}}`, aspectRatio: 1.333 }},
          }});
        }} catch (e) {{
          console.error(e);
          return JSON.stringify({{ error: `Failed: ${{e.message}}` }});
        }}
      }};
    </script>
  </body>
</html>
"""

WEBVIEW_HTML = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{title} view</title>
    <style>
      body {{ font-family: system-ui, sans-serif; margin: 0; display: grid; place-items: center;
              height: 100vh; }}
    </style>
  </head>
  <body>
    <div id="app">Loading…</div>
    <script>
      const value = new URLSearchParams(location.search).get("value");
      document.getElementById("app").textContent = value ?? "(no data)";
    </script>
  </body>
</html>
"""


def main():
    p = argparse.ArgumentParser(description="Scaffold a new AI Edge Gallery skill.")
    p.add_argument("name", help="Skill name in kebab-case (also the folder name).")
    p.add_argument("--type", default="js",
                   choices=["text", "js", "js-webview", "native"])
    p.add_argument("--description", required=True,
                   help="One-line description the model uses to select this skill.")
    p.add_argument("--force", action="store_true", help="Overwrite if the folder exists.")
    args = p.parse_args()

    if not KEBAB.match(args.name):
        sys.exit(f"error: '{args.name}' is not kebab-case (e.g. my-cool-skill).")

    dest = SKILLS_DIR / args.name
    if dest.exists() and not args.force:
        sys.exit(f"error: {dest} already exists (use --force to overwrite).")

    title = args.name.replace("-", " ").title()
    (dest).mkdir(parents=True, exist_ok=True)
    (dest / "SKILL.md").write_text(skill_md(args.name, args.description, args.type))

    if args.type in ("js", "js-webview"):
        scripts = dest / "scripts"
        scripts.mkdir(exist_ok=True)
        tpl = INDEX_HTML_WEBVIEW if args.type == "js-webview" else INDEX_HTML_JS
        (scripts / "index.html").write_text(tpl.format(title=title))
    if args.type == "js-webview":
        assets = dest / "assets"
        assets.mkdir(exist_ok=True)
        (assets / "webview.html").write_text(WEBVIEW_HTML.format(title=title))

    rel = dest.relative_to(REPO_ROOT)
    print(f"Created {args.type} skill at {rel}/")
    print(f"Next: edit {rel}/SKILL.md, then `python3 scripts/validate_skill.py {rel}`")


if __name__ == "__main__":
    main()
