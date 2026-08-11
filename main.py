import telebot
from telebot import types
import requests

# ----------------- আপনার কনফিগারেশন -----------------
BOT_TOKEN = "8810955739:AAER3iDZeDClsCpdDJvAYcqQzFugGMxsUE4"
API_KEY = "Ztru33vtO2GyFwduMfXuKRTGFvnnx7Os"
GRIZZLY_API_URL = "https://api.grizzlysms.com/stubs/handler_api.php"
# -----------------------------------------------

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
        "👋 **ভার্চুয়াল নাম্বার ও ওটিপি বটে স্বাগতম!**\n\nনিচের মেনু থেকে সার্ভিস বেছে নিন।",
        parse_mode="Markdown", 
        reply_markup=markup
    )

# মেনু বাটন হ্যান্ডলার
@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    chat_id = message.chat.id
    text = message.text

    # ১. ব্যালেন্স চেক
    if text == "💰 ব্যালেন্স দেখুন":
        bot.send_message(chat_id, "⏳ ব্যালেন্স চেক করা হচ্ছে...")
        try:
            res = requests.get(GRIZZLY_API_URL, params={"api_key": API_KEY, "action": "getBalance"})
            if "ACCESS_BALANCE" in res.text:
                bal = res.text.split(":")[1]
                bot.send_message(chat_id, f"💵 **আপনার সাইট ব্যালেন্স:** `${bal}`", parse_mode="Markdown")
            else:
                bot.send_message(chat_id, f"❌ রেসপন্স: {res.text}")
        except Exception as e:
            bot.send_message(chat_id, "❌ সার্ভারে কানেক্ট করতে সমস্যা হয়েছে।")

    # ২. সার্ভিস চয়েস
    elif text == "📱 নাম্বার কিনুন":
        markup = types.InlineKeyboardMarkup()
        btn_tg = types.InlineKeyboardButton("Telegram (tg)", callback_data="buy_tg")
        btn_wa = types.InlineKeyboardButton("WhatsApp (wa)", callback_data="buy_wa")
        btn_ig = types.InlineKeyboardButton("Instagram (ig)", callback_data="buy_ig")
        markup.add(btn_tg, btn_wa, btn_ig)
        bot.send_message(chat_id, "কোন সার্ভিসের জন্য নাম্বার চান বেছে নিন:", reply_markup=markup)

    elif text == "❓ সাহায্য":
        bot.send_message(chat_id, "সহায়তার জন্য অ্যাডমিনের সাথে যোগাযোগ করুন।")

# ইনলাইন বাটন হ্যান্ডলার (নাম্বার কেনা ও ওটিপি দেখা)
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    chat_id = call.message.chat.id
    
    # নাম্বার কেনা
    if call.data.startswith("buy_"):
        service = call.data.split("_")[1]
        bot.answer_callback_query(call.id, "নাম্বার রিকোয়েস্ট করা হচ্ছে...")
        
        try:
            # USA (Country Code: 187) নাম্বার রিকোয়েস্ট
            res = requests.get(GRIZZLY_API_URL, params={
                "api_key": API_KEY,
                "action": "getNumber",
                "service": service,
                "country": "187"
            })
            
            if "ACCESS_NUMBER" in res.text:
                parts = res.text.split(":")
                act_id = parts[1]
                number = parts[2]
                
                msg = (
                    f"✅ **নাম্বার তৈরি হয়েছে!**\n\n"
                    f"📱 **নাম্বার:** `{number}`\n"
                    f"🆔 **অর্ডার আইডি:** `{act_id}`\n\n"
                    f"অ্যাপে নাম্বারটি বসিয়ে কোড পাঠান, তারপর নিচে চাপুন।"
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

    # OTP কোড চেক
    elif call.data.startswith("check_"):
        act_id = call.data.split("_")[1]
        bot.answer_callback_query(call.id, "SMS চেক করা হচ্ছে...")
        
        try:
            res = requests.get(GRIZZLY_API_URL, params={
                "api_key": API_KEY,
                "action": "getStatus",
                "id": act_id
            })
            
            if "STATUS_OK" in res.text:
                code = res.text.split(":")[1]
                bot.send_message(chat_id, f"🎉 **আপনার OTP কোড:** `{code}`", parse_mode="Markdown")
            elif "STATUS_WAIT_CODE" in res.text:
                bot.send_message(chat_id, "⏳ এখনো কোনো SMS আসেনি। কিছুক্ষণ পর আবার চেষ্টা করুন।")
            else:
                bot.send_message(chat_id, f"স্ট্যাটাস: {res.text}")
        except Exception as e:
            bot.send_message(chat_id, "❌ চেক করতে সমস্যা হয়েছে।")

    # অর্ডার ক্যানসেল
    elif call.data.startswith("cancel_"):
        act_id = call.data.split("_")[1]
        bot.answer_callback_query(call.id, "ক্যানসেল করা হচ্ছে...")
        
        try:
            requests.get(GRIZZLY_API_URL, params={
                "api_key": API_KEY,
                "action": "setStatus",
                "id": act_id,
                "status": "8"
            })
            bot.send_message(chat_id, "🚫 অর্ডারটি ক্যানসেল করা হয়েছে।")
        except Exception as e:
            bot.send_message(chat_id, "❌ ক্যানসেল করা যায়নি।")

bot.infinity_polling()
