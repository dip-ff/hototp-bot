import telebot
from telebot import types
import requests
import os
from flask import Flask
from threading import Thread

# ---- Render Port Binding ----
app = Flask(__name__)

@app.route('/')
def home():
    return "SmsBower Bot is Running Live!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

Thread(target=run_flask).start()
# -----------------------------

# ----------------- কনফিগারেশন -----------------
BOT_TOKEN = "8810955739:AAFM2xIwPK3PL_PnYu8Ic5VSljdQ3gA1I0Q" # @BotFather থেকে পাওয়া টোকেন
API_KEY = "Ztru33vtO2GyFwduMfXuKRTGFvnnx7Os"
SMS_BOWER_API = "https://smsbower.page/stubs/handler_api.php"
# -----------------------------------------------

# দেশের কোডের সাথে দেশের নাম ও পতাকার ম্যাপ
COUNTRY_NAMES = {
    "0": "🇷🇺 Russia",
    "1": "🇺🇦 Ukraine",
    "2": "🇰🇿 Kazakhstan",
    "3": "🇨🇳 China",
    "4": "🇵🇭 Philippines",
    "5": "🇲🇲 Myanmar",
    "6": "🇮🇩 Indonesia",
    "7": "🇲🇾 Malaysia",
    "11": "🇬🇧 UK",
    "12": "🇻🇳 Vietnam",
    "13": "🇰🇬 Kyrgyzstan",
    "15": "🇵🇱 Poland",
    "19": "🇳🇬 Nigeria",
    "22": "🇮🇳 India",
    "32": "🇷🇴 Romania",
    "36": "🇨🇦 Canada",
    "60": "🇧🇩 Bangladesh",
    "187": "🇺🇸 USA"
}

bot = telebot.TeleBot(BOT_TOKEN)

# /start কমান্ড
@bot.message_handler(commands=['start'])
def welcome(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("📱 নাম্বার কিনুন")
    btn2 = types.KeyboardButton("💰 ব্যালেন্স দেখুন")
    btn3 = types.KeyboardButton("❓ সাহায্য")
    markup.add(btn1, btn2, btn3)
    
    bot.send_message(
        message.chat.id, 
        "👋 **SmsBower ভার্চুয়াল নাম্বার ও ওটিপি বটে স্বাগতম!**\n\nনিচের মেনু থেকে সার্ভিস বেছে নিন।",
        parse_mode="Markdown", 
        reply_markup=markup
    )

# মেনু বাটন হ্যান্ডলার
@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    chat_id = message.chat.id
    text = message.text

    # ১. ব্যালেন্স দেখা
    if text == "💰 ব্যালেন্স দেখুন":
        bot.send_message(chat_id, "⏳ ব্যালেন্স চেক করা হচ্ছে...")
        try:
            res = requests.get(SMS_BOWER_API, params={"api_key": API_KEY, "action": "getBalance"})
            if "ACCESS_BALANCE" in res.text:
                bal = res.text.split(":")[1]
                bot.send_message(chat_id, f"💵 **আপনার সাইট ব্যালেন্স:** `${bal}`", parse_mode="Markdown")
            else:
                bot.send_message(chat_id, f"❌ রেসপন্স: {res.text}")
        except Exception as e:
            bot.send_message(chat_id, "❌ সার্ভারে কানেক্ট করতে সমস্যা হয়েছে।")

    # ২. সার্ভিস চয়েস (এখানে ফেসবুক সহ অন্যান্য সার্ভিস যোগ করা হয়েছে)
    elif text == "📱 নাম্বার কিনুন":
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_fb = types.InlineKeyboardButton("🔵 Facebook (fb)", callback_data="service_fb")
        btn_tg = types.InlineKeyboardButton("✈️ Telegram (tg)", callback_data="service_tg")
        btn_wa = types.InlineKeyboardButton("🟢 WhatsApp (wa)", callback_data="service_wa")
        btn_ig = types.InlineKeyboardButton("📸 Instagram (ig)", callback_data="service_ig")
        btn_im = types.InlineKeyboardButton("🟡 Imo (im)", callback_data="service_im")
        btn_tk = types.InlineKeyboardButton("🎵 TikTok (lf)", callback_data="service_lf")
        markup.add(btn_fb, btn_tg, btn_wa, btn_ig, btn_im, btn_tk)
        
        bot.send_message(chat_id, "কোন সার্ভিসের জন্য নাম্বার চান নিচে থেকে সিলেক্ট করুন:", reply_markup=markup)

    elif text == "❓ সাহায্য":
        bot.send_message(chat_id, "সহায়তার জন্য অ্যাডমিনের সাথে যোগাযোগ করুন।")

# ইনলাইন বাটন হ্যান্ডলার (ডায়নামিক কান্ট্রি, প্রাইস ও স্টক লোড)
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    chat_id = call.message.chat.id
    
    # সার্ভিস পছন্দ করার পর সাইট থেকে লাইভ দাম ও স্টক নিয়ে আসার অংশ
    if call.data.startswith("service_"):
        service = call.data.split("_")[1]
        bot.answer_callback_query(call.id, "সাইট থেকে দাম ও স্টক লোড করা হচ্ছে...")
        
        try:
            # সাইটের getPrices API থেকে লাইভ রেট নিয়ে আসা
            res = requests.get(SMS_BOWER_API, params={
                "api_key": API_KEY,
                "action": "getPrices",
                "service": service
            })
            
            data = res.json()
            markup = types.InlineKeyboardMarkup(row_width=1)
            count = 0
            
            # ডাটা প্রসেস করে দেশের বাটন তৈরি
            for country_id, services in data.items():
                if service in services:
                    price = services[service].get("cost") or services[service].get("price") or "N/A"
                    qty = services[service].get("count") or 0
                    
                    # শুধু যে দেশে স্টক আছে সেগুলো দেখাবে
                    if int(qty) > 0:
                        c_name = COUNTRY_NAMES.get(str(country_id), f"Country #{country_id}")
                        btn_text = f"{c_name} — ${price} (স্টক: {qty} টি)"
                        btn = types.InlineKeyboardButton(btn_text, callback_data=f"buy_{service}_{country_id}")
                        markup.add(btn)
                        count += 1
                        
                        if count >= 15: # বেশি বড় লিস্ট যাতে না হয় তাই টপ ১৫টি দেশ দেখাবে
                            break
            
            if count == 0:
                bot.send_message(chat_id, "❌ দুঃখিত, এই সার্ভিসের জন্য এই মুহূর্তে কোনো দেশের নাম্বার স্টকে নেই।")
            else:
                bot.edit_message_text(
                    f"আপনার নির্বাচিত সার্ভিস: **{service.upper()}**\n\nনিচে উপলব্ধ দেশ, দাম ও স্টকের তালিকা দেওয়া হলো (পছন্দের দেশে ক্লিক করুন):", 
                    chat_id, 
                    call.message.message_id, 
                    parse_mode="Markdown", 
                    reply_markup=markup
                )
        except Exception as e:
            bot.send_message(chat_id, "❌ সাইট থেকে প্রাইস লোড করতে সমস্যা হয়েছে।")

    # নির্দিষ্ট দেশের ওপর ক্লিক করলে ওই নাম্বারটি ক্রয় করা
    elif call.data.startswith("buy_"):
        parts = call.data.split("_")
        service = parts[1]
        country_id = parts[2]
        
        bot.answer_callback_query(call.id, "নাম্বার কেনা হচ্ছে...")
        
        try:
            res = requests.get(SMS_BOWER_API, params={
                "api_key": API_KEY,
                "action": "getNumber",
                "service": service,
                "country": country_id
            })
            
            if "ACCESS_NUMBER" in res.text:
                res_parts = res.text.split(":")
                act_id = res_parts[1]
                number = res_parts[2]
                
                msg = (
                    f"✅ **নাম্বার কেনা সফল হয়েছে!**\n\n"
                    f"📱 **নাম্বার:** `{number}`\n"
                    f"🆔 **অর্ডার আইডি:** `{act_id}`\n\n"
                    f"অ্যাপে নাম্বারটি বসিয়ে কোড পাঠান, তারপর নিচে ওটিপি বাটনে চাপুন।"
                )
                
                markup = types.InlineKeyboardMarkup()
                btn_check = types.InlineKeyboardButton("🔄 OTP / কোড চেক করুন", callback_data=f"check_{act_id}")
                btn_cancel = types.InlineKeyboardButton("❌ ক্যানসেল করুন", callback_data=f"cancel_{act_id}")
                markup.add(btn_check, btn_cancel)
                
                bot.send_message(chat_id, msg, parse_mode="Markdown", reply_markup=markup)
            else:
                bot.send_message(chat_id, f"❌ নাম্বার পাওয়া যায়নি। উত্তর: {res.text}")
        except Exception as e:
            bot.send_message(chat_id, "❌ নেটওয়ার্ক ত্রুটি।")

    # OTP কোড চেক করা
    elif call.data.startswith("check_"):
        act_id = call.data.split("_")[1]
        bot.answer_callback_query(call.id, "SMS চেক করা হচ্ছে...")
        
        try:
            res = requests.get(SMS_BOWER_API, params={
                "api_key": API_KEY,
                "action": "getStatus",
                "id": act_id
            })
            
            if "STATUS_OK" in res.text:
                code = res.text.split(":")[1]
                bot.send_message(chat_id, f"🎉 **আপনার OTP কোড:** `{code}`", parse_mode="Markdown")
            elif "STATUS_WAIT_CODE" in res.text:
                bot.send_message(chat_id, "⏳ এখনো কোনো SMS আসেনি। আবার চেষ্টা করুন।")
            else:
                bot.send_message(chat_id, f"স্ট্যাটাস: {res.text}")
        except Exception as e:
            bot.send_message(chat_id, "❌ চেক করতে সমস্যা হয়েছে।")

    # অর্ডার ক্যানসেল
    elif call.data.startswith("cancel_"):
        act_id = call.data.split("_")[1]
        bot.answer_callback_query(call.id, "ক্যানসেল করা হচ্ছে...")
        
        try:
            requests.get(SMS_BOWER_API, params={
                "api_key": API_KEY,
                "action": "setStatus",
                "id": act_id,
                "status": "8"
            })
            bot.send_message(chat_id, "🚫 অর্ডারটি ক্যানসেল করা হয়েছে।")
        except Exception as e:
            bot.send_message(chat_id, "❌ ক্যানসেল করা যায়নি।")

bot.infinity_polling()
