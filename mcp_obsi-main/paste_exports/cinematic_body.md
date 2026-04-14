## User

/paste-conversation-to-obsidian 아래 대화 옵시디언에 업데이트 하라

## Pasted content

판정: **조건부 예.** RTX 4060 8GB 기준으로 **FP16 + tile 128 + RAFT small + EXR→PNG 업스케일** 구성은 바로 운영 가능합니다.
근거: 현재 제안은 최신 외부 규정 이슈가 아닌 **로컬 실행형 영상 파이프라인** 설계이므로 웹 검증 필수 항목은 아닙니다. 다만 **OCIO/Real-ESRGAN 바이너리 경로는 가정**입니다.
다음행동: 아래 **운영형 폴더 트리 + 배치 스크립트 + 프리셋 3종**을 그대로 복붙해 배포본으로 쓰면 됩니다.

## Exec

목표는 **원본 구도 보존 + 시네마틱 강화 + 8GB VRAM 안정 운용**입니다.
기본 전략은 `도시 네온 / 비 내리는 거리 / 실내 라운지` 3개 프리셋을 JSON으로 분리하고, 공통 러너는 Python 1개, 실행은 BAT 3개로 나눕니다.
가정: `realesrgan-ncnn-vulkan.exe`, `python`, `ffmpeg`, `OCIO config` 경로가 로컬에 이미 있거나 지정 가능합니다.

## 운영 폴더 구조

```text
cinematic_pipeline/
├─ input/
│  ├─ city_neon/
│  ├─ rain_street/
│  └─ indoor_lounge/
├─ output/
│  ├─ exr/
│  ├─ png/
│  └─ logs/
├─ presets/
│  ├─ city_neon.json
│  ├─ rain_street.json
│  └─ indoor_lounge.json
├─ tools/
│  ├─ realesrgan-ncnn-vulkan.exe
│  └─ ffmpeg.exe
├─ ocio/
│  └─ config.ocio
├─ run_pipeline.py
├─ install_env.bat
├─ run_city_neon.bat
├─ run_rain_street.bat
├─ run_indoor_lounge.bat
└─ requirements.txt
```

## 핵심 운영값

| No | Item         |          Value | Risk | Evidence |
| -- | ------------ | -------------: | ---- | -------- |
| 1  | GPU          |   RTX 4060 8GB | 낮음   | 사용자 환경   |
| 2  | 업스케일         |           FP16 | 낮음   | VRAM 절감  |
| 3  | tile         |            128 | 낮음   | 8GB 안정권  |
| 4  | Flow model   |     RAFT small | 낮음   | 메모리 절감   |
| 5  | EXR 저장       | 16-bit half 권장 | 낮음   | 후반 자유도   |
| 6  | Bloom sigma  |     8.00~14.00 | 중간   | 과하면 번짐   |
| 7  | Rain density |  0.0020~0.0040 | 중간   | 과하면 합성 티 |
| 8  | 배치           |              1 | 낮음   | VRAM 안정  |

## 1) requirements.txt

```txt
torch
torchvision
opencv-python
numpy
PyOpenColorIO
imageio
imageio-ffmpeg
tqdm
```

## 2) install_env.bat

```bat
@echo off
setlocal

cd /d "%~dp0"

if not exist .venv (
    py -3.11 -m venv .venv
)

call .venv\Scripts\activate

python -m pip install --upgrade pip
pip install -r requirements.txt

if not exist output\exr mkdir output\exr
if not exist output\png mkdir output\png
if not exist output\logs mkdir output\logs

echo.
echo [OK] Environment installed.
echo [NOTE] Check tools\realesrgan-ncnn-vulkan.exe and ocio\config.ocio path.
pause
```

## 3) 프리셋 3종

### presets\city_neon.json

```json
{
  "name": "city_neon",
  "input_dir": "input/city_neon",
  "output_exr_dir": "output/exr/city_neon",
  "output_png_dir": "output/png/city_neon",
  "seed": 42,
  "apply_rain": false,
  "rain_density": 0.0,
  "rain_gain": 0.0,
  "rain_length": 0,
  "bloom_threshold": 0.78,
  "bloom_sigma": 10.0,
  "bloom_gain": 0.18,
  "contrast_gain": 1.03,
  "saturation_gain": 1.05,
  "upscale_factor": 4,
  "tile": 128,
  "fp16": true,
  "realesrgan_model": "realesr-animevideov3"
}
```

### presets\rain_street.json

```json
{
  "name": "rain_street",
  "input_dir": "input/rain_street",
  "output_exr_dir": "output/exr/rain_street",
  "output_png_dir": "output/png/rain_street",
  "seed": 77,
  "apply_rain": true,
  "rain_density": 0.0032,
  "rain_gain": 1.55,
  "rain_length": 11,
  "bloom_threshold": 0.80,
  "bloom_sigma": 12.0,
  "bloom_gain": 0.22,
  "contrast_gain": 1.02,
  "saturation_gain": 1.00,
  "upscale_factor": 4,
  "tile": 128,
  "fp16": true,
  "realesrgan_model": "realesrgan-x4plus"
}
```

### presets\indoor_lounge.json

```json
{
  "name": "indoor_lounge",
  "input_dir": "input/indoor_lounge",
  "output_exr_dir": "output/exr/indoor_lounge",
  "output_png_dir": "output/png/indoor_lounge",
  "seed": 101,
  "apply_rain": false,
  "rain_density": 0.0,
  "rain_gain": 0.0,
  "rain_length": 0,
  "bloom_threshold": 0.74,
  "bloom_sigma": 8.0,
  "bloom_gain": 0.15,
  "contrast_gain": 1.02,
  "saturation_gain": 1.04,
  "upscale_factor": 4,
  "tile": 128,
  "fp16": true,
  "realesrgan_model": "realesrgan-x4plus"
}
```

## 4) run_pipeline.py

```python
import os
import json
import cv2
import time
import math
import shutil
import random
import subprocess
import numpy as np
from tqdm import tqdm

import torch
from torchvision.models.optical_flow import raft_small


ROOT = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.join(ROOT, "tools")
OCIO_DIR = os.path.join(ROOT, "ocio")

REALESRGAN_EXE = os.path.join(TOOLS_DIR, "realesrgan-ncnn-vulkan.exe")
FFMPEG_EXE = os.path.join(TOOLS_DIR, "ffmpeg.exe")
LOG_DIR = os.path.join(ROOT, "output", "logs")


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def now_str():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def write_log(log_path: str, line: str):
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"{now_str()} | {line}\n")


def load_preset(preset_path: str):
    with open(preset_path, "r", encoding="utf-8") as f:
        return json.load(f)


def srgb_to_linear(img_bgr_u8):
    img = img_bgr_u8.astype(np.float32) / 255.0
    img = img[..., ::-1]  # BGR -> RGB
    out = np.where(img <= 0.04045, img / 12.92, ((img + 0.055) / 1.055) ** 2.4)
    return out.astype(np.float32)


def linear_to_srgb(img_rgb):
    img = np.clip(img_rgb, 0.0, 1.0)
    out = np.where(img <= 0.0031308, img * 12.92, 1.055 * np.power(img, 1.0 / 2.4) - 0.055)
    out = np.clip(out, 0.0, 1.0)
    out = (out[..., ::-1] * 255.0).astype(np.uint8)  # RGB -> BGR
    return out


def apply_basic_grade(img, contrast_gain=1.0, saturation_gain=1.0):
    x = img.copy()
    x = np.clip((x - 0.5) * contrast_gain + 0.5, 0.0, 1.0)

    lum = (0.2126 * x[..., 0] + 0.7152 * x[..., 1] + 0.0722 * x[..., 2])[..., None]
    x = np.clip(lum + (x - lum) * saturation_gain, 0.0, 1.0)
    return x


def make_rain(h, w, density, gain, length, seed):
    rng = np.random.RandomState(seed)
    rain = (rng.rand(h, w) < density).astype(np.float32) * gain
    if length > 1:
        rain = cv2.blur(rain, (1, int(length)))
    rain = rain[..., None]
    return np.repeat(rain, 3, axis=2)


def warp_with_flow(img, flow):
    h, w = flow.shape[:2]
    grid_x, grid_y = np.meshgrid(np.arange(w), np.arange(h))
    map_x = (grid_x + flow[..., 0]).astype(np.float32)
    map_y = (grid_y + flow[..., 1]).astype(np.float32)
    return cv2.remap(img, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def make_bloom(img_linear, threshold, sigma, gain):
    lum = (0.2126 * img_linear[..., 0] + 0.7152 * img_linear[..., 1] + 0.0722 * img_linear[..., 2])[..., None]
    mask = np.maximum(lum - threshold, 0.0)
    src = img_linear * mask
    bloom = cv2.GaussianBlur(src, (0, 0), sigmaX=sigma, sigmaY=sigma)
    return bloom * gain


def save_exr(path, img_linear):
    ensure_dir(os.path.dirname(path))
    exr = np.clip(img_linear, 0.0, 1.0).astype(np.float32)
    cv2.imwrite(path, exr)


def save_png(path, img_linear):
    ensure_dir(os.path.dirname(path))
    bgr = linear_to_srgb(img_linear)
    cv2.imwrite(path, bgr)


def collect_frames(folder):
    files = []
    for f in sorted(os.listdir(folder)):
        if f.lower().endswith((".png", ".jpg", ".jpeg")):
            files.append(os.path.join(folder, f))
    return files


def run_upscale(in_dir, out_dir, scale, tile, fp16, model, log_path):
    ensure_dir(out_dir)

    cmd = [
        REALESRGAN_EXE,
        "-i", in_dir,
        "-o", out_dir,
        "-s", str(scale),
        "-t", str(tile),
        "-n", model
    ]
    if fp16:
        cmd += ["-f", "jpg"]

    write_log(log_path, f"UPSCALE START | {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        write_log(log_path, "UPSCALE DONE")
    except Exception as e:
        write_log(log_path, f"UPSCALE ERROR | {e}")


def build_video_from_png(input_dir, out_mp4, fps, log_path):
    pattern = os.path.join(input_dir, "%06d.png")
    cmd = [
        FFMPEG_EXE,
        "-y",
        "-framerate", str(fps),
        "-i", pattern,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        out_mp4
    ]
    write_log(log_path, f"FFMPEG START | {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        write_log(log_path, f"FFMPEG DONE | {out_mp4}")
    except Exception as e:
        write_log(log_path, f"FFMPEG ERROR | {e}")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--preset", required=True, help="preset json path")
    parser.add_argument("--fps", type=int, default=24)
    args = parser.parse_args()

    preset = load_preset(args.preset)
    preset_name = preset["name"]
    log_path = os.path.join(LOG_DIR, f"{preset_name}_{time.strftime('%Y%m%d_%H%M%S')}.log")
    ensure_dir(LOG_DIR)

    input_dir = os.path.join(ROOT, preset["input_dir"])
    out_exr_dir = os.path.join(ROOT, preset["output_exr_dir"])
    out_png_dir = os.path.join(ROOT, preset["output_png_dir"])

    ensure_dir(out_exr_dir)
    ensure_dir(out_png_dir)

    frames = collect_frames(input_dir)
    if len(frames) < 1:
        write_log(log_path, f"ERROR | No frames in {input_dir}")
        print("No input frames found.")
        return

    device = "cuda" if torch.cuda.is_available() else "cpu"
    write_log(log_path, f"DEVICE | {device}")

    model = raft_small(weights=None).eval().to(device)

    prev_rgb = None
    prev_name = None

    for idx, frame_path in enumerate(tqdm(frames, desc=f"Processing {preset_name}")):
        bgr = cv2.imread(frame_path, cv2.IMREAD_COLOR)
        rgb_lin = srgb_to_linear(bgr)

        rgb_lin = apply_basic_grade(
            rgb_lin,
            contrast_gain=preset.get("contrast_gain", 1.0),
            saturation_gain=preset.get("saturation_gain", 1.0)
        )

        if prev_rgb is not None:
            ta = torch.from_numpy(prev_rgb.transpose(2, 0, 1)).unsqueeze(0).to(device)
            tb = torch.from_numpy(rgb_lin.transpose(2, 0, 1)).unsqueeze(0).to(device)

            with torch.no_grad():
                out = model(ta, tb)
                flow = out["flow1"][0].detach().cpu().numpy().transpose(1, 2, 0)
        else:
            flow = np.zeros((rgb_lin.shape[0], rgb_lin.shape[1], 2), dtype=np.float32)

        comp = rgb_lin.copy()

        if preset.get("apply_rain", False):
            rain = make_rain(
                h=comp.shape[0],
                w=comp.shape[1],
                density=preset.get("rain_density", 0.003),
                gain=preset.get("rain_gain", 1.0),
                length=preset.get("rain_length", 9),
                seed=preset.get("seed", 42) + idx
            )
            rain = warp_with_flow(rain, -flow)
            comp = np.clip(comp + rain, 0.0, 1.0)

        bloom = make_bloom(
            comp,
            threshold=preset.get("bloom_threshold", 0.8),
            sigma=preset.get("bloom_sigma", 12.0),
            gain=preset.get("bloom_gain", 0.2)
        )
        comp = np.clip(comp + bloom, 0.0, 1.0)

        exr_name = f"{idx + 1:06d}.exr"
        png_name = f"{idx + 1:06d}.png"

        save_exr(os.path.join(out_exr_dir, exr_name), comp)
        save_png(os.path.join(out_png_dir, png_name), comp)

        prev_rgb = rgb_lin
        prev_name = frame_path

    upscaled_dir = out_png_dir + "_x4"
    run_upscale(
        in_dir=out_png_dir,
        out_dir=upscaled_dir,
        scale=preset.get("upscale_factor", 4),
        tile=preset.get("tile", 128),
        fp16=preset.get("fp16", True),
        model=preset.get("realesrgan_model", "realesrgan-x4plus"),
        log_path=log_path
    )

    out_mp4 = os.path.join(ROOT, "output", f"{preset_name}_x4.mp4")
    build_video_from_png(upscaled_dir, out_mp4, args.fps, log_path)

    write_log(log_path, "PIPELINE DONE")
    print(f"Done: {preset_name}")


if __name__ == "__main__":
    main()
```

## 5) 실행 BAT 3종

### run_city_neon.bat

```bat
@echo off
setlocal
cd /d "%~dp0"
call .venv\Scripts\activate
python run_pipeline.py --preset presets\city_neon.json --fps 24
pause
```

### run_rain_street.bat

```bat
@echo off
setlocal
cd /d "%~dp0"
call .venv\Scripts\activate
python run_pipeline.py --preset presets\rain_street.json --fps 24
pause
```

### run_indoor_lounge.bat

```bat
@echo off
setlocal
cd /d "%~dp0"
call .venv\Scripts\activate
python run_pipeline.py --preset presets\indoor_lounge.json --fps 24
pause
```

## 운영 포인트

### A. 도시 네온

* 네온 반사광 강조
* 블룸은 얇고 고급스럽게
* 차체/유리/젖은 바닥 반사에 유리

### B. 비 내리는 거리

* 광류 기반 워프된 rain layer
* 카메라 고정 느낌 유지
* 호치민/사이공 야경 톤에 가장 잘 맞음

### C. 실내 라운지

* 하이라이트 번짐 최소
* 바 카운터/간접조명/우드 반사에 적합
* 원본 보존형 고급 무드

## 옵션 A/B/C

| Option | 내용                        |     Cost | Risk | Time   |
| ------ | ------------------------- | -------: | ---- | ------ |
| A      | 현재안 그대로                   | AED 0.00 | 낮음   | 즉시     |
| B      | ACES OCIO 정확 연결 추가        | AED 0.00 | 중간   | 30~60분 |
| C      | ffmpeg 인코딩 튜닝 + LUT 후반 추가 | AED 0.00 | 중간   | 1~2시간  |

## 바로 실행 순서

1. `tools` 폴더에 `realesrgan-ncnn-vulkan.exe`, `ffmpeg.exe` 배치
2. `input\city_neon` 등 폴더에 프레임 이미지 넣기
3. `install_env.bat` 1회 실행
4. 원하는 BAT 실행
5. 결과 확인

   * `output\exr\...`
   * `output\png\...`
   * `output\png\..._x4`
   * `output\*.mp4`
   * `output\logs\*.log`

## QA 체크리스트

* `realesrgan-ncnn-vulkan.exe` 실제 파일명 일치 여부
* Python venv 생성 여부
* CUDA 사용 시 `torch.cuda.is_available()` true 여부
* 입력 프레임 파일명이 정렬 가능한 형식인지
* EXR 저장 실패 시 OpenCV EXR 지원 빌드 여부 확인
* VRAM 부족 시 `tile=96` 또는 `upscale_factor=2`로 하향

## AMBER

가정:

1. 사용 환경이 Windows 11 기준입니다.
2. Real-ESRGAN ncnn 실행파일 경로가 `tools\realesrgan-ncnn-vulkan.exe` 입니다.
3. EXR 저장이 가능한 OpenCV 빌드입니다. 불가 시 PNG/TIFF로 대체해야 합니다.

## cmd

`/switch_mode BRIEF`
`/automate_workflow`
`/visualize_data --type=heatmap <csv>`

원하시면 다음 답변에서 바로 **당신 사진/프레임 기준으로 프리셋 수치까지 이미 맞춘 개인화 버전**으로 다시 정리해 드리겠습니다.
