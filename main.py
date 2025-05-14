import os
import requests
from datetime import datetime
from collections import defaultdict
import time

API_KEY = os.getenv("API_KEY")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
START_TIME = os.getenv("START_TIME")
END_TIME = os.getenv("END_TIME")

BASESCAN_API = "https://api.basescan.org/api"

def to_timestamp(dt_str):
    return int(datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").timestamp())

def get_token_transactions(contract_address, start_ts, end_ts):
    page = 1
    offset = 1000
    all_txs = []

    print(f"🔍 Đang lấy dữ liệu giao dịch từ {start_ts} → {end_ts}...")

    while True:
        url = f"{BASESCAN_API}?module=account&action=tokentx&contractaddress={contract_address}&page={page}&offset={offset}&sort=asc&apikey={API_KEY}"
        res = requests.get(url)
        data = res.json()

        if data["status"] != "1":
            print("❌ API lỗi:", data.get("message", "Unknown"))
            break

        txs = data["result"]
        if not txs:
            break

        for tx in txs:
            ts = int(tx["timeStamp"])
            if ts < start_ts:
                continue
            elif ts > end_ts:
                return all_txs
            else:
                all_txs.append(tx)

        if len(txs) < offset:
            break
        page += 1
        time.sleep(0.25)

    return all_txs

def group_by_minute(txs):
    tx_count = defaultdict(int)
    for tx in txs:
        dt = datetime.fromtimestamp(int(tx["timeStamp"]))
        dt_key = dt.replace(second=0, microsecond=0)
        tx_count[dt_key] += 1
    return tx_count

def main():
    if not (START_TIME and END_TIME and API_KEY and CONTRACT_ADDRESS):
        print("❌ Thiếu biến môi trường. Hãy kiểm tra lại START_TIME, END_TIME, API_KEY, CONTRACT_ADDRESS")
        return

    try:
        start_ts = to_timestamp(START_TIME)
        end_ts = to_timestamp(END_TIME)
    except:
        print("❌ Lỗi định dạng thời gian. Định dạng đúng: YYYY-MM-DD HH:MM:SS")
        return

    print(f"📅 Khoảng thời gian: {START_TIME} → {END_TIME}")
    txs = get_token_transactions(CONTRACT_ADDRESS, start_ts, end_ts)
    print(f"✅ Tổng số giao dịch: {len(txs)}")

    grouped = group_by_minute(txs)
    print("📊 Giao dịch theo phút:")
    for minute in sorted(grouped):
        print(f"{minute.strftime('%Y-%m-%d %H:%M')} => {grouped[minute]} txs")

if __name__ == "__main__":
    main()