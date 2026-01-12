from flask import Flask, request, jsonify
import requests
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

APISPORTS_KEY = "50821732136711c22939fbb8ce18bcc2"

# 한국 시간 기준 오늘 (KST 00:00 ~ 23:59)
kst = timezone(timedelta(hours=9))
today_kst = datetime.now(kst).replace(hour=0, minute=0, second=0, microsecond=0)

# 내일 KST
tomorrow_kst = today_kst + timedelta(days=1)

# UTC 날짜 문자열
today_utc = today_kst.astimezone(timezone.utc).strftime('%Y-%m-%d')
tomorrow_utc = tomorrow_kst.astimezone(timezone.utc).strftime('%Y-%m-%d')

def get_games(date_str):
    url = f"https://v2.nba.api-sports.io/games?date={date_str}"
    headers = {"x-apisports-key": APISPORTS_KEY}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        return r.json().get('response', [])
    except Exception as e:
        print(f"API 오류: {e}")
        return []

def get_filtered_games(target_kst):
    target_utc = target_kst.astimezone(timezone.utc).strftime('%Y-%m-%d')
    games = get_games(target_utc)
    
    filtered = []
    kst_start = target_kst
    kst_end = target_kst + timedelta(days=1)
    
    for game in games:
        start_time = game.get('date', {}).get('start')
        if start_time:
            dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            dt_kst = dt.astimezone(kst)
            if kst_start <= dt_kst < kst_end:
                filtered.append(game)
    
    return sorted(filtered, key=lambda g: g.get('date', {}).get('start') or '')

# 오늘/내일 게임 미리 불러오기 (캐싱 효과)
today_games = get_filtered_games(today_kst)
tomorrow_games = get_filtered_games(tomorrow_kst)

def generate_text_output(date_kst, games_list, label="오늘"):
    if not games_list:
        return f"한국 시간 {date_kst.strftime('%Y-%m-%d')}에 NBA 경기가 없습니다 ㅠㅠ"

    lines = [f"🏀 한국 시간 {date_kst.strftime('%Y-%m-%d')} NBA 경기: {len(games_list)}개"]
    lines.append("-" * 38)

    # 3글자 약어 맵핑
    abbr_map = {
        "New Orleans Pelicans": "NOP", "Orlando Magic": "ORL",
        "Brooklyn Nets": "BKN", "Memphis Grizzlies": "MEM",
        "Philadelphia 76ers": "PHI", "Toronto Raptors": "TOR",
        "New York Knicks": "NYK", "Portland Trail Blazers": "POR",
        "San Antonio Spurs": "SAS", "Minnesota Timberwolves": "MIN",
        "Miami Heat": "MIA", "Oklahoma City Thunder": "OKC",
        "Milwaukee Bucks": "MIL", "Denver Nuggets": "DEN",
        "Washington Wizards": "WAS", "Phoenix Suns": "PHX",
        "Atlanta Hawks": "ATL", "Golden State Warriors": "GSW",
        "Houston Rockets": "HOU", "Sacramento Kings": "SAC",
        "Los Angeles Lakers": "LAL", "Los Angeles Clippers": "LAC",
        "Boston Celtics": "BOS", "Cleveland Cavaliers": "CLE",
        "Dallas Mavericks": "DAL", "Detroit Pistons": "DET",
        "Indiana Pacers": "IND", "Chicago Bulls": "CHI",
        "Utah Jazz": "UTA", "Charlotte Hornets": "CHA",
        # 필요 시 더 추가 (API 응답에 따라)
    }

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

        status_short = game['status']['short']

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
        line = f"{icon} {time_str} | {score_line}{status_part}"
        lines.append(line)

    return "\n".join(lines)

@app.route('/', methods=['POST'])
def kakao_skill():
    data = request.get_json()
    utterance = data.get('userRequest', {}).get('utterance', '').strip().lower()

    if any(k in utterance for k in ["오늘 경기", "nba 스코어", "오늘 nba", "nba 오늘"]):
        text = generate_text_output(today_kst, today_games, "오늘")
    elif any(k in utterance for k in ["내일 경기", "내일 nba", "tomorrow nba", "내일 경기 결과"]):
        text = generate_text_output(tomorrow_kst, tomorrow_games, "내일")
    else:
        text = "NBA 경기 정보를 원하시면 '오늘 경기' 또는 '내일 경기'라고 말씀해주세요! 🏀"

    response = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": text
                    }
                }
            ],
            "quickReplies": [
                {
                    "action": "message",
                    "label": "오늘 경기",
                    "messageText": "오늘 경기"
                },
                {
                    "action": "message",
                    "label": "내일 경기",
                    "messageText": "내일 경기"
                }
            ]
        }
    }

    return jsonify(response)

# Render health check용 (선택적이지만 추천)
@app.route('/health', methods=['GET'])
def health():
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)