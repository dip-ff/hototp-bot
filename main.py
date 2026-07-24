import os
import telebot
import requests
import threading
import time
from flask import Flask
from telebot import types

# ----------------------------------------------------
# ১. Render Port Binding এর জন্য ডামি ওয়েব সার্ভার
# ----------------------------------------------------
app = Flask(__name__)

@app.route('/')
def home():
    return "HotOtp All-Engine Multi Poster Active!", 200

def run_web():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_web, daemon=True).start()

# ----------------------------------------------------
# ২. বটের মূল তথ্য ও চ্যানেলের ইউজারনেম (আপনার বটের লিঙ্কসহ)
# ----------------------------------------------------
BOT_TOKEN = "8810955739:AAFEWvtxNCKFZXpPgv88zKdX-kJmoALnNis"  # আপনার আসল টেলিগ্রাম বট টোকেন
NEXA_API_KEY = "nxa_eb3fc88e55f657d69cd3c4aca3b69cce416dc84e" # আপনার NexaOTP এপিআই কি

BOT_USERNAME = "hot_opt_bot"              # আপনার আসল বটের ইউজারনেম
OTP_GROUP = "@hototpotp"                 # ওটিপি আপডেট গ্রুপ
RANGE_GROUP = "@hototprange"             # আপনার লাইভ রেঞ্জ চ্যানেল

bot = telebot.TeleBot(BOT_TOKEN)
user_ranges = {}
posted_signatures = set()

print("---------------------------------")
print("🔥 HotOtp Console Auto-Poster Active!")
print("---------------------------------")

# ----------------------------------------------------
# ৩. সবকটি ইঞ্জিন (Engine 1, 2, 3 & Recent) স্ক্যান করার ফাংশন
# ----------------------------------------------------
def fetch_all_site_logs():
    headers = {"X-API-Key": NEXA_API_KEY}
    all_items = []
    
    endpoints = [
        "https://nexaotpservice.com/api/v1/console/logs?limit=30",
        "https://nexaotpservice.com/api/v1/console/logs/engine2?limit=30",
        "https://nexaotpservice.com/api/v1/console/logs/engine3?limit=30",
        "https://nexaotpservice.com/api/v1/sms/recent?limit=30",
        "https://nexaotpservice.com/api/v1/console/live"
    ]
    
    for ep in endpoints:
        try:
            r = requests.get(ep, headers=headers, timeout=5).json()
            items = []
            if isinstance(r, list):
                items = r
            elif isinstance(r, dict):
                items = r.get("logs") or r.get("data") or r.get("recent") or r.get("sms") or []
            
            if isinstance(items, list):
                all_items.extend(items)
        except Exception:
            pass
            
    return all_items

# ----------------------------------------------------
# ৪. অল-ইঞ্জিন অটো-পোস্টার লুপ
# ----------------------------------------------------
def auto_post_live_ranges():
    while True:
        try:
            logs = fetch_all_site_logs()

            if isinstance(logs, list) and len(logs) > 0:
                for item in logs:
                    if not isinstance(item, dict):
                        continue
                    
                    number = str(item.get("number") or item.get("range") or "").strip()
                    country = str(item.get("country") or "Global").strip()
                    service = str(item.get("service") or "OTP Service").strip()
                    sms_preview = str(item.get("sms") or item.get("text") or item.get("message") or item.get("code") or "").strip()
                    time_id = str(item.get("id") or item.get("number_id") or item.get("time") or item.get("created_at") or "")

                    if not number or len(number) < 4:
                        continue

                    sig = f"{number}_{service}_{country}_{sms_preview[:15]}_{time_id}"
                    
                    if sig in posted_signatures:
                        continue
                    
                    posted_signatures.add(sig)
                    if len(posted_signatures) > 1500:
                        posted_signatures.clear()

                    raw_num = number.replace("+", "").strip()
                    if "XXX" in raw_num:
                        range_str = raw_num
                    elif len(raw_num) > 8:
                        range_str = raw_num[:8] + "XXX"
                    elif len(raw_num) > 5:
                        range_str = raw_num[:5] + "XXX"
                    else:
                        range_str = raw_num + "XXX"

                    msg_text_display = f"`{sms_preview}`" if sms_preview else "Live Signal Received ⭐"

                    # আপনার নিজস্ব ব্র্যান্ডিং "HOT OTP LIVE CONSOLE"
                    post_text = (
                        f"🔥 **HOT OTP LIVE CONSOLE** 🔥\n\n"
                        f"📱 **Range:** `{range_str}`\n"
                        f"🎯 **Service:** {service}\n"
                        f"🌐 **Country:** {country}\n"
                        f"💬 **SMS:** {msg_text_display}\n\n"
                        f"👇 **১-ক্লিকে এই রেঞ্জ দিয়ে নাম্বার নিতে নিচে চাপ দিন:**"
                    )

                    # আপনার বটের লিংকসহ অটোমেটিক ১-ক্লিক বাটন
                    markup = types.InlineKeyboardMarkup()
                    btn_bot = types.InlineKeyboardButton("🤖 HotOtp Bot-এ এই নাম্বার নিন", url=f"https://t.me/{BOT_USERNAME}?start={range_str}")
                    markup.add(btn_bot)

                    try:
                        bot.send_message(RANGE_GROUP, post_text, reply_markup=markup, parse_mode="Markdown")
                        time.sleep(3) # ৩ সেকেন্ড গ্যাপ
                    except telebot.apihelper.ApiTelegramException as te:
                        if te.error_code == 429:
                            time.sleep(20)
                        else:
                            print(f"Posting error: {te}")
                    except Exception as pe:
                        print(f"Posting error: {pe}")
                        time.sleep(3)
        except Exception as e:
            print(f"Main Loop Error: {e}")
        
        time.sleep(8)

threading.Thread(target=auto_post_live_ranges, daemon=True).start()

# ----------------------------------------------------
# ৫. ম্যানুয়াল টেস্ট কনসোল কমান্ড (/testconsole)
# ----------------------------------------------------
@bot.message_handler(commands=['testconsole'])
def test_console_cmd(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "⏳ NexaOTP সাইটের সবকটি ইঞ্জিন স্ক্যান করা হচ্ছে...")
    try:
        logs = fetch_all_site_logs()
        
        if logs and len(logs) > 0:
            first_item = logs[0]
            number = str(first_item.get("number") or first_item.get("range") or "").strip()
            country = str(first_item.get("country") or "Global").strip()
            service = str(first_item.get("service") or "OTP Service").strip()
            sms_preview = str(first_item.get("sms") or first_item.get("text") or first_item.get("message") or "").strip()
            
            raw_num = number.replace("+", "").strip()
            if "XXX" in raw_num: range_str = raw_num
            elif len(raw_num) > 8: range_str = raw_num[:8] + "XXX"
            else: range_str = raw_num + "XXX"

            msg_text_display = f"`{sms_preview}`" if sms_preview else "Live Signal Received ⭐"

            post_text = (
                f"🔥 **HOT OTP LIVE CONSOLE** 🔥\n\n"
                f"📱 **Range:** `{range_str}`\n"
                f"🎯 **Service:** {service}\n"
                f"🌐 **Country:** {country}\n"
                f"💬 **SMS:** {msg_text_display}\n\n"
                f"👇 **১-ক্লিকে এই রেঞ্জ দিয়ে নাম্বার নিন:**"
            )
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🤖 HotOtp Bot-এ নাম্বার নিন", url=f"https://t.me/{BOT_USERNAME}?start={range_str}"))
            
            bot.send_message(RANGE_GROUP, post_text, reply_markup=markup, parse_mode="Markdown")
            bot.send_message(chat_id, f"🎉 **সফল হয়েছে!**\n\nসাইট থেকে ওটিপি ডাটা পেয়ে `{RANGE_GROUP}` চ্যানেলে পোস্ট পাঠানো হয়েছে!", parse_mode="Markdown")
        else:
            bot.send_message(chat_id, "⚠️ সাইটের কোনো ইঞ্জিনে বর্তমানে ডাটা পাওয়া যায়নি।", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(chat_id, f"❌ এপিআই এরর: {e}")

# ----------------------------------------------------
# ৬. ওটিপি ফিল্টার ও বটের মূল সার্ভিস
# ----------------------------------------------------
def fetch_otp(num_id, number):
    headers = {"X-API-Key": NEXA_API_KEY}
    try:
        url1 = f"https://nexaotpservice.com/api/v1/numbers/{num_id}/sms"
        res1 = requests.get(url1, headers=headers, timeout=5).json()
        if res1.get("success"):
            code = res1.get("code") or res1.get("otp") or res1.get("sms_code")
            sms = res1.get("sms") or res1.get("message") or res1.get("text") or ""
            if code and "******" not in str(code):
                return f"🔢 **OTP Code:** `{code}`\n\n📩 **Full SMS:** `{sms}`"
            if sms and "******" not in str(sms):
                return f"📩 **SMS:** `{sms}`"
    except Exception:
        pass

    try:
        logs = fetch_all_site_logs()
        for item in logs:
            if isinstance(item, dict):
                if item.get("number") == number or item.get("number_id") == num_id:
                    sms = item.get("sms") or item.get("text") or item.get("message") or ""
                    code = item.get("code") or item.get("otp") or ""
                    if code and "******" not in str(code):
                        return f"🔢 **OTP Code:** `{code}`\n\n📩 **SMS:** `{sms}`"
                    if sms and "******" not in str(sms):
                        return f"📩 **SMS:** `{sms}`"
    except Exception:
        pass
    return None

def auto_check_otp(chat_id, num_id, number):
    for _ in range(60):
        time.sleep(3)
        otp = fetch_otp(num_id, number)
        if otp:
            bot.send_message(chat_id, f"🎉 **ওটিপি চলে এসেছে!**\n\n{otp}", parse_mode="Markdown")
            return

def main_menu(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    saved_r = user_ranges.get(chat_id)
    
    if saved_r:
        btn_num = types.InlineKeyboardButton(f"📱 নতুন নাম্বার নিন ({saved_r})", callback_data="get_num_auto")
        btn_range = types.InlineKeyboardButton("⚙️ রেঞ্জ চেঞ্জ করুন", callback_data="ask_range")
        markup.add(btn_num, btn_range)
    else:
        btn_range = types.InlineKeyboardButton("⚙️ প্রথমে রেঞ্জ সেট করুন", callback_data="ask_range")
        markup.add(btn_range)
        
    range_link = f"https://t.me/{RANGE_GROUP.replace('@', '')}"
    
    btn_range_group = types.InlineKeyboardButton("📱 লাইভ রেঞ্জ চ্যানেল (@hototprange)", url=range_link)
    btn_reset = types.InlineKeyboardButton("🔄 সবকিছু রিসেট করুন", callback_data="reset_all")
    
    markup.add(btn_range_group, btn_reset)
    return markup

# /start কমান্ড (১-ক্লিক অটোমেটিক রেঞ্জ রিসিভ করার লজিক সহ)
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    bot.clear_step_handler_by_chat_id(chat_id)
    
    # যদি চ্যানেল থেকে ১-ক্লিকে কোনো রেঞ্জ নিয়ে আসে
    args = message.text.split()
    if len(args) > 1:
        deep_range = args[1].strip()
        user_ranges[chat_id] = deep_range
        bot.send_message(chat_id, f"✅ **চ্যানেল থেকে রেঞ্জ সিলেক্ট করা হয়েছে:** `{deep_range}`", parse_mode="Markdown")
        fetch_and_send_number(chat_id, deep_range)
        return

    user_ranges.pop(chat_id, None)
    bot.send_message(chat_id, "🔄 **সবকিছু রিসেট করা হয়েছে!**\n\nস্বাগতম! নিচে থেকে প্রয়োজনীয় অপশন বেছে নিন:", reply_markup=main_menu(chat_id), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    chat_id = call.message.chat.id
    try: bot.answer_callback_query(call.id)
    except: pass

    if call.data == "reset_all":
        user_ranges.pop(chat_id, None)
        bot.clear_step_handler_by_chat_id(chat_id)
        bot.send_message(chat_id, "🔄 **সবকিছু রিসেট করা হয়েছে!**\n\nনতুন করে কাজ শুরু করতে প্রথমে রেঞ্জ সেট করুন:", reply_markup=main_menu(chat_id), parse_mode="Markdown")
        
    elif call.data == "ask_range":
        msg = bot.send_message(chat_id, "আপনার পছন্দমতো রেঞ্জটি (Range) টাইপ করে পাঠান\n(যেমন: `224671808XXX`):", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_save_range)
        
    elif call.data == "get_num_auto":
        saved_r = user_ranges.get(chat_id)
        if saved_r: fetch_and_send_number(chat_id, saved_r)
        else:
            msg = bot.send_message(chat_id, "আপনার কোনো রেঞ্জ সেট করা নেই। রেঞ্জ টাইপ করুন:")
            bot.register_next_step_handler(msg, process_save_range)

    elif call.data.startswith("check_otp_"):
        parts = call.data.replace("check_otp_", "").split("|")
        otp = fetch_otp(parts[0], parts[1] if len(parts) > 1 else "")
        if otp: bot.send_message(chat_id, f"📩 {otp}", parse_mode="Markdown")

def process_save_range(message):
    chat_id = message.chat.id
    new_range = message.text.strip()
    user_ranges[chat_id] = new_range
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
            msg_text = f"🌐 **Country:** {country}\n🎯 **Active Range:** `{user_range}`\n💎 **Status:** Waiting for OTP ⭐\n\n👇 **নাম্বারটির ওপর চাপ দিলে কপি হবে:**\n`{number}`"
            
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                types.InlineKeyboardButton("📱 লাইভ রেঞ্জ চ্যানেল", url=f"https://t.me/{RANGE_GROUP.replace('@', '')}"),
                types.InlineKeyboardButton("📱 একই রেঞ্জ থেকে আরেকটি নাম্বার নিন", callback_data="get_num_auto"),
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
# ৭. পোলিং চালু রাখা
# ----------------------------------------------------
try:
    bot.polling(none_stop=True, interval=0)
except Exception as e:
    print(f"Error: {e}")
