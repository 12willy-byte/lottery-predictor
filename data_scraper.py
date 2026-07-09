import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# 多个 User-Agent 轮换，降低被封风险
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
]

DLT_URL = "https://datachart.500.com/dlt/history/newinc/history.php?limit=3000&sort=0"
SSQ_URL = "https://datachart.500.com/ssq/history/newinc/history.php?limit=3500&sort=0"

MAX_RETRIES = 3
RETRY_DELAY = 2  # 秒


def _get_headers():
    """轮换 User-Agent 获取请求头"""
    import random
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }


def _fetch_with_retry(url, timeout=30):
    """带重试的 HTTP 请求"""
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.get(url, headers=_get_headers(), timeout=timeout)
            r.raise_for_status()
            r.encoding = "utf-8"
            return r
        except requests.exceptions.Timeout:
            last_error = f"超时(attempt {attempt})"
            print(f"    请求超时，第{attempt}次重试...")
        except requests.exceptions.ConnectionError as e:
            last_error = f"连接错误(attempt {attempt}): {e}"
            print(f"    连接失败，第{attempt}次重试...")
        except requests.exceptions.HTTPError as e:
            sc = e.response.status_code if hasattr(e, "response") else "?"
            last_error = f"HTTP错误(attempt {attempt}): {e}"
            print(f"    HTTP错误 {sc}，第{attempt}次重试...")
        except Exception as e:
            last_error = f"未知错误(attempt {attempt}): {e}"
            print(f"    请求异常，第{attempt}次重试...")
        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY * attempt)  # 递增延迟
    raise Exception(last_error)


def fetch_ssq():
    """从500.com获取双色球全部历史数据 (2003年至今)"""
    results = []
    try:
        print("  双色球: 正在请求数据...")
        r = _fetch_with_retry(SSQ_URL)
        soup = BeautifulSoup(r.text, "html.parser")
        rows = soup.find_all("tr")
        total_rows = len(rows)
        print(f"  双色球: 解析 {total_rows} 行...")
        for tr in rows:
            tds = tr.find_all("td")
            if len(tds) == 16:
                try:
                    texts = [td.get_text(strip=True) for td in tds]
                    reds = sorted([int(texts[1]), int(texts[2]), int(texts[3]),
                                   int(texts[4]), int(texts[5]), int(texts[6])])
                    results.append({
                        "period": texts[0],
                        "red1": reds[0], "red2": reds[1], "red3": reds[2],
                        "red4": reds[3], "red5": reds[4], "red6": reds[5],
                        "blue": int(texts[7]),
                        "date": texts[15] if len(texts) > 15 else ""
                    })
                except (ValueError, IndexError):
                    continue  # 跳过表头或非数据行
        if results:
            print(f"  双色球: 获取 {len(results)} 条 ({results[-1]['period']} ~ {results[0]['period']})")
        else:
            print("  双色球: 未获取到数据（网站结构可能已变化）")
    except Exception as e:
        print(f"  双色球抓取失败: {e}")
    return results


def fetch_dlt():
    """从500.com获取大乐透全部历史数据 (2007年至今)"""
    results = []
    try:
        print("  大乐透: 正在请求数据...")
        r = _fetch_with_retry(DLT_URL)
        soup = BeautifulSoup(r.text, "html.parser")
        rows = soup.find_all("tr")
        total_rows = len(rows)
        print(f"  大乐透: 解析 {total_rows} 行...")
        for tr in rows:
            tds = tr.find_all("td")
            if len(tds) == 15:
                try:
                    texts = [td.get_text(strip=True) for td in tds]
                    fronts = sorted([int(texts[1]), int(texts[2]), int(texts[3]),
                                     int(texts[4]), int(texts[5])])
                    backs = sorted([int(texts[6]), int(texts[7])])
                    results.append({
                        "period": texts[0],
                        "front1": fronts[0], "front2": fronts[1], "front3": fronts[2],
                        "front4": fronts[3], "front5": fronts[4],
                        "back1": backs[0], "back2": backs[1],
                        "date": texts[14] if len(texts) > 14 else ""
                    })
                except (ValueError, IndexError):
                    continue
        if results:
            print(f"  大乐透: 获取 {len(results)} 条 ({results[-1]['period']} ~ {results[0]['period']})")
        else:
            print("  大乐透: 未获取到数据（网站结构可能已变化）")
    except Exception as e:
        print(f"  大乐透抓取失败: {e}")
    return results


def update_all(callback=None):
    """更新所有数据，支持进度回调 callback(step, status, message)"""
    from database import save_ssq_data, save_dlt_data, log_update, init_db, get_ssq_count, get_dlt_count
    init_db()
    print("=" * 50)

    if callback:
        callback("ssq", "fetching", "正在获取双色球数据...")
    print("正在更新双色球数据...")
    try:
        ssq = fetch_ssq()
        if ssq:
            if callback:
                callback("ssq", "saving", f"保存 {len(ssq)} 条双色球数据...")
            c = save_ssq_data(ssq)
            log_update("ssq", "success", "%d new" % c)
            print(f"  双色球: 新增 {c} 条, 共 {get_ssq_count()} 条")
            if callback:
                callback("ssq", "done", f"双色球完成: 新增{c}条, 共{get_ssq_count()}条")
        else:
            print("  双色球: 暂无新数据")
            if callback:
                callback("ssq", "done", "双色球: 暂无新数据")
    except Exception as e:
        print(f"  双色球更新失败: {e}")
        log_update("ssq", "failed", str(e))
        if callback:
            callback("ssq", "failed", str(e))

    print()
    if callback:
        callback("dlt", "fetching", "正在获取大乐透数据...")
    print("正在更新大乐透数据...")
    try:
        dlt = fetch_dlt()
        if dlt:
            if callback:
                callback("dlt", "saving", f"保存 {len(dlt)} 条大乐透数据...")
            c = save_dlt_data(dlt)
            log_update("dlt", "success", "%d new" % c)
            print(f"  大乐透: 新增 {c} 条, 共 {get_dlt_count()} 条")
            if callback:
                callback("dlt", "done", f"大乐透完成: 新增{c}条, 共{get_dlt_count()}条")
        else:
            print("  大乐透: 暂无新数据")
            if callback:
                callback("dlt", "done", "大乐透: 暂无新数据")
    except Exception as e:
        print(f"  大乐透更新失败: {e}")
        log_update("dlt", "failed", str(e))
        if callback:
            callback("dlt", "failed", str(e))

    print("=" * 50)
    print("更新完成!")
    s_count = get_ssq_count()
    d_count = get_dlt_count()
    print(f"双色球: {s_count} 条 | 大乐透: {d_count} 条")
    if callback:
        callback("all", "done", f"全部完成: SSQ {s_count}期, DLT {d_count}期")


if __name__ == "__main__":
    update_all()
