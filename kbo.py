import requests
from datetime import datetime, timezone, timedelta

API_KEY = "50821732136711c22939fbb8ce18bcc2"
HEADERS = {"x-apisports-key": API_KEY}

kst = timezone(timedelta(hours=9))
today_kst = datetime.now(kst)
# date_str = today_kst.strftime("%Y-%m-%d")
date_str = "2026-01-12"

BASE_URL = "https://v1.baseball.api-sports.io"
KBO_LEAGUE_ID = 6  # ← 여기에 찾은 ID 넣어
SEASON = 2026  # 시즌 (무료 플랜 제한 있으면 빼봐)

# season 포함 호출
url = f"{BASE_URL}/games?date={date_str}&league={KBO_LEAGUE_ID}&season={SEASON}"
# season 빼고 시도
# url = f"{BASE_URL}/games?date={date_str}&league={KBO_LEAGUE_ID}"

print(f"호출 URL: {url}")

response = requests.get(url, headers=HEADERS)

if response.status_code == 200:
    data = response.json()
    print("결과 수:", data.get('results', 0))
    print("전체 응답 미리보기:", str(data)[:1000])  # 형태 확인용 (첫 1000자)
    if data.get('results', 0) > 0:
        print("\n첫 번째 경기 데이터 전체:")
        print(data['response'][0])  # 구조 확인
else:
    print("에러:", response.status_code, response.text)

