import akshare as ak
import pandas as pd
import requests
import json
from datetime import datetime
# 钉钉机器人加签所需
import time
import hmac
import hashlib
import base64
import urllib.parse

# ===== 用户配置区 =====
DING_SECRET = "SECdf943efa6d9781c1e1909a00f6f28e382b11d3d444c6ad6c4cce2235e0a4d1d3"                                                 # 钉钉机器人加签密钥
DING_WEBHOOK = "https://oapi.dingtalk.com/robot/send?access_token=19240afb66cf08cdac8d46cd875bdf3cf37b8adc9ad487caa12af54b655a949c"       # 钉钉机器人webhooks链接
STOCKS = [
    #A股股票-新浪 : 需市场标识,股票代码可以在 ak.stock_zh_a_spot() 中获取
    {"code": "sh601988", "market": "A股股票-新浪"},   #中国银行

    #ETF-东财 ： 不需市场标识，ETF 代码可以在 ak.fund_etf_spot_em() 中获取或查看东财主页
    {"code": "512800", "market": "ETF-东财"},  #银行ETF

    # A股指数-东财 ： 需市场标识， 支持：sz深交所, sh上交所, csi中证指数
    {"code": "sh000922", "market": "A股指数-东财"}   #中证红利
]
BOLL_WINDOW = 20


# =====================

def get_stock_data(code, market):
    #通过不同数据源的列名
    # 各数据源列名配置
    COLUMN_CONFIG = {
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
        }
    }

    try:
        # 获取原始数据
        if market == "A股股票-新浪":
            raw_df = ak.stock_zh_a_daily(symbol=code , adjust="qfq")
        elif market == "ETF-东财":
            raw_df = ak.fund_etf_hist_em(symbol=code,adjust="qfq")
        elif market == "A股指数-东财":
            raw_df = ak.stock_zh_index_daily_em(symbol=code)
        else:
            return None

        # 提取并重命名字段
        config = COLUMN_CONFIG[market]
        df = raw_df[[config['date'], config['open'], config['high'],
                     config['low'], config['close']]].copy()
        df.columns = ['date', 'open', 'high', 'low', 'close']

        # 处理数据
        df = df.iloc[-(BOLL_WINDOW + 200):]  # 保留足够计算BOLL的数据
        df['date'] = pd.to_datetime(df['date'])  # 统一日期格式
        return df.sort_values('date', ascending=True).reset_index(drop=True)

    except Exception as e:
        print(f"获取{code}数据失败：{str(e)}")
        return None



def check_boll_signal(df):
    """检查布林线信号（使用标准字段）"""
    if df is None or len(df) < 2:
        return None

    # 计算布林带
    df['MD'] = df['close'].rolling(BOLL_WINDOW).mean()
    df['std'] = df['close'].rolling(BOLL_WINDOW).std(ddof=1)
    df['upper'] = df['MD'] + 2 * df['std']
    df['lower'] = df['MD'] - 2 * df['std']
    # 最新两日数据
    today = df.iloc[-1]
    yesterday = df.iloc[-2]

    # 生成信号
    buy = today['low'] >= today['lower'] and yesterday['low'] <= yesterday['lower']
    sell = today['high'] <= today['upper'] and yesterday['high'] >= yesterday['upper']

    return 'BUY' if buy else 'SELL' if sell else None


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


def send_dingtalk_message(content):
    """发送钉钉消息"""
    timestamp, sign = generate_ding_signature(DING_SECRET)
    webhook_url = f"{DING_WEBHOOK}&timestamp={timestamp}&sign={sign}"

    data = {
        "msgtype": "text",
        "text": {"content": f"BOLL均值回归策略-监控预警\n{content}"}
    }

    try:
        response = requests.post(webhook_url, json=data)
        return response.json()
    except Exception as e:
        print(f"钉钉消息发送失败：{str(e)}")


def main():
    signals = []
    for stock in STOCKS:
        df = get_stock_data(stock['code'], stock['market'])
        signal = check_boll_signal(df)
        if signal:
            # 使用标准字段获取价格
            price = df.iloc[-1]['close']
            signals.append(f'''-----------------------
代码 : {stock['code']}
交易信号 : {signal}
最新价 : {price:.2f}
'''
            )

    if signals:
        result = send_dingtalk_message("\n".join(signals))
        if result.get('errcode') != 0:
            print(f"检测到交易信号,钉钉发送失败：{result.get('errmsg')}")
        else:
            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "检测到交易信号,通知发送成功")
    else:
        print("未检测到交易信号")


if __name__ == "__main__":
    main()
