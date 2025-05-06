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
    #数据源
    #A股股票-新浪 : 需市场标识,股票代码可以在 ak.stock_zh_a_spot() 中获取
    #ETF-东财 ： 不需市场标识，ETF 代码可以在 ak.fund_etf_spot_em() 中获取或查看东财主页
    #A股指数-东财 ： 需市场标识， 支持：sz深交所, sh上交所, csi中证指数
    #港股指数-东财 : 指数代码可以通过 ak.stock_hk_index_spot_em() 获取

    #标的
    #同花顺-适合boll策略:
    {"code": "518850", "market": "ETF-东财"},  #黄金ETF华夏
    {"code": "sz399986", "market": "A股指数-东财"},  #中证银行
    {"code": "sh000922", "market": "A股指数-东财"},  # 中证红利
    {"code": "csiH30269", "market": "A股指数-东财"},  #红利低波
    {"code": "sh000824", "market": "A股指数-东财"},  #国企红利
    {"code": "sh000825", "market": "A股指数-东财"},  #央企红利
    {"code": "csi930914", "market": "A股指数-东财"},  #港股通高股息
    {"code": "HSTECH", "market": "港股指数-东财"},  #恒生科技指数
    {"code": "513520", "market": "ETF-东财"},  #日经ETF
    {"code": "159561", "market": "ETF-东财"},  #德国ETF
    {"code": "513080", "market": "ETF-东财"},  #法国CAC40ETF
    {"code": "164824", "market": "ETF-东财"},  #印度基金LOF
    {"code": "csiH30533", "market": "A股指数-东财"},  #中国互联网50
    {"code": "csiH30094", "market": "A股指数-东财"},  #消费红利
    {"code": "csi931071", "market": "A股指数-东财"},  #人工智能
    {"code": "csi930641", "market": "A股指数-东财"},  #中证中药
    {"code": "csi931024", "market": "A股指数-东财"},  #港股通非银
    {"code": "sh601728", "market": "A股股票-新浪"},  #中国电信
    {"code": "sh600941", "market": "A股股票-新浪"},  #中国移动
    {"code": "sh600050", "market": "A股股票-新浪"},  #中国联通
    {"code": "csi930716", "market": "A股指数-东财"},  #CS物流
    {"code": "sz399967", "market": "A股指数-东财"},  #中证军工
    {"code": "159697", "market": "ETF-东财"},  #国证油气
    {"code": "159985", "market": "ETF-东财"},  #豆粕ETF
    {"code": "159980", "market": "ETF-东财"},  #有色ETF
    {"code": "csi931790", "market": "A股指数-东财"},  #中韩半导体
    {"code": "513350", "market": "ETF-东财"},  #标普油气ETF
    {"code": "sz399995", "market": "A股指数-东财"},  #基建工程
    {"code": "csi931052", "market": "A股指数-东财"},  #国信价值
    {"code": "csi931008", "market": "A股指数-东财"},  #汽车指数
    {"code": "sh000819", "market": "A股指数-东财"},  #有色金属
    {"code": "csiH30199", "market": "A股指数-东财"},  #电力指数


    #同花顺-全部行业指数（除去和 适合boll策略 重复的）
    {"code": "csi930997", "market": "A股指数-东财"},  #新能源车
    {"code": "csi930633", "market": "A股指数-东财"},  #中证旅游
    {"code": "sh000812", "market": "A股指数-东财"},  # 细分机械
    {"code": "sh000813", "market": "A股指数-东财"},  #细分化工
    {"code": "csiH30202", "market": "A股指数-东财"},  #软件指数
    {"code": "sz399998", "market": "A股指数-东财"},  #中证煤炭
    {"code": "sz399989", "market": "A股指数-东财"},  #中证医疗
    {"code": "csi931152", "market": "A股指数-东财"},  #CS创新药
    {"code": "sz399441", "market": "A股指数-东财"},  #生物医药
    {"code": "csiH30217", "market": "A股指数-东财"},  #医疗器械
    {"code": "csi931494", "market": "A股指数-东财"},  #消费电子
    {"code": "sz399975", "market": "A股指数-东财"},  #证券公司
    {"code": "csiH30035", "market": "A股指数-东财"},  #300非银
    {"code": "csi930606", "market": "A股指数-东财"},  #中证钢铁
    {"code": "csiH30184", "market": "A股指数-东财"},  #半导体
    {"code": "csi931160", "market": "A股指数-东财"},  #通信设备
    {"code": "csi931235", "market": "A股指数-东财"},  #中证电信
    {"code": "csi931009", "market": "A股指数-东财"},  #建筑材料
    {"code": "csi930697", "market": "A股指数-东财"},  #家用电器
    {"code": "sh000949", "market": "A股指数-东财"},  #中证农业
    {"code": "csi931151", "market": "A股指数-东财"},  #光伏产业
    {"code": "sh000815", "market": "A股指数-东财"},  #细分食品
    {"code": "sz399971", "market": "A股指数-东财"},  # 中证传媒
    {"code": "csi930901", "market": "A股指数-东财"},  #动漫游戏
    {"code": "csi930781", "market": "A股指数-东财"},  #中证影视
    {"code": "csiH30590", "market": "A股指数-东财"},  # 机器人
    {"code": "csi931456", "market": "A股指数-东财"},  #中国教育
    {"code": "sh000932", "market": "A股指数-东财"},  #中证消费
    {"code": "csi930604", "market": "A股指数-东财"},  #中国互联网30
    {"code": "csi931775", "market": "A股指数-东财"},  #房地产

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
        # 获取原始数据
        if market == "A股股票-新浪":
            raw_df = ak.stock_zh_a_daily(symbol=code , adjust="qfq")
        elif market == "ETF-东财":
            raw_df = ak.fund_etf_hist_em(symbol=code,adjust="qfq")
        elif market == "A股指数-东财":
            raw_df = ak.stock_zh_index_daily_em(symbol=code)
        elif market == "港股指数-东财":
            raw_df = ak.stock_hk_index_daily_em(symbol=code)
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
        print(f"代码 : {stock['code']}")      #用于查看程序运行进度
        df = get_stock_data(stock['code'], stock['market'])
        if df is not None:                                           #用于检查代码和数据是否正确对应
            print(f"最新收盘价 : {df['close'].iloc[-1]}\n")
        else:
            print(f"最新收盘价 : None\n")
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
