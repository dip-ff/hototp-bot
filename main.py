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
    return "HotOtp Bot is Alive and Running!", 200

def run_web():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# ব্যাকগ্রাউন্ডে ডামি ওয়েবসাইট সার্ভার চালু করা
threading.Thread(target=run_web, daemon=True).start()

# ----------------------------------------------------
# ২. বটের তথ্য (আপনার টোকেন ও এপিআই কি বসান)
# ----------------------------------------------------
BOT_TOKEN = "8810955739:AAF3rTAB8au8rJ8VwomgBfs_VWpTzIdrmBk"
NEXA_API_KEY = "nxa_eb3fc88e55f657d69cd3c4aca3b69cce416dc84e"

bot = telebot.TeleBot(BOT_TOKEN)

# প্রতিটি ইউজারের সেভ করা রেঞ্জ রাখার ডিকশনারি
user_ranges = {}

print("---------------------------------")
print("✅ HotOtp Bot Successfully Started on Render!")
print("---------------------------------")

# ওটিপি ফিল্টার করার ফাংশন
def fetch_otp(num_id, number):
    headers = {"X-API-Key": NEXA_API_KEY}
    
    # প্রাইভেট নাম্বার এপিআই
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

    # কনসোল লগ এপিআই
    try:
        url2 = "https://nexaotpservice.com/api/v1/console/logs"
        res2 = requests.get(url2, headers=headers, timeout=5).json()
        if isinstance(res2, list):
            for item in res2:
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

# ব্যাকগ্রাউন্ড ওটিপি চেকার
def auto_check_otp(chat_id, num_id, number):
    for _ in range(60): # ৩ মিনিট ধরে প্রতি ৩ সেকেন্ড পরপর
        time.sleep(3)
        otp = fetch_otp(num_id, number)
        if otp:
            bot.send_message(
                chat_id, 
                f"🎉 **ওটিপি চলে এসেছে!**\n\n{otp}", 
                parse_mode="Markdown"
            )
            return

# ডাইনামিক মেনু তৈরি
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
        
    btn_balance = types.InlineKeyboardButton("💰 ব্যালেন্স দেখুন", callback_data="balance")
    btn_reset = types.InlineKeyboardButton("🔄 সবকিছু রিসেট করুন", callback_data="reset_all")
    markup.add(btn_balance, btn_reset)
    return markup

# /start দিলে সবকিছু রিসেট হয়ে আবার প্রথম থেকে শুরু হবে
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_ranges.pop(chat_id, None)
    bot.clear_step_handler_by_chat_id(chat_id)
    
    bot.send_message(
        chat_id, 
        "🔄 **সবকিছু রিসেট করা হয়েছে!**\n\nস্বাগতম! নতুন করে কাজ শুরু করতে প্রথমে রেঞ্জ সেট করুন:", 
        reply_markup=main_menu(chat_id),
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    chat_id = call.message.chat.id
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass

    headers = {"X-API-Key": NEXA_API_KEY, "Content-Type": "application/json"}

    # ব্যালেন্স বাটন
    if call.data == "balance":
        url = "https://nexaotpservice.com/api/v1/balance"
        try:
            res = requests.get(url, headers={"X-API-Key": NEXA_API_KEY}, timeout=10).json()
            bal = res.get('balance', 'N/A')
            bot.send_message(chat_id, f"💳 আপনার অ্যাকাউন্টের ব্যালেন্স: {bal} টাকা")
        except Exception as e:
            bot.send_message(chat_id, f"❌ ব্যালেন্স চেক এরর: {e}")

    # রিসেট বাটন
    elif call.data == "reset_all":
        user_ranges.pop(chat_id, None)
        bot.clear_step_handler_by_chat_id(chat_id)
        bot.answer_callback_query(call.id, text="সবকিছু রিসেট করা হয়েছে!", show_alert=True)
        bot.send_message(
            chat_id, 
            "🔄 **সবকিছু রিসেট করা হয়েছে!**\n\nনতুন করে কাজ শুরু করতে প্রথমে রেঞ্জ সেট করুন:", 
            reply_markup=main_menu(chat_id),
            parse_mode="Markdown"
        )

    # রেঞ্জ টাইপ করার অপশন
    elif call.data == "ask_range":
        msg = bot.send_message(
            chat_id, 
            "আপনার পছন্দমতো রেঞ্জটি (Range) টাইপ করে পাঠান\n(যেমন: `224671808XXX`):",
            parse_mode="Markdown"
        )
        bot.register_next_step_handler(msg, process_save_range)

    # অটো সেভড রেঞ্জ থেকে নাম্বার আনা
    elif call.data == "get_num_auto":
        saved_r = user_ranges.get(chat_id)
        if saved_r:
            fetch_and_send_number(chat_id, saved_r)
        else:
            msg = bot.send_message(chat_id, "আপনার কোনো রেঞ্জ সেট করা নেই। রেঞ্জ টাইপ করুন:")
            bot.register_next_step_handler(msg, process_save_range)

    # ওটিপি চেক বাটন
    elif call.data.startswith("check_otp_"):
        parts = call.data.replace("check_otp_", "").split("|")
        num_id = parts[0]
        number = parts[1] if len(parts) > 1 else ""
        
        otp = fetch_otp(num_id, number)
        if otp:
            bot.send_message(chat_id, f"📩 {otp}", parse_mode="Markdown")
        else:
            bot.answer_callback_query(call.id, text="এখনো আসল ওটিপি আসেনি! কয়েক সেকেন্ড পর আবার চাপুন...", show_alert=True)

# নতুন রেঞ্জ সেভ করার ফাংশন
def process_save_range(message):
    chat_id = message.chat.id
    new_range = message.text.strip()
    user_ranges[chat_id] = new_range
    
    bot.send_message(
        chat_id, 
        f"✅ **রেঞ্জ সেভ হয়েছে:** `{new_range}`\n\nএখন থেকে 'নতুন নাম্বার নিন' চাপলে এই রেঞ্জ থেকেই নাম্বার আসবে।", 
        parse_mode="Markdown"
    )
    fetch_and_send_number(chat_id, new_range)

# এপিআই দিয়ে নাম্বার আনার ফাংশন
def fetch_and_send_number(chat_id, user_range):
    bot.send_message(chat_id, f"⏳ `{user_range}` রেঞ্জ দিয়ে নাম্বার নেওয়া হচ্ছে...", parse_mode="Markdown")

    url = "https://nexaotpservice.com/api/v1/numbers/get"
    headers = {"X-API-Key": NEXA_API_KEY, "Content-Type": "application/json"}
    
    payload = {
        "service": "google",
        "country": "BD",
        "range": user_range
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10).json()
        
        if res.get("success"):
            country = res.get("country", "Unknown")
            number = res.get("number", "N/A")
            num_id = res.get("number_id", "")
            
            msg_text = (
                f"🌐 **Country:** {country}\n"
                f"🎯 **Active Range:** `{user_range}`\n"
                f"💎 **Status:** Waiting for OTP ⭐ (Max 30 mins)\n\n"
                f"👇 **নাম্বারটির ওপর এক টাচ করলেই কপি হবে:**\n`{number}`\n\n"
                f"💡 _আসল ওটিপি কোড আসার সাথে সাথে বট এখানে পাঠিয়ে দেবে!_"
            )
            
            markup = types.InlineKeyboardMarkup(row_width=1)
            btn_refresh = types.InlineKeyboardButton("🔄 Refresh / Check OTP", callback_data=f"check_otp_{num_id}|{number}")
            btn_next = types.InlineKeyboardButton("📱 একই রেঞ্জ থেকে আরেকটি নাম্বার নিন", callback_data="get_num_auto")
            btn_change = types.InlineKeyboardButton("⚙️ রেঞ্জ চেঞ্জ করুন", callback_data="ask_range")
            btn_reset = types.InlineKeyboardButton("🔄 সবকিছু রিসেট করুন", callback_data="reset_all")
            
            markup.add(btn_refresh, btn_next, btn_change, btn_reset)
            
            bot.send_message(chat_id, msg_text, reply_markup=markup, parse_mode="Markdown")
            
            threading.Thread(target=auto_check_otp, args=(chat_id, num_id, number), daemon=True).start()
            
        else:
            err = res.get("error", "নাম্বার পাওয়া যায়নি")
            bot.send_message(chat_id, f"❌ সমস্যা: {err}\n\nঅন্য রেঞ্জ দিতে '⚙️ রেঞ্জ চেঞ্জ করুন' বাটনে চাপ দিন।", reply_markup=main_menu(chat_id))

    except Exception as e:
        bot.send_message(chat_id, f"❌ আসল সমস্যা (Error): {e}")

# ----------------------------------------------------
# ৩. পোলিং চালু রাখা
# ----------------------------------------------------
try:
    bot.polling(none_stop=True, interval=0)
except Exception as e:
    print(f"Error: {e}")
