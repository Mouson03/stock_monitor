#数据获取渠道：okx-python库，也就是okx官方库
#claude写的程序,在claude的聊天历史名字：“通过okx-python库来写btcMA365预警程序"
#用于放在github actions上每日定时运行
#已经让添加了防错代码，也就是程序中任何一环有问题时。当出现以下的情况时会发送消息至钉钉：
#1.出现交易信号发送提醒            （已测试，突破和跌破都会通知）
#2.数据获取失败时发送错误提醒       （已测试，会通知）
#3.数据行数不足365行时             （已测试，数据不足时确实会通知）
#4.程序运行出错时发送异常提醒       (已测试，会通知）

import okx.MarketData as MarketData
import pandas as pd
from datetime import datetime, timedelta

# 钉钉机器人加签所需库
import time
import requests
import hmac
import hashlib
import base64
import urllib.parse

# ===== 钉钉相关的用户配置区 =====
DING_SECRET = "SEC1e7793627614d78f4637204eeddae3c9f1ed98cb732d0c403445087b2cc27a55"  # 钉钉机器人加签密钥
DING_WEBHOOK = "https://oapi.dingtalk.com/robot/send?access_token=019d9077894208be07ac588bb52c18174968f1f30c3c1683a7580e7bfc76c712"  # 钉钉机器人webhooks链接
# =====================

# 初始化OKX API
flag = "0"  # 实盘
marketDataAPI = MarketData.MarketAPI(flag=flag)


# ========== 钉钉加签 ==========
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


# ========== 钉钉发送消息 ==========
def send_dingtalk_message(content):
    """发送钉钉消息"""
    try:
        timestamp, sign = generate_ding_signature(DING_SECRET)
        webhook_url = f"{DING_WEBHOOK}&timestamp={timestamp}&sign={sign}"

        data = {
            "msgtype": "text",
            "text": {"content": content}
        }

        response = requests.post(webhook_url, json=data, timeout=10)
        result = response.json()

        if result.get("errcode") == 0:
            print("✓ 钉钉消息发送成功")
            return True
        else:
            print(f"✗ 钉钉消息发送失败: {result}")
            return False

    except Exception as e:
        print(f"✗ 钉钉消息发送异常: {str(e)}")
        return False


# ========== 获取最近365天的日K数据 ==========
def get_last_365days_data(instId, bar):
    """
    获取最近365天的K线数据

    返回:
        DataFrame 或 None（失败时）
    """
    try:
        print(f"正在获取 {instId} 最近365天的日K数据...")
        all_data = []

        # 第一次请求：获取最近300条
        print("第1次请求：获取最近300条数据...")
        result1 = marketDataAPI.get_candlesticks(
            instId=instId,
            bar=bar,
            limit="300"
        )

        if result1['code'] != '0' or not result1['data']:
            raise Exception(f"第1次请求失败: {result1.get('msg', '未知错误')}")

        all_data.extend(result1['data'])
        print(f"✓ 已获取 {len(result1['data'])} 条")

        # 获取最早的时间戳
        after = result1['data'][-1][0]
        time.sleep(0.1)

        # 第二次请求：获取更早的100条
        print("第2次请求：获取更早的100条数据...")
        result2 = marketDataAPI.get_candlesticks(
            instId=instId,
            bar=bar,
            limit="100",
            after=after
        )

        if result2['code'] != '0' or not result2['data']:
            raise Exception(f"第2次请求失败: {result2.get('msg', '未知错误')}")

        all_data.extend(result2['data'])
        print(f"✓ 已获取 {len(result2['data'])} 条")

        # 转换为DataFrame
        df = pd.DataFrame(all_data, columns=[
            'timestamp', 'open', 'high', 'low', 'close',
            'volume', 'volCcy', 'volCcyQuote', 'confirm'
        ])

        # 转换时间戳（香港时区 UTC+8）
        df['timestamp'] = pd.to_datetime(df['timestamp'].astype(float), unit='ms')

        # 转换为数值类型
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)

        # 去重并按时间升序排列
        df = df.drop_duplicates(subset=['timestamp']).sort_values('timestamp').reset_index(drop=True)

        # 只保留最近365天
        df = df.tail(365).reset_index(drop=True)
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

        print(f"✓ 成功获取 {len(df)} 条日K数据")
        print(f"时间范围: {df['timestamp'].min()} 至 {df['timestamp'].max()}")

        return df

    except Exception as e:
        error_msg = f"获取 {instId} 数据失败: {str(e)}"
        print(f"✗ {error_msg}")
        send_dingtalk_message(f"【OKX数据获取失败】\n{error_msg}")
        return None


# ========== 检查MA365突破/跌破信号 ==========
def check_ma365_signal(data):
    """
    检查是否突破或跌破MA365

    返回:
        signal_type: "突破" / "跌破" / None
    """
    try:
        # 计算MA365
        data['MA365'] = data['close'].rolling(window=365, min_periods=1).mean()

        # 获取昨天和今天的数据
        yesterday = data.iloc[-2]
        today = data.iloc[-1]

        print(f"\n昨日收盘价: {yesterday['close']:.2f}")
        print(f"昨日MA365: {yesterday['MA365']:.2f}")
        print(f"今日收盘价: {today['close']:.2f}")
        print(f"今日MA365: {today['MA365']:.2f}")

        # 跌破：昨天收盘价 >= MA365，今天收盘价 <= MA365
        condition_fall = (yesterday['close'] >= yesterday['MA365']) and (today['close'] <= today['MA365'])

        # 突破：昨天收盘价 <= MA365，今天收盘价 >= MA365
        condition_rise = (yesterday['close'] <= yesterday['MA365']) and (today['close'] >= today['MA365'])

        if condition_fall:
            return "跌破"
        elif condition_rise:
            return "突破"
        else:
            return None

    except Exception as e:
        error_msg = f"检查MA365信号时出错: {str(e)}"
        print(f"✗ {error_msg}")
        send_dingtalk_message(f"【MA365信号检查失败】\n{error_msg}")
        return None


# ========== 格式化钉钉消息 ==========
def format_signal_message(instId, signal_type, data):
    """格式化交易信号消息"""
    today = data.iloc[-1]
    yesterday = data.iloc[-2]

    deviation = ((today['close'] / today['MA365'] - 1) * 100)

    message = f"""btc出现交易信号!!!
【btc交易信号提醒】

标的: {instId}
信号类型: {signal_type}MA365

时间: {today['timestamp'].strftime('%Y-%m-%d')}
今日收盘价: {today['close']:,.2f}
MA365: {today['MA365']:,.2f}
偏离度: {deviation:+.2f}%

昨日收盘价: {yesterday['close']:,.2f}
昨日MA365: {yesterday['MA365']:,.2f}

365天最高: {data['high'].max():,.2f}
365天最低: {data['low'].min():,.2f}
"""
    return message


# ========== 主函数 ==========
def main():
    print("=" * 60)
    print(f"开始运行程序 时间: {(datetime.now() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    try:
        # 1. 获取BTC-USDT最近365天数据
        instId = "BTC-USDT"
        df = get_last_365days_data(instId=instId, bar="1D")

        if df is None or len(df) < 365:
            error_msg = f"{instId} 数据行数不足，当前只有 {len(df) if df is not None else 0} 条"
            print(f"✗ {error_msg}")
            send_dingtalk_message(f"【数据异常】\n{error_msg}")
            return

        # 2. 检查MA365信号
        signal_type = check_ma365_signal(df)

        # 3. 如果有信号，发送钉钉消息
        if signal_type:
            print(f"\n{'=' * 60}")
            print(f"✓ 检测到交易信号: {signal_type}MA365")
            print(f"{'=' * 60}")

            message = format_signal_message(instId, signal_type, df)
            send_dingtalk_message(message)
        else:
            print(f"\n{'=' * 60}")
            print("未检测到交易信号")
            print(f"{'=' * 60}")

        # 4. 打印统计信息
        today = df.iloc[-1]
        print(f"\n数据统计:")
        print(f"当前价格: {today['close']:,.2f}")
        print(f"MA365: {today['MA365']:,.2f}")
        print(f"偏离度: {((today['close'] / today['MA365'] - 1) * 100):+.2f}%")

        print("\n程序正常运行完成")

    except Exception as e:
        error_msg = f"程序运行出错: {str(e)}"
        print(f"\n✗ {error_msg}")
        send_dingtalk_message(f"【程序异常】\n{error_msg}\n\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")


if __name__ == "__main__":
    main()
