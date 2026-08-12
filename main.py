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
BOT_TOKEN = "8810955739:AAFM2xIwPK3PL_PnYu8Ic5VSljdQ3gA1I0Q"
API_KEY = "Ztru33vtO2GyFwduMfXuKRTGFvnnx7Os"
SMS_BOWER_API = "https://smsbower.page/stubs/handler_api.php"
ALLOWED_USER_ID = 7418898985
# -----------------------------------------------

bot = telebot.TeleBot(BOT_TOKEN)

# সাইট থেকে সব দেশের আসল নাম ডাউনলোড করার ফাংশন
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

GLOBAL_COUNTRIES = get_dynamic_country_names()

def is_authorized(chat_id):
    return str(chat_id) == str(ALLOWED_USER_ID)

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

@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    if not is_authorized(message.chat.id):
        bot.send_message(message.chat.id, "⛔ **অনুমতি নেই!**")
        return

    chat_id = message.chat.id
    text = message.text

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

    # ধাপ ১: সার্ভিস পছন্দ করা (ভিডিওর ধাপ ১)
    elif text == "📱 নাম্বার কিনুন":
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_fb = types.InlineKeyboardButton("🔵 Facebook", callback_data="service_fb")
        btn_tg = types.InlineKeyboardButton("✈️ Telegram", callback_data="service_tg")
        btn_wa = types.InlineKeyboardButton("🟢 WhatsApp", callback_data="service_wa")
        btn_ig = types.InlineKeyboardButton("📸 Instagram", callback_data="service_ig")
        btn_im = types.InlineKeyboardButton("🟡 Imo", callback_data="service_im")
        btn_tk = types.InlineKeyboardButton("🎵 TikTok", callback_data="service_lf")
        markup.add(btn_fb, btn_tg, btn_wa, btn_ig, btn_im, btn_tk)
        
        bot.send_message(chat_id, "১. প্রথমে সার্ভিস সিলেক্ট করুন:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    global GLOBAL_COUNTRIES
    if not is_authorized(call.message.chat.id):
        bot.answer_callback_query(call.id, "⛔ অনুমতি নেই!", show_alert=True)
        return

    chat_id = call.message.chat.id
    
    # ধাপ ২: সার্ভিস সিলেক্ট করার পরই কোয়ালিটি/র‍্যাংক সিলেক্ট করার অপশন আসবে (ভিডিওর ধাপ ২)
    if call.data.startswith("service_"):
        service = call.data.split("_")[1]
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_gold = types.InlineKeyboardButton("🥇 Gold Rank", callback_data=f"rank_{service}_gold")
        btn_silver = types.InlineKeyboardButton("🥈 Silver Rank", callback_data=f"rank_{service}_silver")
        btn_bronze = types.InlineKeyboardButton("🥉 Bronze Rank", callback_data=f"rank_{service}_bronze")
        btn_all = types.InlineKeyboardButton("🌐 All Ranks", callback_data=f"rank_{service}_all")
        markup.add(btn_gold, btn_silver, btn_bronze, btn_all)

        bot.edit_message_text(
            f"সার্ভিস: **{service.upper()}**\n\n২. এবার কোয়ালিটি (Rank) সিলেক্ট করুন:",
            chat_id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )

    # ধাপ ৩: সাইটের আসল হুবহু দাম ও দেশ নিয়ে আসা (ভিডিওর ধাপ ৩)
    elif call.data.startswith("rank_"):
        parts = call.data.split("_")
        service = parts[1]
        rank = parts[2]
        
        bot.answer_callback_query(call.id, f"{rank.upper()} এর দাম ও দেশ লোড করা হচ্ছে...")
        
        try:
            if not GLOBAL_COUNTRIES:
                GLOBAL_COUNTRIES = get_dynamic_country_names()

            # ক্লিন রিকোয়েস্ট (যাতে সাইটের ১০০% আসল দাম আসে)
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
                        c_name = GLOBAL_COUNTRIES.get(str(country_id), f"Country #{country_id}")
                        # সাইটের সাথে ১০০% হুবহু আসল দাম ও স্টক প্রদর্শন
                        btn_text = f"🌐 {c_name} — ${price} ({qty} টি স্টকে)"
                        btn = types.InlineKeyboardButton(btn_text, callback_data=f"buy_{service}_{country_id}_{rank}")
                        markup.add(btn)
                        count += 1
                        if count >= 20: # টপ ২০টি দেশ
                            break
            
            if count == 0:
                bot.send_message(chat_id, f"❌ এই মুহূর্তে {service.upper()} সার্ভিসের কোনো নাম্বার স্টকে নেই।")
            else:
                bot.edit_message_text(
                    f"সার্ভিস: **{service.upper()}** | কোয়ালিটি: **{rank.upper()}**\n\n৩. সাইটের সাথে মিল থাকা স্টকে থাকা দেশ বেছে নিন:", 
                    chat_id, 
                    call.message.message_id, 
                    parse_mode="Markdown", 
                    reply_markup=markup
                )
        except Exception as e:
            bot.send_message(chat_id, "❌ ডাটা লোড করতে সমস্যা হয়েছে।")

    # ধাপ ৪: নাম্বার পারচেজ করা (ভিডিওর ধাপ ৪)
    elif call.data.startswith("buy_"):
        parts = call.data.split("_")
        service = parts[1]
        country_id = parts[2]
        rank = parts[3]
        
        c_name = GLOBAL_COUNTRIES.get(str(country_id), f"Country #{country_id}")
        bot.answer_callback_query(call.id, f"{c_name} এর {rank.upper()} নাম্বার কেনা হচ্ছে...")
        
        try:
            params = {
                "api_key": API_KEY,
                "action": "getNumber",
                "service": service,
                "country": country_id
            }
            
            if rank != "all":
                params["rank"] = rank

            res = requests.get(SMS_BOWER_API, params=params)
            
            if "ACCESS_NUMBER" in res.text:
                res_parts = res.text.split(":")
                act_id = res_parts[1]
                number = res_parts[2]
                
                msg = (
                    f"🎉 **Done. You've gotten a number!**\n\n"
                    f"📱 **সার্ভিস:** `{service.upper()}`\n"
                    f"🏆 **কোয়ালিটি:** `{rank.upper()}`\n"
                    f"🌐 **দেশ:** `{c_name}`\n"
                    f"📞 **নাম্বার:** `{number}`\n"
                    f"🆔 **অর্ডার আইডি:** `{act_id}`\n\n"
                    f"অ্যাপে নাম্বারটি বসিয়ে কোড পাঠান, তারপর নিচে চেক চাপুন।"
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
            bot.send_message(chat_id, "❌ এরর হয়েছে।")

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
