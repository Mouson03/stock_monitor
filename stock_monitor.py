import requests
import json

def send_dingtalk_message(message):
    webhook_url = "https://oapi.dingtalk.com/robot/send?access_token=f9a9044d1c878dfd92d71a18704f623b4cd88296a1762dce858e372dcef76202"
    headers = {'Content-Type': 'application/json'}
    data = {
        "msgtype": "text",
        "text": {
            "content": message
        }
    }
    response = requests.post(webhook_url, headers=headers, data=json.dumps(data))

send_dingtalk_message('测试actions')
