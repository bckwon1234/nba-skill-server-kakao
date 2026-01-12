import requests
from datetime import datetime, timezone, timedelta

APISPORTS_KEY = "50821732136711c22939fbb8ce18bcc2"

# 한국 시간 기준 오늘 (KST 00:00 ~ 23:59)
kst = timezone(timedelta(hours=9))
today_kst = datetime.now(kst).replace(hour=0, minute=0, second=0, microsecond=0)

# UTC로 변환해서 범위 잡기
start_utc = today_kst.astimezone(timezone.utc)
end_utc = (today_kst + timedelta(days=1)).astimezone(timezone.utc) - timedelta(seconds=1)

# API는 date= 하나만 받으니, UTC 어제 + 오늘 합쳐서 필터링
yesterday_utc = start_utc.strftime('%Y-%m-%d')
today_utc = end_utc.strftime('%Y-%m-%d')

def get_games(date_str):
    url = f"https://v2.nba.api-sports.io/games?date={date_str}"
    headers = {"x-apisports-key": APISPORTS_KEY}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        return r.json().get('response', [])
    except:
        return []

all_games = get_games(yesterday_utc) + get_games(today_utc)

# KST 1월 12일 00:00 ~ 23:59 사이 경기만 필터링
kst_start = today_kst
kst_end = today_kst + timedelta(days=1)

filtered_games = []
for game in all_games:
    start_time = game.get('date', {}).get('start')
    if start_time:
        dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        dt_kst = dt.astimezone(kst)
        if kst_start <= dt_kst < kst_end:
            filtered_games.append(game)

# 시간순 정렬
sorted_games = sorted(filtered_games, key=lambda g: g.get('date', {}).get('start') or '')

if sorted_games:
    # 최대 팀 이름 길이 계산 (home과 visitors 모두 고려)
    max_team_len = max(
        max(len(game['teams']['home']['name']), len(game['teams']['visitors']['name']))
        for game in sorted_games
    )

    print(f"🏀 한국 시간 {today_kst.strftime('%Y-%m-%d')} NBA 경기: {len(sorted_games)}개")
    print("-" * 50)

    for game in sorted_games:
        # 시간
        start_time = game['date'].get('start')
        time_str = "시간 미정"
        if start_time:
            dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            dt_kst = dt.astimezone(kst)
            time_str = dt_kst.strftime('%H:%M')

        home = game['teams']['home']['name']
        visitors = game['teams']['visitors']['name']
        home_score = game['scores']['home'].get('points') or '-'
        visitors_score = game['scores']['visitors'].get('points') or '-'

        status_short = game['status']['short']
        
        if status_short in ['1', 'NS']:  # 예정
            icon = "🕒"
            score_line = f"{visitors:<{max_team_len}} vs {home:<{max_team_len}}"
            status_text = ""
        elif status_short in ['2', 'Q1', 'Q2', 'Q3', 'Q4', 'OT', 'BT']:  # 진행중
            icon = "🔴"
            score_line = f"{visitors:<{max_team_len}} {visitors_score:>3} - {home_score:>3} {home:<{max_team_len}}"
            status_text = "LIVE"
        elif status_short in [3, 'FT']:  # 종료
            icon = "🏁"
            score_line = f"{visitors:<{max_team_len}} {visitors_score:>3} - {home_score:>3} {home:<{max_team_len}}"
            status_text = "종료"
        else:
            icon = "❓"
            score_line = f"{visitors:<{max_team_len}} ? - ? {home:<{max_team_len}}"
            status_text = status_short

        status_part = f" ({status_text})" if status_text else ""
        print(f"{icon} {time_str} | {score_line}{status_part}")

else:
    print("오늘 한국 시간 NBA 경기가 없습니다 ㅠㅠ")

