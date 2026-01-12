from flask import Flask, request, jsonify
import requests
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

APISPORTS_KEY = "50821732136711c22939fbb8ce18bcc2"

# 한국 시간 기준 오늘 (KST 00:00 ~ 23:59)
kst = timezone(timedelta(hours=9))
today_kst = datetime.now(kst).replace(hour=0, minute=0, second=0, microsecond=0)

# UTC 범위
start_utc = today_kst.astimezone(timezone.utc)
end_utc = (today_kst + timedelta(days=1)).astimezone(timezone.utc) - timedelta(seconds=1)

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

# KST 오늘 경기 필터링
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

def generate_text_output():
    if not sorted_games:
        return "오늘 한국 시간 NBA 경기가 없습니다 ㅠㅠ"

    lines = [f"🏀 한국 시간 {today_kst.strftime('%Y-%m-%d')} NBA 경기: {len(sorted_games)}개"]
    lines.append("-" * 50)

    if sorted_games:
        max_team_len = max(
            max(len(game['teams']['home']['name']), len(game['teams']['visitors']['name']))
            for game in sorted_games
        )

        for game in sorted_games:
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

            if status_short in ['1', 'NS']:
                icon = "🕒"
                score_line = f"{visitors:<{max_team_len}} vs {home:<{max_team_len}}"
                status_text = ""
            elif status_short in ['2', 'Q1', 'Q2', 'Q3', 'Q4', 'OT', 'BT']:
                icon = "🔴"
                score_line = f"{visitors:<{max_team_len}} {visitors_score:>3} - {home_score:>3} {home:<{max_team_len}}"
                status_text = "LIVE"
            elif status_short in [3, 'FT']:
                icon = "🏁"
                score_line = f"{visitors:<{max_team_len}} {visitors_score:>3} - {home_score:>3} {home:<{max_team_len}}"
                status_text = "종료"
            else:
                icon = "❓"
                score_line = f"{visitors:<{max_team_len}} ? - ? {home:<{max_team_len}}"
                status_text = status_short

            status_part = f" ({status_text})" if status_text else ""
            lines.append(f"{icon} {time_str} | {score_line} {status_part}")

    return "\n".join(lines)

@app.route('/', methods=['POST'])
def kakao_skill():
    data = request.get_json()
    utterance = data.get('userRequest', {}).get('utterance', '').strip()

    # 키워드 체크 (대소문자 무시 + 일부 포함)
    keywords = ["오늘 경기", "nba 스코어", "오늘 nba", "nba 오늘"]
    if any(k.lower() in utterance.lower() for k in keywords):
        text = generate_text_output()

        # 카카오 스킬 응답: SimpleText + QuickReply (재시도용)
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
                        "action": "block",
                        "label": "다시 확인하기",
                        "messageText": "오늘 경기",
                        "blockId": "your_block_id_if_needed"  # 필요 시 블록 ID 넣기 (오픈빌더에서)
                    }
                ]
            }
        }
    else:
        response = {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": "NBA 오늘 경기 정보를 원하시면 '오늘 경기' 또는 'NBA 스코어'라고 말씀해주세요! 🏀"
                        }
                    }
                ]
            }
        }

    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)