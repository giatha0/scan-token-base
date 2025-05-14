import os
import requests
from datetime import datetime, timezone
from decimal import Decimal
import time

API_KEY = os.getenv("API_KEY")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
START_TIME = os.getenv("START_TIME")
END_TIME = os.getenv("END_TIME")
MIN_TOKEN_AMOUNT = Decimal(os.getenv("MIN_TOKEN_AMOUNT", "0"))  # default = 0 nếu không đặt

BASESCAN_API = "https://api.basescan.org/api"

def to_timestamp(dt_str):
    return int(datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").timestamp())

def get_token_transactions(contract_address, start_ts, end_ts):
    page = 1
    offset = 1000
    all_txs = []

    while True:
        url = (
            f"{BASESCAN_API}?module=account&action=tokentx"
            f"&contractaddress={contract_address}"
            f"&page={page}&offset={offset}&sort=asc&apikey={API_KEY}"
        )
        try:
            res = requests.get(url)
            data = res.json()
        except Exception as e:
            print("❌ Lỗi kết nối API:", str(e))
            break

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
            elif ts >= end_ts:
                return all_txs
            else:
                try:
                    token_value = Decimal(tx["value"]) / Decimal(f'1e{tx["tokenDecimal"]}')
                    if token_value >= MIN_TOKEN_AMOUNT:
                        all_txs.append(tx)
                except:
                    continue  # bỏ qua nếu lỗi chuyển đổi

        if len(txs) < offset:
            break
        page += 1
        time.sleep(0.25)

    return all_txs

def get_transactions_by_minute(contract_address, start_ts, end_ts):
    tx_count = {}
    minute_ts = start_ts

    while minute_ts < end_ts:
        next_minute_ts = minute_ts + 60
        print(f"📦 {datetime.fromtimestamp(minute_ts, timezone.utc)} → {datetime.fromtimestamp(next_minute_ts, timezone.utc)}")

        txs = get_token_transactions(contract_address, minute_ts, next_minute_ts)
        tx_count[datetime.fromtimestamp(minute_ts, timezone.utc)] = len(txs)

        minute_ts = next_minute_ts
        time.sleep(0.25)

    return tx_count

def main():
    if not (START_TIME and END_TIME and API_KEY and CONTRACT_ADDRESS):
        print("❌ Thiếu biến môi trường. Cần: START_TIME, END_TIME, API_KEY, CONTRACT_ADDRESS")
        return

    try:
        start_ts = to_timestamp(START_TIME)
        end_ts = to_timestamp(END_TIME)
    except:
        print("❌ Sai định dạng thời gian. Định dạng đúng: YYYY-MM-DD HH:MM:SS")
        return

    print(f"📅 Khoảng thời gian: {START_TIME} → {END_TIME}")
    print(f"⚙️ Lọc giao dịch có token ≥ {MIN_TOKEN_AMOUNT}")

    tx_count = get_transactions_by_minute(CONTRACT_ADDRESS, start_ts, end_ts)

    print(f"✅ Tổng số phút: {len(tx_count)}")
    print("📊 Giao dịch mỗi phút:")
    for minute, count in tx_count.items():
        print(f"{minute.strftime('%Y-%m-%d %H:%M')} => {count} txs")

if __name__ == "__main__":
    main()