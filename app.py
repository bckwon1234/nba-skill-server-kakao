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
        # response.text를 utf-8로 강제 디코딩 (latin-1 대신)
        response_text = response.content.decode('utf-8', errors='replace')  # 깨지면 ?로 대체
        data = json.loads(response_text)  # 직접 json.loads 사용 (response.json() 대신)
        
        games = data.get('response', [])
    
        if not games:
            text = "오늘 예정된 NBA 경기가 없습니다."
        else:
            text = f"🏀 오늘 ({today}) NBA 경기 일정 & 스코어\n\n"
            for game in games[:10]:
                home = game['teams']['home']['name']
                away = game['teams']['visitor']['name']
                score_home = game['scores']['home']['current'] or '-'
                score_away = game['scores']['visitor']['current'] or '-'
                status = game['status']['short']
                clock = game['status']['clock'] or ''
    
                text += f"{home} {score_home} - {score_away} {away}\n"
                text += f"   상태: {status} {clock}\n\n"
    
    except Exception as e:
        # 에러 메시지에 한글 깨짐 방지 위해 str(e)도 안전하게
        error_msg = str(e).encode('utf-8', errors='ignore').decode('utf-8')
        text = f"경기 정보를 가져오지 못했어요 ㅠㅠ\n(에러: {error_msg})"

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