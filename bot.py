import requests
import time
import re
import json
import os
from countries import COUNTRY_PREFIX

# ================= API =================

API_BASE_URL = "https://abysspanel.mega-host.site"
API_TOKEN = "aOC4ksfPPYuOTXYeX0-wavZX-zpK2mUjXcAquYVwJv4"

HEADERS = {
    "X-API-Token": API_TOKEN,
    "Content-Type": "application/json"
}

# ================= TELEGRAM =================

BOT_TOKEN = "8622446560:AAFgfq2ywHtxN6dPhv5XaxzyXWEHcu0w4N4"
CHAT_ID = "-1003762705250"

BOT_LINK = "https://t.me/dynamo_otp_bot?start=_tgr_GfbtfiI1MzI1"
CHANNEL_LINK = "https://t.me/dynamo_otp"

# ================= DUPLICATE STORAGE =================

CACHE_FILE = "sent_ids.json"

if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r") as f:
        sent_ids = set(json.load(f))
else:
    sent_ids = set()

def save_cache():
    with open(CACHE_FILE, "w") as f:
        json.dump(list(sent_ids), f)

# ================= HELPERS =================

def extract_otp(text):
    m = re.search(r"\b(\d{4,8})\b", text)
    return m.group(1) if m else None


def clean_number(text):
    m = re.search(r"\d{8,15}", text)
    return m.group() if m else text


def mask_number(num):
    if len(num) < 8:
        return num
    return f"{num[:4]}****{num[-4:]}"


def detect_country(number):

    for prefix, flag in COUNTRY_PREFIX.items():

        if number.startswith(prefix):
            return flag

    return "🌍 Unknown"

# ================= SERVICE DETECT =================

SERVICE_ICONS = {
    "facebook": ("Facebook", "🔵"),
    "whatsapp": ("WhatsApp", "🟢"),
    "telegram": ("Telegram", "✈️"),
    "google": ("Google", "🔴"),
    "gmail": ("Google", "🔴"),
    "instagram": ("Instagram", "📸"),
    "tiktok": ("TikTok", "🎵"),
    "wechat": ("WeChat", "💬")
}

def detect_service(cdr, message):

    msg = message.lower()

    for key in SERVICE_ICONS:

        if key in msg:
            name, icon = SERVICE_ICONS[key]
            return f"{icon} {name}"

    if cdr.get("service"):
        return f"📡 {cdr.get('service')}"

    if cdr.get("sms_type"):
        return f"📡 {cdr.get('sms_type')}"

    return "📡 Unknown"

# ================= TELEGRAM =================

def send_telegram(msg):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    keyboard = {
        "inline_keyboard": [
            [
                {"text": "🤖 BOT", "url": BOT_LINK},
                {"text": "📢 CHANNEL", "url": CHANNEL_LINK}
            ]
        ]
    }

    try:

        requests.post(
            url,
            json={
                "chat_id": CHAT_ID,
                "text": msg,
                "parse_mode": "HTML",
                "reply_markup": keyboard
            },
            timeout=10
        )

    except Exception as e:

        print("Telegram Error:", e)

# ================= API FETCH =================

def get_user_messages():

    url = f"{API_BASE_URL}/api/sms/cdr"

    try:

        r = requests.get(url, headers=HEADERS, timeout=15)

        if r.status_code != 200:

            print("API ERROR:", r.status_code)
            print(r.text[:200])

            return []

        data = r.json()

        return data.get("results", [])

    except Exception as e:

        print("Fetch error:", e)

        return []

# ================= BOT LOOP =================

print("🚀 ABYSS OTP BOT STARTED")

while True:

    try:

        messages = get_user_messages()

        for cdr in messages:

            cid = str(cdr.get("id"))

            if cid in sent_ids:
                continue

            msg = cdr.get("message", "")

            raw_number = cdr.get("caller_id") or cdr.get("destination") or ""

            number = clean_number(raw_number)

            masked = mask_number(number)

            country = detect_country(number)

            otp = extract_otp(msg)

            if not otp:
                continue

            service = detect_service(cdr, msg)

            text = f"""
<b>🔐 OTP RECEIVED</b>

🌍 <b>Country :</b> {country}
📱 <b>Number :</b> {masked}
📡 <b>Service :</b> {service}

🔑 <b>OTP :</b> <code>{otp}</code>

💬 <b>Message</b>
<code>{msg}</code>
"""

            print("NEW OTP:", otp)

            send_telegram(text)

            sent_ids.add(cid)

            save_cache()

        time.sleep(2)

    except KeyboardInterrupt:

        print("Bot stopped")
        break

    except Exception as e:

        print("Loop Error:", e)
        time.sleep(5)
