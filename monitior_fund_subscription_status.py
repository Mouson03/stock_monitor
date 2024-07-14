import akshare as ak
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



fund_code=['164824','161128']
for symbol in fund_code:
    data = ak.fund_etf_fund_info_em(fund=symbol, start_date="20240701", end_date="20241231")
    print(data)
    if data['申购状态'].iloc[-1]!='暂停申购':
       send_dingtalk_message(f"基金{symbol}开放申购")

# 记录运行日志
log_message = f"{today}  \"ETF溢价率记录及预警\"  程序运行完毕"
log_file = "actions_running_log.txt"
with open(log_file, 'a') as f:
    f.write(f"{log_message}\n")
