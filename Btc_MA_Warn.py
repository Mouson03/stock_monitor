#此代码是通过币安API接口获取btc的行情数据，进行均线策略预警（跌破或突破均线时钉钉提醒）
#此代码放在github actions上，每日定时运行

import requests
import pandas as pd

url = "https://api.binance.com/api/v3/klines"
params = {
    "symbol": "BTCUSDT",
    "interval": "1d",
    "limit": 365    # 最近 365 天
}

r = requests.get(url, params=params)
data = r.json()
print(data)

# 转成 DataFrame
df = pd.DataFrame(data, columns=[
    "open_time","open","high","low","close","volume",
    "close_time","quote_asset_volume","num_trades",
    "taker_buy_base","taker_buy_quote","ignore"
])

# 收盘价转数字
df["close"] = df["close"].astype(float)

print(df.tail())  # 查看最后几天的日K
