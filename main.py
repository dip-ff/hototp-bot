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
    return "HotOtp Site Console Auto-Poster Active!", 200

def run_web():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_web, daemon=True).start()

# ----------------------------------------------------
# ২. বটের মূল তথ্য ও চ্যানেলের ইউজারনেম
# ----------------------------------------------------
BOT_TOKEN = "8810955739:AAFEWvtxNCKFZXpPgv88zKdX-kJmoALnNis"  # আপনার টেলিগ্রাম বট টোকেন বসান
NEXA_API_KEY = "nxa_eb3fc88e55f657d69cd3c4aca3b69cce416dc84e" # আপনার এপিআই কি

OTP_GROUP = "@hototpotp"                 # ওটিপি আপডেট গ্রুপ
RANGE_GROUP = "@hototprange"             # আপনার লাইভ রেঞ্জ চ্যানেল

bot = telebot.TeleBot(BOT_TOKEN)
user_ranges = {}
posted_sms_ids = set()

print("---------------------------------")
print("🔥 NexaOTP Console Real-Time Range Poster Running!")
print("---------------------------------")

# ----------------------------------------------------
# ৩. অনবরত সাইট থেকে লাইভ রেঞ্জ পোস্ট করার ক্র্যাশ-প্রুফ লুপ
# ----------------------------------------------------
def auto_post_live_ranges():
    headers = {"X-API-Key": NEXA_API_KEY}
    
    while True:
        try:
            url = "https://nexaotpservice.com/api/v1/console/logs?limit=50"
            res = requests.get(url, headers=headers, timeout=10).json()
            
            logs = []
            if isinstance(res, list):
                logs = res
            elif isinstance(res, dict):
                logs = res.get("logs") or res.get("data") or res.get("recent") or []

            if isinstance(logs, list) and len(logs) > 0:
                for item in reversed(logs[:15]):
                    if not isinstance(item, dict):
                        continue
                    
                    num_id = str(item.get("number_id") or item.get("id") or item.get("number") or item.get("range") or "")
                    
                    # যদি নতুন ওটিপি হিট হয়
                    if num_id and num_id not in posted_sms_ids:
                        posted_sms_ids.add(num_id)
                        
                        if len(posted_sms_ids) > 800:
                            posted_sms_ids.clear()

                        number = item.get("number") or item.get("range") or ""
                        country = item.get("country") or "Global"
                        service = item.get("service") or "OTP Service"
                        hits = item.get("hits") or item.get("count") or ""
                        hits_str = f"[{hits} hits]" if hits else ""

                        raw_num = str(number).replace("+", "").strip()
                        if "XXX" in raw_num:
                            range_str = raw_num
                        elif len(raw_num) > 8:
                            range_str = raw_num[:8] + "XXX"
                        elif len(raw_num) > 5:
                            range_str = raw_num[:5] + "XXX"
                        else:
                            range_str = raw_num + "XXX"

                        post_text = (
                            f"🔥 **NEXA OTP LIVE SIGNAL HIT** 🔥\n\n"
                            f"📱 **Range:** `{range_str}`\n"
                            f"🎯 **Service:** {service} {hits_str}\n"
                            f"🌐 **Country:** {country}\n"
                            f"⚡ **Signal:** Live Signal (Old/Clone) ⚡\n\n"
                            f"👇 **১-ক্লিকে এই রেঞ্জ দিয়ে নাম্বার নিতে নিচে চাপ দিন:**"
                        )

                        markup = types.InlineKeyboardMarkup()
                        btn_bot = types.InlineKeyboardButton("🤖 HotOtp Bot-এ নাম্বার নিন", url="https://t.me/HotOtpBot")
                        markup.add(btn_bot)

                        try:
                            bot.send_message(RANGE_GROUP, post_text, reply_markup=markup, parse_mode="Markdown")
                        except Exception as pe:
                            print(f"Post Limit Error: {pe}")
                            time.sleep(5)
                            
                        time.sleep(4) # টেলিগ্রাম স্প্যাম ফিল্টার এড়াতে ৪ সেকেন্ড গ্যাপ
        except Exception as e:
            print(f"Loop Error: {e}")
        
        time.sleep(25) # প্রতি ২৫ সেকেন্ড পর পর সাইট অটো স্ক্যান করবে

threading.Thread(target=auto_post_live_ranges, daemon=True).start()

# ----------------------------------------------------
# ৪. ম্যানুয়াল টেস্ট কনসোল কমান্ড (/testconsole)
# ----------------------------------------------------
@bot.message_handler(commands=['testconsole'])
def test_console_cmd(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "⏳ NexaOTP সাইটের লাইভ কনসোল থেকে ডাটা চেক করা হচ্ছে...")
    headers = {"X-API-Key": NEXA_API_KEY}
    try:
        url = "https://nexaotpservice.com/api/v1/console/logs?limit=50"
        res = requests.get(url, headers=headers, timeout=10).json()
        
        logs = []
        if isinstance(res, list): logs = res
        elif isinstance(res, dict): logs = res.get("logs") or res.get("data") or res.get("recent") or []
        
        if logs and len(logs) > 0:
            first_item = logs[0]
            number = first_item.get("number") or first_item.get("range") or ""
            country = first_item.get("country") or "Global"
            service = first_item.get("service") or "OTP Service"
            
            raw_num = str(number).replace("+", "").strip()
            if "XXX" in raw_num: range_str = raw_num
            elif len(raw_num) > 8: range_str = raw_num[:8] + "XXX"
            else: range_str = raw_num + "XXX"

            post_text = (
                f"🔥 **NEXA OTP LIVE SIGNAL HIT** 🔥\n\n"
                f"📱 **Range:** `{range_str}`\n"
                f"🎯 **Service:** {service}\n"
                f"🌐 **Country:** {country}\n"
                f"⚡ **Signal:** Live Signal (Old/Clone) ⚡\n\n"
                f"👇 **১-ক্লিকে এই রেঞ্জ দিয়ে নাম্বার নিন:**"
            )
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🤖 HotOtp Bot-এ নাম্বার নিন", url="https://t.me/HotOtpBot"))
            
            bot.send_message(RANGE_GROUP, post_text, reply_markup=markup, parse_mode="Markdown")
            bot.send_message(chat_id, f"🎉 **সফল হয়েছে!**\n\nসাইট থেকে ওটিপি ডাটা পেয়ে `{RANGE_GROUP}` চ্যানেলে ১টি লাইভ রেঞ্জ পোস্ট পাঠানো হয়েছে!", parse_mode="Markdown")
        else:
            bot.send_message(chat_id, f"⚠️ সাইট থেকে এপিআই রেসপন্স এসেছে কিন্তু কোনো ডাটা মেলেনি:\n`{res}`", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(chat_id, f"❌ এপিআই এরর: {e}")

# ----------------------------------------------------
# ৫. ওটিপি ফিল্টার ও বটের মূল সার্ভিস
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
        url2 = "https://nexaotpservice.com/api/v1/console/logs"
        res2 = requests.get(url2, headers=headers, timeout=5).json()
        
        logs = []
        if isinstance(res2, list): logs = res2
        elif isinstance(res2, dict): logs = res2.get("logs") or res2.get("data") or res2.get("recent") or []
        
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

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_ranges.pop(chat_id, None)
    bot.clear_step_handler_by_chat_id(chat_id)
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
# ৬. পোলিং চালু রাখা
# ----------------------------------------------------
try:
    bot.polling(none_stop=True, interval=0)
except Exception as e:
    print(f"Error: {e}")
