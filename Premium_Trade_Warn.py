#2025.10.27重新启用该监控程序，此时测试过，可正常监控
#2.5,4.5,12.5
#买、卖都可以提醒   上、下限都可以设置
import akshare as ak
import requests
import json

# 持有的ETF及其对应的溢价率上下限    (不想监控的下限设为-999,上限设为999)
holdings = {
    
    #同花顺中纳斯达克100相关ETF（共12个，不含161130LOF。按2025.10.27的规模降序）
    '159941': {'lower': 2.0, 'upper': 999},
    '513100': {'lower': 2.0, 'upper': 999},
    '513300': {'lower': 2.0, 'upper': 999},
    '159632': {'lower': 2.0, 'upper': 999},
    '159501': {'lower': 2.0, 'upper': 999},
    '159659': {'lower': 2.0, 'upper': 999},
    '159513': {'lower': 2.0, 'upper': 999},
    '513110': {'lower': 2.0, 'upper': 999},
    '159696': {'lower': 2.0, 'upper': 999},
    '159660': {'lower': 2.0, 'upper': 999},
    '513390': {'lower': 2.0, 'upper': 999},
    '513870': {'lower': 2.0, 'upper': 999},

    #纳指科技ETF
    '159509': {'lower': 3.0, 'upper': 999},

    #美国50ETF（市值降序）
    '513850': {'lower': 1.8, 'upper': 999},
    '159577': {'lower': 1.8, 'upper': 999},

    #道琼斯
    '513400': {'lower': 1.4, 'upper': 999}    
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
