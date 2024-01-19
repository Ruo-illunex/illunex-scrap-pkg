import json

import requests

from app.config.settings import SYNOLOGY_CHAT


# 시놀로지 챗봇 설정
api_url = SYNOLOGY_CHAT['api_url']


# 보낼 메시지
def send_message_to_synology_chat(message, token):
    # 시놀로지 챗 API URL
    url = f"{api_url}?api=SYNO.Chat.External&method=incoming&version=2&token={token}"

    # 메시지 데이터
    data = {
        "payload": json.dumps({"text": message})
    }

    # POST 요청으로 메시지 전송
    response = requests.post(url, data=data)
    return response.status_code, response.text
