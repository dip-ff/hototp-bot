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

# আপনার Render ওয়েবসাইটের লিংক (এটি রেন্ডারকে অফলাইন হওয়া থেকে বাঁচাবে)
RENDER_URL = "https://hototp-bot-3.onrender.com"

@app.route('/')
def home():
    return "HotOtp Bot is 24/7 Alive & Running!", 200

def run_web():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_web, daemon=True).start()

# অনবরত রেন্ডার সাইটকে জাগিয়ে রাখার পিনগার থ্রেড
def keep_alive_pinger():
    while True:
        time.sleep(300) # প্রতি ৫ মিনিট পর পর নক দেবে
        try:
            requests.get(RENDER_URL, timeout=10)
            print("⚡ Keep-Alive Ping Sent!")
        except Exception:
            pass

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

print("---------------------------------")
print("🔥 HotOtp 24/7 Non-Stop Bot Running!")
print("---------------------------------")

# ----------------------------------------------------
# ৩. সাইটের কনসোল লাইভ অটো-পোস্টার
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
# ৪. ওটিপি ফিল্টার
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
# ৫. মূল মেনু
# ----------------------------------------------------
def main_menu(chat_id):
    chat_str = str(chat_id)
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    saved_r = db["ranges"].get(chat_str)

    if saved_r:
        btn_num = types.InlineKeyboardButton(f"📱 নতুন নাম্বার নিন ({saved_r})", callback_data="get_num_auto")
        btn_range = types.InlineKeyboardButton("⚙️ রেঞ্জ চেঞ্জ করুন", callback_data="ask_range")
        markup.add(btn_num, btn_range)
    else:
        btn_range = types.InlineKeyboardButton("⚙️ প্রথমে রেঞ্জ সেট করুন", callback_data="ask_range")
        markup.add(btn_range)

    btn_wallet = types.InlineKeyboardButton("💳 আমার ওয়ালেট & রিচার্জ", callback_data="view_wallet")
    btn_channel = types.InlineKeyboardButton("📱 লাইভ রেঞ্জ চ্যানেল (@hototprange)", url=f"https://t.me/{RANGE_GROUP.replace('@', '')}")
    btn_reset = types.InlineKeyboardButton("🔄 সবকিছু রিসেট করুন", callback_data="reset_all")

    markup.add(btn_wallet, btn_channel, btn_reset)
    return markup

# ----------------------------------------------------
# ৬. বট কমান্ডস
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
        bot.send_message(chat_id, f"✅ **চ্যানেল থেকে রেঞ্জ সিলেক্ট হয়েছে:** `{deep_range}`", parse_mode="Markdown")
        fetch_and_send_number(chat_id, deep_range)
        return

    db["ranges"].pop(chat_str, None)
    save_data()
    bot.send_message(chat_id, "🔥 **HotOtp Bot**-এ স্বাগতম!\n\nনিচে থেকে আপনার প্রয়োজনীয় অপশন বেছে নিন:", reply_markup=main_menu(chat_id), parse_mode="Markdown")

@bot.message_handler(commands=['myid'])
def my_id_command(message):
    bot.reply_to(message, f"🆔 আপনার টেলিগ্রাম আইডি: `{message.chat.id}`", parse_mode="Markdown")

@bot.message_handler(commands=['stats'])
def stats_command(message):
    total_users = len(db["users"])
    total_otps = db.get("total_otps", 0)
    msg = f"📊 **HotOtp Bot Statistics** 📊\n\n👥 মোট রেজিস্টার্ড ইউজার: `{total_users}` জন\n📩 মোট ওটিপি ডেলিভারি: `{total_otps}` টি\n⚡ স্টেটাস: ১০০% অ্যাক্টিভ (Render Cloud)"
    bot.reply_to(message, msg, parse_mode="Markdown")

@bot.message_handler(commands=['broadcast'])
def broadcast_command(message):
    text = message.text.replace('/broadcast', '').strip()
    if not text:
        bot.reply_to(message, "❌ ব্যবহারের নিয়ম: `/broadcast আপনার মেসেজ টাইপ করুন`", parse_mode="Markdown")
        return

    success_count = 0
    bot.reply_to(message, "⏳ সব ইউজারের কাছে মেসেজ পাঠানো হচ্ছে...")
    for user_id in db["users"]:
        try:
            bot.send_message(user_id, f"📢 **ADMIN ANNOUNCEMENT** 📢\n\n{text}", parse_mode="Markdown")
            success_count += 1
            time.sleep(0.1)
        except: pass
    
    bot.send_message(message.chat.id, f"✅ ব্রডকাস্ট সম্পন্ন হয়েছে!\nমোট `{success_count}` জনের কাছে সফলভাবে পাঠানো হয়েছে।", parse_mode="Markdown")

@bot.message_handler(commands=['addbalance'])
def add_balance_command(message):
    try:
        parts = message.text.split()
        target_id = parts[1]
        amount = float(parts[2])
        
        current_bal = db["balances"].get(target_id, 0.0)
        db["balances"][target_id] = current_bal + amount
        save_data()
        
        bot.reply_to(message, f"✅ ইউজার `{target_id}` কে `{amount}` টাকা এড করা হয়েছে। বর্তমান ব্যালেন্স: `{db['balances'][target_id]}` টাকা", parse_mode="Markdown")
        try: bot.send_message(int(target_id), f"🎉 আপনার ওয়ালেটে `{amount}` টাকা জমা হয়েছে! বর্তমান ব্যালেন্স: `{db['balances'][target_id]}` টাকা", parse_mode="Markdown")
        except: pass
    except:
        bot.reply_to(message, "❌ নিয়ম: `/addbalance <User_ID> <টাকার পরিমাণ>`", parse_mode="Markdown")

# ----------------------------------------------------
# ৭. কলব্যাক হ্যান্ডলার
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
        bot.send_message(chat_id, "🔄 **সবকিছু রিসেট করা হয়েছে!**", reply_markup=main_menu(chat_id), parse_mode="Markdown")
        
    elif call.data == "ask_range":
        msg = bot.send_message(chat_id, "আপনার পছন্দমতো রেঞ্জটি (Range) টাইপ করে পাঠান\n(যেমন: `224671808XXX`):", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_save_range)

    elif call.data == "get_num_auto":
        saved_r = db["ranges"].get(chat_str)
        if saved_r: fetch_and_send_number(chat_id, saved_r)
        else:
            msg = bot.send_message(chat_id, "আপনার কোনো রেঞ্জ সেট করা নেই। রেঞ্জ টাইপ করুন:")
            bot.register_next_step_handler(msg, process_save_range)

    elif call.data == "view_wallet":
        bal = db["balances"].get(chat_str, 0.0)
        text = (
            f"💳 **আপনার ওয়ালেট বিবরণী** 💳\n\n"
            f"🆔 ইউজার আইডি: `{chat_id}`\n"
            f"💰 বর্তমান ব্যালেন্স: `{bal}` টাকা\n\n"
            f"📌 **টাকা রিচার্জের নিয়ম:**\n"
            f"বিকাশ/নগদ এর মাধ্যমে টাকা ডিপোজিট করতে এডমিনের সাথে যোগাযোগ করুন।"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💬 এডমিনের সাথে কথা বলুন", url="https://t.me/hototpotp"))
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

    elif call.data.startswith("cancel_num_"):
        bot.send_message(chat_id, "❌ **নাম্বার ক্যানসেল করা হয়েছে!**\nনতুন নাম্বার নিতে 'নতুন নাম্বার নিন' চাপুন।", reply_markup=main_menu(chat_id), parse_mode="Markdown")

    elif call.data.startswith("check_otp_"):
        parts = call.data.replace("check_otp_", "").split("|")
        otp = fetch_otp(parts[0], parts[1] if len(parts) > 1 else "")
        if otp: bot.send_message(chat_id, f"📩 {otp}", parse_mode="Markdown")

def process_save_range(message):
    chat_id = message.chat.id
    chat_str = str(chat_id)
    new_range = message.text.strip()
    db["ranges"][chat_str] = new_range
    save_data()
    bot.send_message(chat_id, f"✅ **রেঞ্জ সেভ হয়েছে:** `{new_range}`", parse_mode="Markdown")
    fetch_and_send_number(chat_id, new_range)

def fetch_and_send_number(chat_id, user_range):
    bot.send_message(chat_id, f"⏳ `{user_range}` রেঞ্জ দিয়ে নাম্বার নেওয়া হচ্ছে...", parse_mode="Markdown")
    
    url = "https://nexaotpservice.com/api/v1/numbers/get"
    headers = {"X-API-Key": NEXA_API_KEY, "Content-Type": "application/json"}
    payload = {"service": "google", "country": "BD", "range": user_range}
    
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10).json()
        if res.get("success"):
            country = res.get("country", "Unknown")
            number = res.get("number", "N/A")
            num_id = res.get("number_id", "")
            
            msg_text = (
                f"🌐 **Country:** {country}\n"
                f"🎯 **Active Range:** `{user_range}`\n"
                f"💎 **Status:** Waiting for OTP ⭐\n\n"
                f"👇 **নাম্বারটির ওপর চাপ দিলে কপি হবে:**\n`{number}`"
            )
            
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                types.InlineKeyboardButton("📱 লাইভ রেঞ্জ চ্যানেল", url=f"https://t.me/{RANGE_GROUP.replace('@', '')}"),
                types.InlineKeyboardButton("📱 একই রেঞ্জ থেকে আরেকটি নাম্বার নিন", callback_data="get_num_auto"),
                types.InlineKeyboardButton("❌ এই নাম্বার বাতিল করুন (Cancel)", callback_data=f"cancel_num_{num_id}"),
                types.InlineKeyboardButton("⚙️ রেঞ্জ চেঞ্জ করুন", callback_data="ask_range"),
                types.InlineKeyboardButton("🔄 সবকিছু রিসেট করুন", callback_data="reset_all")
            )
            bot.send_message(chat_id, msg_text, reply_markup=markup, parse_mode="Markdown")
            threading.Thread(target=auto_check_otp, args=(chat_id, num_id, number), daemon=True).start()
        else:
            bot.send_message(chat_id, f"❌ সমস্যা: {res.get('error')}", reply_markup=main_menu(chat_id))
    except Exception as e:
        bot.send_message(chat_id, f"❌ আসল সমস্যা: {e}")

# ----------------------------------------------------
# ৮. পোলিং চালু রাখা
# ----------------------------------------------------
try:
    bot.polling(none_stop=True, interval=0)
except Exception as e:
    print(f"Error: {e}")
