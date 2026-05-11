"""
Script gửi lệnh /syncchat đến các nhóm Telegram từ file Test_Syncchat.xlsx
Sử dụng Telegram Bot API trực tiếp (aiohttp) để tránh lỗi Peer ID của Pyrogram
"""
import asyncio
import json
import sys
import io
import openpyxl
import aiohttp

# Fix Unicode output trên Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BOT_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


def load_config() -> dict:
    """Đọc config từ appsettings.json"""
    with open("appsettings.json", "r", encoding="utf-8") as f:
        return json.load(f)


def load_chat_ids(file_path: str = "Test_Syncchat.xlsx") -> list[dict]:
    """Đọc danh sách chat_id từ file Excel"""
    wb = openpyxl.load_workbook(file_path)
    ws = wb.active

    groups = []
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, values_only=True):
        stt, diem_thu_mua, ten_kh, ma_ho, chat_id = row
        if chat_id is not None:
            groups.append({
                "stt": int(stt),
                "diem_thu_mua": diem_thu_mua,
                "ten_kh": ten_kh,
                "ma_ho": ma_ho,
                "chat_id": int(chat_id),
            })
    return groups


async def main():
    config = load_config()
    bot_token = config["Telegram"]["Bot_Token"]
    url = BOT_API_URL.format(token=bot_token)

    groups = load_chat_ids()

    print(f"=== Tìm thấy {len(groups)} nhóm từ file Excel ===")
    for g in groups:
        print(f"   - [{g['ma_ho']}] {g['ten_kh']} | Chat ID: {g['chat_id']}")
    print()

    async with aiohttp.ClientSession() as session:
        for group in groups:
            chat_id = group["chat_id"]
            ten_kh = group["ten_kh"]
            ma_ho = group["ma_ho"]
            try:
                async with session.post(url, json={
                    "chat_id": chat_id,
                    "text": "/syncchat"
                }) as resp:
                    result = await resp.json()
                    if result.get("ok"):
                        print(f"✅ Đã gửi /syncchat đến nhóm [{ma_ho}] {ten_kh} (chat_id: {chat_id})")
                    else:
                        print(f"❌ Lỗi từ API [{ma_ho}] {ten_kh} (chat_id: {chat_id}): {result.get('description')}")
            except Exception as e:
                print(f"❌ Lỗi khi gửi đến nhóm [{ma_ho}] {ten_kh} (chat_id: {chat_id}): {e}")

            # Delay giữa các tin nhắn để tránh rate limit
            await asyncio.sleep(0.5)

    print("\n🎉 Hoàn tất!")


if __name__ == "__main__":
    asyncio.run(main())
