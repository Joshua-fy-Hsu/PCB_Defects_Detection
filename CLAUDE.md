# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

YOLOv12-based PCB defect detection (4 classes: missing hole, mouse bite, open circuit, short circuit), packaged as a simulated AOI inspection station for the **Machine Vision Inspection (MVI)** course final project. The pipeline trains on an augmented PCB dataset (brightness, contrast, flip, rotation) using `yolov12s.pt` pretrained weights. See [README.md](README.md) for the full experiment writeup and metrics.

> **Important — course framing:** This work was originally submitted to a Deep Learning course (baseline vs enhanced comparison). For the MVI course re-submission, the **baseline pipeline has been removed**; everything in this repo focuses on the enhanced model only. Do not reintroduce baseline references.

## Commands

Install deps:
```
pip install -r code/requirements.txt
```

Train (from repo root so `runs/` lands in the expected place):
```
python code/train.py --config configs/yolov12_enhanced.yaml
```

Inference on a folder of test images:
```
python code/infer.py --model runs/enhanced/weights/best.pt --source dataset/Enhanced/test/images --output outputs --name enhanced
```

Summarize final metrics from `results.csv`:
```
python code/eval_metrics.py
```

Launch the simulated AOI dashboard:
```
streamlit run code/dashboard.py
```

The Python entry points are thin wrappers — they shell out to the Ultralytics CLI (`yolo detect train cfg=...` and `yolo detect predict ...`). Any Ultralytics CLI flag can be added to the YAML configs.

## Architecture notes

- [code/train.py](code/train.py) and [code/infer.py](code/infer.py) are `subprocess.run` wrappers around the `yolo` CLI. There is no custom model code — all training/inference logic lives in the `ultralytics` package.
- **Ultralytics version matters**: the checkpoint at `runs/enhanced/weights/best.pt` was trained with the YOLOv12 fork at `github.com/sunsmarterjie/yolov12` (which uses `AAttn` with separate `qk`/`v` layers). The official `ultralytics` package on PyPI ships a refactored `AAttn` with a combined `qkv` layer and **will fail to load this checkpoint** with `AttributeError: 'AAttn' object has no attribute 'qkv'`. `code/requirements.txt` pins the fork via `pip install git+https://github.com/sunsmarterjie/yolov12.git`.
- [code/dashboard.py](code/dashboard.py) is a Streamlit AOI simulator: feeds the first 20 test images through the enhanced model one at a time, shows live PASS/FAIL verdicts, defect-class distribution, yield trend, and consecutive-fail alarm (≥3 → SPC-style warning). Appends every result to `outputs/inspection_log.csv`. Two render paths exist (running vs idle) — only one must execute per Streamlit rerun, otherwise duplicate `plotly_chart` keys error out.
- Configs in [configs/](configs/) are passed verbatim as the Ultralytics `cfg=` file. The `data:` field points at a `data.yaml` inside `dataset/Enhanced/` — **this path is currently absolute and hardcoded to `D:/University/Junior/Deep_Learning/PCB_Defects/...`, which does not match the current repo location. Update the `data:` path before training.**
- Training results land in `runs/<name>/` (per the `project:`/`name:` fields). [code/eval_metrics.py](code/eval_metrics.py) reads `runs/enhanced/results.csv` and extracts the last-row `metrics/precision(B)`, `recall(B)`, `mAP50(B)`, `mAP50-95(B)` columns.
- `outputs/` holds the curated artifacts referenced by the README (training curves, confusion matrices, sample predictions); `runs/` holds raw Ultralytics output. Keep them separate.
- `dataset/` is gitignored (too large — 3000+ images). Re-download from the Roboflow link in the original `data.yaml`. Pretrained checkpoints (`yolov12s.pt`, `yolov12n.pt`) live at the repo root and are tracked.
