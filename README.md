# PCB Defect Detection Using YOLOv12
**Machine Vision Inspection (MVI) – Final Project 2026**

🔗 **Live project page:** https://joshua-fy-hsu.github.io/PCB_Defects_Detection/

---

## Overview
A YOLOv12 object-detection pipeline for printed-circuit-board (PCB) defect identification, packaged as a **simulated AOI (Automatic Optical Inspection) inspection station**.

The model detects four major defect types:

- **Missing Hole**
- **Mouse Bite**
- **Open Circuit**
- **Short Circuit**

An interactive **Streamlit dashboard** ([code/dashboard.py](code/dashboard.py)) simulates a production line: test images are fed sequentially through the trained model with live PASS/FAIL verdicts, running yield trend, defect-class distribution, an SPC-style consecutive-fail alarm (≥ 3 fails → warning), and an auto-generated inspection log (CSV).

---

## Dataset
- **Source:** [Kaggle PCB Defects](https://www.kaggle.com/datasets/akhatova/pcb-defects), processed via **Roboflow** with augmentation (brightness, contrast, flip, rotation).
- **Format:** YOLO-compatible (images / labels)
- **Resolution:** 512 × 512 pixels
- **Splits:** Train 969 / Validation 92 / Test 46

> The `dataset/` folder is **not tracked in this repo** (3000+ images, too large). Re-download from the Roboflow link in the original `data.yaml`.

---

## Environment & Training Configuration
| Item | Specification |
|------|----------------|
| OS | Windows 11 |
| GPU | NVIDIA RTX 4060 Laptop GPU (8 GB VRAM) |
| Framework | PyTorch + YOLOv12 |
| Python | 3.10 |
| Optimizer | AdamW |
| Epochs | 100 |
| Batch Size | 16 |
| Image Size | 512 × 512 |
| Pretrained Weights | `yolov12s.pt` |

Full config: [configs/yolov12_enhanced.yaml](configs/yolov12_enhanced.yaml).

---

## Results

| Precision | Recall | mAP @ 0.5 | mAP @ 0.5–0.95 |
|-----------|--------|-----------|-----------------|
| **0.9514** | **0.8710** | **0.9254** | **0.4789** |

*(final-epoch metrics from [runs/enhanced/results.csv](runs/enhanced/results.csv))*

### 1. Training & Validation Trends

![Training Curves](outputs/enhanced/results.png)

Box, classification, and distribution-focal losses converge smoothly over 100 epochs. Validation mAP@0.5–0.95 grows steadily and flattens near the end of training without divergence — no sign of overfitting.

### 2. Confusion Matrix

![Confusion Matrix](outputs/enhanced/confusion_matrix.png)

- Strong performance on **short circuit** and **missing hole**, exceeding 90% true-positive accuracy.
- Some false positives appear where background solder pads or silkscreen patterns resemble defects.

### 3. Qualitative Results

| Missing Hole | Open Circuit |
|---------------|---------------|
| ![Missing Hole](outputs/enhanced/sample_predictions/01_missing_hole_12_jpg.rf.7ff6e00a55ca57709e86012989a8235c.jpg) | ![Open Circuit](outputs/enhanced/sample_predictions/12_open_circuit_04_jpg.rf.f361bc284492a3fbf5ed7ee5c32e0b7e.jpg) |

Clear, confident detections with tight bounding boxes under varied lighting and orientation.

---

## Repository Structure
```text
PCB_Defects/
├── code/
│   ├── dashboard.py        # Streamlit AOI inspection dashboard
│   ├── train.py            # yolo CLI wrapper — training
│   ├── infer.py            # yolo CLI wrapper — batch inference
│   ├── eval_metrics.py     # summarize final metrics from results.csv
│   ├── make_figures.py     # generate presentation figures → outputs/figures/
│   ├── make_pptx.py        # build the final-project slide deck
│   └── requirements.txt
│
├── configs/
│   └── yolov12_enhanced.yaml
│
├── dataset/                # NOT tracked — download from Roboflow
│
├── metrics/enhanced/       # curated curves, confusion matrices, sample preds
├── outputs/
│   ├── enhanced/           # results.png, confusion_matrix.png, sample_predictions/
│   └── figures/            # presentation figures
│
├── runs/enhanced/          # raw Ultralytics output
│   ├── results.csv
│   ├── *_curve.png
│   └── weights/best.pt     # trained checkpoint
│
├── index.html              # GitHub Pages landing page
├── yolov12s.pt             # pretrained weights
└── README.md
```

---

## Setup & Usage

### Install
```bash
pip install -r code/requirements.txt
```

> **⚠️ Ultralytics version matters.** The checkpoint `runs/enhanced/weights/best.pt` was trained with the YOLOv12 fork at [`github.com/sunsmarterjie/yolov12`](https://github.com/sunsmarterjie/yolov12). The official `ultralytics` package on PyPI uses a refactored attention module and **will fail to load this checkpoint**. `requirements.txt` already pins the correct fork — do not replace it with the PyPI `ultralytics`.

### Train
Run from the repo root so `runs/` lands in the expected place:
```bash
python code/train.py --config configs/yolov12_enhanced.yaml
```
> Before training, update the `data:` field in [configs/yolov12_enhanced.yaml](configs/yolov12_enhanced.yaml) to point at your local `dataset/Enhanced/data.yaml`.

### Inference on a folder of test images
```bash
python code/infer.py --model runs/enhanced/weights/best.pt --source dataset/Enhanced/test/images --output outputs --name enhanced
```

### Summarize final metrics
```bash
python code/eval_metrics.py
```

### Launch the simulated AOI dashboard
```bash
streamlit run code/dashboard.py
```

---

## Key Findings

- YOLOv12 achieves stable convergence without overfitting over 100 epochs.
- Augmentation (brightness / contrast / flip / rotation) effectively simulates production-line variance in lighting and orientation.
- The model is well suited to real-time PCB quality inspection, with few false alarms on reflective or rotated boards.
- The pipeline demonstrates an efficient, reproducible deep-learning workflow for automated defect detection in manufacturing — from training to a deployable inspection-station simulation.
