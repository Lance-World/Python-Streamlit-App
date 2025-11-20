import streamlit as st
from datetime import datetime, date
import os, csv, platform
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


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

# 圖檔輸出解析度（DPI）→ 想更清楚可以調高，例如 300
IMAGE_DPI = 300

# ✅ 中文字型支援 + 圖表字體大小設定
if platform.system() == "Windows":
    plt.rcParams["font.family"] = "Microsoft JhengHei"
elif platform.system() == "Darwin":
    plt.rcParams["font.family"] = "AppleGothic"
else:
    plt.rcParams["font.family"] = "Noto Sans CJK JP"

plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["axes.labelsize"] = 14      # x/y label
plt.rcParams["xtick.labelsize"] = 14     # x 軸刻度字
plt.rcParams["ytick.labelsize"] = 14     # y 軸刻度字


# ✅ 輸出圖表：自動存檔，若同名檔存在則自動加上時間戳記避免覆蓋
def save_chart(fig, title: str, filename: str, dpi: int = IMAGE_DPI):
    """
    fig      ：matplotlib Figure
    title    ：圖表標題（顯示在圖上）
    filename：儲存的檔名（只要檔名，不含路徑）
    特色：
      - 不再詢問是否覆蓋
      - 若同名檔案已存在，自動在檔名後加上 _HHMMSS 重新命名
      - 標題字體：18pt、加粗
      - 可指定 DPI（解析度）
    """
    filepath = os.path.join(PHOTO_DIR, filename)

    if os.path.exists(filepath):
        base, ext = os.path.splitext(filename)
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"{base}_{timestamp}{ext}"
        filepath = os.path.join(PHOTO_DIR, filename)
        st.warning(f"⚠️ 圖檔已存在，自動改名儲存為：{filename}")

    # 在圖上加上標題（suptitle 比較不會壓到軸標）
    fig.suptitle(title, fontsize=18, fontweight="bold")
    # rect 留一點空間給 suptitle
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])

    fig.savefig(filepath, dpi=dpi, bbox_inches="tight")
    st.info(f"📈 圖片已自動儲存：{filepath}")
    return filepath


# 📝 寫入每日任務（取代原本 daily_checklist 的 input/print）
def save_daily_record(target_date: date, results, overwrite_existing: bool) -> bool:
    """
    target_date       : datetime.date（st.date_input 選到的日期）
    results           : 對應 TASKS 的 0/1 list
    overwrite_existing: 若該日期已存在紀錄，是否覆蓋
    回傳 True 表示有成功寫入
    """
    today_str = target_date.isoformat()

    # 檢查是否已存在同一天紀錄
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE, encoding="utf-8")
        if "日期" in df.columns and today_str in df["日期"].values:
            if not overwrite_existing:
                st.warning(f"🚫 {today_str} 已存在紀錄，且未勾選『覆蓋當天紀錄』，不寫入。")
                return False

            # 覆蓋：刪除舊紀錄後再寫新紀錄
            df = df[df["日期"] != today_str]
            df.to_csv(CSV_FILE, index=False, encoding="utf-8")
            st.info("🗑️ 舊資料已刪除。")

    # 寫入 CSV（append 模式）
    file_exists = os.path.exists(CSV_FILE) and os.stat(CSV_FILE).st_size > 0
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["日期"] + TASKS)
        writer.writerow([today_str] + results)

    st.success(f"✅ 資料已寫入：{CSV_FILE}")
    return True


# 📊 分析與圖表（Streamlit 版本）
def analyze_data_streamlit():
    if not os.path.exists(CSV_FILE):
        st.error(f"❌ 找不到資料檔：{CSV_FILE}，請先至少寫入一筆每日紀錄。")
        return

    df = pd.read_csv(CSV_FILE, encoding="utf-8")

    if "日期" not in df.columns:
        st.error("❌ CSV 缺少『日期』欄位，請確認檔案格式。")
        return

    if len(df) == 0:
        st.warning("⚠️ 沒有任何紀錄，無法分析。")
        return

    # 每日完成總數
    df["Total Completed"] = df.iloc[:, 1:].sum(axis=1)

    st.subheader("📑 目前資料表")
    st.dataframe(df, use_container_width=True)

    # 取得今天日期字串，用來做圖檔檔名
    today_str = date.today().isoformat()

    # === 折線圖：每日完成數 ===
    st.subheader("📈 每日完成總數（折線圖）")

    fig_line, ax_line = plt.subplots(figsize=(10, 5))
    ax_line.plot(df["日期"], df["Total Completed"], marker="o")

    # x 軸字旋轉＋字體大小
    ax_line.tick_params(axis="x", labelrotation=45)
    ax_line.set_ylabel("Total Tasks Completed")

    line_title = "Daily Task Line"
    line_filename = f"{line_title}_{today_str}.png".replace(" ", "_")
    save_chart(fig_line, line_title, line_filename)
    st.pyplot(fig_line)

    # === 雷達圖：各任務完成率(%) ===
    st.subheader("📊 各任務完成率 (Completion %) — 雷達圖")

    task_cols = df.columns[1:-1]  # 除去「日期」與最後一欄 Total Completed
    total_days = len(df)

    if len(task_cols) == 0:
        st.warning("⚠️ 沒有任務欄位，無法畫雷達圖。")
        return

    # 完成率(%) = 任務完成次數 / 紀錄天數 × 100
    completion_rates = (df[task_cols].sum() / total_days * 100).tolist()

    # 角度：為每個任務分配一個角度
    angles = np.linspace(0, 2 * np.pi, len(task_cols), endpoint=False)
    # 關閉雷達圖的線條：頭尾再接回第一個點
    angles_closed = np.concatenate([angles, [angles[0]]])
    rates_closed = np.concatenate([np.array(completion_rates), [completion_rates[0]]])

    fig_radar, ax = plt.subplots(figsize=(6, 6), subplot_kw={"polar": True})
    ax.plot(angles_closed, rates_closed, "o-", linewidth=2)
    ax.fill(angles_closed, rates_closed, alpha=0.25)

    # θ 軸標籤：任務名稱 + 字體 14
    ax.set_xticks(angles)
    ax.set_xticklabels(task_cols, fontsize=14)

    # r 軸：0～100%，刻度 0, 20, 40, 60, 80, 100
    ax.set_ylim(0, 100)
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.set_yticklabels(["0%", "20%", "40%", "60%", "80%", "100%"], fontsize=14)

    radar_title = "Daily Task Radar (Completion %)"
    radar_filename = f"Daily_Task_Radar_{today_str}.png".replace(" ", "_")
    save_chart(fig_radar, radar_title, radar_filename)
    st.pyplot(fig_radar)


# 🚀 Streamlit 主介面
def main():
    st.title("📅 每日任務追蹤 & 完成率分析（Streamlit 版）")

    st.markdown(
        """
這個小工具會幫你做三件事：

1. 在網頁上勾選每日任務完成狀況  
2. 把結果寫入 `todoCHECK.csv`  
3. 產生「每日完成數折線圖」＋「完成率(%) 雷達圖」，存在 `Results/Photos`，並在頁面顯示  
"""
    )

    st.markdown("---")

    # 左邊：填寫今日紀錄；右邊：只看統計
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("📝 填寫 / 更新每日紀錄")

        selected_date = st.date_input("紀錄日期", value=date.today())

        st.write("請勾選今天完成的任務：")
        task_results = []
        for i, task in enumerate(TASKS):
            done = st.checkbox(task, key=f"task_{i}")
            task_results.append(1 if done else 0)

        overwrite_existing = st.checkbox(
            "若該日期已有紀錄，覆蓋當天紀錄",
            value=True,
            help="勾選時：同一天只保留最新一次的勾選結果。",
        )

        if st.button("💾 儲存紀錄並產生圖表"):
            ok = save_daily_record(selected_date, task_results, overwrite_existing)
            if ok:
                analyze_data_streamlit()

    with col_right:
        st.subheader("🔍 僅重新產生圖表（不寫入新資料）")
        st.caption("當 CSV 已存在，只想更新圖表時可以用。")
        if st.button("📊 重新分析現有資料"):
            analyze_data_streamlit()


if __name__ == "__main__":
    main()

