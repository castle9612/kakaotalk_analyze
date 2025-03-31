import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkcalendar import Calendar
from collections import Counter
from wordcloud import WordCloud
import pandas as pd
import re
import matplotlib.pyplot as plt
import platform

def get_font_path():
    system_name = platform.system()
    if system_name == "Windows":
        return "C:/Windows/Fonts/malgun.ttf"
    elif system_name == "Darwin":
        return "/System/Library/Fonts/Supplemental/AppleGothic.ttf"
    else:
        return "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"

font_path = get_font_path()
plt.rc("font", family="Malgun Gothic" if platform.system() == "Windows" else "AppleGothic")

def load_chat_data(filepath):
    with open(filepath, "r", encoding="utf-8") as file:
        lines = file.readlines()

    chat_data = []
    current_date = None
    
    date_pattern = re.compile(r"-+ (\d{4})년 (\d{1,2})월 (\d{1,2})일 .+ -+")
    message_pattern_old = re.compile(r"\[(.*?)\] \[(오전|오후) (\d+):(\d+)\] (.*)")
    message_pattern_new = re.compile(r"(\d{4})년 (\d{1,2})월 (\d{1,2})일 (오전|오후) (\d+):(\d+), (.*?): (.*)")
    
    for line in lines:
        line = line.strip()
        date_match = date_pattern.match(line)
        if date_match:
            year, month, day = map(int, date_match.groups())
            current_date = pd.Timestamp(year=year, month=month, day=day)
        else:
            old_match = message_pattern_old.match(line)
            new_match = message_pattern_new.match(line)
            
            if old_match and current_date:
                user, am_pm, hour, minute, message = old_match.groups()
                hour = int(hour)
                if am_pm == "오후" and hour != 12:
                    hour += 12
                elif am_pm == "오전" and hour == 12:
                    hour = 0
                chat_data.append([current_date, user, hour, int(minute), message])
            
            elif new_match:
                year, month, day, am_pm, hour, minute, user, message = new_match.groups()
                date = pd.Timestamp(year=int(year), month=int(month), day=int(day))
                hour = int(hour)
                if am_pm == "오후" and hour != 12:
                    hour += 12
                elif am_pm == "오전" and hour == 12:
                    hour = 0
                chat_data.append([date, user, hour, int(minute), message])

    df = pd.DataFrame(chat_data, columns=["Date", "User", "Hour", "Minute", "Message"])
    return df

def analyze_chat_between_dates(df, start_date, end_date):
    filtered_df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
    
    if filtered_df.empty:
        messagebox.showwarning("분석 결과 없음", "해당 기간 동안 채팅 데이터가 없습니다.")
        return
    
    user_message_counts = filtered_df['User'].value_counts()
    # top_users = user_message_counts.head(10)
    top_users = user_message_counts

    all_text = " ".join(filtered_df["Message"])
    words = re.findall(r'\b\w+\b', all_text.lower())
    word_counts = Counter(words)
    top_words = word_counts.most_common(10)
    
    result_text = "📊 채팅 기록 분석 결과\n\n"
    result_text += "👤 유저별 채팅 횟수\n"
    result_text += "\n".join([f"{user}: {count}회" for user, count in top_users.items()])
    result_text += "\n\n📝 가장 많이 사용된 단어 (Top 10)\n"
    result_text += "\n".join([f"{word}: {count}회" for word, count in top_words])
    
    new_window = tk.Toplevel(root)
    new_window.title("기간별 채팅 분석 결과")
    new_window.geometry("500x500")

    # 텍스트 위젯으로 결과 출력
    text_widget = tk.Text(new_window, wrap="word")
    text_widget.insert("1.0", result_text)
    text_widget.config(state="disabled")
    text_widget.pack(expand=True, fill="both", padx=10, pady=10)

    # 유저 검색 기능
    search_frame = ttk.Frame(new_window)
    search_frame.pack(pady=5)

    search_label = ttk.Label(search_frame, text="유저 검색:")
    search_label.pack(side="left", padx=5)

    search_var = tk.StringVar()
    search_entry = ttk.Entry(search_frame, textvariable=search_var)
    search_entry.pack(side="left", padx=5)

    search_result_label = ttk.Label(new_window, text="")
    search_result_label.pack()

    def search_user_message_count():
        search_user = search_var.get().strip()
        if search_user:
            matched_df = filtered_df[filtered_df["User"].str.contains(search_user, na=False)]
            matched_users = matched_df["User"].unique()
            count = matched_df.shape[0]

            if count > 0:
                user_names = ", ".join(matched_users)
                search_result_label.config(
                    text=f"🔎 '{user_names}'님의 채팅 수: {count}회"
                )
            else:
                search_result_label.config(text=f"'{search_user}'를 포함한 유저가 없습니다.")
        else:
            messagebox.showwarning("입력 필요", "유저 이름을 입력해주세요.")


    search_button = ttk.Button(search_frame, text="검색", command=search_user_message_count)
    search_button.pack(side="left", padx=5)

def analyze_selected_user():
    selected_user = user_var.get()
    if not selected_user:
        messagebox.showwarning("유저 선택", "유저를 선택해주세요.")
        return

    # 날짜 범위 가져오기
    start_date = pd.to_datetime(start_cal.get_date())
    end_date = pd.to_datetime(end_cal.get_date())

    # 필터된 데이터 전달
    filtered_df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]
    analyze_user_chat(selected_user, filtered_df)

def analyze_user_chat(user_name, filtered_df):
    user_df = filtered_df[filtered_df["User"] == user_name]
    if user_df.empty:
        messagebox.showwarning("유저 없음", f"'{user_name}'님의 채팅이 해당 기간에 없습니다.")
        return

    all_text = " ".join(user_df["Message"])

    # 워드클라우드 생성
    wordcloud = WordCloud(width=800, height=400, background_color="white", font_path=font_path).generate(all_text)

    # 단어 빈도 분석
    words = re.findall(r'\b\w+\b', all_text.lower())
    word_counts = Counter(words)
    total = sum(word_counts.values())
    top_words = word_counts.most_common(10)

    result_text = f"📊 {user_name}님의 주요 단어 사용 비율 (Top 10):\n"
    for word, count in top_words:
        result_text += f"{word}: {count}회 ({count/total:.2%})\n"

    # 새 창 생성
    new_window = tk.Toplevel(root)
    new_window.title(f"{user_name}님의 분석 결과")
    new_window.geometry("800x700")

    # 텍스트 출력 위젯
    text_widget = tk.Text(new_window, wrap="word", height=10)
    text_widget.insert("1.0", result_text)
    text_widget.config(state="disabled")
    text_widget.pack(padx=10, pady=10, fill="x")

    # 워드클라우드 표시
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.title(f"📌 {user_name}님의 워드클라우드", fontsize=16)
    plt.tight_layout()
    plt.show()

def open_file():
    global df
    file_path = filedialog.askopenfilename(title="채팅 데이터 파일 선택", filetypes=[["Text Files", "*.txt"]])
    if file_path:
        df = load_chat_data(file_path)
        df["Date"] = pd.to_datetime(df["Date"])
        users = df["User"].unique().tolist()
        user_combo["values"] = users
        messagebox.showinfo("파일 로드 완료", "채팅 데이터가 성공적으로 로드되었습니다!")

def analyze_date_range():
    start_date = pd.to_datetime(start_cal.get_date())
    end_date = pd.to_datetime(end_cal.get_date())
    analyze_chat_between_dates(df, start_date, end_date)

# GUI 설정
root = tk.Tk()
root.title("카카오톡 채팅 분석 도구 made by MSY")
root.geometry("600x600")

file_button = ttk.Button(root, text="파일 열기", command=open_file)
file_button.pack(pady=5)

start_cal = Calendar(root, selectmode="day")
start_cal.pack()
end_cal = Calendar(root, selectmode="day")
end_cal.pack()

date_analyze_button = ttk.Button(root, text="📅 기간별 분석 실행", command=analyze_date_range)
date_analyze_button.pack(pady=10)

user_label = ttk.Label(root, text="특정 유저 선택")
user_label.pack()

user_var = tk.StringVar()
user_combo = ttk.Combobox(root, textvariable=user_var, state="readonly")
user_combo.pack(pady=5)

analyze_user_button = ttk.Button(root, text="🔍 유저별 분석 실행", command=analyze_selected_user)
analyze_user_button.pack(pady=10)

root.mainloop()
