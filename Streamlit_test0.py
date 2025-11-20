from datetime import datetime, date, timedelta
import os, platform, calendar
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

# === 輸出圖檔解析度設定（DPI）===
IMAGE_DPI = 300   # 想更清楚就改 300, 400

# === 路徑設定 ===
BASE_DIR = r"C:\Lance\Study\PythonLearning"
CSV_DIR = os.path.join(BASE_DIR, "Results", "Csv")
PHOTO_DIR = os.path.join(BASE_DIR, "Results", "Photos")

# 確保資料夾存在
os.makedirs(CSV_DIR, exist_ok=True)
os.makedirs(PHOTO_DIR, exist_ok=True)

# 📌 任務與檔案（每日）
TASKS = ["Duolingo", "Python", "Reading", "Financial", "Inner Dialogue", "Mindful Rest"]
CSV_FILE = os.path.join(CSV_DIR, "todoCHECK.csv")

# 📌 一週目標任務與檔案（Weekly 數值欄位）
WEEKLY_TASKS = [
    "Workout_Chest",
    "Workout_Back",
    "Workout_Legs",
    "Workout_Shoulders_Core",
    "Learning_Drawing",
    "Learning_Flowchart",
    "Date_With_Myself",
]
SKILLS_FIELD = "Skills_Plus"  # 自由輸入文字（原本 Others）

WEEKLY_TASK_LABELS = {
    "Workout_Chest": "Workout – Chest",
    "Workout_Back": "Workout – Back",
    "Workout_Legs": "Workout – Legs",
    "Workout_Shoulders_Core": "Workout – Shoulders + Core",
    "Learning_Drawing": "Learning – Drawing",
    "Learning_Flowchart": "Learning – Flowchart",
    "Date_With_Myself": "Date With Myself",
}
WEEKLY_CSV_FILE = os.path.join(CSV_DIR, "weeklyGoals.csv")

# ✅ 中文字型 & 預設字型大小
if platform.system() == "Windows":
    plt.rcParams["font.family"] = "Microsoft JhengHei"
elif platform.system() == "Darwin":
    plt.rcParams["font.family"] = "AppleGothic"
else:
    plt.rcParams["font.family"] = "Noto Sans CJK JP"
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["font.size"] = 12  # 預設字型大小（備用）


# ✅ 儲存並顯示圖表：存到 PHOTO_DIR，自動檔名與標題一致
def save_and_show_chart(fig, title: str, overwrite_images: bool = True):
    filename = title.replace(" ", "_") + ".png"
    filepath = os.path.join(PHOTO_DIR, filename)

    # 檔案覆蓋邏輯
    if os.path.exists(filepath) and not overwrite_images:
        st.warning(f"圖檔已存在，未覆蓋：{filepath}")
    else:
        fig.tight_layout()
        fig.savefig(filepath, dpi=IMAGE_DPI)
        st.info(f"已儲存圖檔：{filepath}")

    st.pyplot(fig)
    plt.close(fig)


# 🔁 取得某日期所在週的「週一」日期
def get_week_start(date_str: str) -> date:
    d = datetime.strptime(date_str, "%Y-%m-%d").date()
    # weekday(): Monday=0, Sunday=6
    return d - timedelta(days=d.weekday())


# 📝 每日紀錄 UI
def daily_checklist_ui():
    st.subheader("📅 Daily Checklist")

    # 選擇日期
    selected_date = st.date_input("紀錄日期（Date）", value=date.today(), format="YYYY-MM-DD")
    date_str = selected_date.isoformat()

    # 載入現有每日資料
    if os.path.exists(CSV_FILE) and os.stat(CSV_FILE).st_size > 0:
        df = pd.read_csv(CSV_FILE, encoding="utf-8")
    else:
        df = pd.DataFrame(columns=["日期"] + TASKS)

    existing_row = df[df["日期"] == date_str] if "日期" in df.columns else pd.DataFrame()

    if not existing_row.empty:
        st.info("此日期已有紀錄，下面顯示的是可編輯版本，按下「儲存每日紀錄」後會覆蓋該日資料。")
        defaults = {task: int(existing_row[task].iloc[0]) == 1 for task in TASKS}
    else:
        defaults = {task: False for task in TASKS}

    st.write("請勾選今天完成的任務：")
    task_results = {}
    cols = st.columns(3)
    for i, task in enumerate(TASKS):
        with cols[i % 3]:
            task_results[task] = st.checkbox(task, value=defaults[task])

    if st.button("💾 儲存每日紀錄"):
        # 轉成 0/1
        row_values = [1 if task_results[task] else 0 for task in TASKS]

        # 移除舊同日資料，再加入新紀錄
        if not df.empty and "日期" in df.columns:
            df = df[df["日期"] != date_str]

        new_row = pd.DataFrame([[date_str] + row_values], columns=["日期"] + TASKS)
        df = pd.concat([df, new_row], ignore_index=True)

        df.to_csv(CSV_FILE, index=False, encoding="utf-8")
        st.success(f"已寫入每日資料：{CSV_FILE}")


# 📊 每日分析與圖表
def analyze_daily_data_ui(overwrite_images: bool):
    st.subheader("📊 Daily Analysis")

    if not os.path.exists(CSV_FILE):
        st.error(f"找不到每日資料檔：{CSV_FILE}，請先建立紀錄。")
        return

    df = pd.read_csv(CSV_FILE, encoding="utf-8")

    if "日期" not in df.columns:
        st.error("CSV 缺少『日期』欄位，請確認檔案格式。")
        return

    # 確保以日期排序（如果你有需要）
    df = df.sort_values("日期").reset_index(drop=True)

    df["Total Completed"] = df.iloc[:, 1:].sum(axis=1)

    st.write("原始每日資料：")
    st.dataframe(df)

    # 折線圖：每日完成數
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df["日期"], df["Total Completed"], marker="o")
    ax.set_xticklabels(df["日期"], rotation=45, fontsize=14)
    ax.set_ylabel("Total Tasks Completed", fontsize=14)
    ax.tick_params(axis="y", labelsize=14)
    ax.set_title("Daily Total Tasks Completed", fontsize=18, fontweight="bold")
    save_and_show_chart(fig, "Daily Total Tasks Completed", overwrite_images)

    # 雷達圖：各任務完成率（百分比）
    task_cols = df.columns[1:-1]  # 除去「日期」與最後一欄 Total Completed
    total_days = len(df)
    if total_days == 0:
        st.warning("沒有每日紀錄資料，略過雷達圖。")
        return

    completion_rates = (df[task_cols].sum() / total_days * 100).tolist()

    angles = np.linspace(0, 2 * np.pi, len(task_cols), endpoint=False).tolist()
    completion_rates += [completion_rates[0]]
    angles += [angles[0]]

    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111, polar=True)
    ax.plot(angles, completion_rates, "o-", linewidth=2)
    ax.fill(angles, completion_rates, alpha=0.25)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(task_cols, fontsize=14)

    ax.set_ylim(0, 100)
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.set_yticklabels(["0%", "20%", "40%", "60%", "80%", "100%"])
    ax.tick_params(axis="y", labelsize=14)

    ax.set_title("Task Completion Rate (%)", fontsize=18, fontweight="bold")
    save_and_show_chart(fig, "Task Completion Rate (%)", overwrite_images)


# 📝 Weekly 目標紀錄 UI
def weekly_goal_checklist_ui():
    st.subheader("📆 Weekly Goals")

    # 以某一天來代表本週（Mon–Sun）
    ref_date = st.date_input(
        "本次一週目標紀錄日期（會自動找到該週的週一 ~ 週日）",
        value=date.today(),
        format="YYYY-MM-DD",
        key="weekly_ref_date",
    )
    today_str = ref_date.isoformat()

    try:
        datetime.strptime(today_str, "%Y-%m-%d")
    except ValueError:
        st.error("日期格式錯誤，請用 YYYY-MM-DD")
        return

    week_start = get_week_start(today_str)
    week_end = week_start + timedelta(days=6)
    week_label = f"{week_start.isoformat()} ~ {week_end.isoformat()}"
    st.info(f"Weekly Goals for {week_label} (Mon–Sun)")

    # 讀取或建立 weekly CSV
    if os.path.exists(WEEKLY_CSV_FILE) and os.stat(WEEKLY_CSV_FILE).st_size > 0:
        df_w = pd.read_csv(WEEKLY_CSV_FILE, encoding="utf-8")
    else:
        df_w = pd.DataFrame(columns=["Week_Start"] + WEEKLY_TASKS + [SKILLS_FIELD])

    if "Week_Start" not in df_w.columns:
        st.error("Weekly CSV 缺少 'Week_Start' 欄位，請確認檔案格式。")
        return
    if SKILLS_FIELD not in df_w.columns:
        df_w[SKILLS_FIELD] = ""

    week_str = week_start.isoformat()
    df_w["Week_Start"] = df_w["Week_Start"].astype(str)

    # 找出本週 row；若不存在則新增並初始化 0
    if week_str in df_w["Week_Start"].values:
        row_index = df_w.index[df_w["Week_Start"] == week_str][0]
        st.info("已存在本週紀錄，此次輸入為『本次增加/減少』，儲存後會在原有基礎上加總。")
    else:
        row_index = len(df_w)
        df_w.loc[row_index, "Week_Start"] = week_str
        for col in WEEKLY_TASKS:
            df_w.loc[row_index, col] = 0
        df_w.loc[row_index, SKILLS_FIELD] = ""
        st.success("建立新的本週紀錄（所有數值欄位初始為 0）。")

    # 顯示目前本週已有數值
    st.write("目前本週累計值：")
    current_vals = {}
    for col in WEEKLY_TASKS:
        current_vals[col] = int(pd.to_numeric(df_w.at[row_index, col], errors="coerce") or 0)
    st.table(
        pd.DataFrame(
            {
                "Task": [WEEKLY_TASK_LABELS.get(c, c) for c in WEEKLY_TASKS],
                "Current Total": [current_vals[c] for c in WEEKLY_TASKS],
            }
        )
    )

    st.write("請輸入『本次要增加／減少』的次數（可輸入負數）：")
    deltas = {}
    cols_num = st.columns(2)
    for i, task in enumerate(WEEKLY_TASKS):
        label = WEEKLY_TASK_LABELS.get(task, task)
        with cols_num[i % 2]:
            deltas[task] = st.number_input(
                f"{label} Δ", value=0, step=1, format="%d", key=f"delta_{task}"
            )

    # Skills Plus：自由輸入文字，追加在本週清單
    old_skills = str(df_w.at[row_index, SKILLS_FIELD]) if pd.notna(df_w.at[row_index, SKILLS_FIELD]) else ""
    new_skills = st.text_input(
        "Skills Plus 本週新技能（自由輸入文字，逗號或分號分隔，留白＝略過）：",
        value="",
        key="skills_plus_input",
    )

    if st.button("💾 儲存 Weekly 更新"):
        # 重新載入一次 df（保守作法）
        if os.path.exists(WEEKLY_CSV_FILE) and os.stat(WEEKLY_CSV_FILE).st_size > 0:
            df_w = pd.read_csv(WEEKLY_CSV_FILE, encoding="utf-8")
        else:
            df_w = pd.DataFrame(columns=["Week_Start"] + WEEKLY_TASKS + [SKILLS_FIELD])

        if "Week_Start" not in df_w.columns:
            df_w["Week_Start"] = ""

        if SKILLS_FIELD not in df_w.columns:
            df_w[SKILLS_FIELD] = ""

        df_w["Week_Start"] = df_w["Week_Start"].astype(str)

        if week_str in df_w["Week_Start"].values:
            row_index = df_w.index[df_w["Week_Start"] == week_str][0]
        else:
            row_index = len(df_w)
            df_w.loc[row_index, "Week_Start"] = week_str
            for col in WEEKLY_TASKS:
                df_w.loc[row_index, col] = 0
            df_w.loc[row_index, SKILLS_FIELD] = ""

        # 加總數值欄位
        for task in WEEKLY_TASKS:
            current_val = pd.to_numeric(df_w.at[row_index, task], errors="coerce")
            if np.isnan(current_val):
                current_val = 0
            df_w.at[row_index, task] = int(current_val) + int(deltas[task])

        # Skills Plus 文字追加
        if new_skills.strip():
            if old_skills.strip():
                df_w.at[row_index, SKILLS_FIELD] = old_skills + "; " + new_skills.strip()
            else:
                df_w.at[row_index, SKILLS_FIELD] = new_skills.strip()

        # 排序後寫回
        df_w = df_w.sort_values("Week_Start")
        df_w.to_csv(WEEKLY_CSV_FILE, index=False, encoding="utf-8")
        st.success(f"Weekly 資料已寫入：{WEEKLY_CSV_FILE}")


# 📊 Weekly 分析與圖表
def analyze_weekly_data_ui(overwrite_images: bool):
    st.subheader("📊 Weekly Analysis")

    if not os.path.exists(WEEKLY_CSV_FILE):
        st.warning(f"找不到 weekly 資料檔：{WEEKLY_CSV_FILE}，略過 weekly 分析。")
        return

    df_w = pd.read_csv(WEEKLY_CSV_FILE, encoding="utf-8")
    if "Week_Start" not in df_w.columns:
        st.error("Weekly CSV 缺少 'Week_Start' 欄位，請確認檔案格式。")
        return
    if df_w.empty:
        st.warning("Weekly 資料為空，略過 weekly 分析。")
        return

    if SKILLS_FIELD not in df_w.columns:
        df_w[SKILLS_FIELD] = ""

    # 確保所有 weekly 數值欄位為數值
    for col in WEEKLY_TASKS:
        if col in df_w.columns:
            df_w[col] = pd.to_numeric(df_w[col], errors="coerce").fillna(0)
        else:
            df_w[col] = 0

    # 依週一日期排序
    df_w["Week_Start"] = pd.to_datetime(df_w["Week_Start"])
    df_w = df_w.sort_values("Week_Start").reset_index(drop=True)

    # 產生 Week_Label：MonthAbbr.N（同月份內按週數編號）
    years = df_w["Week_Start"].dt.year.to_list()
    months = df_w["Week_Start"].dt.month.to_list()

    week_index_in_month: list[int] = []
    last_ym = None
    counter = 0
    for y, m in zip(years, months):
        ym = (int(y), int(m))
        if ym != last_ym:
            last_ym = ym
            counter = 1
        else:
            counter += 1
        week_index_in_month.append(counter)

    df_w["Week_Index_In_Month"] = week_index_in_month

    labels: list[str] = []
    for m, idx in zip(months, week_index_in_month):
        abbr = calendar.month_abbr[int(m)]  # e.g. 'Nov'
        labels.append(f"{abbr}.{int(idx)}")
    df_w["Week_Label"] = labels

    st.write("Weekly 資料：")
    st.dataframe(df_w)

    x = np.arange(len(df_w))
    week_labels = df_w["Week_Label"].tolist()

    # 1) Workout 圖：四條線 + 數字標註
    workout_cols = ["Workout_Chest", "Workout_Back", "Workout_Legs", "Workout_Shoulders_Core"]
    fig, ax = plt.subplots(figsize=(10, 6))
    for col in workout_cols:
        y = df_w[col].to_numpy()
        ax.plot(x, y, marker="o", label=WEEKLY_TASK_LABELS.get(col, col))
        for i, val in enumerate(y):
            ax.text(float(i), float(val), str(int(val)), ha="center", va="bottom", fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(week_labels, rotation=45, fontsize=14)
    ax.set_ylabel("Count per Week", fontsize=14)
    ax.tick_params(axis="y", labelsize=14)
    ax.legend(loc="best")
    ax.set_title("Weekly Workout", fontsize=18, fontweight="bold")
    save_and_show_chart(fig, "Weekly Workout", overwrite_images)

    # 2) Learning 圖：兩條線 + 數字標註
    learning_cols = ["Learning_Drawing", "Learning_Flowchart"]
    fig, ax = plt.subplots(figsize=(10, 6))
    for col in learning_cols:
        y = df_w[col].to_numpy()
        ax.plot(x, y, marker="o", label=WEEKLY_TASK_LABELS.get(col, col))
        for i, val in enumerate(y):
            ax.text(float(i), float(val), str(int(val)), ha="center", va="bottom", fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(week_labels, rotation=45, fontsize=14)
    ax.set_ylabel("Count per Week", fontsize=14)
    ax.tick_params(axis="y", labelsize=14)
    ax.legend(loc="best")
    ax.set_title("Weekly Learning", fontsize=18, fontweight="bold")
    save_and_show_chart(fig, "Weekly Learning", overwrite_images)

    # 3) Date With Myself 圖：單條線 + 數字標註
    col = "Date_With_Myself"
    fig, ax = plt.subplots(figsize=(10, 6))
    y = df_w[col].to_numpy()
    ax.plot(x, y, marker="o", label=WEEKLY_TASK_LABELS.get(col, col))
    for i, val in enumerate(y):
        ax.text(float(i), float(val), str(int(val)), ha="center", va="bottom", fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(week_labels, rotation=45, fontsize=14)
    ax.set_ylabel("Count per Week", fontsize=14)
    ax.tick_params(axis="y", labelsize=14)
    ax.legend(loc="best")
    ax.set_title("Weekly Date With Myself", fontsize=18, fontweight="bold")
    save_and_show_chart(fig, "Weekly Date With Myself", overwrite_images)

    # 4) Skills Plus 圖：每週新技能文字列表
    lines: list[str] = []
    for i in range(len(df_w)):
        label = str(df_w.at[i, "Week_Label"])
        skills = str(df_w.at[i, SKILLS_FIELD]) if pd.notna(df_w.at[i, SKILLS_FIELD]) else ""
        skills = skills.strip() if skills else ""
        if not skills:
            skills = "-"
        lines.append(f"{label}: {skills}")

    text_content = "\n".join(lines)
    fig = plt.figure(figsize=(10, max(4.0, 0.6 * len(lines) + 1.0)))
    ax = fig.add_subplot(111)
    ax.axis("off")
    ax.text(0.01, 0.99, text_content, va="top", ha="left", fontsize=14)
    ax.set_title("Weekly Skills Plus List", fontsize=18, fontweight="bold", pad=20)
    save_and_show_chart(fig, "Weekly Skills Plus List", overwrite_images)


# 🚀 Streamlit 主入口
def main():
    st.title("📘 Daily & Weekly Habit Tracker")

    # 側邊欄設定
    st.sidebar.header("設定 / Settings")
    overwrite_images = st.sidebar.checkbox(
        "Overwrite existing image files when saving charts?",
        value=True,
    )
    st.sidebar.write("CSV 目錄：")
    st.sidebar.code(CSV_DIR)
    st.sidebar.write("圖片輸出目錄：")
    st.sidebar.code(PHOTO_DIR)

    tab_daily, tab_weekly = st.tabs(["Daily", "Weekly"])

    with tab_daily:
        daily_checklist_ui()
        st.markdown("---")
        if st.button("📊 產生每日統計圖"):
            analyze_daily_data_ui(overwrite_images)

    with tab_weekly:
        weekly_goal_checklist_ui()
        st.markdown("---")
        if st.button("📊 產生 Weekly 統計圖"):
            analyze_weekly_data_ui(overwrite_images)


if __name__ == "__main__":
    main()


