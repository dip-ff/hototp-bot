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
    return "Personal SmsBower Bot is Running Live!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

Thread(target=run_flask).start()
# -----------------------------

# ----------------- কনফিগারেশন -----------------
BOT_TOKEN = "8810955739:AAFM2xIwPK3PL_PnYu8Ic5VSljdQ3gA1I0Q" # @BotFather থেকে পাওয়া বটের টোকেন
API_KEY = "Ztru33vtO2GyFwduMfXuKRTGFvnnx7Os"
SMS_BOWER_API = "https://smsbower.page/stubs/handler_api.php"

# আপনার নিজস্ব টেলিগ্রাম ইউজার আইডি
ALLOWED_USER_ID = 7418898985 
# -----------------------------------------------

bot = telebot.TeleBot(BOT_TOKEN)

# সাইট থেকে ডায়নামিক্যালি সব দেশের আসল নাম ডাউনলোড করার ফাংশন
def get_dynamic_country_names():
    try:
        res = requests.get(SMS_BOWER_API, params={"api_key": API_KEY, "action": "getCountries"})
        data = res.json()
        countries_map = {}
        
        if isinstance(data, list):
            for c in data:
                c_id = str(c.get("id"))
                name = c.get("eng") or c.get("name") or c.get("rus") or f"Country #{c_id}"
                countries_map[c_id] = name
        elif isinstance(data, dict):
            for c_id, c in data.items():
                if isinstance(c, dict):
                    name = c.get("eng") or c.get("name") or c.get("rus") or f"Country #{c_id}"
                    countries_map[str(c_id)] = name
                else:
                    countries_map[str(c_id)] = str(c)
        return countries_map
    except Exception as e:
        return {}

# গ্লোবালি সব দেশের নাম ক্যাশে রাখা
GLOBAL_COUNTRIES = get_dynamic_country_names()

# সিকিউরিটি ফিল্টার (অন্য কেউ বট চালাতে পারবে না)
def is_authorized(chat_id):
    return str(chat_id) == str(ALLOWED_USER_ID)

# /start কমান্ড
@bot.message_handler(commands=['start'])
def welcome(message):
    if not is_authorized(message.chat.id):
        bot.send_message(message.chat.id, "⛔ **দুঃখিত!** এটি একটি পার্সোনাল বট। আপনার এটি ব্যবহারের অনুমতি নেই।")
        return

    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("📱 নাম্বার কিনুন")
    btn2 = types.KeyboardButton("💰 ব্যালেন্স দেখুন")
    markup.add(btn1, btn2)
    
    bot.send_message(
        message.chat.id, 
        "👋 **স্বাগতম! আপনার পার্সোনাল ওটিপি বটে আপনাকে স্বাগতম।**",
        parse_mode="Markdown", 
        reply_markup=markup
    )

# মেনু বাটন হ্যান্ডলার
@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    if not is_authorized(message.chat.id):
        bot.send_message(message.chat.id, "⛔ **অনুমতি নেই!**")
        return

    chat_id = message.chat.id
    text = message.text

    # ১. ব্যালেন্স দেখা
    if text == "💰 ব্যালেন্স দেখুন":
        bot.send_message(chat_id, "⏳ সাইট ব্যালেন্স চেক করা হচ্ছে...")
        try:
            res = requests.get(SMS_BOWER_API, params={"api_key": API_KEY, "action": "getBalance"})
            if "ACCESS_BALANCE" in res.text:
                bal = res.text.split(":")[1]
                bot.send_message(chat_id, f"💵 **আপনার সাইট ব্যালেন্স:** `${bal}`", parse_mode="Markdown")
            else:
                bot.send_message(chat_id, f"❌ রেসপন্স: {res.text}")
        except Exception as e:
            bot.send_message(chat_id, "❌ সার্ভার কানেকশন এরর।")

    # ২. সার্ভিস চয়েস
    elif text == "📱 নাম্বার কিনুন":
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_fb = types.InlineKeyboardButton("🔵 Facebook", callback_data="service_fb")
        btn_tg = types.InlineKeyboardButton("✈️ Telegram", callback_data="service_tg")
        btn_wa = types.InlineKeyboardButton("🟢 WhatsApp", callback_data="service_wa")
        btn_ig = types.InlineKeyboardButton("📸 Instagram", callback_data="service_ig")
        btn_im = types.InlineKeyboardButton("🟡 Imo", callback_data="service_im")
        btn_tk = types.InlineKeyboardButton("🎵 TikTok", callback_data="service_lf")
        markup.add(btn_fb, btn_tg, btn_wa, btn_ig, btn_im, btn_tk)
        
        bot.send_message(chat_id, "কোন সার্ভিসের জন্য নাম্বার চান বেছে নিন:", reply_markup=markup)

# ইনলাইন বাটন হ্যান্ডলার
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    global GLOBAL_COUNTRIES
    if not is_authorized(call.message.chat.id):
        bot.answer_callback_query(call.id, "⛔ অনুমতি নেই!", show_alert=True)
        return

    chat_id = call.message.chat.id
    
    if call.data.startswith("service_"):
        service = call.data.split("_")[1]
        bot.answer_callback_query(call.id, "সাইট থেকে ডায়নামিক তথ্য আনা হচ্ছে...")
        
        try:
            # ক্যানট্রি লিস্ট খালি থাকলে নতুন করে লোড করবে
            if not GLOBAL_COUNTRIES:
                GLOBAL_COUNTRIES = get_dynamic_country_names()

            res = requests.get(SMS_BOWER_API, params={
                "api_key": API_KEY,
                "action": "getPrices",
                "service": service
            })
            
            data = res.json()
            markup = types.InlineKeyboardMarkup(row_width=1)
            count = 0
            
            for country_id, services in data.items():
                if service in services:
                    price = services[service].get("cost") or services[service].get("price") or "N/A"
                    qty = services[service].get("count") or 0
                    
                    if int(qty) > 0:
                        # সম্পূর্ণ সাইটের ডাটাবেজ থেকে আসা দেশের আসল নাম
                        c_name = GLOBAL_COUNTRIES.get(str(country_id), f"Country #{country_id}")
                        btn_text = f"🌐 {c_name} — ${price} ({qty} টি খালি আছে)"
                        btn = types.InlineKeyboardButton(btn_text, callback_data=f"buy_{service}_{country_id}")
                        markup.add(btn)
                        count += 1
                        if count >= 20: # টপ ২০টি খালি থাকা দেশ দেখাবে
                            break
            
            if count == 0:
                bot.send_message(chat_id, "❌ এই মুহূর্তে কোনো নাম্বার স্টকে নেই।")
            else:
                bot.edit_message_text(
                    f"সার্ভিস: **{service.upper()}**\n\nসাইটে স্টকে থাকা সকল দেশের আসল তালিকা:", 
                    chat_id, 
                    call.message.message_id, 
                    parse_mode="Markdown", 
                    reply_markup=markup
                )
        except Exception as e:
            bot.send_message(chat_id, "❌ ডাটা লোড করতে সমস্যা হয়েছে।")

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
                    f"✅ **নাম্বার কেনা সফল হয়েছে!**\n\n"
                    f"📱 **নাম্বার:** `{number}`\n"
                    f"🆔 **অর্ডার আইডি:** `{act_id}`\n\n"
                    f"কোড পাঠাতে এই নাম্বারটি ব্যবহার করুন।"
                )
                
                markup = types.InlineKeyboardMarkup()
                btn_check = types.InlineKeyboardButton("🔄 OTP / কোড চেক করুন", callback_data=f"check_{act_id}")
                btn_cancel = types.InlineKeyboardButton("❌ ক্যানসেল করুন", callback_data=f"cancel_{act_id}")
                markup.add(btn_check, btn_cancel)
                
                bot.send_message(chat_id, msg, parse_mode="Markdown", reply_markup=markup)
            else:
                bot.send_message(chat_id, f"❌ নাম্বার পাওয়া যায়নি: {res.text}")
        except Exception as e:
            bot.send_message(chat_id, "❌ এরর হয়েছে।")

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
            bot.send_message(chat_id, "❌ এরর হয়েছে।")

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
