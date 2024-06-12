#监控未持有的,只分析买入信号
import akshare as ak
import requests
import json
from time import sleep
from datetime import datetime,time



index_poll = ['sz399998','sz399986','513080','513030','159985','159981','159518','513880','159502','513310','159941','513500','513850']
start_date = '20240430'
end_date = '20240831'
period = 20
k = 2

def analysis():
    buy_signal_index_code=[]
    for index_code in index_poll:
        if any(char.isalpha() for char in str(index_code)):
            data = ak.stock_zh_index_daily_em(symbol=index_code, start_date=start_date, end_date=end_date)     #指数接口
        else:
            data = ak.fund_etf_hist_em(symbol=index_code, period="daily", start_date=start_date, end_date=end_date,adjust="qfq")      #基金接口
            new_names = {'收盘': 'close', '最高': 'high', '最低': 'low','成交量':'volume'}
            data.rename(columns=new_names, inplace=True)
    
        data['SD'] = data['close'].rolling(window=period).std(ddof=1)
        data['MB'] = data['close'].rolling(window=period).mean()
        data['UB'] = data['MB'] + k * data['SD']
        data['LB'] = data['MB'] - k * data['SD']
        data['low_boll_percentage'] = data['low'].sub(data['LB']).div(data['UB'].sub(data['LB']))
        #data['high_boll_percentage'] = data['high'].sub(data['LB']).div(data['UB'].sub(data['LB']))
        #if data['low_boll_percentage'].iloc[-1]>=0:
        if data['low_boll_percentage'].iloc[-1]>=0 and data['low_boll_percentage'].iloc[-2]<0:
            buy_signal_index_code.append(index_code)

    return buy_signal_index_code



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

send_dingtalk_message('actions每日监控程序开始运行 | 未持有')

def is_rest_time():    #判断是否午盘休息
    now = datetime.now()

    morning_end = time(11-8, 30)
    afternoon_start = time(13-8, 00)

    if (morning_end <= now.time() <= afternoon_start):
        return True
    else:
        return False



def main():
    buy_signal_index_code=analysis()
    if len(buy_signal_index_code)>0:
        send_dingtalk_message(f"未持有 | 买:\n{buy_signal_index_code}")



while True:
    if not is_rest_time():
        main()
        sleep(5*60)
    else:
        sleep(90*60)
        
