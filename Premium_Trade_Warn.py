#买、卖都可以提醒   上、下限都可以设置
import akshare as ak
import requests
import json

# 持有的ETF及其对应的溢价率上下限    (不想监控的下限设为-999,上限设为999)
holdings = {
    #'159941': {'lower': -2.0, 'upper': 2.0},
    '513100': {'lower': -999, 'upper': 3.5},
    '513300': {'lower': 4.0, 'upper': 999},
    '159509': {'lower': 12.0, 'upper': 999},
}

# 钉钉发送函数
def send_dingtalk_message(message):
    webhook_url = "https://oapi.dingtalk.com/robot/send?access_token=f9a9044d1c878dfd92d71a18704f623b4cd88296a1762dce858e372dcef76202"
    headers = {'Content-Type': 'application/json'}
    data = {
        "msgtype": "text",
        "text": {
            "content": message
        }
    }
    requests.post(webhook_url, headers=headers, data=json.dumps(data))

# 获取所有ETF的实时数据
df = ak.fund_etf_spot_em()

# 检查每个ETF的溢价率
for etf, limits in holdings.items():
    etf_data = df[df["代码"] == etf]
    if not etf_data.empty:
        latest_price = float(etf_data["最新价"].values[0])
        iopv = float(etf_data["IOPV实时估值"].values[0])
        premium_rate = (latest_price - iopv) / iopv * 100

        # 判断溢价率是否超出上下限
        if premium_rate < limits['lower']:
            send_dingtalk_message(f"买!买!买!  买入提醒:{etf} 溢价率为 {round(premium_rate, 2)}%，低于设定下限 {limits['lower']}%")
        elif premium_rate > limits['upper']:
            send_dingtalk_message(f"卖!卖!卖!  卖出提醒:{etf} 溢价率为 {round(premium_rate, 2)}%，高于设定上限 {limits['upper']}%")