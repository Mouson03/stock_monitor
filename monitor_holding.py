#轻量化
#相较于原版: 1.取消非周末检查,非交易时间检查,sys,datetime,取消pandas(直接只用指数)2.index_poll改成列表 3.接口暂时只用指数的https://github.com/Mouson03/stock_monitor/blob/main/stock_monitor.py
#直接一直一天运行6个小时,每3分钟运行一次.如果当天出现信号从而一直通知的话可以手机关弹窗或进github修改代码
import akshare as ak
import requests
import json
from time import sleep
from datetime import datetime,time



index_poll = ['sz399971','csi930606','sz399987','csi930653','csi930641']
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
        elif data['high_boll_percentage'].iloc[-1]>=0.9:
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

send_dingtalk_message('actions每日监控程序开始运行')

def is_rest_time():    #判断是否午盘休息
    now = datetime.now()

    morning_end = time(11-8, 30)
    afternoon_start = time(13-8, 00)

    if (morning_end <= now.time() <= afternoon_start):
        return True
    else:
        return False



def main():
    buy_signal_index_code,sell_signal_index_code=analysis()
    if len(buy_signal_index_code)>0:
        send_dingtalk_message(f"出现买入信号:\n{buy_signal_index_code}")
    if len(sell_signal_index_code)>0:
        send_dingtalk_message(f"出现卖出信号:\n{sell_signal_index_code}")



while True:
    if not is_rest_time():
        main()
        sleep(5*60)
    else:
        sleep(90*60)
        
