"""
PCB AOI 線上檢測模擬 Dashboard
================================
以 Streamlit 模擬實際產線：
測試集影像依序「送入」檢測站，YOLOv12 推論後即時更新統計與圖表。

執行方式（於 repo 根目錄）：
    streamlit run code/dashboard.py
"""

from __future__ import annotations

import time
from collections import Counter, deque
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from PIL import Image
from ultralytics import YOLO

# ---------- 路徑與常數 ----------
REPO_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = REPO_ROOT / "runs" / "enhanced" / "weights" / "best.pt"
IMAGE_DIR = REPO_ROOT / "dataset" / "Enhanced" / "test" / "images"
LOG_PATH = REPO_ROOT / "outputs" / "inspection_log.csv"

CLASS_ZH = {
    "missing_hole": "缺孔 Missing Hole",
    "mouse_bite": "鼠咬 Mouse Bite",
    "open_circuit": "斷路 Open Circuit",
    "short_circuit": "短路 Short Circuit",
}
CLASS_COLORS = {
    "missing_hole": "#EF4444",
    "mouse_bite": "#F59E0B",
    "open_circuit": "#3B82F6",
    "short_circuit": "#8B5CF6",
}

# ---------- 頁面設定 ----------
st.set_page_config(
    page_title="PCB AOI 線上檢測系統",
    page_icon="🔍",
    layout="wide",
)


# ---------- 模型載入（cache 避免每次 rerun 重載） ----------
@st.cache_resource
def load_model(weights_path: str) -> YOLO:
    return YOLO(weights_path)


@st.cache_data
def list_test_images(image_dir: str) -> list[str]:
    exts = {".jpg", ".jpeg", ".png", ".bmp"}
    return sorted(str(p) for p in Path(image_dir).iterdir() if p.suffix.lower() in exts)


# ---------- Session state 初始化 ----------
def init_state() -> None:
    defaults = {
        "running": False,
        "index": 0,
        "results": [],          # list[dict] — 每片 PCB 紀錄
        "latencies": [],        # list[float] ms
        "consec_fail": 0,
        "alarm_active": False,
        "conf_threshold": 0.25,
        "images": {},          # board_id -> annotated PIL.Image
        "selected_board": None, # 使用者於 sidebar 選擇要檢視的 board_id
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


init_state()


# ---------- Sidebar 控制 ----------
with st.sidebar:
    st.title("⚙️ 產線控制台")

    st.subheader("檢測參數")
    st.session_state.conf_threshold = st.slider(
        "信心度閾值", 0.05, 0.95, st.session_state.conf_threshold, 0.05
    )

    st.subheader("執行控制")
    col_a, col_b = st.columns(2)
    start_btn = col_a.button(
        "▶ 啟動" if not st.session_state.running else "⏸ 暫停",
        use_container_width=True,
        type="primary",
    )
    reset_btn = col_b.button("⟲ 重設", use_container_width=True)

    if start_btn:
        st.session_state.running = not st.session_state.running
    if reset_btn:
        for k in ["running", "index", "results", "latencies",
                  "consec_fail", "alarm_active"]:
            st.session_state[k] = [] if isinstance(st.session_state[k], list) else (
                False if isinstance(st.session_state[k], bool) else 0
            )
        st.session_state.images = {}
        st.session_state.selected_board = None

    # 已檢測 PCB 選擇器（檢測中自動跟隨；閒置時可任選）
    if st.session_state.results:
        st.divider()
        st.subheader("檢視 PCB")
        board_ids = [r["board_id"] for r in st.session_state.results]
        default_idx = (
            len(board_ids) - 1
            if st.session_state.running or st.session_state.selected_board is None
            else board_ids.index(st.session_state.selected_board)
            if st.session_state.selected_board in board_ids else len(board_ids) - 1
        )
        st.session_state.selected_board = st.selectbox(
            f"選擇要檢視的 PCB（共 {len(board_ids)} 片）",
            board_ids, index=default_idx,
            disabled=st.session_state.running,
            help="檢測中會自動顯示最新一片；暫停／結束後可任意瀏覽",
        )

    st.divider()
    st.caption(f"模型：`{MODEL_PATH.relative_to(REPO_ROOT)}`")
    st.caption(f"資料夾：`{IMAGE_DIR.relative_to(REPO_ROOT)}`")


# ---------- 載入資源 ----------
if not MODEL_PATH.exists():
    st.error(f"找不到模型檔：{MODEL_PATH}")
    st.stop()
if not IMAGE_DIR.exists():
    st.error(f"找不到測試影像資料夾：{IMAGE_DIR}")
    st.stop()

MAX_BOARDS = 20
model = load_model(str(MODEL_PATH))
image_paths = list_test_images(str(IMAGE_DIR))[:MAX_BOARDS]
total_images = len(image_paths)


# ---------- 標題列 ----------
header_l, header_r = st.columns([3, 1])
with header_l:
    st.title("🔍 PCB AOI 線上檢測系統")
    st.caption("YOLOv12 · Enhanced Model · 模擬產線運行")
with header_r:
    status = "● RUNNING" if st.session_state.running else "○ IDLE"
    color = "#22C55E" if st.session_state.running else "#94A3B8"
    st.markdown(
        f"<div style='text-align:right;font-size:1.1rem;'>"
        f"<span style='color:{color};font-weight:bold'>{status}</span><br>"
        f"<span style='color:#64748B'>{datetime.now():%Y-%m-%d %H:%M:%S}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

st.divider()


# ---------- 版面 placeholders ----------
alarm_box = st.empty()

left, right = st.columns([1.1, 1])
with left:
    st.subheader("📷 即時影像")
    image_box = st.empty()
    board_info_box = st.empty()

with right:
    st.subheader("📊 即時統計")
    metrics_box = st.empty()
    st.subheader("🧱 缺陷類別分布")
    defect_chart_box = st.empty()

st.subheader("📈 良率趨勢")
trend_box = st.empty()

st.subheader("📝 檢測紀錄（最新 8 筆）")
log_box = st.empty()


# ---------- 渲染函式 ----------
def render_metrics() -> None:
    total = len(st.session_state.results)
    fails = sum(1 for r in st.session_state.results if r["verdict"] == "FAIL")
    passes = total - fails
    yield_rate = (passes / total * 100) if total else 0.0

    with metrics_box.container():
        c1, c2 = st.columns(2)
        c3, c4 = st.columns(2)
        c1.metric("已檢測", f"{total} / {total_images}")
        c2.metric("良率", f"{yield_rate:.1f} %")
        c3.metric("✅ PASS", passes)
        c4.metric("❌ FAIL", fails, delta=None)


def render_defect_chart() -> None:
    counter: Counter[str] = Counter()
    for r in st.session_state.results:
        counter.update(r["classes"])
    data = [
        {"類別": CLASS_ZH[k], "數量": counter.get(k, 0), "key": k}
        for k in CLASS_ZH
    ]
    df = pd.DataFrame(data)
    fig = px.bar(
        df, x="數量", y="類別", orientation="h",
        color="key", color_discrete_map=CLASS_COLORS,
        text="數量",
    )
    fig.update_layout(
        showlegend=False, height=240,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis_title=None, yaxis_title=None,
    )
    fig.update_traces(textposition="outside")
    defect_chart_box.plotly_chart(fig, use_container_width=True, key="defect_chart")


def render_trend() -> None:
    window = st.session_state.results[-20:]
    if not window:
        trend_box.info("尚無資料")
        return
    cum_pass = 0
    rates = []
    for i, r in enumerate(window, 1):
        if r["verdict"] == "PASS":
            cum_pass += 1
        rates.append(cum_pass / i * 100)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(1, len(rates) + 1)),
        y=rates,
        mode="lines+markers",
        line=dict(color="#10B981", width=3),
        fill="tozeroy",
        fillcolor="rgba(16,185,129,0.15)",
    ))
    fig.update_layout(
        height=220, margin=dict(l=10, r=10, t=10, b=10),
        yaxis=dict(range=[0, 105], title="累積良率 (%)"),
        xaxis=dict(title="片序"),
    )
    trend_box.plotly_chart(fig, use_container_width=True, key="trend_chart")


def render_log() -> None:
    if not st.session_state.results:
        log_box.info("尚無紀錄")
        return
    rows = []
    for r in st.session_state.results[-8:][::-1]:
        rows.append({
            "時間": r["timestamp"][-8:],
            "Board ID": r["board_id"],
            "判定": "❌ FAIL" if r["verdict"] == "FAIL" else "✅ PASS",
            "缺陷數": r["n_defects"],
            "類別": ", ".join(CLASS_ZH[c].split()[0] for c in r["classes"]) or "—",
        })
    log_box.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render_alarm() -> None:
    if st.session_state.alarm_active:
        alarm_box.error(
            f"⚠️ **連續不良警示** — 連續 {st.session_state.consec_fail} 片 FAIL，"
            "請立即檢查上游製程（SMT 焊接 / 蝕刻 / 鑽孔）"
        )
    else:
        alarm_box.empty()


def render_image(img: Image.Image, board_id: str, verdict: str,
                 classes: list[str]) -> None:
    image_box.image(img, use_container_width=True)
    color = "#22C55E" if verdict == "PASS" else "#EF4444"
    icon = "✅" if verdict == "PASS" else "❌"
    cls_str = "、".join(CLASS_ZH[c] for c in classes) if classes else "無缺陷"
    board_info_box.markdown(
        f"""
        <div style='padding:12px;border-radius:8px;background:{color}15;
                    border-left:6px solid {color};'>
          <div style='font-size:0.9rem;color:#64748B;'>Board ID</div>
          <div style='font-size:1.3rem;font-weight:bold'>{board_id}</div>
          <div style='font-size:1.5rem;color:{color};font-weight:bold;margin-top:6px'>
            {icon} {verdict}
          </div>
          <div style='font-size:0.95rem;margin-top:4px'>缺陷：{cls_str}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def append_log(record: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_header = not LOG_PATH.exists()
    df = pd.DataFrame([{
        "timestamp": record["timestamp"],
        "board_id": record["board_id"],
        "verdict": record["verdict"],
        "n_defects": record["n_defects"],
        "classes": ";".join(record["classes"]),
        "confidences": ";".join(f"{c:.3f}" for c in record["confidences"]),
        "latency_ms": round(record["latency_ms"], 2),
    }])
    df.to_csv(LOG_PATH, mode="a", header=write_header, index=False,
              encoding="utf-8-sig")


# ---------- 推論一張 ----------
def inspect_one(img_path: str, idx: int) -> dict:
    t0 = time.perf_counter()
    res = model.predict(
        source=img_path, conf=st.session_state.conf_threshold,
        verbose=False,
    )[0]
    latency_ms = (time.perf_counter() - t0) * 1000.0

    names = res.names
    classes = [names[int(c)] for c in res.boxes.cls.cpu().numpy()] if res.boxes else []
    confs = res.boxes.conf.cpu().numpy().tolist() if res.boxes else []

    annotated = res.plot()[:, :, ::-1]   # BGR → RGB
    annotated_img = Image.fromarray(annotated)

    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "board_id": f"PCB-{idx + 1:04d}",
        "image": annotated_img,
        "classes": classes,
        "confidences": confs,
        "n_defects": len(classes),
        "verdict": "FAIL" if classes else "PASS",
        "latency_ms": latency_ms,
    }


# ---------- 執行一次推論（若 running） ----------
if st.session_state.running and st.session_state.index < total_images:
    idx = st.session_state.index
    record = inspect_one(image_paths[idx], idx)

    st.session_state.results.append({k: v for k, v in record.items() if k != "image"})
    st.session_state.latencies.append(record["latency_ms"])
    append_log(record)

    if record["verdict"] == "FAIL":
        st.session_state.consec_fail += 1
    else:
        st.session_state.consec_fail = 0
    st.session_state.alarm_active = st.session_state.consec_fail >= 3
    st.session_state.index += 1
    st.session_state.images[record["board_id"]] = record["image"]
    st.session_state.selected_board = record["board_id"]

# ---------- 顯示選定 PCB ----------
if st.session_state.results:
    target_id = (
        st.session_state.selected_board
        or st.session_state.results[-1]["board_id"]
    )
    rec = next((r for r in st.session_state.results if r["board_id"] == target_id),
               st.session_state.results[-1])
    img = st.session_state.images.get(rec["board_id"])
    if img is not None:
        render_image(img, rec["board_id"], rec["verdict"], rec["classes"])
else:
    image_box.info("👈 請於左側點擊「啟動」開始模擬產線")

# 統計面板每次 rerun 只渲染一次
render_metrics()
render_defect_chart()
render_trend()
render_log()
render_alarm()

# 自動進入下一張
if st.session_state.running and st.session_state.index < total_images:
    st.rerun()

if st.session_state.index >= total_images and st.session_state.running:
    st.session_state.running = False
    st.success(f"✅ 已完成全部 {total_images} 片 PCB 之檢測")
