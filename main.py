import os
import telebot
import requests
import threading
import time
import json
from flask import Flask
from telebot import types

# ----------------------------------------------------
# ১. Render Port Binding ও Keep-Alive সার্ভার
# ----------------------------------------------------
app = Flask(__name__)
RENDER_URL = "https://hototp-bot-3.onrender.com"

@app.route('/')
def home():
    return "HotOtp GetPaid Style Active!", 200

def run_web():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_web, daemon=True).start()

def keep_alive_pinger():
    while True:
        time.sleep(300)
        try: requests.get(RENDER_URL, timeout=10)
        except: pass

threading.Thread(target=keep_alive_pinger, daemon=True).start()

# ----------------------------------------------------
# ২. বটের মূল তথ্য ও কনফিগারেশন
# ----------------------------------------------------
BOT_TOKEN = "8810955739:AAFEWvtxNCKFZXpPgv88zKdX-kJmoALnNis"  # আপনার আসল টেলিগ্রাম বট টোকেন
NEXA_API_KEY = "nxa_eb3fc88e55f657d69cd3c4aca3b69cce416dc84e" # আপনার NexaOTP এপিআই কি

BOT_USERNAME = "hot_opt_bot"              # বটের ইউজারনেম
OTP_GROUP = "@hototpotp"                 # ওটিপি আপডেট গ্রুপ
RANGE_GROUP = "@hototprange"             # লাইভ রেঞ্জ চ্যানেল

bot = telebot.TeleBot(BOT_TOKEN)

# ডাটাবেজ ফাইল
DATA_FILE = "user_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except: pass
    return {"users": [], "balances": {}, "ranges": {}, "total_otps": 0}

def save_data():
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(db, f)
    except: pass

db = load_data()
posted_signatures = set()

# ----------------------------------------------------
# ৩. টেলিগ্রাম পপ-আপ মেনু কমান্ডস
# ----------------------------------------------------
try:
    bot_commands = [
        types.BotCommand("start", "🚀 Start"),
        types.BotCommand("home", "🏠 Home"),
        types.BotCommand("number", "☎️ Get Number"),
        types.BotCommand("range", "⚙️ Change Range"),
        types.BotCommand("tempmail", "✉️ Get Tempmail"),
        types.BotCommand("twofa", "🔐 2FA"),
        types.BotCommand("balances", "💰 Balances"),
        types.BotCommand("withdraw", "💸 Withdraw"),
        types.BotCommand("history", "📜 Withdraw History"),
        types.BotCommand("help", "💬 Support"),
        types.BotCommand("other", "🔽 OTHER")
    ]
    bot.set_my_commands(bot_commands)
except Exception as e:
    print(f"Commands set error: {e}")

# ----------------------------------------------------
# ৪. স্থায়ী নিচের কিবোর্ড বাটন (Change Range ও Range Group সহ)
# ----------------------------------------------------
def bottom_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("☎️ Get Number"), types.KeyboardButton("⚙️ Change Range"))
    markup.add(types.KeyboardButton("📱 Range Group"), types.KeyboardButton("✉️ Get Tempmail"))
    markup.add(types.KeyboardButton("🔐 2FA"), types.KeyboardButton("👤 Fake Name"))
    markup.add(types.KeyboardButton("🔽 OTHER"))
    return markup

def bottom_other_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("💰 Balances"), types.KeyboardButton("💸 Withdraw"))
    markup.add(types.KeyboardButton("💬 Support"), types.KeyboardButton("🏠 Home"))
    return markup

print("---------------------------------")
print("🔥 HotOtp Complete Panel Active!")
print("---------------------------------")

# ----------------------------------------------------
# ৫. সাইটের কনসোল লাইভ অটো-পোস্টার
# ----------------------------------------------------
def fetch_all_site_logs():
    headers = {"X-API-Key": NEXA_API_KEY}
    all_items = []
    endpoints = [
        "https://nexaotpservice.com/api/v1/console/logs?limit=30",
        "https://nexaotpservice.com/api/v1/console/logs/engine2?limit=30",
        "https://nexaotpservice.com/api/v1/console/logs/engine3?limit=30",
        "https://nexaotpservice.com/api/v1/sms/recent?limit=30"
    ]
    for ep in endpoints:
        try:
            r = requests.get(ep, headers=headers, timeout=5).json()
            items = []
            if isinstance(r, list): items = r
            elif isinstance(r, dict): items = r.get("logs") or r.get("data") or r.get("recent") or []
            if isinstance(items, list): all_items.extend(items)
        except Exception: pass
    return all_items

def auto_post_live_ranges():
    while True:
        try:
            logs = fetch_all_site_logs()
            if isinstance(logs, list) and len(logs) > 0:
                for item in logs:
                    if not isinstance(item, dict): continue
                    number = str(item.get("number") or item.get("range") or "").strip()
                    country = str(item.get("country") or "Global").strip()
                    service = str(item.get("service") or "OTP Service").strip()
                    sms_preview = str(item.get("sms") or item.get("text") or item.get("message") or "").strip()
                    time_id = str(item.get("id") or item.get("number_id") or item.get("time") or "")

                    if not number or len(number) < 4: continue
                    sig = f"{number}_{service}_{country}_{sms_preview[:15]}_{time_id}"
                    if sig in posted_signatures: continue
                    posted_signatures.add(sig)
                    if len(posted_signatures) > 1500: posted_signatures.clear()

                    raw_num = number.replace("+", "").strip()
                    if "XXX" in raw_num: range_str = raw_num
                    elif len(raw_num) > 8: range_str = raw_num[:8] + "XXX"
                    elif len(raw_num) > 5: range_str = raw_num[:5] + "XXX"
                    else: range_str = raw_num + "XXX"

                    msg_text_display = f"`{sms_preview}`" if sms_preview else "Live Signal Received ⭐"

                    post_text = (
                        f"🔥 **HOT OTP LIVE CONSOLE** 🔥\n\n"
                        f"📱 **Range:** `{range_str}`\n"
                        f"🎯 **Service:** {service}\n"
                        f"🌐 **Country:** {country}\n"
                        f"💬 **SMS:** {msg_text_display}\n\n"
                        f"👇 **১-ক্লিকে এই রেঞ্জ দিয়ে নাম্বার নিতে নিচে চাপ দিন:**"
                    )

                    markup = types.InlineKeyboardMarkup()
                    btn_bot = types.InlineKeyboardButton("🤖 HotOtp Bot-এ এই নাম্বার নিন", url=f"https://t.me/{BOT_USERNAME}?start={range_str}")
                    markup.add(btn_bot)

                    try:
                        bot.send_message(RANGE_GROUP, post_text, reply_markup=markup, parse_mode="Markdown")
                        time.sleep(3)
                    except telebot.apihelper.ApiTelegramException as te:
                        if te.error_code == 429: time.sleep(20)
                    except Exception: time.sleep(3)
        except Exception as e: print(f"Loop error: {e}")
        time.sleep(8)

threading.Thread(target=auto_post_live_ranges, daemon=True).start()

# ----------------------------------------------------
# ৬. ওটিপি ফিল্টার
# ----------------------------------------------------
def fetch_otp(num_id, number):
    headers = {"X-API-Key": NEXA_API_KEY}
    try:
        url1 = f"https://nexaotpservice.com/api/v1/numbers/{num_id}/sms"
        res1 = requests.get(url1, headers=headers, timeout=5).json()
        if res1.get("success"):
            code = res1.get("code") or res1.get("otp") or res1.get("sms_code")
            sms = res1.get("sms") or res1.get("message") or res1.get("text") or ""
            if code and "******" not in str(code): return f"🔢 **OTP Code:** `{code}`\n\n📩 **Full SMS:** `{sms}`"
            if sms and "******" not in str(sms): return f"📩 **SMS:** `{sms}`"
    except Exception: pass

    try:
        logs = fetch_all_site_logs()
        for item in logs:
            if isinstance(item, dict):
                if item.get("number") == number or item.get("number_id") == num_id:
                    sms = item.get("sms") or item.get("text") or item.get("message") or ""
                    code = item.get("code") or item.get("otp") or ""
                    if code and "******" not in str(code): return f"🔢 **OTP Code:** `{code}`\n\n📩 **SMS:** `{sms}`"
                    if sms and "******" not in str(sms): return f"📩 **SMS:** `{sms}`"
    except Exception: pass
    return None

def auto_check_otp(chat_id, num_id, number):
    for _ in range(60):
        time.sleep(3)
        otp = fetch_otp(num_id, number)
        if otp:
            db["total_otps"] = db.get("total_otps", 0) + 1
            save_data()
            bot.send_message(chat_id, f"🎉 **ওটিপি চলে এসেছে!**\n\n{otp}", parse_mode="Markdown")
            return

# ----------------------------------------------------
# ৭. বট মেসেজ হ্যান্ডলারস
# ----------------------------------------------------
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    chat_str = str(chat_id)
    bot.clear_step_handler_by_chat_id(chat_id)

    if chat_id not in db["users"]:
        db["users"].append(chat_id)
        if chat_str not in db["balances"]: db["balances"][chat_str] = 20.0
        save_data()

    args = message.text.split()
    if len(args) > 1:
        deep_range = args[1].strip()
        db["ranges"][chat_str] = deep_range
        save_data()
        bot.send_message(chat_id, f"✅ **চ্যানেল থেকে রেঞ্জ সিলেক্ট হয়েছে:** `{deep_range}`", reply_markup=bottom_main_keyboard(), parse_mode="Markdown")
        fetch_and_send_number(chat_id, deep_range)
        return

    db["ranges"].pop(chat_str, None)
    save_data()
    bot.send_message(chat_id, "👋 **Welcome back to HotOtp Bot**", reply_markup=bottom_main_keyboard(), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "☎️ Get Number" or m.text == "/number")
def get_number_handler(message):
    chat_id = message.chat.id
    chat_str = str(chat_id)
    saved_r = db["ranges"].get(chat_str)
    if saved_r:
        fetch_and_send_number(chat_id, saved_r)
    else:
        msg = bot.send_message(chat_id, "আপনার পছন্দমতো রেঞ্জটি (Range) টাইপ করে পাঠান\n(যেমন: `224671808XXX`):", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_save_range)

@bot.message_handler(func=lambda m: m.text == "⚙️ Change Range" or m.text == "/range")
def change_range_handler(message):
    msg = bot.send_message(message.chat.id, "আপনার পছন্দমতো রেঞ্জটি (Range) টাইপ করে পাঠান\n(যেমন: `224671808XXX`):", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_save_range)

@bot.message_handler(func=lambda m: m.text == "📱 Range Group")
def range_group_handler(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📱 লাইভ রেঞ্জ চ্যানেলে যান", url=f"https://t.me/{RANGE_GROUP.replace('@', '')}"))
    bot.send_message(message.chat.id, f"📢 **আমাদের লাইভ রেঞ্জ চ্যানেল:** {RANGE_GROUP}\n\nনিচের বাটনে চাপ দিয়ে চ্যানেলে যুক্ত হন:", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🔽 OTHER" or m.text == "/other")
def other_handler(message):
    bot.send_message(message.chat.id, "📋 **OTHER OPTIONS**\n\nনিচের অপশন থেকে সিলেক্ট করুন:", reply_markup=bottom_other_keyboard(), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🏠 Home" or m.text == "/home")
def home_handler(message):
    bot.send_message(message.chat.id, "👋 **Welcome to HotOtp Bot**", reply_markup=bottom_main_keyboard())

@bot.message_handler(func=lambda m: m.text == "💰 Balances" or m.text == "/balances")
def balances_handler(message):
    chat_str = str(message.chat.id)
    bal = db["balances"].get(chat_str, 20.0)
    bot.send_message(message.chat.id, f"💳 **আপনার বর্তমান ব্যালেন্স:** `{bal}` TK\n\nরিচার্জ করতে এডমিনের সাথে যোগাযোগ করুন: @hototpotp", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "💬 Support" or m.text == "/help")
def support_handler(message):
    bot.send_message(message.chat.id, "💬 **সহায়তার জন্য এডমিন চ্যাট:** @hototpotp", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "✉️ Get Tempmail" or m.text == "/tempmail")
def tempmail_handler(message):
    bot.send_message(message.chat.id, "✉️ **Tempmail Feature:** শীঘ্রই আসছে!", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🔐 2FA" or m.text == "/twofa")
def twofa_handler(message):
    bot.send_message(message.chat.id, "🔐 **2FA Code Generator:** শীঘ্রই আসছে!", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "👤 Fake Name")
def fakename_handler(message):
    bot.send_message(message.chat.id, "👤 **Fake Name Generator:** John Doe", parse_mode="Markdown")

# ----------------------------------------------------
# ৮. কলব্যাক হ্যান্ডলার (ইনলাইন বাটন)
# ----------------------------------------------------
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    chat_id = call.message.chat.id
    chat_str = str(chat_id)
    try: bot.answer_callback_query(call.id)
    except: pass

    if call.data == "reset_all":
        db["ranges"].pop(chat_str, None)
        save_data()
        bot.clear_step_handler_by_chat_id(chat_id)
        bot.send_message(chat_id, "🔄 **সবকিছু রিসেট করা হয়েছে!**", reply_markup=bottom_main_keyboard(), parse_mode="Markdown")
        
    elif call.data == "ask_range":
        msg = bot.send_message(chat_id, "আপনার পছন্দমতো রেঞ্জটি (Range) টাইপ করে পাঠান\n(যেমন: `224671808XXX`):", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_save_range)

    elif call.data == "get_num_auto":
        saved_r = db["ranges"].get(chat_str)
        if saved_r: fetch_and_send_number(chat_id, saved_r)
        else:
            msg = bot.send_message(chat_id, "আপনার কোনো রেঞ্জ সেট করা নেই। রেঞ্জ টাইপ করুন:")
            bot.register_next_step_handler(msg, process_save_range)

    elif call.data.startswith("check_otp_"):
        parts = call.data.replace("check_otp_", "").split("|")
        otp = fetch_otp(parts[0], parts[1] if len(parts) > 1 else "")
        if otp: bot.send_message(chat_id, f"📩 {otp}", parse_mode="Markdown")
        else: bot.answer_callback_query(call.id, text="এখনো ওটিপি আসেনি! ২-৩ সেকেন্ড পর আবার চাপুন...", show_alert=True)

def process_save_range(message):
    chat_id = message.chat.id
    chat_str = str(chat_id)
    new_range = message.text.strip()
    db["ranges"][chat_str] = new_range
    save_data()
    bot.send_message(chat_id, f"✅ **রেঞ্জ সেভ হয়েছে:** `{new_range}`", reply_markup=bottom_main_keyboard(), parse_mode="Markdown")
    fetch_and_send_number(chat_id, new_range)

def fetch_and_send_number(chat_id, user_range):
    bot.send_message(chat_id, f"⏳ `{user_range}` রেঞ্জ দিয়ে নাম্বার নেওয়া হচ্ছে...", parse_mode="Markdown")
    
    url = "https://nexaotpservice.com/api/v1/numbers/get"
    headers = {"X-API-Key": NEXA_API_KEY, "Content-Type": "application/json"}
    payload = {"service": "google", "country": "BD", "range": user_range}
    
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10).json()
        if res.get("success"):
            country = res.get("country", "Global")
            number = res.get("number", "N/A")
            num_id = res.get("number_id", "")
            raw_num = str(number).replace("+", "").strip()

            msg_text = f"✅ **Number:** 🌐 {country} (0.20TK)"
            
            markup = types.InlineKeyboardMarkup(row_width=2)
            
            btn_num1 = types.InlineKeyboardButton(f"📋 📱 {raw_num}", callback_data="copy_ignore")
            btn_otp_group = types.InlineKeyboardButton("🔔 OTP GROUP", url=f"https://t.me/{OTP_GROUP.replace('@', '')}")
            btn_range_group = types.InlineKeyboardButton("📱 RANGE GROUP", url=f"https://t.me/{RANGE_GROUP.replace('@', '')}")
            btn_change = types.InlineKeyboardButton("⚙️ Change Range", callback_data="ask_range")
            btn_refresh = types.InlineKeyboardButton("🔄 Refresh", callback_data=f"check_otp_{num_id}|{number}")
            btn_back = types.InlineKeyboardButton("⬅️ Back", callback_data="reset_all")

            markup.add(btn_num1)
            markup.add(btn_otp_group, btn_range_group)
            markup.add(btn_change, btn_refresh)
            markup.add(btn_back)
            
            bot.send_message(chat_id, msg_text, reply_markup=markup, parse_mode="Markdown")
            threading.Thread(target=auto_check_otp, args=(chat_id, num_id, number), daemon=True).start()
        else:
            bot.send_message(chat_id, f"❌ সমস্যা: {res.get('error')}", reply_markup=bottom_main_keyboard())
    except Exception as e:
        bot.send_message(chat_id, f"❌ আসল সমস্যা: {e}")

# ----------------------------------------------------
# ৯. পোলিং চালু রাখা
# ----------------------------------------------------
try:
    bot.polling(none_stop=True, interval=0)
except Exception as e:
    print(f"Error: {e}")
