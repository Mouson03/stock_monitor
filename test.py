import akshare as ak
#A股股票-新浪
df = ak.stock_zh_a_daily(symbol='sz002807' , adjust="qfq")
print(df)
