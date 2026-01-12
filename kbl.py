import requests
from datetime import datetime, timezone, timedelta

API_KEY = "50821732136711c22939fbb8ce18bcc2"
HEADERS = {"x-apisports-key": API_KEY}

# 한국 시간 기준 오늘
kst = timezone(timedelta(hours=9))
today_kst = datetime.now(kst).replace(hour=0, minute=0, second=0, microsecond=0)
# date_str = today_kst.strftime("%Y-%m-%d")
date_str = "2026-01-11"#today_kst.strftime("%Y-%m-%d")

# API 호출 (season 없이, league 없이 전체 → 무료 플랜 호환)
url = f"https://v1.basketball.api-sports.io/games?date={date_str}"

print(f"🏀 KBL 오늘 경기 확인 중... ({date_str})")
print(f"호출 URL: {url}")
print("-" * 60)

response = requests.get(url, headers=HEADERS)

if response.status_code != 200:
    print(f"API 호출 실패: {response.status_code}")
    print(response.text)
    exit()

data = response.json()
all_games = data.get('response', [])

# KBL 경기만 필터링 (league id 91)
kbl_games = [g for g in all_games if g.get('league', {}).get('id') == 91]
print(f"전체 농구 경기 수: {len(kbl_games)}")

if not kbl_games:
    print("오늘 KBL 경기가 없습니다 ㅠㅠ (또는 데이터 업데이트 대기 중)")
    exit()

# 시간순 정렬
kbl_games.sort(key=lambda g: g.get('date') or '9999')

# 최대 팀 이름 길이 계산
max_team_len = max(
    max(len(g['teams']['home']['name']), len(g['teams']['away']['name']))
    for g in kbl_games
)

print(f"\n🏀 한국 시간 {date_str} KBL 경기: {len(kbl_games)}개")
print("-" * 60)

for game in kbl_games[:10]:  # 최대 10개 제한
    # 시간 변환
    date_raw = game.get('date')
    time_str = "시간 미정"
    if isinstance(date_raw, str):
        try:
            dt = datetime.fromisoformat(date_raw.replace('Z', '+00:00'))
            dt_kst = dt.astimezone(kst)
            time_str = dt_kst.strftime('%H:%M')
        except:
            pass

    home = game['teams']['home']['name']
    away = game['teams']['away']['name']

    # 스코어 (total 사용, None이면 '-')
    home_score = game['scores']['home']['total'] or '-'
    away_score = game['scores']['away']['total'] or '-'

    status_short = game['status']['short']

    # 상태별 아이콘 + 출력 형식
    if status_short == 'NS':
        icon = "🕒"
        score_line = f"{away:<{max_team_len}} vs {home:<{max_team_len}}"
        status_text = ""
    elif status_short in ['LIVE', 'Q1', 'Q2', 'Q3', 'Q4', 'OT']:
        icon = "🔴"
        score_line = f"{away:<{max_team_len}} {away_score:>3} - {home_score:>3} {home:<{max_team_len}}"
        status_text = "LIVE"
    elif status_short in ['FT', 'END']:
        icon = "🏁"
        score_line = f"{away:<{max_team_len}} {away_score:>3} - {home_score:>3} {home:<{max_team_len}}"
        status_text = "종료"
    else:
        icon = "❓"
        score_line = f"{away:<{max_team_len}} ? - ? {home:<{max_team_len}}"
        status_text = status_short

    status_part = f" ({status_text})" if status_text else ""
    print(f"{icon} {time_str} | {score_line}{status_part}")

print("\n(현재 예정 경기라 스코어는 '-'로 표시됩니다. 경기 시작 후 다시 실행해보세요!)")