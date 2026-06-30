---
name: ascii-cam
description: Take a photo with the camera and turn it into colorful ASCII art stamped with a random word.
---

# ASCII Cam

Opens the device camera in an interactive view. The user snaps a photo, and the skill renders it
as colorful ASCII art (each character tinted by the source pixel) with a randomly chosen word
stamped on top.

## Examples

- "Make ASCII art with my camera"
- "Turn a photo into ascii art"
- "ascii cam"
- "Take a picture and asciify it"

## Instructions

Call the `run_js` tool with the following exact parameters:

- data: A JSON string with the following field:
  - word: String. Optional. A specific word to stamp on the art. If the user did NOT request a
    particular word, OMIT this field entirely so the skill picks a random word itself. Only set
    it when the user explicitly names the word they want.

After the tool returns, briefly tell the user to tap **Capture** in the view to take the photo.
