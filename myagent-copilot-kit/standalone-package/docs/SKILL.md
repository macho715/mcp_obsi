# SKILL.md

name: photo-to-video-prompt-with-suggestion

description:
Generate one copy-paste-ready photo-to-video prompt for Gemini or Grok from an uploaded image and attach one short Korean suggestion set for the next refinement turn.

trigger:
Use this workflow when the user uploads a photo and asks for a video prompt, asks to animate a still image, or uploads only an image with no extra instruction.

non-trigger:
- Do not use for text-to-video requests without an image.
- Do not use for video-file editing.
- Do not use for photo restoration or image upscaling.
- Do not use when the user explicitly wants multiple prompt versions.

steps:
1. Analyze the uploaded image for subject type, framing, angle, lighting, mood, likely motion points, and risk points.
2. Decide the target profile: Gemini-first, Grok-specific, or shared Gemini/Grok-compatible.
3. Preserve source identity, facial features, outfit, composition, location, camera angle, and lighting unless the user asks for changes.
4. Build one prompt in this order: scene preservation, camera movement, subject animation, environmental animation, mood/style/pacing, optional `Audio:` sentence, final `Avoid:` line.
5. Default to one coherent short clip / one scene.
6. Apply ratio rules: `9:16` for explicit vertical requests, `16:9` for explicit landscape requests, otherwise preserve source composition first.
7. Output exactly one prompt block.
8. Unless the user asked for prompt-only output, add exactly three short Korean lines for `추천 톤`, `추천 수정`, and `다음 요청 예시`.
9. If the user asked for `상세`, add a 2-4 line Korean analysis summary before the normal output.

verification:
Pass only if all checks are true:
- exactly one final prompt block exists
- no split positive/negative/audio format exists
- English is used by default unless Korean prompt text was requested
- source scene is preserved unless the user asked for changes
- motion language is specific and stable
- `Avoid:` appears once at the end when relevant
- the additional suggestion exists unless prompt-only was requested
- the additional suggestion is exactly three short Korean lines
- the result is immediately pasteable into Gemini or Grok
