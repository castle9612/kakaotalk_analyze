# 📊 카카오톡 채팅 분석 도구 made by MSY

이 도구는 **카카오톡 대화 내용을 분석**하여, 기간별 채팅 빈도, 사용자별 채팅 수, 그리고 워드클라우드를 시각적으로 확인할 수 있도록 도와주는 **Tkinter GUI 애플리케이션**입니다.

---

## 🛠️ 설치 및 실행 방법

### 1. 필요한 라이브러리 설치
```bash
pip install pandas matplotlib wordcloud tkcalendar
```

> ✅ `tkinter`는 Python 표준 라이브러리로 포함되어 있으나, macOS나 Linux의 경우 별도 설치가 필요할 수 있습니다.

---

### 2. 실행 방법
```bash
python kakao_chat_analyzer.py
```

---

## 📁 카카오톡 채팅 파일 준비하기

1. 카카오톡에서 **텍스트로 내보낸 대화 파일 (`.txt`)** 을 준비하세요.
2. 인코딩은 **UTF-8** 형식이어야 합니다. (기본 설정 그대로 내보내면 됩니다.)
3. 구 버전/신 버전 모두 인식됩니다:
   - 구버전: `[홍길동] [오후 9:13] 안녕하세요`
   - 신버전: `2023년 10월 1일 오전 9:13, 홍길동: 안녕하세요`

---

## 📌 기능 소개

### 🔓 1. 채팅 파일 열기
- **[파일 열기] 버튼** 클릭 후, 카카오톡 채팅 `.txt` 파일을 선택합니다.
- 유저 목록이 자동으로 로드됩니다.

### 📅 2. 기간별 채팅 분석
- 시작/종료 날짜를 선택한 뒤, **[📅 기간별 분석 실행]** 버튼을 클릭하세요.
- 전체 채팅 분석 결과:
  - **유저별 채팅 수**
  - **가장 많이 사용된 단어 Top 10**
  - 유저명 검색 기능 제공

### 🔍 3. 특정 유저 분석
- 콤보박스에서 유저를 선택 후, **[🔍 유저별 분석 실행]** 버튼 클릭
- 해당 유저의:
  - **워드클라우드 시각화**
  - **Top 10 단어 사용 비율**

---

## 💻 플랫폼 호환성

| 운영체제 | 지원 여부 | 폰트 경로 |
|----------|-----------|------------|
| Windows  | ✅ 지원   | `C:/Windows/Fonts/malgun.ttf` |
| macOS    | ✅ 지원   | `/System/Library/Fonts/Supplemental/AppleGothic.ttf` |
| Linux    | ✅ 지원   | `/usr/share/fonts/truetype/nanum/NanumGothic.ttf` |

> 💡 `Malgun Gothic`, `AppleGothic`, 또는 `NanumGothic`이 없을 경우, 워드클라우드에 한글이 깨질 수 있습니다.

---

## 🖼️ 예시 화면

- 분석 결과 텍스트 창  
- 유저 워드클라우드 (Matplotlib 팝업으로 표시)

---

## 🙋‍♂️ 만든이

- Made by **MSY**
- Python, Tkinter, Pandas, WordCloud, Matplotlib, tkcalendar 사용
