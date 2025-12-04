#此代码是通过币安API接口获取btc的行情数据，进行均线策略预警（跌破或突破均线时钉钉提醒）
#此代码放在github actions上，每日定时运行

import okx.MarketData as MarketData
import pandas as pd
from datetime import datetime

# 初始化Market Data API
# flag: "0" = 实盘, "1" = 模拟盘
flag = "0"
marketDataAPI = MarketData.MarketAPI(flag=flag)

# 获取BTC-USDT的历史K线数据
try:
    # 参数说明:
    # instId: 交易对，注意OKX使用 "BTC-USDT" 格式（中划线而非斜杠）
    # bar: K线周期 - 1m/3m/5m/15m/30m/1H/2H/4H/6H/12H/1D/1W/1M/3M/6M/1Y
    # limit: 数据条数，默认100，最大100
    # after: 请求此时间戳之前的分页内容（毫秒）
    # before: 请求此时间戳之后的分页内容（毫秒）

    result = marketDataAPI.get_candlesticks(
        instId="BTC-USDT",
        bar="1D",  # 1天K线
        limit="10"  # 获取10条数据（最近10天）
    )

    if result['code'] == '0':  # 请求成功
        data = result['data']

        # 将数据转换为DataFrame
        # OKX返回的数据格式: [ts, o, h, l, c, vol, volCcy, volCcyQuote, confirm]
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close',
            'volume', 'volCcy', 'volCcyQuote', 'confirm'
        ])

        # 转换时间戳为可读格式
        df['timestamp'] = pd.to_datetime(df['timestamp'].astype(float), unit='ms')

        # 转换价格和成交量为数值类型
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)

        # 按时间升序排列
        df = df.sort_values('timestamp').reset_index(drop=True)

        # 选择主要列
        df_main = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

        print(f"成功获取 {len(df_main)} 条 BTC-USDT 最近10天的日K线数据")
        print("\n最近10天的数据:")
        print(df_main.to_string(index=False))

        # 保存到CSV文件
        df_main.to_csv('btc_usdt_okx_history.csv', index=False)
        print("\n数据已保存到 btc_usdt_okx_history.csv")

    else:
        print(f"请求失败: {result['msg']}")

except Exception as e:
    print(f"获取数据时出错: {str(e)}")

# ========== 示例2: 获取特定时间段的数据 ==========
print("\n" + "=" * 60)
print("获取特定时间段的数据示例:")

try:
    # 使用before参数获取指定时间之后的数据
    # 时间戳需要是毫秒级别
    before_ts = int(datetime(2024, 12, 1).timestamp() * 1000)

    result = marketDataAPI.get_candlesticks(
        instId="BTC-USDT",
        bar="1D",  # 日K线
        before=str(before_ts),  # 获取此时间之后的数据
        limit="30"  # 获取30条数据
    )

    if result['code'] == '0':
        data = result['data']
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close',
            'volume', 'volCcy', 'volCcyQuote', 'confirm'
        ])

        df['timestamp'] = pd.to_datetime(df['timestamp'].astype(float), unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)

        df = df.sort_values('timestamp').reset_index(drop=True)
        df_main = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

        print(f"\n从 2024-12-01 开始的 {len(df_main)} 条日K数据:")
        print(df_main.head(10).to_string(index=False))

    else:
        print(f"请求失败: {result['msg']}")

except Exception as e:
    print(f"获取特定时间段数据时出错: {str(e)}")

# ========== 示例3: 获取实时ticker数据 ==========
print("\n" + "=" * 60)
print("获取实时ticker数据:")

try:
    result = marketDataAPI.get_ticker(instId="BTC-USDT")

    if result['code'] == '0':
        ticker = result['data'][0]
        print(f"\nBTC-USDT 实时行情:")
        print(f"最新价: {ticker['last']}")
        print(f"24h最高: {ticker['high24h']}")
        print(f"24h最低: {ticker['low24h']}")
        print(f"24h成交量: {ticker['vol24h']}")
        print(f"24h涨跌幅: {float(ticker.get('changeRate24h', 0)) * 100:.2f}%")
    else:
        print(f"请求失败: {result['msg']}")

except Exception as e:
    print(f"获取ticker数据时出错: {str(e)}")

