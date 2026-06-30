# ASCII Cam

Take a photo with the device camera and turn it into colorful ASCII art stamped with a random word.

![type](https://img.shields.io/badge/JS-0a9396)
![type](https://img.shields.io/badge/Webview-ee9b00)
![type](https://img.shields.io/badge/Camera-656d4a)

An [AI Edge Gallery](https://github.com/google-ai-edge/gallery/tree/main/skills) Agent Skill for
on-device Gemma models.

## What it does

1. The model invokes the skill via `run_js`, which opens an interactive view in chat.
2. The view shows a live camera preview with a **Capture** button.
3. On capture, the current frame is sampled to a character grid and rendered as ASCII art where
   **each glyph is tinted by its source pixel color**, with a **random word** and a **random
   accent color** stamped on top. A **Retake** button restarts the camera.

The camera is opened with `getUserMedia()` **inside the webview** — no image is passed through the
model, which keeps it fast and private on-device.

## Usage

Say something like:

- "Make ASCII art with my camera"
- "Turn a photo into ascii art"
- "ascii cam"

To stamp a specific word instead of a random one, name it: "ascii cam with the word NOVA".

## Files

```
ascii-cam/
├── SKILL.md            # frontmatter + instructions the model reads
├── scripts/
│   └── index.html      # run_js entry point; returns the webview (forwards optional `word`)
└── assets/
    └── webview.html    # camera capture + ASCII rendering (the interactive view)
```

## Parameters

`run_js` `data` is a JSON string with one optional field:

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `word` | String | No | A specific word to stamp. Omit to let the skill pick a random word. |

## Install / test

JS skills must be served from a real host (camera and correct MIME types do **not** work from
`raw.githubusercontent.com`).

- **From URL** — serve the repo and point the app at the skill folder:
  ```bash
  python3 -m http.server 8000
  # Skills chip → + → Load skill from URL → http://<your-ip>:8000/skills/ascii-cam
  ```
- **Local import** — push the folder and import it:
  ```bash
  adb push ascii-cam /sdcard/Download/
  # Skills chip → + → Import local skill → select the ascii-cam folder
  ```

Grant the in-app webview **camera permission** when prompted. The live preview is mirrored
(selfie-style); the captured frame is mirrored to match, so the ASCII matches what you saw.

## Notes

- The luminance→glyph ramp runs light→dense (`" .:-=+*#%@"`) so bright pixels render as visible
  glyphs and dark pixels fade into the black background.
- Grid size adapts to the viewport (~48–110 columns); monospace cells are treated as ~2× taller
  than wide to keep proportions correct.

Validate with: `python3 scripts/validate_skill.py skills/ascii-cam`
