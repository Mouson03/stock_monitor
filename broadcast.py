import akshare as ak
import pandas as pd
import requests
import json



def MACD_calculate(data):

    # 定义计算EMA的函数
    def EMA(values, window):
        return pd.Series(values).ewm(span=window, adjust=False).mean()

    # 计算短期和长期EMA
    data['EMA_short'] = EMA(data['close'], 12)
    data['EMA_long'] = EMA(data['close'], 26)

    # 计算DIF
    data['DIF'] = data['EMA_short'] - data['EMA_long']

    # 计算信号线DEA
    data['DEA'] = EMA(data['DIF'], 9)

    # 计算MACD直方图
    data['MACD'] =2 * (data['DIF'] - data['DEA'])

    return data['MACD'].iloc[-1].round(2)



data = ak.index_us_stock_sina(symbol=".NDX")
NDX_price_change_percentage=((data['close'].iloc[-1]-data['close'].iloc[-2])/data['close'].iloc[-2]*100).round(2)
NDX_MACD=MACD_calculate(data)

data = ak.index_us_stock_sina(symbol=".INX")
INX_price_change_percentage=((data['close'].iloc[-1]-data['close'].iloc[-2])/data['close'].iloc[-2]*100).round(2)
INX_MACD=MACD_calculate(data)

data = ak.index_us_stock_sina(symbol=".DJI")
DJI_price_change_percentage=((data['close'].iloc[-1]-data['close'].iloc[-2])/data['close'].iloc[-2]*100).round(2)
DJI_MACD=MACD_calculate(data)



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


message=f'''纳斯达克100     {NDX_price_change_percentage}%
标普500           {INX_price_change_percentage}%
道琼斯              {DJI_price_change_percentage}%

MACD:
纳斯达克100     {NDX_MACD}
标普500           {INX_MACD}
道琼斯              {DJI_MACD}
'''
send_dingtalk_message(message)
