# PCB Defect Detection Using YOLOv12
**Machine Vision Inspection – Final Project 2026**

---

## Overview
This project implements a YOLOv12 object-detection pipeline for printed-circuit-board (PCB) defect identification, packaged as a **simulated AOI (Automatic Optical Inspection) inspection station**.
The objective is to detect four major defect types:

- Missing Hole
- Mouse Bite
- Open Circuit
- Short Circuit

A **Streamlit dashboard** ([code/dashboard.py](code/dashboard.py)) is included to simulate a production line: test images are fed sequentially through the trained model, with live PASS/FAIL verdicts, yield trend, defect distribution, consecutive-fail alarms, and an auto-generated inspection log (CSV).

---

## Dataset
- **Source:** [Kaggle PCB Defects](https://www.kaggle.com/datasets/akhatova/pcb-defects), processed via **Roboflow** with augmentation (brightness, contrast, flip, rotation).
- **Format:** YOLOv12-compatible (images / labels)
- **Resolution:** 512 × 512 pixels
- **Splits:** Train 969 / Validation 92 / Test 46

> The `dataset/` folder is **not tracked in this repo** (too large). Re-download from the Roboflow link in [dataset/Enhanced/data.yaml](dataset/Enhanced/data.yaml).

---

## Environment
| Item | Specification |
|------|----------------|
| OS | Windows 11 |
| GPU | NVIDIA RTX 4060 Laptop GPU (8 GB VRAM) |
| Framework | PyTorch + YOLOv12 |
| Python | 3.10.19 |
| Optimizer | AdamW |
| Epochs | 100 |
| Batch Size | 16 |
| Image Size | 512 × 512 |
| Pretrained Weights | YOLOv12s.pt |

---

## Results

| Precision | Recall | mAP @ 0.5 | mAP @ 0.5 – 0.95 |
|-----------|--------|-----------|------------------|
| 0.9514 | 0.8710 | 0.9254 | 0.4789 |

### 1. Training and Validation Trends

![Training Curves](outputs/enhanced/results.png)

Box, classification, and distribution focal losses converge smoothly over 100 epochs.
Validation mAP@0.5–0.95 grows steadily and flattens near the end of training without divergence, indicating no overfitting.

---

### 2. Confusion Matrix

![Confusion Matrix](outputs/enhanced/confusion_matrix.png)

- Strong performance on **short circuit** and **missing hole**, exceeding 90% true-positive accuracy.
- Some false positives appear where background solder pads or silkscreen patterns resemble defects.

---

### 3. Qualitative Results

| Missing Hole | Open Circuit |
|---------------|---------------|
| ![Missing Hole](outputs/enhanced/sample_predictions/01_missing_hole_12_jpg.rf.7ff6e00a55ca57709e86012989a8235c.jpg) | ![Open Circuit](outputs/enhanced/sample_predictions/12_open_circuit_04_jpg.rf.f361bc284492a3fbf5ed7ee5c32e0b7e.jpg) |

- Clear and confident detections under varied lighting and orientation.
- Tight bounding boxes around defect edges.

---

## Repository Structure
```text
PCB_DEFECTS/
├── code/
│   ├── dashboard.py        # Streamlit AOI dashboard
│   ├── eval_metrics.py
│   ├── infer.py
│   ├── requirements.txt
│   └── train.py
│
├── configs/
│   └── yolov12_enhanced.yaml
│
├── dataset/                # Not tracked — download from Roboflow
│
├── outputs/
│   └── enhanced/
│       ├── results.png
│       ├── confusion_matrix.png
│       └── sample_predictions/
│
├── runs/
│   └── enhanced/
│       ├── results.csv
│       ├── *_curve.png
│       └── weights/best.pt
│
├── yolov12s.pt
└── README.md
```

---

## Running

Install:
```bash
pip install -r code/requirements.txt
```

Train:
```bash
python code/train.py --config configs/yolov12_enhanced.yaml
```

Inference on test folder:
```bash
python code/infer.py --model runs/enhanced/weights/best.pt --source dataset/Enhanced/test/images --output outputs --name enhanced
```

Launch simulated AOI dashboard:
```bash
streamlit run code/dashboard.py
```

---

## Key Findings

- YOLOv12 achieves stable convergence without overfitting over 100 epochs.
- Data augmentation (brightness / contrast / flip / rotation) effectively simulates production-line variance in lighting and orientation.
- The model is suitable for real-time PCB quality inspection with fewer false alarms on reflective or rotated boards.
- This workflow demonstrates an efficient and reproducible deep-learning pipeline for automated defect detection in manufacturing environments.
