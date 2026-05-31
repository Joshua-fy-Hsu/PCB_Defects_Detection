"""
產生簡報用 6 張視覺化圖
輸出至 outputs/figures/
"""
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from PIL import Image, ImageEnhance, ImageOps

REPO = Path(__file__).resolve().parent.parent
SAMPLES = REPO / "outputs" / "enhanced" / "sample_predictions"
OUT = REPO / "outputs" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

# 中文字型（Windows 內建）
plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei", "Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

CLASS_ZH = {
    "missing_hole": "缺孔 Missing Hole",
    "mouse_bite":   "鼠咬 Mouse Bite",
    "open_circuit": "斷路 Open Circuit",
    "short":        "短路 Short Circuit",
}
CLASS_COLORS = {
    "missing_hole": "#EF4444",
    "mouse_bite":   "#F59E0B",
    "open_circuit": "#3B82F6",
    "short":        "#8B5CF6",
}


def pick_sample(prefix: str) -> Path:
    matches = sorted(SAMPLES.glob(f"*_{prefix}_*.jpg"))
    if not matches:
        raise FileNotFoundError(f"找不到 {prefix} 樣本")
    return matches[0]


# ============================================================
# Fig 1: 四類缺陷對照圖
# ============================================================
def fig1_defect_samples():
    fig, axes = plt.subplots(2, 2, figsize=(10, 10))
    fig.suptitle("PCB 四類常見缺陷", fontsize=20, fontweight="bold", y=0.98)

    for ax, (key, zh) in zip(axes.flat, CLASS_ZH.items()):
        img = Image.open(pick_sample(key))
        ax.imshow(img)
        ax.set_title(zh, fontsize=16, color=CLASS_COLORS[key], fontweight="bold",
                     pad=10)
        ax.axis("off")
        for spine in ax.spines.values():
            spine.set_edgecolor(CLASS_COLORS[key])
            spine.set_linewidth(3)

    plt.tight_layout()
    fig.savefig(OUT / "fig1_defect_samples.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("[OK] Fig 1: defect samples")


# ============================================================
# Fig 2: 系統架構側視圖
# ============================================================
def fig2_system_architecture():
    fig, ax = plt.subplots(figsize=(12, 9))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 10)
    ax.axis("off")

    # 暗箱外框（虛線）
    enclosure = mpatches.FancyBboxPatch(
        (0.5, 0.5), 11, 9, boxstyle="round,pad=0.05",
        edgecolor="#475569", facecolor="#F1F5F9", linestyle="--", linewidth=2,
    )
    ax.add_patch(enclosure)
    ax.text(0.7, 9.2, "暗箱（隔絕環境光）", fontsize=11, color="#475569", style="italic")

    # 相機
    cam = mpatches.FancyBboxPatch(
        (5, 7.5), 2, 1, boxstyle="round,pad=0.05",
        edgecolor="#1E293B", facecolor="#CBD5E1", linewidth=2,
    )
    ax.add_patch(cam)
    ax.text(6, 8.0, "工業相機\n(5MP CMOS)", ha="center", va="center",
            fontsize=10, fontweight="bold")

    # 鏡頭
    lens = mpatches.FancyBboxPatch(
        (5.4, 6.5), 1.2, 0.8, boxstyle="round,pad=0.03",
        edgecolor="#1E293B", facecolor="#94A3B8", linewidth=2,
    )
    ax.add_patch(lens)
    ax.text(6, 6.9, "遠心鏡頭", ha="center", va="center", fontsize=9, fontweight="bold")

    # 同軸光
    coax = mpatches.FancyBboxPatch(
        (4.5, 5.3), 3, 0.9, boxstyle="round,pad=0.03",
        edgecolor="#0369A1", facecolor="#BAE6FD", linewidth=2,
    )
    ax.add_patch(coax)
    ax.text(6, 5.75, "同軸光源 (Coaxial)", ha="center", va="center",
            fontsize=10, fontweight="bold", color="#0369A1")

    # 環形光
    ring_l = mpatches.FancyBboxPatch(
        (3.8, 4.0), 1.2, 0.8, boxstyle="round,pad=0.03",
        edgecolor="#15803D", facecolor="#BBF7D0", linewidth=2,
    )
    ring_r = mpatches.FancyBboxPatch(
        (7.0, 4.0), 1.2, 0.8, boxstyle="round,pad=0.03",
        edgecolor="#15803D", facecolor="#BBF7D0", linewidth=2,
    )
    ax.add_patch(ring_l); ax.add_patch(ring_r)
    ax.text(4.4, 4.4, "環形光", ha="center", va="center", fontsize=9,
            color="#15803D", fontweight="bold")
    ax.text(7.6, 4.4, "環形光", ha="center", va="center", fontsize=9,
            color="#15803D", fontweight="bold")

    # 光路示意（細虛線）
    for x in [5.5, 6.0, 6.5]:
        ax.plot([x, x], [5.3, 3.0], color="#0EA5E9", linewidth=0.8,
                linestyle=":", alpha=0.6)
    ax.plot([4.4, 5.7], [4.0, 3.0], color="#22C55E", linewidth=0.8,
            linestyle=":", alpha=0.6)
    ax.plot([7.6, 6.3], [4.0, 3.0], color="#22C55E", linewidth=0.8,
            linestyle=":", alpha=0.6)

    # PCB 板
    pcb = mpatches.FancyBboxPatch(
        (4.8, 2.6), 2.4, 0.4, boxstyle="round,pad=0.02",
        edgecolor="#166534", facecolor="#16A34A", linewidth=2,
    )
    ax.add_patch(pcb)
    ax.text(6, 2.8, "PCB", ha="center", va="center", fontsize=11,
            fontweight="bold", color="white")

    # 輸送帶
    belt = mpatches.Rectangle(
        (1, 2.0), 10, 0.4, edgecolor="#1E293B", facecolor="#64748B", linewidth=2,
    )
    ax.add_patch(belt)
    ax.annotate("", xy=(10.5, 2.2), xytext=(9.5, 2.2),
                arrowprops=dict(arrowstyle="->", color="white", lw=2))
    ax.text(1.5, 2.2, "→ 輸送方向", fontsize=9, color="white",
            fontweight="bold", va="center")

    # 觸發感測器
    sensor = mpatches.FancyBboxPatch(
        (8.5, 2.6), 0.9, 0.4, boxstyle="round,pad=0.02",
        edgecolor="#B91C1C", facecolor="#FCA5A5", linewidth=2,
    )
    ax.add_patch(sensor)
    ax.text(8.95, 2.8, "感測器", ha="center", va="center", fontsize=8,
            fontweight="bold", color="#B91C1C")
    ax.annotate("觸發訊號", xy=(8.95, 3.0), xytext=(9.5, 3.6),
                fontsize=8, color="#B91C1C",
                arrowprops=dict(arrowstyle="->", color="#B91C1C", lw=1))

    # 防震底座
    base = mpatches.Rectangle(
        (0.8, 1.3), 10.4, 0.5, edgecolor="#1E293B", facecolor="#334155", linewidth=2,
    )
    ax.add_patch(base)
    ax.text(6, 1.55, "防震底座", ha="center", va="center", fontsize=10,
            color="white", fontweight="bold")

    fig.suptitle("PCB AOI 線上檢測系統架構", fontsize=18, fontweight="bold")
    plt.tight_layout()
    fig.savefig(OUT / "fig2_system_architecture.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("[OK] Fig 2: system architecture")


# ============================================================
# Fig 3: 打光方式對比
# ============================================================
def fig3_lighting_comparison():
    fig, axes = plt.subplots(1, 3, figsize=(15, 6))

    lighting_configs = [
        {
            "title": "同軸光 (Coaxial)",
            "color": "#0EA5E9",
            "rays": [(2.5, 5.5, 2.5, 1.5), (3.0, 5.5, 3.0, 1.5),
                     (3.5, 5.5, 3.5, 1.5), (4.0, 5.5, 4.0, 1.5)],
            "desc": "光線垂直入射\n金屬反射均勻\n適合銅箔、焊墊",
        },
        {
            "title": "低角度環形光 (Ring)",
            "color": "#22C55E",
            "rays": [(0.8, 4.5, 3.2, 1.5), (1.3, 5.0, 3.0, 1.5),
                     (5.7, 4.5, 3.3, 1.5), (5.2, 5.0, 3.5, 1.5)],
            "desc": "低角度斜射\n邊緣產生陰影\n突顯鼠咬、斷路",
        },
        {
            "title": "散射光 (Diffuse)",
            "color": "#A855F7",
            "rays": [(1.5, 5.5, 3.0, 1.5), (2.0, 5.5, 2.5, 1.5),
                     (4.0, 5.5, 3.5, 1.5), (4.5, 5.5, 3.0, 1.5),
                     (5.0, 5.5, 3.3, 1.5)],
            "desc": "全方位柔光\n陰影柔和\n反光強的物件",
        },
    ]

    for ax, cfg in zip(axes, lighting_configs):
        ax.set_xlim(0, 6.5)
        ax.set_ylim(0, 7)
        ax.axis("off")

        # 標題
        ax.text(3.25, 6.6, cfg["title"], ha="center", fontsize=15,
                fontweight="bold", color=cfg["color"])

        # 光源（上方矩形）
        light = mpatches.FancyBboxPatch(
            (1.5, 5.5), 3.5, 0.4, boxstyle="round,pad=0.05",
            edgecolor=cfg["color"], facecolor=cfg["color"], alpha=0.4, linewidth=2,
        )
        ax.add_patch(light)

        # 光線
        for x1, y1, x2, y2 in cfg["rays"]:
            ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                        arrowprops=dict(arrowstyle="->", color=cfg["color"],
                                        lw=1.5, alpha=0.7))

        # PCB
        pcb = mpatches.FancyBboxPatch(
            (1.0, 1.0), 4.5, 0.5, boxstyle="round,pad=0.02",
            edgecolor="#166534", facecolor="#16A34A", linewidth=2,
        )
        ax.add_patch(pcb)
        ax.text(3.25, 1.25, "PCB 表面", ha="center", va="center",
                fontsize=10, color="white", fontweight="bold")

        # 描述
        ax.text(3.25, 0.2, cfg["desc"], ha="center", va="center",
                fontsize=11, color="#475569",
                bbox=dict(boxstyle="round,pad=0.4", facecolor="#F8FAFC",
                          edgecolor=cfg["color"]))

    fig.suptitle("PCB 檢測常見打光方式比較", fontsize=18, fontweight="bold", y=1.02)
    plt.tight_layout()
    fig.savefig(OUT / "fig3_lighting_comparison.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("[OK] Fig 3: lighting comparison")


# ============================================================
# Fig 4: 檢測流程方塊圖
# ============================================================
def fig4_flow_chart():
    fig, ax = plt.subplots(figsize=(16, 4))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 4)
    ax.axis("off")

    steps = [
        ("影像擷取", "Image\nCapture", "#0EA5E9"),
        ("預處理", "Resize 512×512\nNormalize", "#22C55E"),
        ("YOLOv12 推論", "GPU Inference\n(~15 ms)", "#F59E0B"),
        ("後處理", "NMS\nConf Filter", "#A855F7"),
        ("缺陷判定", "PASS / FAIL\nClassification", "#EF4444"),
        ("輸出記錄", "Log + MES\nSPC Alarm", "#0EA5E9"),
    ]

    box_w, box_h = 2.2, 1.8
    gap = 0.4
    total_w = len(steps) * box_w + (len(steps) - 1) * gap
    start_x = (16 - total_w) / 2

    for i, (zh, en, color) in enumerate(steps):
        x = start_x + i * (box_w + gap)
        y = 1.2
        box = mpatches.FancyBboxPatch(
            (x, y), box_w, box_h, boxstyle="round,pad=0.1",
            edgecolor=color, facecolor=color, alpha=0.15, linewidth=2.5,
        )
        ax.add_patch(box)
        ax.text(x + box_w / 2, y + box_h * 0.65, zh, ha="center", va="center",
                fontsize=13, fontweight="bold", color=color)
        ax.text(x + box_w / 2, y + box_h * 0.25, en, ha="center", va="center",
                fontsize=9, color="#475569", style="italic")

        if i < len(steps) - 1:
            arrow_x1 = x + box_w
            arrow_x2 = x + box_w + gap
            ax.annotate("", xy=(arrow_x2, y + box_h / 2),
                        xytext=(arrow_x1, y + box_h / 2),
                        arrowprops=dict(arrowstyle="->", color="#475569", lw=2))

    fig.suptitle("PCB AOI 檢測流程", fontsize=18, fontweight="bold", y=0.95)
    plt.tight_layout()
    fig.savefig(OUT / "fig4_flow_chart.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("[OK] Fig 4: flow chart")


# ============================================================
# Fig 5: 資料擴增前後對照
# ============================================================
def fig5_augmentation_demo():
    src = pick_sample("missing_hole")
    img = Image.open(src).convert("RGB")

    augs = [
        ("原圖 Original", img),
        ("亮度 ↑30%", ImageEnhance.Brightness(img).enhance(1.3)),
        ("對比 ↑40%", ImageEnhance.Contrast(img).enhance(1.4)),
        ("水平翻轉", ImageOps.mirror(img)),
        ("旋轉 +15°", img.rotate(15, fillcolor=(0, 0, 0))),
    ]

    fig, axes = plt.subplots(1, 5, figsize=(20, 5))
    for ax, (title, im) in zip(axes, augs):
        ax.imshow(im)
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.axis("off")

    fig.suptitle("資料擴增（模擬實際產線變異）", fontsize=18, fontweight="bold", y=1.02)
    plt.tight_layout()
    fig.savefig(OUT / "fig5_augmentation_demo.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("[OK] Fig 5: augmentation demo")


# ============================================================
# Fig 6: 模型效能指標長條圖
# ============================================================
def fig6_metrics_bar():
    df = pd.read_csv(REPO / "runs" / "enhanced" / "results.csv")
    last = df.iloc[-1]
    metrics = {
        "Precision\n精確度": last["metrics/precision(B)"],
        "Recall\n召回率":   last["metrics/recall(B)"],
        "mAP @ 0.5":       last["metrics/mAP50(B)"],
        "mAP @ 0.5–0.95":  last["metrics/mAP50-95(B)"],
    }
    colors = ["#0EA5E9", "#22C55E", "#F59E0B", "#A855F7"]

    fig, ax = plt.subplots(figsize=(11, 6.5))
    bars = ax.bar(metrics.keys(), metrics.values(), color=colors,
                  edgecolor="white", linewidth=2, width=0.55)

    for bar, val in zip(bars, metrics.values()):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.015,
                f"{val:.4f}", ha="center", fontsize=14, fontweight="bold")

    ax.set_ylim(0, 1.05)
    ax.set_ylabel("數值", fontsize=13)
    ax.set_title("YOLOv12 PCB 缺陷檢測模型效能指標", fontsize=18, fontweight="bold", pad=15)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="x", labelsize=11)

    plt.tight_layout()
    fig.savefig(OUT / "fig6_metrics_bar.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("[OK] Fig 6: metrics bar")


if __name__ == "__main__":
    fig1_defect_samples()
    fig2_system_architecture()
    fig3_lighting_comparison()
    fig4_flow_chart()
    fig5_augmentation_demo()
    fig6_metrics_bar()
    print(f"\n所有圖已輸出至 {OUT}")
