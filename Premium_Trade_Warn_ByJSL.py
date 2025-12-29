#此代码是通过爬取集思录T+0 QDII网页的基金的溢价率数据，进行阈值监控，从而实现美股溢价套利。
#由ChatGPT于2025.11.14完成。已测试，代码正常可用。
import requests
import json

# 持有的ETF及其对应的溢价率上下限
holdings = {
    # 纳指科技ETF
    '159509': {'lower': 3.5, 'upper': 999},

    # 同花顺中纳斯达克100相关ETF（共12个，不含161130LOF。按2025.10.27的规模降序
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
    #'161130': {'lower': 1.5, 'upper': 999},  #纳斯达克100LOF      #20251202已全仓买入此基金，因此不需要监控这个基金了。

    # 美国50ETF（规模降序）
    '513850': {'lower': 1.5, 'upper': 999},
    '159577': {'lower': 1.5, 'upper': 999},

    # 标普500（规模降序）
    '513500': {'lower': -999, 'upper': 999},
    '513650': {'lower': -999, 'upper': 999},
    '159655': {'lower': -999, 'upper': 999},
    '161125': {'lower': -999, 'upper': 999},
    '159612': {'lower': -999, 'upper': 999},

    # 道琼斯
    '513400': {'lower': -999, 'upper': 999},

    #日经指数（规模降序）
    '513880': {'lower': -999, 'upper': 999},
    '513520': {'lower': -999, 'upper': 999},
    '513000': {'lower': -999, 'upper': 999},
    '159866': {'lower': -999, 'upper': 999}
}


# 钉钉发送函数
def send_dingtalk_message(message):
    webhook_url = "https://oapi.dingtalk.com/robot/send?access_token=f9a9044d1c878dfd92d71a18704f623b4cd88296a1762dce858e372dcef76202"
    headers = {'Content-Type': 'application/json'}
    data = {"msgtype": "text", "text": {"content": message}}
    requests.post(webhook_url, headers=headers, data=json.dumps(data))


# 爬取集思录实时溢价率
def fetch_qdii_premium(fund_codes):
    """
    输入: 基金代码列表
    输出: 返回字典 {基金代码: 溢价率（float）}
    """
    url = "https://www.jisilu.cn/data/qdii/qdii_list/?qtype=E"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.jisilu.cn/data/qdii/#qdiie",
        "X-Requested-With": "XMLHttpRequest"
    }
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    result = {}
    for row in data.get("rows", []):
        cell = row.get("cell", {})
        code = cell.get("fund_id")
        if code in fund_codes:
            # discount_rt字段就是溢价率，去掉百分号转换为float
            val = cell.get("discount_rt", "0").replace("%", "")
            try:
                result[code] = float(val)
            except:
                result[code] = None
    return result


# 核心监控逻辑
def monitor_premium():
    fund_codes = list(holdings.keys())
    premiums = fetch_qdii_premium(fund_codes)

    for code in fund_codes:
        premium = premiums.get(code)
        lower = holdings[code]['lower']
        upper = holdings[code]['upper']

        if premium is None:
            print(f"{code} 溢价率获取失败")
            continue

        # 打印过程信息
        print(f"代码: {code}, 溢价率: {premium}%, 阈值: ({lower}, {upper})")

        # 判断是否超出阈值
        if premium < lower:
            print(f"!!!!!!低于下限！触发买入提醒: {code} 溢价率 {premium}% < {lower}%\n!!!!!!")
            send_dingtalk_message(f"买! 买入提醒:{code} 溢价率 {premium}%，低于设定下限 {lower}%")
        elif premium > upper:
            print(f"!!!!!!高于上限！触发卖出提醒: {code} 溢价率 {premium}% > {upper}%\n!!!!!!")
            send_dingtalk_message(f"卖! 卖出提醒:{code} 溢价率 {premium}%，高于设定上限 {upper}%")
        else:
            print(f"溢价率在阈值范围内\n")


# 运行监控
if __name__ == "__main__":
    monitor_premium()




