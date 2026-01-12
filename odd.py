import requests
from datetime import datetime, timezone, timedelta

API_KEY = "b207cc636981bd20769d1ebdf6042f59"  # ← 네 키 넣기

# 오늘 + 내일 경기 가져오기 (시간 범위 필터링)
url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds/?apiKey={API_KEY}&regions=us&markets=h2h,spreads,totals&oddsFormat=decimal"

response = requests.get(url)

if response.status_code != 200:
    print("에러:", response.status_code, response.text)
    exit()

data = response.json()
remaining = response.headers.get('x-requests-remaining', '알수없음')
print(f"사용 credits 남음: {remaining}")

kst = timezone(timedelta(hours=9))
today_start = datetime.now(kst).replace(hour=0, minute=0, second=0, microsecond=0)
tomorrow_end = today_start + timedelta(days=2)

filtered_games = []
for game in data:
    commence = datetime.fromisoformat(game['commence_time'].replace('Z', '+00:00'))
    commence_kst = commence.astimezone(kst)
    if today_start <= commence_kst < tomorrow_end:
        filtered_games.append(game)

filtered_games.sort(key=lambda g: datetime.fromisoformat(g['commence_time'].replace('Z', '+00:00')))

print(f"\n🏀 한국 시간 오늘 + 내일 NBA 경기: {len(filtered_games)}개")
print("-" * 60)

for game in filtered_games:
    home = game['home_team']
    away = game['away_team']
    commence = datetime.fromisoformat(game['commence_time'].replace('Z', '+00:00'))
    time_kst = commence.astimezone(kst).strftime('%m-%d %H:%M')

    status_icon = "🕒"  # 예정 경기 기본 (실시간 상태는 별도 API 필요)

    print(f"{status_icon} {time_kst} | {away} vs {home}")

    # FanDuel 하나만 선택 (없으면 DraftKings로 fallback)
    fanduel_book = next((b for b in game['bookmakers'] if b['key'] == 'fanduel'), None)
    if not fanduel_book:
        fanduel_book = next((b for b in game['bookmakers'] if b['key'] == 'draftkings'), None)

    if fanduel_book:
        print(f"  - FanDuel 배당:")
        for m in fanduel_book['markets']:
            if m['key'] == 'h2h':
                outcomes = [f"{o['name']} @ {o['price']}" for o in m['outcomes']]
                print(f"    승무패: {', '.join(outcomes)}")
            elif m['key'] == 'spreads':
                outcomes = [f"{o['name']} {o['point']} @ {o['price']}" for o in m['outcomes']]
                print(f"    핸디캡: {', '.join(outcomes)}")
            elif m['key'] == 'totals':
                outcomes = [f"{o['name']} {o['point']} @ {o['price']}" for o in m['outcomes']]
                print(f"    O/U: {', '.join(outcomes)}")
    else:
        print("  - 배당 정보 없음 (북메이커 미지원)")

    print("-" * 60)