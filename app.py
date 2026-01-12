from flask import Flask, request, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

# ← 여기에 당신의 RapidAPI 키를 넣으세요!
# https://rapidapi.com 에서 API-Basketball 구독 후 키 복사
RAPIDAPI_KEY = "여기에_당신의_RapidAPI_키_입력"

@app.route('/nba_today', methods=['POST'])
def nba_today():
    data = request.json
    utterance = data.get('userRequest', {}).get('utterance', '')

    # 오늘 날짜 (UTC 기준)
    today = datetime.utcnow().strftime('%Y-%m-%d')

    url = f"https://api-basketball.p.rapidapi.com/games?date={today}"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "api-basketball.p.rapidapi.com"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        games = response.json().get('response', [])

        if not games:
            text = "오늘 예정된 NBA 경기가 없습니다."
        else:
            text = f"🏀 오늘 ({today}) NBA 경기 일정 & 스코어\n\n"
            for game in games[:10]:  # 너무 많으면 상위 10개만
                home = game['teams']['home']['name']
                away = game['teams']['visitor']['name']
                score_home = game['scores']['home']['current'] or '-'
                score_away = game['scores']['visitor']['current'] or '-'
                status = game['status']['short']
                clock = game['status']['clock'] or ''

                text += f"{home} {score_home} - {score_away} {away}\n"
                text += f"   상태: {status} {clock}\n\n"

    except Exception as e:
        text = f"경기 정보를 가져오지 못했어요 ㅠㅠ\n({str(e)})"

    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": text
                    }
                }
            ]
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)