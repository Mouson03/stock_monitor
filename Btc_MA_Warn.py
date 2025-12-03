#此代码是通过币安API接口获取btc的行情数据，进行均线策略预警（跌破或突破均线时钉钉提醒）
#此代码放在github actions上，每日定时运行

import requests
from datetime import datetime, timedelta


def get_btc_365days_close_prices():
    """
    使用Binance.US API获取BTC最近365天的每日收盘价

    优点:
    - 完全免费，无需API key
    - 适用于美国IP（GitHub Actions）

    返回:
    - 包含日期和收盘价的列表
    """

    # Binance.US API端点
    url = "https://api.binance.us/api/v3/klines"

    # 计算时间范围（最近365天）
    end_time = int(datetime.now().timestamp() * 1000)
    start_time = int((datetime.now() - timedelta(days=365)).timestamp() * 1000)

    # 请求参数
    params = {
        'symbol': 'BTCUSDT',  # 交易对
        'interval': '1d',  # 时间间隔：1天
        'startTime': start_time,  # 开始时间（毫秒）
        'endTime': end_time,  # 结束时间（毫秒）
        'limit': 1000  # 最多返回1000条（足够365天）
    }

    print("正在从 Binance.US 获取数据...")
    print(
        f"请求时间范围: {datetime.fromtimestamp(start_time / 1000).strftime('%Y-%m-%d')} 至 {datetime.fromtimestamp(end_time / 1000).strftime('%Y-%m-%d')}")
    print()

    try:
        # 发送请求
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()  # 检查HTTP错误

        # 解析数据
        klines = response.json()

        # 提取日期和收盘价
        # Binance K线数据格式：
        # [开盘时间, 开盘价, 最高价, 最低价, 收盘价, 成交量,
        #  收盘时间, 成交额, 成交笔数, 主动买入成交量, 主动买入成交额, 忽略]

        results = []
        for kline in klines:
            timestamp = kline[0]  # 开盘时间戳（毫秒）
            close_price = float(kline[4])  # 收盘价
            date = datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d')

            results.append({
                'date': date,
                'close_price': close_price
            })

        print(f"✅ 成功获取 {len(results)} 天的数据")
        print()

        return results

    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP错误: {e}")
        print(f"   状态码: {e.response.status_code}")
        print(f"   响应: {e.response.text}")
        return None

    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求失败: {e}")
        return None

    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return None


# 主程序
if __name__ == "__main__":
    print("=" * 60)
    print("  BTC 最近365天收盘价获取程序")
    print("  数据源: Binance.US (无需API key)")
    print("=" * 60)
    print()

    # 获取数据
    data = get_btc_365days_close_prices()

    if data:
        # 显示统计信息
        prices = [item['close_price'] for item in data]
        print("📊 数据统计:")
        print(f"   总天数: {len(data)} 天")
        print(f"   日期范围: {data[0]['date']} 至 {data[-1]['date']}")
        print(f"   最高价: ${max(prices):,.2f}")
        print(f"   最低价: ${min(prices):,.2f}")
        print(f"   最新收盘价: ${data[-1]['close_price']:,.2f}")
        print()

        # 显示最近10天的数据
        print("📅 最近10天的收盘价:")
        print("-" * 60)
        print(f"{'日期':<12} {'收盘价':>15}")
        print("-" * 60)

        for item in data[-10:]:
            print(f"{item['date']:<12} ${item['close_price']:>14,.2f}")

        print("-" * 60)
        print()

        # 保存到CSV（可选）
        try:
            import csv

            with open('btc_365days.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['date', 'close_price'])
                writer.writeheader()
                writer.writerows(data)

            print("💾 数据已保存到: btc_365days.csv")
        except Exception as e:
            print(f"⚠️  保存CSV失败: {e}")

    else:
        print("❌ 数据获取失败")

    print()
    print("=" * 60)
    print("  程序运行完成")
    print("=" * 60)
