import streamlit as st
from datetime import datetime, date
import os, csv, platform
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# === 輸出圖檔解析度設定（DPI）===
IMAGE_DPI = 300   # 想更清楚就改 300, 400

# === 路徑設定 ===
BASE_DIR = r"C:\Lance\Study\PythonLearning"
CSV_DIR = os.path.join(BASE_DIR, "Results", "Csv")
PHOTO_DIR = os.path.join(BASE_DIR, "Results", "Photos")

# 確保資料夾存在
os.makedirs(CSV_DIR, exist_ok=True)
os.makedirs(PHOTO_DIR, exist_ok=True)

# 📌 任務與檔案
TASKS = ["Duolingo", "Python", "Reading", "Financial", "Inner Dialogue", "Mindful Rest"]
CSV_FILE = os.path.join(CSV_DIR, "todoCHECK.csv")

# ✅ 中文字型支援
if platform.system() == "Windows":
    plt.rcParams["font.family"] = "Microsoft JhengHei"
elif platform.system() == "Darwin":
    plt.rcParams["font.family"] = "AppleGothic"
else:
    plt.rcParams["font.family"] = "Noto Sans CJK JP"
plt.rcParams["axes.unicode_minus"] = False


# ✅ 儲存圖表：自動存檔，若同名檔存在則自動加時間戳避免覆蓋
def save_chart(fig, title: str, filename: str):
    """
    fig      ：matplotlib Figure
    title    ：圖表標題（顯示在圖上）
    filename：儲存的檔名（只要檔名，不含路徑）

    - 不詢問是否覆蓋
    - 若同名檔案已存在，自動在檔名後加上 _HHMMSS 重新命名
    """
    filepath = os.path.join(PHOTO_DIR, filename)

    if os.path.exists(filepath):
        base, ext = os.path.splitext(filename)
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"{base}_{timestamp}{ext}"
        filepath = os.path.join(PHOTO_DIR, filename)
        st.warning(f"⚠️ 圖檔已存在，自動改名儲存為：{filename}")

    fig.tight_layout()
    fig.savefig(filepath, bbox_inches="tight")
    st.info(f"📈 圖片已自動儲存：{filepath}")
    return filepath


# 📝 寫入每日紀錄（取代原本 daily_checklist 的 input / print）
def save_daily_record(target_date: date, results, overwrite_existing: bool) -> bool:
    """
    target_date       : datetime.date（st.date_input 選到的日期）
    results           : 對應 TASKS 的 0/1 list
    overwrite_existing: 若該日期已存在紀錄，是否覆蓋
    回傳 True 表示有成功寫入
    """
    today_str = target_date.isoformat()

    # 若已存在 CSV，檢查是否有同日紀錄
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE, encoding="utf-8")

        if "日期" in df.columns and today_str in df["日期"].values:
            if not overwrite_existing:
                st.warning(f"🚫 {today_str} 已有紀錄，未勾選『覆蓋舊資料』，不寫入。")
                return False

            # 覆蓋：先刪除舊紀錄，再重寫 CSV
            df = df[df["日期"] != today_str]
            df.to_csv(CSV_FILE, index=False, encoding="utf-8")
            st.info(f"🗑️ 已刪除 {today_str} 舊紀錄。")

    # 寫入新的紀錄（append 模式，如果檔案不存在則寫 header）
    file_exists = os.path.exists(CSV_FILE) and os.stat(CSV_FILE).st_size > 0
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["日期"] + TASKS)
        writer.writerow([today_str] + results)

    st.success(f"✅ 已寫入 {today_str} 的紀錄。")
    return True


# 📊 分析與圖表（改成在 Streamlit 裡顯示＋存檔）
def analyze_data_streamlit():
    if not os.path.exists(CSV_FILE):
        st.error(f"❌ 找不到資料檔：{CSV_FILE}，請先至少寫入一筆每日紀錄。")
        return

    df = pd.read_csv(CSV_FILE, encoding="utf-8")

    if "日期" not in df.columns:
        st.error("❌ CSV 缺少『日期』欄位，請確認檔案格式。")
        return

    # 每日完成總數
    df["Total Completed"] = df.iloc[:, 1:].sum(axis=1)

    st.subheader("📑 目前資料表")
    st.dataframe(df, use_container_width=True)

    today_str = date.today().isoformat()

    # === 折線圖：每日完成數 ===
    st.subheader("📈 每日完成總數（折線圖）")

    fig_line, ax_line = plt.subplots(figsize=(10, 5))
    ax_line.plot(df["日期"], df["Total Completed"], marker="o")
    ax_line.set_xlabel("日期")
    ax_line.set_ylabel("Total Tasks Completed")
    ax_line.set_title("Daily Task Line")
    plt.setp(ax_line.get_xticklabels(), rotation=45, ha="right")

    line_title = "Daily Task Line"
    line_filename = f"{line_title}_{today_str}.png".replace(" ", "_")
    save_chart(fig_line, line_title, line_filename)
    st.pyplot(fig_line)

    # === 雷達圖：各任務平均完成度 ===
    st.subheader("📊 各任務平均完成度（雷達圖）")

    # task_cols：除去「日期」與最後一欄 Total Completed
    task_cols = df.columns[1:-1]
    if len(task_cols) == 0:
        st.warning("⚠️ 沒有可用的任務欄位，無法畫雷達圖。")
        return

    avg_scores = df[task_cols].mean().tolist()

    angles = np.linspace(0, 2 * np.pi, len(task_cols), endpoint=False).tolist()
    # 收尾相接
    avg_scores += [avg_scores[0]]
    angles += [angles[0]]

    fig_radar, ax = plt.subplots(figsize=(6, 6), subplot_kw={"polar": True})
    ax.plot(angles, avg_scores, "o-", linewidth=2)
    ax.fill(angles, avg_scores, alpha=0.25)
    ax.set_thetagrids(np.degrees(angles[:-1]), task_cols)
    ax.set_ylim(0, 1)
    ax.set_title("Daily Task Radar")

    radar_title = "Daily Task Radar"
    radar_filename = f"{radar_title}_{today_str}.png".replace(" ", "_")
    save_chart(fig_radar, radar_title, radar_filename)
    st.pyplot(fig_radar)


# 🚀 Streamlit 主介面
def main():
    st.title("📅 每日任務追蹤 & 圖表分析（Streamlit 版）")

    st.markdown(
        """
這個小工具會：
1. 讓你在網頁上勾選今日任務完成狀況  
2. 把結果寫入 `todoCHECK.csv`  
3. 產生折線圖 + 雷達圖，存在 `Results/Photos`，並在下方顯示  
"""
    )

    st.markdown("---")

    # ===== 左半：填寫今日紀錄 =====
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("📝 填寫每日紀錄")

        selected_date = st.date_input("紀錄日期", value=date.today())

        st.write("請勾選今天完成的任務：")
        task_results = []
        for i, task in enumerate(TASKS):
            done = st.checkbox(task, key=f"task_{i}")
            task_results.append(1 if done else 0)

        overwrite_existing = st.checkbox(
            "若該日期已有紀錄，覆蓋舊資料",
            value=True,
            help="勾選時：同一天只會保留最新一次的勾選結果。",
        )

        if st.button("💾 儲存紀錄並產生圖表"):
            ok = save_daily_record(selected_date, task_results, overwrite_existing)
            if ok:
                analyze_data_streamlit()

    with col_right:
        st.subheader("🔍 只看目前統計")
        st.caption("不改動資料，只重新讀取 CSV 並畫圖。")
        if st.button("📊 重新產生圖表（不寫入新紀錄）"):
            analyze_data_streamlit()


if __name__ == "__main__":
    main()
