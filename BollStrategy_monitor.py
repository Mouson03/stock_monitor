# v4说明:
# 更新的原因:解决v2的缺点,即A股股票接口在盘中的数据是昨日的.而v3用bs接口,发现依然是昨日的.因此v4要用ak新浪实时接口.
# 解决方案:# (×接口用不了)1.原数据＋ak雪球实时   # 2.将ak新浪实时的5000个股存起来,然后分别添加到原数据   3.(×已在盘中验证,bs的数据也是昨日的)用baostock的A股K线数据
# 已实现的功能:A股股票-新浪＋实时数据
# 缺点:
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
STOCKS = [
    # 数据源
    # A股股票-新浪 : 需市场标识,股票代码可以在 ak.stock_zh_a_spot() 中获取
    # ETF-东财 ： 不需市场标识，ETF 代码可以在 ak.fund_etf_spot_em() 中获取或查看东财主页
    # A股指数-东财 ： 需市场标识， 支持：sz深交所, sh上交所, csi中证指数
    # 港股指数-东财 : 指数代码可以通过 ak.stock_hk_index_spot_em() 获取

    # 标的-监控买入信号
    # 同花顺-适合boll策略:
    {"code": "518850", "market": "ETF-东财", "monitor": "buy"},  # 黄金ETF华夏
    {"code": "161226", "market": "ETF-东财", "monitor": "buy"},  # 国投白银LOF
    {"code": "sz399986", "market": "A股指数-东财", "monitor": "buy"},  # 中证银行
    {"code": "sh000922", "market": "A股指数-东财", "monitor": "buy"},  # 中证红利
    {"code": "csiH30269", "market": "A股指数-东财", "monitor": "buy"},  # 红利低波
    {"code": "sh000824", "market": "A股指数-东财", "monitor": "buy"},  # 国企红利
    {"code": "sh000825", "market": "A股指数-东财", "monitor": "buy"},  # 央企红利
    {"code": "csi930914", "market": "A股指数-东财", "monitor": "buy"},  # 港股通高股息
    {"code": "159509", "market": "ETF-东财", "monitor": "buy"},  # 纳指科技ETF 上穿下轨就买几份
    {"code": "513520", "market": "ETF-东财", "monitor": "buy"},  # 日经ETF
    {"code": "159561", "market": "ETF-东财", "monitor": "buy"},  # 德国ETF
    {"code": "513080", "market": "ETF-东财", "monitor": "buy"},  # 法国CAC40ETF
    {"code": "164824", "market": "ETF-东财", "monitor": "buy"},  # 印度基金LOF
    {"code": "csiH30533", "market": "A股指数-东财", "monitor": "buy"},  # 中国互联网50
    {"code": "csiH30094", "market": "A股指数-东财", "monitor": "buy"},  # 消费红利
    {"code": "csi931071", "market": "A股指数-东财", "monitor": "buy"},  # 人工智能
    {"code": "csi930641", "market": "A股指数-东财", "monitor": "buy"},  # 中证中药
    {"code": "csi931024", "market": "A股指数-东财", "monitor": "buy"},  # 港股通非银
    {"code": "csi930716", "market": "A股指数-东财", "monitor": "buy"},  # CS物流
    {"code": "sz399967", "market": "A股指数-东财", "monitor": "buy"},  # 中证军工
    {"code": "159697", "market": "ETF-东财", "monitor": "buy"},  # 国证油气
    {"code": "csi931790", "market": "A股指数-东财", "monitor": "buy"},  # 中韩半导体
    {"code": "513350", "market": "ETF-东财", "monitor": "buy"},  # 标普油气ETF
    {"code": "sz399995", "market": "A股指数-东财", "monitor": "buy"},  # 基建工程
    {"code": "csi931052", "market": "A股指数-东财", "monitor": "buy"},  # 国信价值
    {"code": "csi931008", "market": "A股指数-东财", "monitor": "buy"},  # 汽车指数
    {"code": "sh000819", "market": "A股指数-东财", "monitor": "buy"},  # 有色金属
    {"code": "csiH30199", "market": "A股指数-东财", "monitor": "buy"},  # 电力指数

    # 同花顺-全部行业指数（除去和 适合boll策略 重复的）
    {"code": "csi930997", "market": "A股指数-东财", "monitor": "buy"},  # 新能源车
    {"code": "csi930633", "market": "A股指数-东财", "monitor": "buy"},  # 中证旅游
    {"code": "sh000812", "market": "A股指数-东财", "monitor": "buy"},  # 细分机械
    {"code": "sh000813", "market": "A股指数-东财", "monitor": "buy"},  # 细分化工
    {"code": "csiH30202", "market": "A股指数-东财", "monitor": "buy"},  # 软件指数
    {"code": "sz399998", "market": "A股指数-东财", "monitor": "buy"},  # 中证煤炭
    {"code": "sz399989", "market": "A股指数-东财", "monitor": "buy"},  # 中证医疗
    {"code": "csi931152", "market": "A股指数-东财", "monitor": "buy"},  # CS创新药
    {"code": "sz399441", "market": "A股指数-东财", "monitor": "buy"},  # 生物医药
    {"code": "csiH30217", "market": "A股指数-东财", "monitor": "buy"},  # 医疗器械
    {"code": "csi931494", "market": "A股指数-东财", "monitor": "buy"},  # 消费电子
    {"code": "sz399975", "market": "A股指数-东财", "monitor": "buy"},  # 证券公司
    {"code": "csiH30035", "market": "A股指数-东财", "monitor": "buy"},  # 300非银
    {"code": "csi930606", "market": "A股指数-东财", "monitor": "buy"},  # 中证钢铁
    {"code": "csiH30184", "market": "A股指数-东财", "monitor": "buy"},  # 半导体
    {"code": "csi931160", "market": "A股指数-东财", "monitor": "buy"},  # 通信设备
    {"code": "csi931235", "market": "A股指数-东财", "monitor": "buy"},  # 中证电信
    {"code": "csi931009", "market": "A股指数-东财", "monitor": "buy"},  # 建筑材料
    {"code": "csi930697", "market": "A股指数-东财", "monitor": "buy"},  # 家用电器
    {"code": "sh000949", "market": "A股指数-东财", "monitor": "buy"},  # 中证农业
    {"code": "csi931151", "market": "A股指数-东财", "monitor": "buy"},  # 光伏产业
    {"code": "sh000815", "market": "A股指数-东财", "monitor": "buy"},  # 细分食品
    {"code": "sz399971", "market": "A股指数-东财", "monitor": "buy"},  # 中证传媒
    {"code": "csi930901", "market": "A股指数-东财", "monitor": "buy"},  # 动漫游戏
    {"code": "csi930781", "market": "A股指数-东财", "monitor": "buy"},  # 中证影视
    {"code": "csiH30590", "market": "A股指数-东财", "monitor": "buy"},  # 机器人
    {"code": "csi931456", "market": "A股指数-东财", "monitor": "buy"},  # 中国教育
    {"code": "sh000932", "market": "A股指数-东财", "monitor": "buy"},  # 中证消费
    {"code": "csi930604", "market": "A股指数-东财", "monitor": "buy"},  # 中国互联网30
    {"code": "csi931775", "market": "A股指数-东财", "monitor": "buy"},  # 房地产

    # 同花顺-全港股ETF
    #{"code": "HSI", "market": "港股指数-东财", "monitor": "buy"},  # 恒生指数
    #{"code": "HSTECH", "market": "港股指数-东财", "monitor": "buy"},  # 恒生科技指数
    #{"code": "HSCEI", "market": "港股指数-东财", "monitor": "buy"},  # 国企指数
    {"code": "513060", "market": "ETF-东财", "monitor": "buy"},  #
    {"code": "159792", "market": "ETF-东财", "monitor": "buy"},  #
    {"code": "513330", "market": "ETF-东财", "monitor": "buy"},  #
    {"code": "513630", "market": "ETF-东财", "monitor": "buy"},  #
    {"code": "513120", "market": "ETF-东财", "monitor": "buy"},  #
    {"code": "513090", "market": "ETF-东财", "monitor": "buy"},  #
    {"code": "513970", "market": "ETF-东财", "monitor": "buy"},  #
    {"code": "513750", "market": "ETF-东财", "monitor": "buy"},  #
    {"code": "513530", "market": "ETF-东财", "monitor": "buy"},  #
    {"code": "513050", "market": "ETF-东财", "monitor": "buy"},  #
    {"code": "159636", "market": "ETF-东财", "monitor": "buy"},  #
    {"code": "159691", "market": "ETF-东财", "monitor": "buy"},  #
    {"code": "159892", "market": "ETF-东财", "monitor": "buy"},  #
    {"code": "513690", "market": "ETF-东财", "monitor": "buy"},  #
    {"code": "513920", "market": "ETF-东财", "monitor": "buy"},  #
    {"code": "513200", "market": "ETF-东财", "monitor": "buy"},  #
    {"code": "513550", "market": "ETF-东财", "monitor": "buy"},  #
    {"code": "159506", "market": "ETF-东财", "monitor": "buy"},  #
    {"code": "513860", "market": "ETF-东财", "monitor": "buy"},  #
    {"code": "159567", "market": "ETF-东财", "monitor": "buy"},  #
    {"code": "513160", "market": "ETF-东财", "monitor": "buy"},  #
    {"code": "513950", "market": "ETF-东财", "monitor": "buy"},  #
    {"code": "513040", "market": "ETF-东财", "monitor": "buy"},  #
    {"code": "513190", "market": "ETF-东财", "monitor": "buy"},  #
    {"code": "159735", "market": "ETF-东财", "monitor": "buy"},  #
    {"code": "513170", "market": "ETF-东财", "monitor": "buy"},  #
    {"code": "159333", "market": "ETF-东财", "monitor": "buy"},  #
    {"code": "159726", "market": "ETF-东财", "monitor": "buy"},  #
    {"code": "159747", "market": "ETF-东财", "monitor": "buy"},  #
    {"code": "513590", "market": "ETF-东财", "monitor": "buy"},  #
    {"code": "520500", "market": "ETF-东财", "monitor": "buy"},  #
    {"code": "513320", "market": "ETF-东财", "monitor": "buy"},  #
    {"code": "520700", "market": "ETF-东财", "monitor": "buy"},  #
    {"code": "159788", "market": "ETF-东财", "monitor": "buy"},  #
    {"code": "159519", "market": "ETF-东财", "monitor": "buy"},  #
    {"code": "513140", "market": "ETF-东财", "monitor": "buy"},  #

    # 同花顺-跨境商品ETF
    {"code": "159981", "market": "ETF-东财", "monitor": "buy"},  # 能源化工ETF

    # 同花顺-个股
    {"code": "sh601988", "market": "A股股票-新浪", "monitor": "buy"},  # 中国银行
    {"code": "sh601398", "market": "A股股票-新浪", "monitor": "buy"},  # 工商银行
    {"code": "sh601288", "market": "A股股票-新浪", "monitor": "buy"},  # 农业银行
    {"code": "sh601939", "market": "A股股票-新浪", "monitor": "buy"},  # 建设银行
    {"code": "sh601728", "market": "A股股票-新浪", "monitor": "buy"},  # 中国电信
    {"code": "sh600941", "market": "A股股票-新浪", "monitor": "buy"},  # 中国移动
    {"code": "sh600050", "market": "A股股票-新浪", "monitor": "buy"},  # 中国联通
    {"code": "sh600900", "market": "A股股票-新浪", "monitor": "buy"},  # 长江电力
    {"code": "sh601088", "market": "A股股票-新浪", "monitor": "buy"},  # 中国神华
    {"code": "sh600036", "market": "A股股票-新浪", "monitor": "buy"},  # 招商银行
    {"code": "sh601166", "market": "A股股票-新浪", "monitor": "buy"},  # 兴业银行
    {"code": "sh601328", "market": "A股股票-新浪", "monitor": "buy"},  # 交通银行
    {"code": "sh600919", "market": "A股股票-新浪", "monitor": "buy"},  # 江苏银行
    {"code": "sh600000", "market": "A股股票-新浪", "monitor": "buy"},  # 浦发银行
    {"code": "sh601899", "market": "A股股票-新浪", "monitor": "buy"},  # 紫金矿业
    {"code": "sh600028", "market": "A股股票-新浪", "monitor": "buy"},  # 中国石化
    {"code": "sz000333", "market": "A股股票-新浪", "monitor": "buy"},  # 美的集团
    {"code": "sh601658", "market": "A股股票-新浪", "monitor": "buy"},  # 邮储银行
    {"code": "sh601998", "market": "A股股票-新浪", "monitor": "buy"},  # 中信银行
    {"code": "sh600276", "market": "A股股票-新浪", "monitor": "buy"},  # 恒瑞医药
    {"code": "sh601816", "market": "A股股票-新浪", "monitor": "buy"},  # 京沪高铁
    {"code": "sz002415", "market": "A股股票-新浪", "monitor": "buy"},  # 海康威视
    {"code": "sz000651", "market": "A股股票-新浪", "monitor": "buy"},  # 格力电器
    {"code": "sh601668", "market": "A股股票-新浪", "monitor": "buy"},  # 中国建筑
    {"code": "sz002352", "market": "A股股票-新浪", "monitor": "buy"},  # 顺丰控股
    {"code": "sh600887", "market": "A股股票-新浪", "monitor": "buy"},  # 伊利股份
    {"code": "sh600406", "market": "A股股票-新浪", "monitor": "buy"},  # 国电南瑞
    {"code": "sh600025", "market": "A股股票-新浪", "monitor": "buy"},  # 华能水电
    {"code": "sh600031", "market": "A股股票-新浪", "monitor": "buy"},  # 三一重工
    {"code": "sh600019", "market": "A股股票-新浪", "monitor": "buy"},  # 宝钢股份
    {"code": "sz000429", "market": "A股股票-新浪", "monitor": "buy"},  # 粤高速A
    {"code": "sh600350", "market": "A股股票-新浪", "monitor": "buy"},  # 山东高速
    {"code": "sh601006", "market": "A股股票-新浪", "monitor": "buy"},  # 大秦铁路
    {"code": "sh600377", "market": "A股股票-新浪", "monitor": "buy"},  # 宁沪高速
    {"code": "sh600482", "market": "A股股票-新浪", "monitor": "buy"},  # 中国动力
    {"code": "sz002179", "market": "A股股票-新浪", "monitor": "buy"},  # 中航光电
    {"code": "sh601111", "market": "A股股票-新浪", "monitor": "buy"},  # 中国国航

    {"code": "sz000999", "market": "A股股票-新浪", "monitor": "buy"},  # 华润三九   持有
    {"code": "sz002818", "market": "A股股票-新浪", "monitor": "buy"},  # 富森美     持有
    {"code": "sz000975", "market": "A股股票-新浪", "monitor": "buy"},  # 山金国际   持有
    {"code": "sz000564", "market": "A股股票-新浪", "monitor": "buy"},  # 供销大集   持有
    {"code": "sh600489", "market": "A股股票-新浪", "monitor": "buy"},  # 中金黄金   持有
    {"code": "sz002739", "market": "A股股票-新浪", "monitor": "buy"},  # 万达电影   持有
    {"code": "sz002042", "market": "A股股票-新浪", "monitor": "buy"},  # 华孚时尚   持有
    {"code": "sz002262", "market": "A股股票-新浪", "monitor": "buy"},  # 恩华药业   持有
    {"code": "sh600233", "market": "A股股票-新浪", "monitor": "buy"},  # 圆通速递   持有
    {"code": "518800", "market": "ETF-东财", "monitor": "buy"},       # 黄金基金   持有
    {"code": "sz000938", "market": "A股股票-新浪", "monitor": "buy"},  # 紫金股份   持有
    {"code": "sh601398", "market": "A股股票-新浪", "monitor": "buy"},  # 工商银行   持有

    # 标的-监控卖出信号
    # 同花顺-持仓股
    {"code": "sz000999", "market": "A股股票-新浪", "monitor": "sell"},  # 华润三九   持有,补仓
    {"code": "sz002818", "market": "A股股票-新浪", "monitor": "sell"},  # 富森美     持有,补仓
    {"code": "sz000975", "market": "A股股票-新浪", "monitor": "sell"},  # 山金国际   持有,补仓
    {"code": "sz000564", "market": "A股股票-新浪", "monitor": "sell"},  # 供销大集   持有,补仓
    {"code": "sh600489", "market": "A股股票-新浪", "monitor": "sell"},  # 中金黄金   持有,补仓
    {"code": "sz002739", "market": "A股股票-新浪", "monitor": "sell"},  # 万达电影   持有,补仓
    {"code": "sz002042", "market": "A股股票-新浪", "monitor": "sell"},  # 华孚时尚   持有,补仓
    {"code": "sz002262", "market": "A股股票-新浪", "monitor": "sell"},  # 恩华药业    持有,补仓
    {"code": "sh600233", "market": "A股股票-新浪", "monitor": "sell"},  # 圆通速递   持有,补仓
    {"code": "518800", "market": "ETF-东财", "monitor": "sell"},       # 黄金基金   长期持,上穿补
    {"code": "sz000938", "market": "A股股票-新浪", "monitor": "sell"},  # 紫金股份   持有
    {"code": "sh601398", "market": "A股股票-新浪", "monitor": "sell"},  # 工商银行   持有

    #test

]
BOLL_WINDOW = 20


# =====================

def get_stock_data(code, market):
    # 通过不同数据源的列名
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
            raw_df = ak.stock_zh_a_daily(symbol=code, start_date="20250401", adjust="qfq")

            # 确保spot_df中有当前标的的数据并提取出来
            if spot_df is not None:
                try:
                    spot_data = spot_df[spot_df['代码'] == code].iloc[0]  # 将spot_df中的当前标的的数据赋值给spot_data
                except IndexError:
                    print(f"spot_df中无 A股股票{code} 的数据")
            # 构建当日K线
            today_date = datetime.now().strftime("%Y-%m-%d")
            today_kline = {
                'date': today_date,
                'open': spot_data['今开'],
                'high': spot_data['最高'],
                'low': spot_data['最低'],
                'close': spot_data['最新价']
            }
            # 合并数据
            if today_date not in raw_df['date'].astype(str).values:  # 当A股股票-新浪的数据中没有当日数据,才合并数据
                raw_df = pd.concat([raw_df, pd.DataFrame([today_kline])], ignore_index=True)

        elif market == "ETF-东财":
            raw_df = ak.fund_etf_hist_em(symbol=code, start_date="20250401", adjust="qfq")
        elif market == "A股指数-东财":
            raw_df = ak.stock_zh_index_daily_em(symbol=code, start_date="20250401")
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
        df = df.iloc[-(BOLL_WINDOW + 2):]  # 保留足够计算BOLL的数据
        df['date'] = pd.to_datetime(df['date'])  # 统一日期格式
        return df.sort_values('date', ascending=True).reset_index(drop=True)

    except Exception as e:
        print(f"获取{code}数据失败：{str(e)}\n ")
        return None


def check_boll_signal(df, monitor_type="buy"):  # 默认监控买入信号
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

    if monitor_type == "buy" and buy:
        return 'BUY'
    elif monitor_type == "sell" and sell:
        return 'SELL'
    return None  # 不符合条件的信号被过滤


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
    print("开始运行程序    时间:" + (datetime.now() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M"))
    global spot_df
    spot_df = None
    spot_df = ak.stock_zh_a_spot()  # 获取时数据-新浪并存为全局变量
    signals = []
    for stock in STOCKS:
        print(f"代码 : {stock['code']}")  # 用于查看程序运行进度
        df = get_stock_data(stock['code'], stock['market'])
        if df is not None:  # 用于检查代码和数据是否正确对应
            print(f"最新日期 : {df['date'].iloc[-1].strftime('%Y-%m-%d')}")  # 只打印日期(本来也只有日期)
            #print(f"最新价 : {df['close'].iloc[-1]}\n")
        signal = check_boll_signal(df, stock.get('monitor', 'buy'))  # 默认buy
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
            print("检测到交易信号,通知发送成功")
    else:
        print("未检测到交易信号")


if __name__ == "__main__":
    main()
