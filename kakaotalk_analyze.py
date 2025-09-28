import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from tkcalendar import Calendar
from collections import Counter
from wordcloud import WordCloud
import pandas as pd
import re
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import platform
import sys
import os

class ChatParser:
    """
    다양한 형식의 카카오톡 채팅 로그 파일을 파싱하여 pandas DataFrame으로 변환하는 클래스.
    제공된 최신 형식에 맞게 수정되었습니다.
    """
    def __init__(self, filepath):
        """
        ChatParser 인스턴스를 초기화합니다.
        
        :param filepath: 분석할 채팅 로그 파일의 경로
        """
        self.filepath = filepath
        self.message_pattern = re.compile(
            r"^(\d{4}년 \d{1,2}월 \d{1,2}일 (?:오전|오후) \d{1,2}:\d{2}), (.*?) : (.*)$"
        )
        self.system_message_pattern = re.compile(
            r"^(\d{4}년 \d{1,2}월 \d{1,2}일 (?:오전|오후) \d{1,2}:\d{2}), (.*)$"
        )

    def parse_file(self):
        try:
            with open(self.filepath, "r", encoding="utf-8") as file:
                lines = file.readlines()
        except (FileNotFoundError, UnicodeDecodeError) as e:
            messagebox.showerror("파일 오류", f"파일을 읽는 중 오류가 발생했습니다: {e}")
            return None

        chat_data = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            

            message_match = self.message_pattern.match(line)
            if message_match:
                timestamp_str, user, message = message_match.groups()
                try:
                    processed_ts_str = timestamp_str.replace('오전', 'AM').replace('오후', 'PM')
                    timestamp = pd.to_datetime(processed_ts_str, format='%Y년 %m월 %d일 %p %I:%M')
                    chat_data.append([timestamp.date(), user, timestamp.hour, timestamp.minute, message])
                except ValueError:
                    continue
                continue

            system_match = self.system_message_pattern.match(line)
            if system_match:
                timestamp_str, message = system_match.groups()
                if not message.strip():
                    continue
                try:
                    processed_ts_str = timestamp_str.replace('오전', 'AM').replace('오후', 'PM')
                    timestamp = pd.to_datetime(processed_ts_str, format='%Y년 %m월 %d일 %p %I:%M')
                    chat_data.append([timestamp.date(), 'System', timestamp.hour, timestamp.minute, message])
                except ValueError:
                    continue
                continue
            
            if chat_data:
                chat_data[-1][4] += "\n" + line

        if not chat_data:
            messagebox.showwarning("파싱 실패", "채팅 데이터를 인식할 수 없습니다.\n카카오톡 대화 내용 내보내기 텍스트 파일이 맞는지 확인해주세요.")
            return None

        df = pd.DataFrame(chat_data, columns=["Date", "User", "Hour", "Minute", "Message"])
        df["Date"] = pd.to_datetime(df["Date"])
        print(df.head())
        return df

class ChatAnalyzerApp:
    ADMIN_PASSWORD = ""

    def __init__(self, root):
        self.root = root
        self.root.title("카카오톡 채팅 분석기 by MSY")
        self.root.geometry("650x650")
        
        self.style = ttk.Style()
        self.style.theme_use('clam')

        self.df = None
        self.font_path = self._get_font_path()
        
        self._setup_ui()
        self._update_widget_states()

    def _get_font_path(self):
        """
        운영체제에 맞는 한글 폰트 경로를 반환합니다.
        .exe로 패키징된 경우, 함께 포함된 폰트 파일의 경로를 반환합니다.
        """
        if getattr(sys, 'frozen', False):
            bundle_dir = sys._MEIPASS
            font_path = os.path.join(bundle_dir, 'malgun.ttf')
        else:
            system_name = platform.system()
            if system_name == "Windows":
                font_path = "C:/Windows/Fonts/malgun.ttf"
            elif system_name == "Darwin": # macOS
                font_path = "/System/Library/Fonts/Supplemental/AppleGothic.ttf"
            else: # Linux
                font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
        
        if not os.path.exists(font_path):
            messagebox.showwarning("폰트 없음", f"기본 한글 폰트를 찾을 수 없습니다: {font_path}\n워드클라우드가 정상적으로 표시되지 않을 수 있습니다.")
            return None
        return font_path

    def _setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill="both", expand=True)

        file_frame = ttk.LabelFrame(main_frame, text="1. 파일 선택", padding="10")
        file_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)
        self.file_label = ttk.Label(file_frame, text="선택된 파일이 없습니다.")
        self.file_label.pack(side="left", fill="x", expand=True, padx=5)
        file_button = ttk.Button(file_frame, text="채팅 파일 열기", command=self._open_file)
        file_button.pack(side="right")

        self.date_range_var = tk.StringVar(value="로드된 데이터 기간: 없음")
        date_range_label = ttk.Label(file_frame, textvariable=self.date_range_var, foreground="gray")
        date_range_label.pack(side="left", anchor="sw", pady=(5, 0))

        date_frame = ttk.LabelFrame(main_frame, text="2. 분석 기간 설정", padding="10")
        date_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        date_frame.columnconfigure(0, weight=1); date_frame.columnconfigure(1, weight=1)
        ttk.Label(date_frame, text="시작 날짜").grid(row=0, column=0, pady=2)
        self.start_cal = Calendar(date_frame, selectmode="day", date_pattern="yyyy-mm-dd")
        self.start_cal.grid(row=1, column=0, sticky="nsew", padx=5)
        ttk.Label(date_frame, text="종료 날짜").grid(row=0, column=1, pady=2)
        self.end_cal = Calendar(date_frame, selectmode="day", date_pattern="yyyy-mm-dd")
        self.end_cal.grid(row=1, column=1, sticky="nsew", padx=5)

        action_frame = ttk.LabelFrame(main_frame, text="3. 분석 실행", padding="10")
        action_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)
        action_frame.columnconfigure(0, weight=1); action_frame.columnconfigure(1, weight=1)
        self.date_analyze_button = ttk.Button(action_frame, text="📅 기간별 전체 분석", command=self._analyze_date_range)
        self.date_analyze_button.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5, padx=5)
        ttk.Label(action_frame, text="특정 유저 선택:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.user_var = tk.StringVar()
        self.user_combo = ttk.Combobox(action_frame, textvariable=self.user_var, state="readonly")
        self.user_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.analyze_user_button = ttk.Button(action_frame, text="🔍 선택 유저 상세 분석", command=self._analyze_selected_user)
        self.analyze_user_button.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5, padx=5)

        ttk.Separator(action_frame, orient="horizontal").grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)
        self.admin_button = ttk.Button(action_frame, text="👑 관리자 기능 (입장/퇴장 분석)", command=self._prompt_admin_password)
        self.admin_button.grid(row=4, column=0, columnspan=2, sticky="ew", padx=5)

        self.status_var = tk.StringVar()
        self.status_var.set("준비 완료. 분석할 파일을 열어주세요.")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, anchor="w", relief="sunken")
        status_bar.pack(side="bottom", fill="x")

    def _update_widget_states(self):
        is_df_loaded = self.df is not None
        state = "normal" if is_df_loaded else "disabled"
        self.date_analyze_button.config(state=state)
        self.analyze_user_button.config(state=state)
        self.user_combo.config(state="readonly" if is_df_loaded else "disabled")
        self.admin_button.config(state=state)

    def _open_file(self):
        file_path = filedialog.askopenfilename(title="카카오톡 채팅 데이터 파일 선택", filetypes=[("텍스트 파일", "*.txt"), ("모든 파일", "*.*")])
        if not file_path: return
        self.status_var.set(f"'{os.path.basename(file_path)}' 파일을 로드하는 중...")
        self.root.update_idletasks()
        parser = ChatParser(file_path)
        self.df = parser.parse_file()
        if self.df is not None:
            users = sorted([user for user in self.df["User"].unique() if user != 'System'])
            self.user_combo["values"] = users
            if users: self.user_var.set(users[0])
            self.file_label.config(text=os.path.basename(file_path))
            self.status_var.set("파일 로드 완료. 분석을 시작하세요.")

            min_date = self.df['Date'].min().strftime('%Y-%m-%d')
            max_date = self.df['Date'].max().strftime('%Y-%m-%d')
            self.date_range_var.set(f"로드된 데이터 기간: {min_date} ~ {max_date}")

            messagebox.showinfo("파일 로드 완료", "채팅 데이터가 성공적으로 로드되었습니다!")
        else:
            self.file_label.config(text="선택된 파일이 없습니다.")
            self.status_var.set("파일 로드 실패. 다른 파일을 선택해주세요.")
            self.date_range_var.set("로드된 데이터 기간: 없음")
        self._update_widget_states()

    def _get_filtered_df(self):
        try:
            start_date = pd.to_datetime(self.start_cal.get_date())
            end_date = pd.to_datetime(self.end_cal.get_date())
        except Exception as e:
            messagebox.showerror("날짜 오류", f"유효한 날짜를 선택해주세요: {e}")
            return None
        if start_date > end_date:
            messagebox.showwarning("날짜 오류", "시작 날짜는 종료 날짜보다 이전이어야 합니다.")
            return None
        filtered_df = self.df[(self.df['Date'] >= start_date) & (self.df['Date'] <= end_date)]
        if filtered_df.empty:
            messagebox.showinfo("데이터 없음", "선택하신 기간 동안의 채팅 데이터가 없습니다.")
            return None
        return filtered_df

    def _prompt_admin_password(self):
        password = simpledialog.askstring("비밀번호 인증", "관리자 비밀번호를 입력하세요:", show='*')
        if password == self.ADMIN_PASSWORD:
            self._analyze_entry_exit()
        elif password is not None:
            messagebox.showerror("인증 실패", "비밀번호가 올바르지 않습니다.")

    def _analyze_entry_exit(self):
        """
        사용자별 입장, 퇴장, 재입장 횟수를 분석합니다. (수정됨)
        """
        filtered_df = self._get_filtered_df()
        if filtered_df is None: return

        system_messages_df = filtered_df[filtered_df['User'] == 'System']

        if system_messages_df.empty:
            messagebox.showinfo("결과 없음", "선택된 기간에 분석할 시스템 메시지(입장/퇴장)가 없습니다.")
            return

        enter_pattern = re.compile(r"(.+)님이 들어왔습니다\.")
        invite_pattern = re.compile(r".+님이 (.+)님을 초대했습니다\.")
        leave_pattern = re.compile(r"(.+)님이 나갔습니다\.")

        entry_counts = Counter()
        exit_counts = Counter()

        for message in system_messages_df["Message"]:
            enter_match = enter_pattern.match(message)
            if enter_match:
                entry_counts[enter_match.group(1)] += 1
                continue
            
            invite_match = invite_pattern.match(message)
            if invite_match:
                invited_users = invite_match.group(1).split(", ")
                for user in invited_users: entry_counts[user.strip()] += 1
                continue

            leave_match = leave_pattern.match(message)
            if leave_match:
                exit_counts[leave_match.group(1)] += 1
        
        all_users = set(entry_counts.keys()) | set(exit_counts.keys())
        analysis_data = []
        for user in sorted(list(all_users)):
            entries = entry_counts.get(user, 0)
            exits = exit_counts.get(user, 0)
            re_entries = min(entries, exits)
            if entries > 0 or exits > 0:
                analysis_data.append((user, entries, exits, re_entries))

        if not analysis_data:
            messagebox.showinfo("결과 없음", "선택된 기간에 입장 또는 퇴장 기록이 없습니다.")
            return

        sorted_data = sorted(analysis_data, key=lambda item: item[3], reverse=True)

        self._show_admin_analysis_window(sorted_data)
    
    def _show_admin_analysis_window(self, data):
        win = tk.Toplevel(self.root)
        win.title("관리자 분석: 사용자 입장/퇴장 횟수")
        win.geometry("600x400")
        frame = ttk.Frame(win, padding=10)
        frame.pack(fill="both", expand=True)
        tree = ttk.Treeview(frame, columns=("User", "Entries", "Exits", "ReEntries"), show="headings")
        tree.heading("User", text="사용자"); tree.heading("Entries", text="입장 횟수")
        tree.heading("Exits", text="퇴장 횟수"); tree.heading("ReEntries", text="재입장 횟수 (최소치)")
        tree.column("User", anchor="w", width=150); tree.column("Entries", anchor="center", width=100)
        tree.column("Exits", anchor="center", width=100); tree.column("ReEntries", anchor="center", width=120)
        for item in data: tree.insert("", "end", values=item)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _analyze_date_range(self):
        filtered_df = self._get_filtered_df()
        if filtered_df is None: return
        user_message_counts = filtered_df[filtered_df['User'] != 'System']['User'].value_counts()
        all_text = " ".join(filtered_df[filtered_df['User'] != 'System']["Message"])
        words = re.findall(r'[가-힣a-zA-Z0-9]+', all_text)
        word_counts = Counter(words); top_words = word_counts.most_common(20)
        self._show_range_analysis_window(user_message_counts, top_words)

    def _show_range_analysis_window(self, user_counts, top_words):
        win = tk.Toplevel(self.root)
        win.title("기간별 전체 분석 결과")
        win.geometry("600x500")
        user_frame = ttk.LabelFrame(win, text="👤 유저별 채팅 횟수", padding=10)
        user_frame.pack(fill="both", expand=True, padx=10, pady=5)
        tree = ttk.Treeview(user_frame, columns=("User", "Count"), show="headings")
        tree.heading("User", text="사용자"); tree.heading("Count", text="채팅 수")
        tree.column("User", width=200); tree.column("Count", width=100, anchor="e")
        for user, count in user_counts.items(): tree.insert("", "end", values=(user, count))
        tree.pack(fill="both", expand=True)
        word_frame = ttk.LabelFrame(win, text="📝 가장 많이 사용된 단어 (Top 20)", padding=10)
        word_frame.pack(fill="x", padx=10, pady=5)
        words_text = "\n".join([f"{word}: {count}회" for word, count in top_words])
        word_label = ttk.Label(word_frame, text=words_text, justify="left")
        word_label.pack(anchor="w")

    def _analyze_selected_user(self):
        selected_user = self.user_var.get()
        if not selected_user:
            messagebox.showwarning("유저 선택", "분석할 유저를 선택해주세요.")
            return
        filtered_df = self._get_filtered_df()
        if filtered_df is None: return
        user_df = filtered_df[filtered_df["User"] == selected_user]
        if user_df.empty:
            messagebox.showinfo("데이터 없음", f"선택하신 기간 동안 '{selected_user}'님의 채팅 데이터가 없습니다.")
            return
        all_text = " ".join(user_df["Message"])
        if not all_text.strip():
            messagebox.showinfo("분석 불가", f"'{selected_user}'님의 메시지에 분석할 단어가 없습니다.")
            return
        try:
            wordcloud = WordCloud(width=800, height=400, background_color="white", font_path=self.font_path).generate(all_text)
        except Exception as e:
            messagebox.showerror("워드클라우드 오류", f"워드클라우드 생성 중 오류 발생: {e}")
            return
        words = re.findall(r'[가-힣a-zA-Z0-9]+', all_text)
        word_counts = Counter(words); top_words = word_counts.most_common(10)
        self._show_user_analysis_window(selected_user, wordcloud, word_counts)

    def _show_user_analysis_window(self, user_name, wordcloud, word_counts):
        win = tk.Toplevel(self.root); win.title(f"{user_name}님 상세 분석 결과"); win.geometry("800x700")
        wc_frame = ttk.LabelFrame(win, text="☁️ 워드클라우드", padding=10)
        wc_frame.pack(fill="both", expand=True, padx=10, pady=5)
        fig, ax = plt.subplots(figsize=(8, 4)); ax.imshow(wordcloud, interpolation="bilinear"); ax.axis("off")
        canvas = FigureCanvasTkAgg(fig, master=wc_frame); canvas.draw(); canvas.get_tk_widget().pack(fill="both", expand=True)
        word_frame = ttk.LabelFrame(win, text="📝 주요 단어 사용 빈도 (Top 10)", padding=10)
        word_frame.pack(fill="x", padx=10, pady=5)
        total_words = sum(word_counts.values())
        result_text = ""
        for word, count in word_counts.most_common(10):
            percentage = (count / total_words) * 100 if total_words > 0 else 0
            result_text += f"▪️ {word}: {count}회 ({percentage:.2f}%)\n"
        word_label = ttk.Label(word_frame, text=result_text.strip(), justify="left"); word_label.pack(anchor="w")

if __name__ == "__main__":
    plt.rcParams['font.family'] = 'Malgun Gothic' if platform.system() == "Windows" else 'AppleGothic'
    plt.rcParams['axes.unicode_minus'] = False
    
    root = tk.Tk()
    app = ChatAnalyzerApp(root)

    root.mainloop()
