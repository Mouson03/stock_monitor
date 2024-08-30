#1.溢价率和涨跌幅单位是%  2.记录每天中午休息时的溢价率(即actions每周1-5早11点15分运行)
import akshare as ak
import pandas as pd
import datetime
import requests
import json

# ETF列表，替换为你的基金代码列表
etf_list = ['159941','513100','159632','159513','513300','159501','513390','159696','513110','159659','159660','513870','513850']

# 持有的ETF及其对应的溢价率阈值
holdings = {
    #'000000':0.0    #添加这个避免无持有ETF时字典为空
    '159941': 3.0,
    '513100': 3.0,
    '513300': 4.0
    # 添加更多的持有ETF和阈值
}

# 获取当前日期
today = datetime.datetime.today().strftime('%Y-%m-%d')

#获取昨天纳指100涨跌幅
data_NDX= ak.index_us_stock_sina(symbol=".NDX")
change_percentage=((data_NDX['close'].iloc[-1] - data_NDX['close'].iloc[-2]) / data_NDX['close'].iloc[-2] * 100).round(2)

# 超出阈值的ETF列表
alert_messages = []

# 获取所有ETF的实时数据
df = ak.fund_etf_spot_em()

# 创建一个空的字典用于存储结果
result_dict = {"日期": today,"昨晚纳指100涨跌幅":change_percentage}

for etf in etf_list:
    # 获取当前ETF的行
    etf_data = df[df["代码"] == etf]

    if not etf_data.empty:
        # 获取最新价和IOPV实时估值
        latest_price = float(etf_data["最新价"].values[0])
        iopv = float(etf_data["IOPV实时估值"].values[0])

        # 计算溢价率
        premium_rate = (latest_price - iopv) / iopv

        # 将溢价率添加到字典中
        result_dict[f"{etf}"] = round(premium_rate*100,2)

        # 检查持有的ETF的溢价率是否超过阈值
        if etf in holdings and result_dict[f"{etf}"] < holdings[etf]:
            alert_message = f"提醒: ETF {etf} 的溢价率为 {result_dict[f'{etf}']}%，超过了设定的阈值 {holdings[etf]}%"
            alert_messages.append(alert_message)

# 转换字典为DataFrame
result_df = pd.DataFrame([result_dict])

# 文件名
file_name = "etf_premium_rates.csv"

# 读取现有的CSV文件
existing_df = pd.read_csv(file_name)

# 追加新数据
result_df = pd.concat([existing_df, result_df], ignore_index=True)

# 保存结果到csv文件
result_df.to_csv(file_name, index=False)

# 发送超出阈值的ETF信息至钉钉
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
for message in alert_messages:
    send_dingtalk_message(message)

# 记录运行日志
log_message = f"{today}  \"ETF溢价率记录及预警\"  程序运行完毕"
log_file = "actions_running_log.txt"
with open(log_file, 'a') as f:
    f.write(f"{log_message}\n")

print(f"{today}的ETF溢价率已记录，持有ETF溢价率阈值已检查,运行日志已记录。")
