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


# ===== 用户配置区 =====
DING_SECRET = "SECdf943efa6d9781c1e1909a00f6f28e382b11d3d444c6ad6c4cce2235e0a4d1d3"  # 钉钉机器人加签密钥
DING_WEBHOOK = "https://oapi.dingtalk.com/robot/send?access_token=19240afb66cf08cdac8d46cd875bdf3cf37b8adc9ad487caa12af54b655a949c"  # 钉钉机器人webhooks链接
BOLL_WINDOW = 20
# =====================

#获取标的列表
def load_stocks_list_from_csv():
    df = pd.read_csv("BollRegressionStrategy_stock_monitor_list_merge.csv", encoding="gbk" , dtype=str)  # 全部按字符串读取，防止股票代码前缀或 0 被丢失.用Excel保存的csv的编码不是utf-8
    #df_unique = df.drop_duplicates(subset=["symbol","monitor_signal"], keep="first").copy()      #去重,symbol和monitor_signal都相同的标的,只保留第一个.加.copy(),此时df_unique是独立的dataframe而非视图

    # 给列填充默认值
    df["monitor_signal"] = df["monitor_signal"].fillna("最低上穿下轨")    # monitor_signal列 默认 "最低上穿下轨"
    df["importance_degree"] = df["importance_degree"].fillna("默认")     # importance_degree列 默认 "默认"
    df["stock_category"] = df["stock_category"].fillna("默认")
    df["cost"] = df["cost"].fillna("1")   #成本默认1,防止忘填而报错

    needed_cols = ['symbol','name','data_interface','monitor_signal','stock_category','importance_degree','total_mv','cost']    # 选择需要的列
    stocks_list=df[needed_cols].to_dict(orient="records")      #将df转为字典数列

#    for stock in stocks_list:   #用于检查标的列表是否正确
#        print(stock)

    return stocks_list

#获取标的行情数据
def get_stock_data(symbol, data_interface):
    COLUMN_CONFIG = {                  # 各数据源列名配置
        "A股股票-新浪": {
            'date': 'date',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close'
        },
        "ETF-东财": {
            'date': '日期',
            'open': '开盘',
            'high': '最高',
            'low': '最低',
            'close': '收盘'
        },
        "A股指数-东财": {
            'date': 'date',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close'
        },
        "港股指数-东财": {
            'date': 'date',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'latest'
        }
    }

    try:
        # 获取原始数据          # 通过不同数据源的列名
        if data_interface == "A股股票-新浪":
            raw_df = ak.stock_zh_a_daily(symbol=symbol, start_date="20250401", adjust="qfq")

            # 确保spot_df中有当前标的的数据并提取出来
            if spot_df is not None:
                try:
                    spot_data = spot_df[spot_df['代码'] == symbol].iloc[0]  # 将spot_df中的当前标的的数据赋值给spot_data

                except IndexError:
                    print(f"spot_df中无 A股股票{symbol} 的数据")

            # 合并数据
            today_date = datetime.now().strftime("%Y-%m-%d")

            #测试

            if today_date not in raw_df['date'].astype(str).values:  # 当A股股票-新浪的数据中没有当日数据,才合并数据
                # 构建当日K线
                today_kline = {
                    'date': today_date,
                    'open': spot_data['今开'],
                    'high': spot_data['最高'],
                    'low': spot_data['最低'],
                    'close': spot_data['最新价']
                }

                #合并数据
                raw_df = pd.concat([raw_df, pd.DataFrame([today_kline])], ignore_index=True)

        elif data_interface == "ETF-东财":
            raw_df = ak.fund_etf_hist_em(symbol=symbol, start_date="20250401", adjust="qfq")
        elif data_interface == "A股指数-东财":
            raw_df = ak.stock_zh_index_daily_em(symbol=symbol, start_date="20250401")
        elif data_interface == "港股指数-东财":
            raw_df = ak.stock_hk_index_daily_em(symbol=symbol)
        else:
            return None

        # 提取并重命名字段
        config = COLUMN_CONFIG[data_interface]
        data = raw_df[[config['date'], config['open'], config['high'],
                       config['low'], config['close']]].copy()
        data.columns = ['date', 'open', 'high', 'low', 'close']

        # 处理数据
        data = data.iloc[-(BOLL_WINDOW + 2):]  # 保留足够计算BOLL的数据    如果是有别的策略,可以多保留一些
        data['date'] = pd.to_datetime(data['date'])  # 统一日期格式
        return data.sort_values('date', ascending=True).reset_index(drop=True)

    except Exception as e:
        print(f"\n获取{symbol}数据失败：{str(e)}\n ")
        return None


#==========各种信号判断部分==========================================================================
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

# 跌5%且最低上穿下轨或跌10%或收盘上穿上轨
def foll_5percent_and_low_rise_lower_or_foll_10percent_or_close_rise_upper(data,cost):
    #指标计算
    data['mid'] = data['close'].rolling(BOLL_WINDOW).mean()
    data['std'] = data['close'].rolling(BOLL_WINDOW).std(ddof=1)
    data['lower'] = data['mid'] - 2 * data['std']
    data['upper'] = data['mid'] + 2 * data['std']
    yesterday = data.iloc[-2]
    today = data.iloc[-1]

    #信号判断
    condition1 = ((today['close']-cost)/cost<-0.05) and ((yesterday['low'] <= yesterday['lower']) and (today['low'] >= today['lower']))    # 条件1: 跌5%且最低上穿下轨
    condition2 = (today['close']-cost)/cost<-0.10                                                                                          # 条件2: 跌10%
    condition3 = (today['close'] >= today['upper'])    # 条件3: 收盘上穿上轨
    signal_conditons =condition1 or condition2 or condition3

    if signal_conditons:
        return True
    else:
        return False

# 最高下穿上轨
def high_foll_upper(data):
    #指标计算
    data['mid'] = data['close'].rolling(BOLL_WINDOW).mean()
    data['std'] = data['close'].rolling(BOLL_WINDOW).std(ddof=1)
    data['upper'] = data['mid'] + 2 * data['std']
    yesterday = data.iloc[-2]
    today = data.iloc[-1]

    #信号判断
    signal_cond = (yesterday['high'] >= yesterday['upper']) and (today['high'] <= today['upper'])

    if signal_cond:
        return True
    else:
        return False

# 收盘低于下轨
def close_beoow_lower(data):
    #指标计算
    data['mid'] = data['close'].rolling(BOLL_WINDOW).mean()
    data['std'] = data['close'].rolling(BOLL_WINDOW).std(ddof=1)
    data['lower'] = data['mid'] - 2 * data['std']
    today = data.iloc[-1]

    #信号判断
    signal_cond = today['close'] <= today['lower']

    if signal_cond:
        return True
    else:
        return False

# 收盘低于下轨或最低上穿下轨
def close_beoow_lower_or_low_rise_lower(data):
    #指标计算
    data['mid'] = data['close'].rolling(BOLL_WINDOW).mean()
    data['std'] = data['close'].rolling(BOLL_WINDOW).std(ddof=1)
    data['lower'] = data['mid'] - 2 * data['std']
    data['upper'] = data['mid'] + 2 * data['std']
    yesterday = data.iloc[-2]
    today = data.iloc[-1]

    #信号判断
    signal_cond = today['close'] <= today['lower'] or (yesterday['low'] <= yesterday['lower']) and (today['low'] >= today['lower'])
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
        total_mv_float = float(stock["total_mv"])      # CSV里的市值字符串转为浮点数.如果是nan,转后也是nan

        # 拉取标的行情数据
        data = get_stock_data(symbol, data_interface)

        if data is None or len(data) < (BOLL_WINDOW + 2):  # 确保数据足够
            print(f"\n{symbol} {name}  的数据行数不足")
            continue

        print(f"\n名称 : {stock['name']}")   # 用于查看程序运行进度
        print(f"代码 : {stock['symbol']}")  # 用于查看程序运行进度
        if data is not None:  # 用于检查代码和数据是否正确对应
            print(f"最新日期 : {data['date'].iloc[-1].strftime('%Y-%m-%d')}")  # 只打印日期(本来也只有日期)
            #print(f"最新价 : {data['close'].iloc[-1]}")

        if data is None or len(data) < (BOLL_WINDOW + 2):  # 确保data有数据
            continue

        # 根据 monitor_signal 分发到各个判断函数
        signal_appear = False
        if monitor_signal == "最低上穿下轨":     #默认监控信号
            signal_appear = low_rise_lower(data)
        elif monitor_signal == "跌5%且最低上穿下轨或跌10%或收盘上穿上轨":
            cost = float(stock["cost"])    #只有持仓股才传入成本
            signal_appear = foll_5percent_and_low_rise_lower_or_foll_10percent_or_close_rise_upper(data,cost)    # 跌5%且最低上穿下轨或跌10%或收盘上穿上轨
        elif monitor_signal == "最高下穿上轨":
            signal_appear = high_foll_upper(data)
        elif monitor_signal == "收盘低于下轨":
            signal_appear = close_beoow_lower(data)
        elif monitor_signal == "收盘低于下轨或最低上穿下轨":
            signal_appear = close_beoow_lower_or_low_rise_lower(data)
        else:
            print(f"{symbol} {name} 未指定监控信号")

        if signal_appear:
            # 添加一个“布林带分位”的钉钉字段
            data['mid'] = data['close'].rolling(BOLL_WINDOW).mean()
            data['std'] = data['close'].rolling(BOLL_WINDOW).std(ddof=1)
            data['lower'] = data['mid'] - 2 * data['std']
            data['upper'] = data['mid'] + 2 * data['std']
            today = data.iloc[-1]
            boll_percentile = ((today['close']-today['lower']) / (today['upper']-today['lower']))*100   # 计算布林带分位
            boll_percentile = round(boll_percentile, 2)  # 保留两位小数

            all_signals.append({
                "name": name,
                "symbol": symbol,
                "stock_category": stock_category,
                "total_mv":   total_mv_float,
                "boll_percentile": boll_percentile,    # 布林带分位钉钉字段
                "signal_monitor":  monitor_signal,
                "importance_degree":importance_degree
            })

    return all_signals

# 格式化消息
def format_signals_message(signals):
    if not signals:
        return None

    #将信号列表,按“重要程度”排序，相同就按“总市值”排序
    importance_order = {"持仓": 7, "选出待买":6, "非常高": 5, "高": 4, "中": 3, "低": 2, "非常低": 1, "默认": 0}
    signals_sorted = sorted(signals, key=lambda x: (
        -importance_order.get(x.get("importance_degree", ""), 0),
#        -x.get("total_mv", 0)   # 市值作为第二排序依据，缺失值排最后
        x.get("boll_percentile", 999)  # 布林带分位作为第二排序依据，缺失值排最后
    ))

    #格式化排序后的信息
    format_message = []

    current_importance = None      #在一组重要程度前添加小标题，如【高】
    for s in signals_sorted:
        imp = s.get("importance_degree", "")
        if imp != current_importance:
            format_message.append(f"【{imp}】")
            current_importance = imp

        format_message.append(f'''
名称: {s["name"]}
代码: {s["symbol"]}
标的类型: {s["stock_category"]}
市值: {s["total_mv"]} 亿
布林带分位: {s["boll_percentile"]} %
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

    # 2. 获取全局变量 spot_df，即实时行情,用于构造当日K线
    global spot_df
    spot_df = ak.stock_zh_a_spot()

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
