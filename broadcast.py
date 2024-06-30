import akshare as ak
import requests
import json

data = ak.index_us_stock_sina(symbol=".NDX")    
NDX_price_change_percentage=((data['close'].iloc[-1]-data['close'].iloc[-2])/data['close'].iloc[-2]*100).round(2)

data = ak.index_us_stock_sina(symbol=".INX")    
INX_price_change_percentage=((data['close'].iloc[-1]-data['close'].iloc[-2])/data['close'].iloc[-2]*100).round(2)

data = ak.index_us_stock_sina(symbol=".DJI")    
DJI_price_change_percentage=((data['close'].iloc[-1]-data['close'].iloc[-2])/data['close'].iloc[-2]*100).round(2)

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

send_dingtalk_message(f"纳斯达克100 {NDX_price_change_percentage}%\n标普500 {INX_price_change_percentage}%\n道琼斯 {DJI_price_change_percentage}%")  
