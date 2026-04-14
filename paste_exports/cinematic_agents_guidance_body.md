## User

/paste-conversation-to-obsidian 아래 대화 옵시디언 업로드 하라

## Pasted content

판정: **AMBER / 조건부 예** — 지금 주신 스펙만으로 **이 파이프라인용 초기 agent guidance 세트**는 바로 작성할 수 있습니다.
근거: 폴더 구조, 실행 BAT, preset JSON, Python runner, VRAM 운용값은 확인되지만 **실제 repo 증거 파일(README, package manifest, CI, tests/lint)** 이 없습니다. 현재 공식 문서도 공통 규칙은 `AGENTS.md`, Claude의 deterministic enforcement는 hooks, Gemini override는 `GEMINI.md`로 분리하는 방식을 뒷받침합니다.
다음행동: 아래 초안을 repo에 넣고, 실제 증거 파일이 생기면 **`[ASSUMPTION]` 줄부터 실증값으로 교체**하면 됩니다.

또 하나 확인된 리스크가 있습니다. PyTorch의 torchvision RAFT 예시는 **pretrained weights + `list_of_flows[-1]`** 패턴을 쓰는데, 지금 붙여주신 러너는 `raft_small(weights=None)`와 dict-style access를 사용합니다. 따라서 **rain warp 블록은 “구현 검증 필요”** 상태로 두는 편이 안전합니다.

## 검증됨 / 가정 / 누락

| No | Item                           | Status   | Value                                                                          | Risk | Evidence                |
| -- | ------------------------------ | -------- | ------------------------------------------------------------------------------ | ---- | ----------------------- |
| 1  | Project skeleton               | Verified | `input/`, `output/`, `presets/`, `tools/`, `ocio/`, BAT launchers              | 낮음   | 사용자 제공 스펙               |
| 2  | Run commands                   | Verified | `install_env.bat`, `run_*.bat`, `python run_pipeline.py --preset ... --fps 24` | 낮음   | 사용자 제공 스펙               |
| 3  | Preset model                   | Verified | `city_neon`, `rain_street`, `indoor_lounge`                                    | 낮음   | 사용자 제공 스펙               |
| 4  | Test / lint / format / CI      | Missing  | 확인 불가                                                                          | 중간   | repo evidence 부재        |
| 5  | OCIO execution                 | Missing  | 경로는 있으나 적용 로직은 현재 스크립트에 없음                                                     | 중간   | 사용자 제공 코드               |
| 6  | Optical-flow block correctness | Missing  | torchvision RAFT 사용법과 현재 코드 패턴 불일치 가능성                                         | 높음   | PyTorch vision RAFT docs |

### AGENTS.md

```md
# AGENTS.md

## Mission
- This repository is a local, Windows-first cinematic frame-processing pipeline.
- Primary goal: preserve original composition while applying preset-driven grade, optional rain warp, bloom, upscale, and MP4 assembly.
- Optimize for stable execution on an RTX 4060 8 GB class GPU before pursuing visual ambition.

- Repository name is treated as `cinematic_pipeline`.
# [ASSUMPTION] Inferred from the provided folder tree -- verify with: repository root folder name or README title.

## Source of Truth
- `run_pipeline.py`
- `install_env.bat`
- `run_city_neon.bat`
- `run_rain_street.bat`
- `run_indoor_lounge.bat`
- `presets/*.json`
- The folder contract shown in the provided tree
- Do not invent cloud steps, APIs, services, or extra entrypoints that are not defined by these sources.

## Runtime Profile
- Target GPU class: RTX 4060 8 GB
- Baseline operating profile: batch size 1, tile 128, RAFT small, EXR intermediate, PNG upscale, MP4 encode
- Reduce memory pressure by lowering tile size before changing preset semantics.

## Commands
- Install environment: `install_env.bat`
- Direct run: `python run_pipeline.py --preset presets/<preset>.json --fps 24`
- Preset launchers:
  - `run_city_neon.bat`
  - `run_rain_street.bat`
  - `run_indoor_lounge.bat`

- Launcher model assumes local virtual environment activation from `.venv\Scripts\activate`.
# [ASSUMPTION] Inferred from the provided BAT files -- verify with: actual repo launcher scripts.

## Project Structure
- `input/<preset>/`: source frames
- `output/exr/<preset>/`: linear intermediate frames
- `output/png/<preset>/`: graded PNG frames
- `output/png/<preset>_x4/`: upscaled frames
- `output/logs/`: run logs
- `presets/`: preset JSON definitions
- `tools/`: local executables such as ffmpeg and Real-ESRGAN
- `ocio/`: optional OCIO configuration path

## Boundaries
- Preserve original framing and scene composition unless the task explicitly requests a creative deviation.
- Keep preset behavior isolated. Do not change all presets for a one-look request.
- Ask before changing output naming, directory contracts, or executable file names.
- Ask before replacing Real-ESRGAN, RAFT, ffmpeg, or image I/O libraries.
- Do not add cloud services, telemetry, uploads, or external APIs.
- Do not delete user source frames from `input/`.

## Preset Rules
- `city_neon`: emphasize clean neon reflections with controlled bloom and no synthetic rain.
- `rain_street`: synthetic rain is allowed, but preserve a fixed-camera street realism.
- `indoor_lounge`: protect highlight rolloff, wood/glass reflections, and avoid aggressive bloom.
- Prefer tuning preset JSON values over hardcoding visual changes in Python.

## Implementation Rules
- Keep deterministic mechanics in Python or BAT files.
- Keep aesthetic intent in preset JSON or markdown references, not scattered constants.
- Preserve numbered frame naming (`%06d`) for downstream ffmpeg assembly.
- Maintain explicit log lines for each major stage: device, processing, upscale, encode, done/error.
- Treat OCIO as optional until an actual transform path is implemented.
- Treat optical-flow-dependent rain warping as implementation-sensitive and verify against the current torchvision RAFT API before refactoring that block.

## Verification
- Do not report success unless the selected preset run produces:
  - a log file in `output/logs/`
  - at least one EXR frame
  - at least one PNG frame
  - an upscaled output directory with rendered frames
  - a final MP4 in `output/`
- For performance-safe work, run the smallest relevant preset workflow first.
- Fix root causes. Do not suppress errors only to complete the run.

## Quality Gates
- No preset regression across other looks.
- No silent path changes.
- No destructive file operations in `input/`.
- No hardcoded secrets, machine-specific private paths, or hidden downloads.
- Keep Windows-first operability unless cross-platform support is explicitly requested.

## Known Gaps
- OCIO path exists in the provided structure but no active OCIO transform is evidenced in the provided runner.
- Test, lint, formatter, and CI commands were not provided.
- OpenCV EXR write support must be verified in the target environment.

- OpenCV EXR write support is assumed to exist.
# [ASSUMPTION] The provided plan expects EXR output -- verify with: one-frame smoke test on the target Python/OpenCV build.

## Output Contract
- Summarize what changed.
- List files touched.
- List commands run and pass/fail results.
- State remaining assumptions, runtime risks, and unverified areas.
```

### CLAUDE.md

```md
# CLAUDE.md

## Purpose
- Use `AGENTS.md` as the primary repository-wide contract.
- Keep this file short and Claude-specific.

## Claude-Specific Working Rules
- Prefer small diffs and minimal-scope edits.
- Use the smallest relevant preset run before broader changes.
- When command behavior changes, show the exact command and result.
- Do not claim OCIO, FP16, or rain-warp correctness unless verified in this repo.

## Separation of Concerns
- Keep always-on repo rules in `AGENTS.md`.
- Move deterministic enforcement to hooks.
- Move repeatable procedures to a skill only after trigger and pass/fail checks are stable.

## Verification
- For Python changes, run the directly relevant preset command first.
- For tool-path edits, verify executable resolution in `tools/`.
- For output-contract edits, verify frame numbering and MP4 assembly.
- Do not report completion until the relevant run has produced files and logs.

## Output Contract
- Summary of change
- Files touched
- Commands run with results
- Remaining risks or assumptions
```

### GEMINI.md

```md
# GEMINI.md

## Purpose
- `AGENTS.md` remains the primary cross-tool contract.
- This file only contains Gemini-specific overrides.

## Gemini Overrides
- Keep context narrow: prefer the current preset JSON, `run_pipeline.py`, and the active BAT launcher when debugging.
- Prefer editing preset JSON for look tuning before changing Python logic.
- Do not expand context with unrelated preset folders unless the task is explicitly cross-preset.
- If extra guidance files are added later, use markdown imports such as `@./file.md` only when those files actually exist.

## Verification
- Verify the exact preset path being discussed.
- Verify output folder naming remains consistent with the selected preset.
- Verify the final MP4 path remains under `output/`.

## Output Contract
- Summary of change
- Files touched
- Commands considered or run
- Unverified areas
```

### SKILL.md (draft note — repo에 넣지 않음)

```md
# NOT GENERATED

Reason:
- Workflow frequency was not evidenced in the provided input.
- Skill adoption criteria are therefore not fully met yet.

Promote to a skill only after confirming:
1. The same operation is repeated at least weekly.
2. The trigger can be stated in one sentence.
3. Completion can be verified with pass/fail checks.
```

## QA checklist

| Check                                  | Result | Note                                                        |
| -------------------------------------- | ------ | ----------------------------------------------------------- |
| commands exist                         | PASS   | 실행 BAT와 direct Python command는 제공됨                          |
| paths exist                            | PASS   | 폴더 계약이 명시됨                                                  |
| boundaries explicit                    | PASS   | 입력 보존, preset 격리, tool 교체 승인 조건 명시                          |
| no redundant architecture essay        | PASS   | 코드로 추론 가능한 설명은 최소화                                          |
| verification present                   | PASS   | log/frame/MP4 기준으로 pass/fail 정의                             |
| side-effect workflow manual by default | PASS   | destructive change, tool replacement, path contract 변경은 승인형 |
| tool-specific separation               | PASS   | 공통=`AGENTS.md`, Claude/Gemini override 분리                   |
| hooks/skills separation respected      | PASS   | deterministic enforcement는 hooks로, skill은 미생성 처리            |
| unsupported items fabricated           | PASS   | test/lint/CI는 비워 두고 Missing 처리                              |
| major implementation risk surfaced     | PASS   | RAFT block 검증 필요 표시 (PyTorch vision RAFT)                 |

실제 repo 증거 파일이 붙으면 이 초안은 **[ASSUMPTION] 제거판**으로 바로 줄일 수 있습니다.

## References (URLs from paste)

- developers.openai.com — Codex AGENTS.md
- docs.pytorch.org — Optical Flow RAFT
