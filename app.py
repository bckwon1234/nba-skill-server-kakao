from flask import Flask, request, jsonify
import requests
from datetime import datetime, timezone, timedelta
from flask import make_response

app = Flask(__name__)
@app.after_request
def add_no_cache_headers(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


APISPORTS_KEY = "50821732136711c22939fbb8ce18bcc2"

kst = timezone(timedelta(hours=9))
today_kst = datetime.now(kst).replace(hour=0, minute=0, second=0, microsecond=0)

# 오늘용 UTC 범위 (시차 때문에 어제+오늘 불러옴)
start_utc = today_kst.astimezone(timezone.utc)
end_utc = (today_kst + timedelta(days=1)).astimezone(timezone.utc) - timedelta(seconds=1)
yesterday_utc = start_utc.strftime('%Y-%m-%d')
today_utc = end_utc.strftime('%Y-%m-%d')

# 내일용 UTC 범위 (내일+모레 불러와서 안전하게)
tomorrow_kst = today_kst + timedelta(days=1)
tomorrow_start_utc = tomorrow_kst.astimezone(timezone.utc)
tomorrow_end_utc = (tomorrow_kst + timedelta(days=1)).astimezone(timezone.utc) - timedelta(seconds=1)
tomorrow_utc = tomorrow_start_utc.strftime('%Y-%m-%d')
day_after_utc = tomorrow_end_utc.strftime('%Y-%m-%d')

def get_games(date_str):
    url = f"https://v2.nba.api-sports.io/games?date={date_str}"
    headers = {"x-apisports-key": APISPORTS_KEY}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        return r.json().get('response', [])
    except Exception as e:
        print(f"API Error on {date_str}: {e}")
        return []

def get_filtered_sorted_games(all_g, kst_start, kst_end):
    filtered = []
    for game in all_g:
        start_time = game.get('date', {}).get('start')
        if start_time:
            dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            dt_kst = dt.astimezone(kst)
            if kst_start <= dt_kst < kst_end:
                filtered.append(game)
    return sorted(filtered, key=lambda g: g.get('date', {}).get('start') or '')

# 오늘 경기 데이터
all_today = get_games(yesterday_utc) + get_games(today_utc)
today_games = get_filtered_sorted_games(all_today, today_kst, today_kst + timedelta(days=1))

# 내일 경기 데이터
all_tomorrow = get_games(tomorrow_utc) + get_games(day_after_utc)
tomorrow_games = get_filtered_sorted_games(all_tomorrow, tomorrow_kst, tomorrow_kst + timedelta(days=1))

# 3글자 약어 맵 - NBA 30개 팀 전체 (공식 약어 기준)
abbr_map = {
    "Atlanta Hawks": "ATL",
    "Boston Celtics": "BOS",
    "Brooklyn Nets": "BKN",
    "Charlotte Hornets": "CHA",
    "Chicago Bulls": "CHI",
    "Cleveland Cavaliers": "CLE",
    "Dallas Mavericks": "DAL",
    "Denver Nuggets": "DEN",
    "Detroit Pistons": "DET",
    "Golden State Warriors": "GSW",
    "Houston Rockets": "HOU",
    "Indiana Pacers": "IND",
    "Los Angeles Clippers": "LAC",          # 공식: Los Angeles Clippers → LAC
    "LA Clippers": "LAC",                   # 변형 이름 대비
    "Los Angeles Lakers": "LAL",            # 공식: Los Angeles Lakers → LAL
    "LA Lakers": "LAL",                     # 변형 이름 대비
    "Memphis Grizzlies": "MEM",
    "Miami Heat": "MIA",
    "Milwaukee Bucks": "MIL",
    "Minnesota Timberwolves": "MIN",
    "New Orleans Pelicans": "NOP",
    "New York Knicks": "NYK",
    "Oklahoma City Thunder": "OKC",
    "Orlando Magic": "ORL",
    "Philadelphia 76ers": "PHI",
    "Phoenix Suns": "PHX",
    "Portland Trail Blazers": "POR",
    "Sacramento Kings": "SAC",
    "San Antonio Spurs": "SAS",
    "Toronto Raptors": "TOR",
    "Utah Jazz": "UTA",
    "Washington Wizards": "WAS",
}

def generate_text_output(date_kst, games_list, label="오늘"):
    if not games_list:
        return f"한국 시간 {date_kst.strftime('%Y-%m-%d')}에 NBA 경기가 없습니다 ㅠㅠ"

    lines = [f"🏀 한국 시간 {date_kst.strftime('%Y-%m-%d')} NBA 경기: {len(games_list)}개"]
    lines.append("-" * 38)

    for game in games_list:
        start_time = game['date'].get('start')
        time_str = "시간 미정"
        if start_time:
            dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            dt_kst = dt.astimezone(kst)
            time_str = dt_kst.strftime('%H:%M')

        home_name = game['teams']['home']['name']
        visitors_name = game['teams']['visitors']['name']
        home_abbr = abbr_map.get(home_name, home_name[:3].upper())
        visitors_abbr = abbr_map.get(visitors_name, visitors_name[:3].upper())

        home_score = game['scores']['home'].get('points') or '-'
        visitors_score = game['scores']['visitors'].get('points') or '-'

        status_short = str(game['status']['short'])
        
        if status_short in ['1', 'NS']:
            icon = "🕒"
            score_line = f"{visitors_abbr} vs {home_abbr}"
            status_text = ""
        elif status_short in ['2', 'Q1', 'Q2', 'Q3', 'Q4', 'OT', 'BT']:
            icon = "🔴"
            score_line = f"{visitors_abbr} {visitors_score:>3} - {home_score:>3} {home_abbr}"
            status_text = "LIVE"
        elif status_short in ['3', 'FT']:
            icon = "🏁"
            score_line = f"{visitors_abbr} {visitors_score:>3} - {home_score:>3} {home_abbr}"
            status_text = "종료"
        else:
            icon = "❓"
            score_line = f"{visitors_abbr} ? - ? {home_abbr}"
            status_text = status_short

        status_part = f" ({status_text})" if status_text else ""
        lines.append(f"{icon} {time_str} | {score_line}{status_part}")

    return "\n".join(lines)

@app.route('/', methods=['POST'])
def kakao_skill():
    data = request.get_json()
    utterance = data.get('userRequest', {}).get('utterance', '').strip().lower()

    if any(k in utterance for k in ["오늘 경기", "nba 스코어", "오늘 nba", "nba 오늘"]):
        text = generate_text_output(today_kst, today_games, "오늘")
    elif any(k in utterance for k in ["내일 경기", "내일 nba", "tomorrow", "내일 경기 일정"]):
        text = generate_text_output(tomorrow_kst, tomorrow_games, "내일")
    else:
        text = "NBA 경기 정보를 원하시면 '오늘 경기' 또는 '내일 경기'라고 말씀해주세요! 🏀"

    response = {
        "version": "2.0",
        "template": {
            "outputs": [{"simpleText": {"text": text}}],
            "quickReplies": [
                {"action": "message", "label": "오늘 경기", "messageText": "오늘 경기"},
                {"action": "message", "label": "내일 경기", "messageText": "내일 경기"}
            ]
        }
    }
    return jsonify(response)

# Render 무료 플랜 sleep 방지용
@app.route('/health', methods=['GET'])
def health():
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
else:
    # Render에서는 gunicorn이 실행하니 여기서 아무것도 안 해도 됨
    pass