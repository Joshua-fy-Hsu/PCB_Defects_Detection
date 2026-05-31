"""
eval_metrics.py
----------------
Loads YOLOv12 evaluation metrics and compares baseline vs enhanced models.

Reads YOLOv12's `results.csv` files generated after training and computes
basic statistics: Precision, Recall, mAP@0.5, and mAP@0.5:0.95.
"""

import pandas as pd
import os


def summarize_results(csv_path: str):
    """
    Print final validation metrics from YOLOv12's results.csv file.

    Args:
        csv_path (str): Path to YOLO results.csv file (e.g., runs/train/results.csv).
    """
    if not os.path.exists(csv_path):
        print(f"[WARN] File not found: {csv_path}")
        return None

    df = pd.read_csv(csv_path)
    last_row = df.iloc[-1]

    summary = {
        "Precision": last_row.get("metrics/precision(B)", None),
        "Recall": last_row.get("metrics/recall(B)", None),
        "mAP@0.5": last_row.get("metrics/mAP50(B)", None),
        "mAP@0.5:0.95": last_row.get("metrics/mAP50-95(B)", None),
    }

    print(f"\nResults for {os.path.dirname(csv_path)}:")
    for k, v in summary.items():
        print(f"  {k:<12}: {v:.4f}" if v is not None else f"  {k:<12}: N/A")

    return summary


if __name__ == "__main__":
    print("=== Evaluating YOLOv12 Results ===")
    summarize_results("./runs/enhanced/results.csv")
