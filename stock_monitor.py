#轻量化
#1.取消非周末检查,非交易时间检查,sys,datetime,取消pandas(直接只用指数)2.index_poll改成列表 3.接口只用指数的
import akshare as ak
import requests
import json
import time


index_poll = ['sz399673','sz399971','csi930606','sz399987','csi930653','csi930641']
start_date = '20240430'
end_date = '20240831'
period = 20
k = 2

def analysis():
    buy_signal_index_code=[]
    sell_signal_index_code=[]

    for index_code in index_poll:
        data = ak.stock_zh_index_daily_em(symbol=index_code, start_date=start_date, end_date=end_date)

        data['SD'] = data['close'].rolling(window=period).std(ddof=1)
        data['MB'] = data['close'].rolling(window=period).mean()
        data['UB'] = data['MB'] + k * data['SD']
        data['LB'] = data['MB'] - k * data['SD']
        data['low_boll_percentage'] = data['low'].sub(data['LB']).div(data['UB'].sub(data['LB']))
        data['high_boll_percentage'] = data['high'].sub(data['LB']).div(data['UB'].sub(data['LB']))

        if data['low_boll_percentage'].iloc[-1]>=0 and data['low_boll_percentage'].iloc[-2]<0:
            buy_signal_index_code.append(index_code)
        elif data['high_boll_percentage'].iloc[-1]>=0:
            sell_signal_index_code.append(index_code)

    return buy_signal_index_code,sell_signal_index_code



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

send_dingtalk_message('actions监控程序长时间测试开始')



def main():
    buy_signal_index_code,sell_signal_index_code=analysis()
    if len(buy_signal_index_code)>0:
        send_dingtalk_message(f"出现买入信号:\n{buy_signal_index_code}")
    if len(sell_signal_index_code)>0:
        send_dingtalk_message(f"出现卖出信号:\n{sell_signal_index_code}")



while True:
    main()
    print('分析一次')
    sleep(10*60)
