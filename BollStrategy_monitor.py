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

    # 一.监控买入信号
    # 1.同花顺-适合boll策略:
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
    {"code": "159981", "market": "ETF-东财", "monitor": "buy"},  # 能源化工ETF
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

    # 2.同花顺-个股boll监控
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

    # 3.通达信-250波幅小30,即(250日最高价-最低价)/250日均价<0.3    2025.5.21选出,共31个,总市值降序    已验证代码,名称和对应关系
    {"code": "sh600941", "market": "A股股票-新浪", "monitor": "buy"},  # 中国移动
    {"code": "sh600900", "market": "A股股票-新浪", "monitor": "buy"},  # 长江电力
    {"code": "sh601328", "market": "A股股票-新浪", "monitor": "buy"},  # 交通银行
    {"code": "sh601658", "market": "A股股票-新浪", "monitor": "buy"},  # 邮储银行
    {"code": "sh601006", "market": "A股股票-新浪", "monitor": "buy"},  # 大秦铁路
    {"code": "sh601169", "market": "A股股票-新浪", "monitor": "buy"},  # 北京银行
    {"code": "sh600905", "market": "A股股票-新浪", "monitor": "buy"},  # 三峡能源
    {"code": "sh601868", "market": "A股股票-新浪", "monitor": "buy"},  # 中国能建
    {"code": "sz001965", "market": "A股股票-新浪", "monitor": "buy"},  # 招商公路
    {"code": "sh600115", "market": "A股股票-新浪", "monitor": "buy"},  # 中国东航
    {"code": "sh601916", "market": "A股股票-新浪", "monitor": "buy"},  # 浙商银行
    {"code": "sh601018", "market": "A股股票-新浪", "monitor": "buy"},  # 宁波港
    {"code": "sh600642", "market": "A股股票-新浪", "monitor": "buy"},  # 申能股份
    {"code": "sh600925", "market": "A股股票-新浪", "monitor": "buy"},  # 苏能股份
    {"code": "sz000088", "market": "A股股票-新浪", "monitor": "buy"},  # 盐田港
    {"code": "sh601228", "market": "A股股票-新浪", "monitor": "buy"},  # 广州港
    {"code": "sh601158", "market": "A股股票-新浪", "monitor": "buy"},  # 重庆水务
    {"code": "sh601128", "market": "A股股票-新浪", "monitor": "buy"},  # 常熟银行
    {"code": "sz001213", "market": "A股股票-新浪", "monitor": "buy"},  # 中铁特货
    {"code": "sz000089", "market": "A股股票-新浪", "monitor": "buy"},  # 深圳机场
    {"code": "sh601827", "market": "A股股票-新浪", "monitor": "buy"},  # 三峰环境
    {"code": "sh600116", "market": "A股股票-新浪", "monitor": "buy"},  # 三峡水利
    {"code": "sh600821", "market": "A股股票-新浪", "monitor": "buy"},  # 金开新能
    {"code": "sh600033", "market": "A股股票-新浪", "monitor": "buy"},  # 福建高速
    {"code": "sh603053", "market": "A股股票-新浪", "monitor": "buy"},  # 成都燃气
    {"code": "sh600035", "market": "A股股票-新浪", "monitor": "buy"},  # 楚天高速
    {"code": "sh600897", "market": "A股股票-新浪", "monitor": "buy"},  # 厦门空港
    {"code": "sh600681", "market": "A股股票-新浪", "monitor": "buy"},  # 百川能源
    {"code": "sh603689", "market": "A股股票-新浪", "monitor": "buy"},  # 皖天然气
    {"code": "sh603856", "market": "A股股票-新浪", "monitor": "buy"},  # 东宏股份
    {"code": "sz002763", "market": "A股股票-新浪", "monitor": "buy"},  # 汇洁股份

    # 4.通达信-250标准差小5,即250日标准差/250日均价<0.05    2025.5.21选出,共24个(42-18),总市值降序    已验证代码,名称和对应关系    与3(250幅低30)重复的18只股已删除,只在3中保留
    {"code": "sh600018", "market": "A股股票-新浪", "monitor": "buy"},  # 上港集团
    {"code": "sh601009", "market": "A股股票-新浪", "monitor": "buy"},  # 南京银行
    {"code": "sh600009", "market": "A股股票-新浪", "monitor": "buy"},  # 上海机场
    {"code": "sh600803", "market": "A股股票-新浪", "monitor": "buy"},  # 新奥股份
    {"code": "sh601021", "market": "A股股票-新浪", "monitor": "buy"},  # 春秋航空
    {"code": "sz002032", "market": "A股股票-新浪", "monitor": "buy"},  # 苏泊尔
    {"code": "sz002252", "market": "A股股票-新浪", "monitor": "buy"},  # 上海莱士
    {"code": "sz000513", "market": "A股股票-新浪", "monitor": "buy"},  # 丽珠集团
    {"code": "sh601928", "market": "A股股票-新浪", "monitor": "buy"},  # 凤凰传媒
    {"code": "sh600098", "market": "A股股票-新浪", "monitor": "buy"},  # 广州发展
    {"code": "sh600004", "market": "A股股票-新浪", "monitor": "buy"},  # 白云机场
    {"code": "sh600007", "market": "A股股票-新浪", "monitor": "buy"},  # 中国国贸
    {"code": "sh601811", "market": "A股股票-新浪", "monitor": "buy"},  # 新华文轩
    {"code": "sh601139", "market": "A股股票-新浪", "monitor": "buy"},  # 深圳燃气
    {"code": "sh601326", "market": "A股股票-新浪", "monitor": "buy"},  # 秦港股份
    {"code": "sh601952", "market": "A股股票-新浪", "monitor": "buy"},  # 苏垦农发
    {"code": "sh603235", "market": "A股股票-新浪", "monitor": "buy"},  # 天新药业
    {"code": "sh603281", "market": "A股股票-新浪", "monitor": "buy"},  # 江翰新材
    {"code": "sh600054", "market": "A股股票-新浪", "monitor": "buy"},  # 黄山旅游
    {"code": "sh600987", "market": "A股股票-新浪", "monitor": "buy"},  # 航民股份
    {"code": "sh600138", "market": "A股股票-新浪", "monitor": "buy"},  # 中青旅
    {"code": "sh601065", "market": "A股股票-新浪", "monitor": "buy"},  # 江盐集团
    {"code": "sh601199", "market": "A股股票-新浪", "monitor": "buy"},  # 江南水务
    {"code": "sz002033", "market": "A股股票-新浪", "monitor": "buy"},  # 丽江股份

    # 5.通达信-250波幅30标5   共1个（18-17），与3，4重复的没添加
    {"code": "sz001213", "market": "A股股票-新浪", "monitor": "buy"},  # 中特特货

    # 6.通达信-120波幅小20   共154个，未筛选与前面面重复的，懒得选了
    {"code": "sh601398", "market": "A股股票-新浪", "monitor": "buy"},  # 工商银行
    {"code": "sh600941", "market": "A股股票-新浪", "monitor": "buy"},  # 中国移动
    {"code": "sh601939", "market": "A股股票-新浪", "monitor": "buy"},  # 建设银行
    {"code": "sh600519", "market": "A股股票-新浪", "monitor": "buy"},  # 贵州茅台
    {"code": "sh601288", "market": "A股股票-新浪", "monitor": "buy"},  # 农业银行
    {"code": "sh601988", "market": "A股股票-新浪", "monitor": "buy"},  # 中国银行
    {"code": "sh601318", "market": "A股股票-新浪", "monitor": "buy"},  # 中国平安
    {"code": "sh600900", "market": "A股股票-新浪", "monitor": "buy"},  # 长江电力
    {"code": "sz000333", "market": "A股股票-新浪", "monitor": "buy"},  # 美的集团
    {"code": "sh601328", "market": "A股股票-新浪", "monitor": "buy"},  # 交通银行
    {"code": "sh601658", "market": "A股股票-新浪", "monitor": "buy"},  # 邮储银行
    {"code": "sh601998", "market": "A股股票-新浪", "monitor": "buy"},  # 中信银行
    {"code": "sh601816", "market": "A股股票-新浪", "monitor": "buy"},  # 京沪高铁
    {"code": "sz000651", "market": "A股股票-新浪", "monitor": "buy"},  # 格力电器
    {"code": "sh601818", "market": "A股股票-新浪", "monitor": "buy"},  # 光大银行
    {"code": "sz002352", "market": "A股股票-新浪", "monitor": "buy"},  # 顺丰控股
    {"code": "sz000001", "market": "A股股票-新浪", "monitor": "buy"},  # 平安银行
    {"code": "sh601985", "market": "A股股票-新浪", "monitor": "buy"},  # 中国核电
    {"code": "sh600887", "market": "A股股票-新浪", "monitor": "buy"},  # 伊利股份
    {"code": "sh600016", "market": "A股股票-新浪", "monitor": "buy"},  # 民生银行
    {"code": "sh600025", "market": "A股股票-新浪", "monitor": "buy"},  # 华能水电
    {"code": "sz002142", "market": "A股股票-新浪", "monitor": "buy"},  # 宁波银行
    {"code": "sh600019", "market": "A股股票-新浪", "monitor": "buy"},  # 宝钢股份
    {"code": "sh600660", "market": "A股股票-新浪", "monitor": "buy"},  # 福耀玻璃
    {"code": "sh600018", "market": "A股股票-新浪", "monitor": "buy"},  # 上港集团
    {"code": "sh601006", "market": "A股股票-新浪", "monitor": "buy"},  # 大秦铁路
    {"code": "sh601169", "market": "A股股票-新浪", "monitor": "buy"},  # 北京银行
    {"code": "sh600585", "market": "A股股票-新浪", "monitor": "buy"},  # 海螺水泥
    {"code": "sh600905", "market": "A股股票-新浪", "monitor": "buy"},  # 三峡能源
    {"code": "sh600015", "market": "A股股票-新浪", "monitor": "buy"},  # 华夏银行
    {"code": "sh601009", "market": "A股股票-新浪", "monitor": "buy"},  # 南京银行
    {"code": "sh600346", "market": "A股股票-新浪", "monitor": "buy"},  # 恒力石化
    {"code": "sz002027", "market": "A股股票-新浪", "monitor": "buy"},  # 分众传媒
    {"code": "sh600926", "market": "A股股票-新浪", "monitor": "buy"},  # 杭州银行
    {"code": "sz000538", "market": "A股股票-新浪", "monitor": "buy"},  # 云南白药
    {"code": "sh603195", "market": "A股股票-新浪", "monitor": "buy"},  # 公牛集团
    {"code": "sh601868", "market": "A股股票-新浪", "monitor": "buy"},  # 中国能建
    {"code": "sz000895", "market": "A股股票-新浪", "monitor": "buy"},  # 双汇发展
    {"code": "sh601916", "market": "A股股票-新浪", "monitor": "buy"},  # 浙商银行
    {"code": "sh601825", "market": "A股股票-新浪", "monitor": "buy"},  # 沪农商行
    {"code": "sh600795", "market": "A股股票-新浪", "monitor": "buy"},  # 国电电力
    {"code": "sh600377", "market": "A股股票-新浪", "monitor": "buy"},  # 宁沪高速
    {"code": "sh600023", "market": "A股股票-新浪", "monitor": "buy"},  # 浙能电力
    {"code": "sz002001", "market": "A股股票-新浪", "monitor": "buy"},  # 新和成
    {"code": "sh600196", "market": "A股股票-新浪", "monitor": "buy"},  # 复星医药
    {"code": "sh600741", "market": "A股股票-新浪", "monitor": "buy"},  # 华域汽车
    {"code": "sz002028", "market": "A股股票-新浪", "monitor": "buy"},  # 思源电气
    {"code": "sz000708", "market": "A股股票-新浪", "monitor": "buy"},  # 中信特钢
    {"code": "sh600875", "market": "A股股票-新浪", "monitor": "buy"},  # 东方电气
    {"code": "sz000999", "market": "A股股票-新浪", "monitor": "buy"},  # 华润三九
    {"code": "sz001872", "market": "A股股票-新浪", "monitor": "buy"},  # 招商港口
    {"code": "sh600236", "market": "A股股票-新浪", "monitor": "buy"},  # 桂冠电力
    {"code": "sz002032", "market": "A股股票-新浪", "monitor": "buy"},  # 苏泊尔
    {"code": "sz002252", "market": "A股股票-新浪", "monitor": "buy"},  # 上海莱士
    {"code": "sh600642", "market": "A股股票-新浪", "monitor": "buy"},  # 申能股份
    {"code": "sh600332", "market": "A股股票-新浪", "monitor": "buy"},  # 白云山
    {"code": "sh600426", "market": "A股股票-新浪", "monitor": "buy"},  # 华鲁恒升
    {"code": "sh600096", "market": "A股股票-新浪", "monitor": "buy"},  # XD云天化
    {"code": "sz002601", "market": "A股股票-新浪", "monitor": "buy"},  # 龙佰集团
    {"code": "sz002078", "market": "A股股票-新浪", "monitor": "buy"},  # 太阳纸业
    {"code": "sh601577", "market": "A股股票-新浪", "monitor": "buy"},  # 长沙银行
    {"code": "sz002966", "market": "A股股票-新浪", "monitor": "buy"},  # 苏州银行
    {"code": "sh601061", "market": "A股股票-新浪", "monitor": "buy"},  # 中信金属
    {"code": "sz000423", "market": "A股股票-新浪", "monitor": "buy"},  # 东阿阿胶
    {"code": "sh601598", "market": "A股股票-新浪", "monitor": "buy"},  # 中国外运
    {"code": "sh600925", "market": "A股股票-新浪", "monitor": "buy"},  # 苏能股份
    {"code": "sz001286", "market": "A股股票-新浪", "monitor": "buy"},  # 陕西能源
    {"code": "sh600956", "market": "A股股票-新浪", "monitor": "buy"},  # 新天绿能
    {"code": "sz000513", "market": "A股股票-新浪", "monitor": "buy"},  # 丽珠集团
    {"code": "sh600298", "market": "A股股票-新浪", "monitor": "buy"},  # 安琪酵母
    {"code": "sh600995", "market": "A股股票-新浪", "monitor": "buy"},  # XD南网储
    {"code": "sz000027", "market": "A股股票-新浪", "monitor": "buy"},  # 深圳能源
    {"code": "sz000883", "market": "A股股票-新浪", "monitor": "buy"},  # 湖北能源
    {"code": "sh601928", "market": "A股股票-新浪", "monitor": "buy"},  # 凤凰传媒
    {"code": "sz002007", "market": "A股股票-新浪", "monitor": "buy"},  # 华兰生物
    {"code": "sh600153", "market": "A股股票-新浪", "monitor": "buy"},  # 建发股份
    {"code": "sz002608", "market": "A股股票-新浪", "monitor": "buy"},  # 江苏国信
    {"code": "sh600704", "market": "A股股票-新浪", "monitor": "buy"},  # 物产中大
    {"code": "sh600483", "market": "A股股票-新浪", "monitor": "buy"},  # 福能股份
    {"code": "sh600282", "market": "A股股票-新浪", "monitor": "buy"},  # 南钢股份
    {"code": "sh600582", "market": "A股股票-新浪", "monitor": "buy"},  # 天地科技
    {"code": "sh600021", "market": "A股股票-新浪", "monitor": "buy"},  # 上海电力
    {"code": "sh601000", "market": "A股股票-新浪", "monitor": "buy"},  # 唐山港
    {"code": "sh600329", "market": "A股股票-新浪", "monitor": "buy"},  # 达仁堂
    {"code": "sh600535", "market": "A股股票-新浪", "monitor": "buy"},  # 天士力
    {"code": "sz002318", "market": "A股股票-新浪", "monitor": "buy"},  # 久立特材
    {"code": "sh601158", "market": "A股股票-新浪", "monitor": "buy"},  # 重庆水务
    {"code": "sh601128", "market": "A股股票-新浪", "monitor": "buy"},  # 常熟银行
    {"code": "sh600008", "market": "A股股票-新浪", "monitor": "buy"},  # 首创环保
    {"code": "sh600098", "market": "A股股票-新浪", "monitor": "buy"},  # 广州发展
    {"code": "sz000539", "market": "A股股票-新浪", "monitor": "buy"},  # 粤电力A
    {"code": "sh600004", "market": "A股股票-新浪", "monitor": "buy"},  # 白云机场
    {"code": "sh601997", "market": "A股股票-新浪", "monitor": "buy"},  # 贵阳银行
    {"code": "sz000703", "market": "A股股票-新浪", "monitor": "buy"},  # 恒逸石化
    {"code": "sh600007", "market": "A股股票-新浪", "monitor": "buy"},  # 中国国贸
    {"code": "sz000598", "market": "A股股票-新浪", "monitor": "buy"},  # 兴蓉环境
    {"code": "sz000830", "market": "A股股票-新浪", "monitor": "buy"},  # 鲁西化工
    {"code": "sh600737", "market": "A股股票-新浪", "monitor": "buy"},  # 中粮糖业
    {"code": "sh600380", "market": "A股股票-新浪", "monitor": "buy"},  # 健康元
    {"code": "sz000875", "market": "A股股票-新浪", "monitor": "buy"},  # 吉电股份
    {"code": "sh601811", "market": "A股股票-新浪", "monitor": "buy"},  # 新华文轩
    {"code": "sz002958", "market": "A股股票-新浪", "monitor": "buy"},  # 青农商行
    {"code": "sh601326", "market": "A股股票-新浪", "monitor": "buy"},  # 秦港股份
    {"code": "sz001213", "market": "A股股票-新浪", "monitor": "buy"},  # 中铁特货
    {"code": "sz003035", "market": "A股股票-新浪", "monitor": "buy"},  # 南网能源
    {"code": "sh600528", "market": "A股股票-新浪", "monitor": "buy"},  # 中铁工业
    {"code": "sh601187", "market": "A股股票-新浪", "monitor": "buy"},  # 厦门银行
    {"code": "sz000869", "market": "A股股票-新浪", "monitor": "buy"},  # 张裕A
    {"code": "sh600750", "market": "A股股票-新浪", "monitor": "buy"},  # 江中药业
    {"code": "sz000089", "market": "A股股票-新浪", "monitor": "buy"},  # 深圳机场
    {"code": "sh600916", "market": "A股股票-新浪", "monitor": "buy"},  # 中国黄金
    {"code": "sh601827", "market": "A股股票-新浪", "monitor": "buy"},  # 三峰环境
    {"code": "sh600755", "market": "A股股票-新浪", "monitor": "buy"},  # 厦门国贸
    {"code": "sh600116", "market": "A股股票-新浪", "monitor": "buy"},  # 三峡水利
    {"code": "sh600285", "market": "A股股票-新浪", "monitor": "buy"},  # 羚锐制药
    {"code": "sh600908", "market": "A股股票-新浪", "monitor": "buy"},  # 无锡银行
    {"code": "sz000685", "market": "A股股票-新浪", "monitor": "buy"},  # 中山公用
    {"code": "sh600461", "market": "A股股票-新浪", "monitor": "buy"},  # 洪城环境
    {"code": "sh600639", "market": "A股股票-新浪", "monitor": "buy"},  # 浦东金桥
    {"code": "sh600211", "market": "A股股票-新浪", "monitor": "buy"},  # 西藏药业
    {"code": "sh600572", "market": "A股股票-新浪", "monitor": "buy"},  # 康恩贝
    {"code": "sh605507", "market": "A股股票-新浪", "monitor": "buy"},  # 国邦医药
    {"code": "sz002807", "market": "A股股票-新浪", "monitor": "buy"},  # 江阴银行
    {"code": "sh601200", "market": "A股股票-新浪", "monitor": "buy"},  # 上海环境
    {"code": "sz002053", "market": "A股股票-新浪", "monitor": "buy"},  # 云南能投
    {"code": "sz002839", "market": "A股股票-新浪", "monitor": "buy"},  # 张家港行
    {"code": "sh603323", "market": "A股股票-新浪", "monitor": "buy"},  # 苏农银行
    {"code": "sh601860", "market": "A股股票-新浪", "monitor": "buy"},  # 紫金银行
    {"code": "sh600033", "market": "A股股票-新浪", "monitor": "buy"},  # 福建高速
    {"code": "sz002233", "market": "A股股票-新浪", "monitor": "buy"},  # 塔牌集团
    {"code": "sh600874", "market": "A股股票-新浪", "monitor": "buy"},  # 创业环保
    {"code": "sz002100", "market": "A股股票-新浪", "monitor": "buy"},  # 天康生物
    {"code": "sh605116", "market": "A股股票-新浪", "monitor": "buy"},  # 奥锐特
    {"code": "sh603053", "market": "A股股票-新浪", "monitor": "buy"},  # 成都燃气
    {"code": "sh600054", "market": "A股股票-新浪", "monitor": "buy"},  # 黄山旅游
    {"code": "sz000544", "market": "A股股票-新浪", "monitor": "buy"},  # 中原环保
    {"code": "sh600502", "market": "A股股票-新浪", "monitor": "buy"},  # 安徽建工
    {"code": "sh601089", "market": "A股股票-新浪", "monitor": "buy"},  # 福元医药
    {"code": "sz000650", "market": "A股股票-新浪", "monitor": "buy"},  # 仁和药业
    {"code": "sh603299", "market": "A股股票-新浪", "monitor": "buy"},  # 苏盐井神
    {"code": "sh600987", "market": "A股股票-新浪", "monitor": "buy"},  # 航民股份
    {"code": "sh600035", "market": "A股股票-新浪", "monitor": "buy"},  # 楚天高速
    {"code": "sh605368", "market": "A股股票-新浪", "monitor": "buy"},  # 蓝天燃气
    {"code": "sh603071", "market": "A股股票-新浪", "monitor": "buy"},  # 物产环能
    {"code": "sh603368", "market": "A股股票-新浪", "monitor": "buy"},  # 柳药集团
    {"code": "sh603367", "market": "A股股票-新浪", "monitor": "buy"},  # 辰欣药业
    {"code": "sh600976", "market": "A股股票-新浪", "monitor": "buy"},  # 健民集团
    {"code": "sh600897", "market": "A股股票-新浪", "monitor": "buy"},  # 厦门空港
    {"code": "sz002088", "market": "A股股票-新浪", "monitor": "buy"},  # 鲁阳节能
    {"code": "sh600251", "market": "A股股票-新浪", "monitor": "buy"},  # 冠农股份
    {"code": "sh601065", "market": "A股股票-新浪", "monitor": "buy"},  # 江盐集团
    {"code": "sh603689", "market": "A股股票-新浪", "monitor": "buy"},  # 皖天然气
    {"code": "sh603167", "market": "A股股票-新浪", "monitor": "buy"},  # 渤海轮渡
    {"code": "sh600573", "market": "A股股票-新浪", "monitor": "buy"},  # 惠泉啤酒

    # 7.通达信-120标准差小3.5   共103个，未筛选与前面面重复的，懒得选了
    {"code": "sh600941", "market": "A股股票-新浪", "monitor": "buy"},  # 中国移动
    {"code": "sh601318", "market": "A股股票-新浪", "monitor": "buy"},  # 中国平安
    {"code": "sh600900", "market": "A股股票-新浪", "monitor": "buy"},  # 长江电力
    {"code": "sz000333", "market": "A股股票-新浪", "monitor": "buy"},  # 美的集团
    {"code": "sh601328", "market": "A股股票-新浪", "monitor": "buy"},  # 交通银行
    {"code": "sh601658", "market": "A股股票-新浪", "monitor": "buy"},  # 邮储银行
    {"code": "sh601818", "market": "A股股票-新浪", "monitor": "buy"},  # 光大银行
    {"code": "sz000001", "market": "A股股票-新浪", "monitor": "buy"},  # 平安银行
    {"code": "sh601985", "market": "A股股票-新浪", "monitor": "buy"},  # 中国核电
    {"code": "sh600887", "market": "A股股票-新浪", "monitor": "buy"},  # 伊利股份
    {"code": "sh600016", "market": "A股股票-新浪", "monitor": "buy"},  # 民生银行
    {"code": "sz002142", "market": "A股股票-新浪", "monitor": "buy"},  # 宁波银行
    {"code": "sh600018", "market": "A股股票-新浪", "monitor": "buy"},  # 上港集团
    {"code": "sh601006", "market": "A股股票-新浪", "monitor": "buy"},  # 大秦铁路
    {"code": "sh601169", "market": "A股股票-新浪", "monitor": "buy"},  # 北京银行
    {"code": "sh600585", "market": "A股股票-新浪", "monitor": "buy"},  # 海螺水泥
    {"code": "sz000776", "market": "A股股票-新浪", "monitor": "buy"},  # 广发证券
    {"code": "sh600905", "market": "A股股票-新浪", "monitor": "buy"},  # 三峡能源
    {"code": "sh600015", "market": "A股股票-新浪", "monitor": "buy"},  # 华夏银行
    {"code": "sh601009", "market": "A股股票-新浪", "monitor": "buy"},  # 南京银行
    {"code": "sh600346", "market": "A股股票-新浪", "monitor": "buy"},  # 恒力石化
    {"code": "sh600926", "market": "A股股票-新浪", "monitor": "buy"},  # 杭州银行
    {"code": "sz000538", "market": "A股股票-新浪", "monitor": "buy"},  # 云南白药
    {"code": "sh603195", "market": "A股股票-新浪", "monitor": "buy"},  # 公牛集团
    {"code": "sh601868", "market": "A股股票-新浪", "monitor": "buy"},  # 中国能建
    {"code": "sh601825", "market": "A股股票-新浪", "monitor": "buy"},  # 沪农商行
    {"code": "sh601916", "market": "A股股票-新浪", "monitor": "buy"},  # 浙商银行
    {"code": "sz000895", "market": "A股股票-新浪", "monitor": "buy"},  # 双汇发展
    {"code": "sz000792", "market": "A股股票-新浪", "monitor": "buy"},  # 盐湖股份
    {"code": "sh600362", "market": "A股股票-新浪", "monitor": "buy"},  # 江西铜业
    {"code": "sh600023", "market": "A股股票-新浪", "monitor": "buy"},  # 浙能电力
    {"code": "sz002001", "market": "A股股票-新浪", "monitor": "buy"},  # 新和成
    {"code": "sh600803", "market": "A股股票-新浪", "monitor": "buy"},  # 新奥股份
    {"code": "sz002028", "market": "A股股票-新浪", "monitor": "buy"},  # 思源电气
    {"code": "sh600875", "market": "A股股票-新浪", "monitor": "buy"},  # 东方电气
    {"code": "sz000999", "market": "A股股票-新浪", "monitor": "buy"},  # 华润三九
    {"code": "sz000786", "market": "A股股票-新浪", "monitor": "buy"},  # 北新建材
    {"code": "sh600642", "market": "A股股票-新浪", "monitor": "buy"},  # 申能股份
    {"code": "sz002078", "market": "A股股票-新浪", "monitor": "buy"},  # 太阳纸业
    {"code": "sz002966", "market": "A股股票-新浪", "monitor": "buy"},  # 苏州银行
    {"code": "sz002223", "market": "A股股票-新浪", "monitor": "buy"},  # 鱼跃医疗
    {"code": "sh601598", "market": "A股股票-新浪", "monitor": "buy"},  # 中国外运
    {"code": "sh600925", "market": "A股股票-新浪", "monitor": "buy"},  # 苏能股份
    {"code": "sh600685", "market": "A股股票-新浪", "monitor": "buy"},  # 中船防务
    {"code": "sz001286", "market": "A股股票-新浪", "monitor": "buy"},  # 陕西能源
    {"code": "sh601958", "market": "A股股票-新浪", "monitor": "buy"},  # 金钥股份
    {"code": "sz000513", "market": "A股股票-新浪", "monitor": "buy"},  # 丽珠集团
    {"code": "sh600298", "market": "A股股票-新浪", "monitor": "buy"},  # 安琪酵母
    {"code": "sh600995", "market": "A股股票-新浪", "monitor": "buy"},  # XD南网储
    {"code": "sz000027", "market": "A股股票-新浪", "monitor": "buy"},  # 深圳能源
    {"code": "sz000883", "market": "A股股票-新浪", "monitor": "buy"},  # 湖北能源
    {"code": "sz002007", "market": "A股股票-新浪", "monitor": "buy"},  # 华兰生物
    {"code": "sz002608", "market": "A股股票-新浪", "monitor": "buy"},  # 江苏国信
    {"code": "sh600329", "market": "A股股票-新浪", "monitor": "buy"},  # 达仁堂
    {"code": "sh601158", "market": "A股股票-新浪", "monitor": "buy"},  # 重庆水务
    {"code": "sh600008", "market": "A股股票-新浪", "monitor": "buy"},  # 首创环保
    {"code": "sh600098", "market": "A股股票-新浪", "monitor": "buy"},  # 广州发展
    {"code": "sz000539", "market": "A股股票-新浪", "monitor": "buy"},  # 粤电力A
    {"code": "sh601997", "market": "A股股票-新浪", "monitor": "buy"},  # 贵阳银行
    {"code": "sz000703", "market": "A股股票-新浪", "monitor": "buy"},  # 厦逸石化
    {"code": "sz000875", "market": "A股股票-新浪", "monitor": "buy"},  # 吉电股份
    {"code": "sz002372", "market": "A股股票-新浪", "monitor": "buy"},  # 伟星新材
    {"code": "sz001213", "market": "A股股票-新浪", "monitor": "buy"},  # 中铁特货
    {"code": "sz003035", "market": "A股股票-新浪", "monitor": "buy"},  # 南网能源
    {"code": "sh600648", "market": "A股股票-新浪", "monitor": "buy"},  # 外高桥
    {"code": "sz000089", "market": "A股股票-新浪", "monitor": "buy"},  # 深圳机场
    {"code": "sh600916", "market": "A股股票-新浪", "monitor": "buy"},  # 中国黄金
    {"code": "sh601827", "market": "A股股票-新浪", "monitor": "buy"},  # 三峰环境
    {"code": "sh600755", "market": "A股股票-新浪", "monitor": "buy"},  # 厦门国贸
    {"code": "sh600116", "market": "A股股票-新浪", "monitor": "buy"},  # 三峡水利
    {"code": "sh600908", "market": "A股股票-新浪", "monitor": "buy"},  # 无锡银行
    {"code": "sz000685", "market": "A股股票-新浪", "monitor": "buy"},  # 中山公用
    {"code": "sh600269", "market": "A股股票-新浪", "monitor": "buy"},  # 赣粤高速
    {"code": "sh600639", "market": "A股股票-新浪", "monitor": "buy"},  # 浦东金桥
    {"code": "sh600273", "market": "A股股票-新浪", "monitor": "buy"},  # 嘉化能源
    {"code": "sh600211", "market": "A股股票-新浪", "monitor": "buy"},  # 西藏药业
    {"code": "sh600572", "market": "A股股票-新浪", "monitor": "buy"},  # 康恩贝
    {"code": "sh603132", "market": "A股股票-新浪", "monitor": "buy"},  # 金徽股份
    {"code": "sz002807", "market": "A股股票-新浪", "monitor": "buy"},  # 江阴银行
    {"code": "sh600459", "market": "A股股票-新浪", "monitor": "buy"},  # 贵研铂业
    {"code": "sz002839", "market": "A股股票-新浪", "monitor": "buy"},  # 张家港行
    {"code": "sh601860", "market": "A股股票-新浪", "monitor": "buy"},  # 紫金银行
    {"code": "sz002053", "market": "A股股票-新浪", "monitor": "buy"},  # 云南能投
    {"code": "sh603323", "market": "A股股票-新浪", "monitor": "buy"},  # 苏农银行
    {"code": "sh600033", "market": "A股股票-新浪", "monitor": "buy"},  # 福建高速
    {"code": "sh600874", "market": "A股股票-新浪", "monitor": "buy"},  # 创业环保
    {"code": "sh605116", "market": "A股股票-新浪", "monitor": "buy"},  # 奥锐特
    {"code": "sh603053", "market": "A股股票-新浪", "monitor": "buy"},  # 成都燃气
    {"code": "sz000544", "market": "A股股票-新浪", "monitor": "buy"},  # 中原环保
    {"code": "sh601069", "market": "A股股票-新浪", "monitor": "buy"},  # 福元医药
    {"code": "sh600987", "market": "A股股票-新浪", "monitor": "buy"},  # 航民股份
    {"code": "sh600035", "market": "A股股票-新浪", "monitor": "buy"},  # 楚天高速
    {"code": "sh605368", "market": "A股股票-新浪", "monitor": "buy"},  # 蓝天燃气
    {"code": "sh603071", "market": "A股股票-新浪", "monitor": "buy"},  # 物产环能
    {"code": "sh603367", "market": "A股股票-新浪", "monitor": "buy"},  # 辰欣药业
    {"code": "sh600897", "market": "A股股票-新浪", "monitor": "buy"},  # 厦门空港
    {"code": "sh601065", "market": "A股股票-新浪", "monitor": "buy"},  # 江盐集团
    {"code": "sh601518", "market": "A股股票-新浪", "monitor": "buy"},  # 吉林高速
    {"code": "sh600351", "market": "A股股票-新浪", "monitor": "buy"},  # 亚宝药业
    {"code": "sh603689", "market": "A股股票-新浪", "monitor": "buy"},  # 皖天然气
    {"code": "sh603167", "market": "A股股票-新浪", "monitor": "buy"},  # 渤海轮渡
    {"code": "sh600222", "market": "A股股票-新浪", "monitor": "buy"},  # 太龙药业
    {"code": "sh603755", "market": "A股股票-新浪", "monitor": "buy"},   # 日辰股份

    # 99.同花顺-持仓股
    {"code": "sz000999", "market": "A股股票-新浪", "monitor": "buy"},  # 华润三九   持有
    {"code": "sz002818", "market": "A股股票-新浪", "monitor": "buy"},  # 富森美     持有
    {"code": "sz000975", "market": "A股股票-新浪", "monitor": "buy"},  # 山金国际   持有
    {"code": "sz000564", "market": "A股股票-新浪", "monitor": "buy"},  # 供销大集   持有
    {"code": "sh600489", "market": "A股股票-新浪", "monitor": "buy"},  # 中金黄金   持有
    {"code": "sz002739", "market": "A股股票-新浪", "monitor": "buy"},  # 万达电影   持有
    {"code": "sz002042", "market": "A股股票-新浪", "monitor": "buy"},  # 华孚时尚   已割肉,待上穿接回来
    {"code": "sz002262", "market": "A股股票-新浪", "monitor": "buy"},  # 恩华药业   持有
    {"code": "sh600233", "market": "A股股票-新浪", "monitor": "buy"},  # 圆通速递   持有
    {"code": "518800", "market": "ETF-东财", "monitor": "buy"},       # 黄金基金   持有
    {"code": "sz000938", "market": "A股股票-新浪", "monitor": "buy"},  # 紫金股份   持有
    {"code": "sh601398", "market": "A股股票-新浪", "monitor": "buy"},  # 工商银行   持有
    {"code": "159865", "market": "ETF-东财", "monitor": "buy"},       # 养殖ETF   持有,跟火哥投
    {"code": "159766", "market": "ETF-东财", "monitor": "buy"},       # 旅游ETF   持有,跟火哥投
    {"code": "sh600233", "market": "A股股票-新浪", "monitor": "buy"},  # 华兰生物   持有

    # 二.监控卖出信号
    # 同花顺-持仓股
    {"code": "sz000999", "market": "A股股票-新浪", "monitor": "sell"},  # 华润三九   持有,补仓
    {"code": "sz002818", "market": "A股股票-新浪", "monitor": "sell"},  # 富森美     持有,补仓
    {"code": "sz000975", "market": "A股股票-新浪", "monitor": "sell"},  # 山金国际   持有,补仓
    {"code": "sz000564", "market": "A股股票-新浪", "monitor": "sell"},  # 供销大集   持有,补仓
    {"code": "sh600489", "market": "A股股票-新浪", "monitor": "sell"},  # 中金黄金   持有,补仓
    {"code": "sz002739", "market": "A股股票-新浪", "monitor": "sell"},  # 万达电影   持有,补仓
    {"code": "sz002262", "market": "A股股票-新浪", "monitor": "sell"},  # 恩华药业   持有,补仓
    {"code": "sh600233", "market": "A股股票-新浪", "monitor": "sell"},  # 圆通速递   持有,补仓
    {"code": "518800", "market": "ETF-东财", "monitor": "sell"},       # 黄金基金   长期持,上穿补
    {"code": "sz000938", "market": "A股股票-新浪", "monitor": "sell"},  # 紫金股份   持有
    {"code": "sh601398", "market": "A股股票-新浪", "monitor": "sell"},  # 工商银行   长期持,上穿补
    {"code": "159865", "market": "ETF-东财", "monitor": "buy"},        # 养殖ETF   持有,跟火哥投
    {"code": "159766", "market": "ETF-东财", "monitor": "buy"},        # 旅游ETF   持有,跟火哥投
    {"code": "sh600233", "market": "A股股票-新浪", "monitor": "buy"},  # 圆通速递   持有

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
