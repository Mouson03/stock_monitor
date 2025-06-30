# 此代码在actions运行。
# 仅用于在监控：1.纳斯达克100的”下穿或上穿N日均线“ 2.纳指ETF的”最低上穿下轨“
#测试:1.已经测试过数据行数不足时能发送错误信息至钉钉 2.已经用ETF测试了”下穿或上穿N日均线“和”最低上穿下轨“信号,都是正常可用的
'''更新内容:
相较于”监控 for_actions_v5.py“，此代码更新内容：
1.代码每天只在A股开盘时运行3次(1次就够了,3次是为了避免出现运行失败)
2.如果说出现错误(某标的check_signal的data行数不足),就发送消息到钉钉,避免因为接口出问题,后续错过监控信号
3.添加了超时时长,避免actions网速慢而获取数据失败
'''
import akshare as ak
import pandas as pd
import requests
from datetime import datetime, timedelta
# 钉钉机器人加签所需
import time
import hmac
import hashlib
import base64
import urllib.parse
import socket   #用于设置请求的超时时长
socket.setdefaulttimeout(120)  # 全局 socket 超时设为 30s


# ===== 用户配置区 =====
DING_SECRET = "SECdf943efa6d9781c1e1909a00f6f28e382b11d3d444c6ad6c4cce2235e0a4d1d3"  # 钉钉机器人加签密钥
DING_WEBHOOK = "https://oapi.dingtalk.com/robot/send?access_token=19240afb66cf08cdac8d46cd875bdf3cf37b8adc9ad487caa12af54b655a949c"  # 钉钉机器人webhooks链接
BOLL_WINDOW = 20
RETAIN_DATA = 260
# =====================

#获取标的列表
def load_stocks_list_from_csv():
    df = pd.read_csv("OnlyNDX_stock_monitor_list.csv", encoding="gbk" , dtype=str)  # 全部按字符串读取，防止股票代码前缀或 0 被丢失.用Excel保存的csv的编码不是utf-8
    needed_cols = ['symbol','name','data_interface','monitor_signal','stock_category','importance_degree']    # 选择需要的列
    stocks_list=df[needed_cols].to_dict(orient="records")      #将df转为字典数列

#    for stock in stocks_list:   #用于检查标的列表是否正确
#        print(stock)

    return stocks_list

#获取标的行情数据
def get_stock_data(symbol, data_interface):
    COLUMN_CONFIG = {                  # 各数据源列名配置
        "ETF-东财": {
            'date': '日期',
            'open': '开盘',
            'high': '最高',
            'low': '最低',
            'close': '收盘'
        },
        "美股指数-新浪": {
            'date': 'date',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close'
        }
    }

    try:
        # 获取原始数据          # 通过不同数据源的列名
        if data_interface == "美股指数-新浪":
            raw_df = ak.index_us_stock_sina(symbol=symbol)
        elif data_interface == "ETF-东财":
            raw_df = ak.fund_etf_hist_em(symbol=symbol, start_date="20240401", adjust="qfq")
        else:
            print(f"{symbol}未指定数据接口")
            return None

        # 提取并重命名字段
        config = COLUMN_CONFIG[data_interface]
        data = raw_df[[config['date'], config['open'], config['high'],
                       config['low'], config['close']]].copy()
        data.columns = ['date', 'open', 'high', 'low', 'close']

        # 处理数据
        data = data.iloc[-RETAIN_DATA:]  # 保留足够的数据    如果是有别的策略,可以多保留一些
        data['date'] = pd.to_datetime(data['date'])  # 统一日期格式
        return data.sort_values('date', ascending=True).reset_index(drop=True)

    except Exception as e:
        print(f"\n获取{symbol}数据失败：{str(e)}\n ")
        return None


#==========各种信号判断部分==========================================================================
#下穿或上穿250日均线
def foll_or_rise_250Day_MA(data):

    #指标计算
    data['ma'] = data['close'].rolling(250).mean()    #250日均线
    yesterday = data.iloc[-2]
    today = data.iloc[-1]

    #信号判断
    condition1 = yesterday['high'] >= yesterday['ma'] and today['high'] <= today['ma']  #下穿N日均线
    condition2 = yesterday['low'] <= yesterday['ma'] and today['low'] >= today['ma']  #上穿N日均线
    signal_conditons =condition1 or condition2

    if signal_conditons:
        return True
    else:
        return False

# 最低上穿下轨
def low_rise_lower(data):

    #指标计算
    data['mid'] = data['close'].rolling(BOLL_WINDOW).mean()
    data['std'] = data['close'].rolling(BOLL_WINDOW).std(ddof=1)
    data['lower'] = data['mid'] - 2 * data['std']
    yesterday = data.iloc[-2]
    today = data.iloc[-1]

    #信号判断
    signal_cond = (yesterday['low'] <= yesterday['lower']) and (today['low'] >= today['lower'])

    if signal_cond:
        return True
    else:
        return False
#==============================================================================================

#遍历标的,检查信号
def check_signal(stocks_list):
    all_signals = []
    for stock in stocks_list:
        # 拉取当前标的的数据
        name = stock["name"]
        symbol = stock["symbol"]
        data_interface = stock["data_interface"]
        monitor_signal = stock["monitor_signal"]
        stock_category = stock['stock_category']
        importance_degree = stock["importance_degree"]

        # 拉取标的行情数据
        data = get_stock_data(symbol, data_interface)

        if data is None or len(data) < RETAIN_DATA:  # 确保数据足够
            send_dingtalk_message("有标的的数据行数不足,检查策略失败")
            print(f"\n检查 {symbol} {name} 的信号失败,数据行数不足,错误信息已发送至钉钉")    #如果有标的的数据行数不足,就发送消息都钉钉
            continue

        print(f"\n名称 : {stock['name']}")   # 用于查看程序运行进度
        print(f"代码 : {stock['symbol']}")  # 用于查看程序运行进度
        if data is not None:  # 用于检查代码和数据是否正确对应
            print(f"最新日期 : {data['date'].iloc[-1].strftime('%Y-%m-%d')}")  # 只打印日期(本来也只有日期)
            print(f"最新价 : {data['close'].iloc[-1]}")
            print(f"行情数据 : {data}")
            print(f"\n----------------------------------------------------------------------------------")

        # 根据 monitor_signal 分发到各个判断函数
        signal_appear = False
        if monitor_signal == "下穿或上穿250日均线":
            signal_appear = foll_or_rise_250Day_MA(data)
        elif monitor_signal == "最低上穿下轨":
                signal_appear = low_rise_lower(data)
        else:
            print(f"{symbol} {name} 未指定监控信号")

        if signal_appear:
            all_signals.append({
                "name": name,
                "symbol": symbol,
                "stock_category": stock_category,
                "signal_monitor":  monitor_signal,
                "importance_degree":importance_degree
            })

    return all_signals

# 格式化消息
def format_signals_message(signals):
    if not signals:
        return None

    #格式化排序后的信息
    format_message = []

    current_importance = None      #在一组重要程度前添加小标题，如【高】
    for s in signals:
        imp = s.get("importance_degree", "")
        if imp != current_importance:
            format_message.append(f"【{imp}】")
            current_importance = imp

        format_message.append(f'''
名称: {s["name"]}
代码: {s["symbol"]}
标的类型: {s["stock_category"]}
监控信号: {s["signal_monitor"]}
重要程度: {imp}
--------------------'''
        )

    return "\n".join(format_message)    #将列表的字符串合并为一个字符串



#钉钉加签
def generate_ding_signature(secret):
    """生成钉钉安全加签参数"""
    timestamp = str(round(time.time() * 1000))
    secret_enc = secret.encode('utf-8')
    string_to_sign = f"{timestamp}\n{secret}"
    string_to_sign_enc = string_to_sign.encode('utf-8')

    hmac_code = hmac.new(
        secret_enc,
        string_to_sign_enc,
        digestmod=hashlib.sha256
    ).digest()

    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    return timestamp, sign


#钉钉发送消息
def send_dingtalk_message(content):
    """发送钉钉消息"""
    timestamp, sign = generate_ding_signature(DING_SECRET)
    webhook_url = f"{DING_WEBHOOK}&timestamp={timestamp}&sign={sign}"

    data = {
        "msgtype": "text",
        "text": {"content": content}
    }

    response = requests.post(webhook_url, json=data)
    return response.json()

#主函数    职责:读CSV → 拉现价 → 调 check_signal → 条件结束或格式化+发送。
def main():
    print("开始运行程序    时间:" + (datetime.now() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M"))

    # 1. 加载标的列表
    stocks_list = load_stocks_list_from_csv()

    # 3. 遍历所有标的，收集触发信号
    all_signals = check_signal(stocks_list)

    # 4. 如果没有信号，直接结束main函数,不执行后续函数
    if not all_signals:
        print("未检测到交易信号")
        return

    # 5. 格式化信号消息
    message_text = format_signals_message(all_signals)
    if not message_text:
        print("格式化消息失败或无可发送内容")
        return

    # 6. 发送钉钉消息
    result = send_dingtalk_message(message_text)
    if result and result.get("errcode") == 0:
        print("检测到交易信号，钉钉消息发送成功")
    else:
        print("检测到交易信号，钉钉消息发送失败：", result)


if __name__ == "__main__":
    main()
