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
    return "HotOtp Deep Smart OTP Catcher Active!", 200

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

# ⚠️ এখানে /myid লিখে পাওয়া আপনার টেলিগ্রাম আইডি বসিয়ে দেবেন (যেমন: 123456789)
ADMIN_ID = None  

BOT_USERNAME = "hot_opt_bot"              # বটের ইউজারনেম

bot = telebot.TeleBot(BOT_TOKEN)

# ডাটাবেজ ফাইল
DATA_FILE = "user_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                d = json.load(f)
                if "settings" not in d:
                    d["settings"] = {"support": "@hototpotp", "otp_group": "@hototpotp", "range_group": "@hototprange"}
                return d
        except: pass
    return {
        "users": [], 
        "ranges": {}, 
        "total_otps": 0, 
        "settings": {"support": "@hototpotp", "otp_group": "@hototpotp", "range_group": "@hototprange"}
    }

def save_data():
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(db, f)
    except: pass

db = load_data()

def mask_phone_number(number_str):
    clean = str(number_str).replace("+", "").strip()
    if len(clean) >= 10: return clean[:5] + "****" + clean[-3:]
    elif len(clean) >= 7: return clean[:3] + "***" + clean[-2:]
    return clean

def is_admin(chat_id):
    if ADMIN_ID is None: return True
    return str(chat_id) == str(ADMIN_ID) or chat_id == ADMIN_ID

def get_setting(key, default_val):
    try:
        val = db.get("settings", {}).get(key)
        return val if val else default_val
    except:
        return default_val

posted_signatures = set()

# কিবোর্ড বাটনের লিস্ট
MENU_BUTTONS = [
    "☎️ Get Number", "⚙️ Change Range", "📱 Range Group", 
    "✉️ Get Tempmail", "🔐 2FA", "👤 Fake Name", "🔽 OTHER", 
    "💬 Support", "🏠 Home"
]

# ----------------------------------------------------
# ৩. স্মার্ট ওটিপি এক্সট্রাক্টর (যে কোনো ফিল্ড থেকে কোড বের করবে)
# ----------------------------------------------------
def extract_otp_smart(res_json):
    if not res_json:
        return None

    if isinstance(res_json, dict):
        # ১. নির্দিষ্ট জানা কি (Keys) স্ক্যান করা
        for key in ['code', 'otp', 'sms', 'sms_code', 'data', 'message', 'text', 'full']:
            val = res_json.get(key)
            if val is not None and str(val).strip() != "" and str(val).strip().lower() not in ["null", "none", "false"]:
                return str(val).strip()
        
        # ২. ডিকশনারির সব ফিল্ড চেক করা
        for k, v in res_json.items():
            if k not in ['success', 'status', 'expires_in', 'number_id', 'id', 'country', 'number'] and v:
                if isinstance(v, (str, int)) and str(v).strip() != "":
                    return str(v).strip()
                elif isinstance(v, dict):
                    sub = extract_otp_smart(v)
                    if sub: return sub
                elif isinstance(v, list) and len(v) > 0:
                    sub = extract_otp_smart(v[0])
                    if sub: return sub

    elif isinstance(res_json, list) and len(res_json) > 0:
        return extract_otp_smart(res_json[0])

    return None

# ----------------------------------------------------
# ৪. টেলিগ্রাম পপ-আপ মেনু কমান্ডস
# ----------------------------------------------------
try:
    bot_commands = [
        types.BotCommand("start", "🚀 Start"),
        types.BotCommand("home", "🏠 Home"),
        types.BotCommand("number", "☎️ Get Number"),
        types.BotCommand("range", "⚙️ Change Range"),
        types.BotCommand("tempmail", "✉️ Get Tempmail"),
        types.BotCommand("twofa", "🔐 2FA"),
        types.BotCommand("admin", "⚙️ Admin Panel"),
        types.BotCommand("help", "💬 Support"),
        types.BotCommand("other", "🔽 OTHER")
    ]
    bot.set_my_commands(bot_commands)
except Exception as e:
    print(f"Commands set error: {e}")

# ----------------------------------------------------
# ৫. স্থায়ী নিচের কিবোর্ড বাটন
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
    markup.add(types.KeyboardButton("💬 Support"), types.KeyboardButton("🏠 Home"))
    return markup

print("---------------------------------")
print("🔥 HotOtp Smart Deep Catcher Active!")
print("---------------------------------")

# ----------------------------------------------------
# ৬. সাইটের কনসোল লাইভ অটো-পোস্টার
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
    last_post_time = time.time()
    while True:
        try:
            range_group = get_setting("range_group", "@hototprange")
            logs = fetch_all_site_logs()
            posted_any = False

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
                    if len(posted_signatures) > 500: posted_signatures.clear()

                    raw_num = number.replace("+", "").strip()
                    if "XXX" in raw_num: range_str = raw_num
                    elif len(raw_num) > 8: range_str = raw_num[:8] + "XXX"
                    elif len(raw_num) > 5: range_str = raw_num[:5] + "XXX"
                    else: range_str = raw_num + "XXX"

                    msg_text_display = f"<code>{sms_preview}</code>" if sms_preview else "Live Signal Received ⭐"

                    post_text = (
                        f"🔥 <b>HOT OTP LIVE CONSOLE</b> 🔥\n\n"
                        f"📱 <b>Range:</b> <code>{range_str}</code>\n"
                        f"🎯 <b>Service:</b> {service}\n"
                        f"🌐 <b>Country:</b> {country}\n"
                        f"💬 <b>SMS:</b> {msg_text_display}\n\n"
                        f"👇 <b>১-ক্লিকে এই রেঞ্জ দিয়ে নাম্বার নিতে নিচে চাপ দিন:</b>"
                    )

                    markup = types.InlineKeyboardMarkup()
                    btn_bot = types.InlineKeyboardButton("🤖 HotOtp Bot-এ এই নাম্বার নিন", url=f"https://t.me/{BOT_USERNAME}?start={range_str}")
                    markup.add(btn_bot)

                    try:
                        bot.send_message(range_group, post_text, reply_markup=markup, parse_mode="HTML")
                        last_post_time = time.time()
                        posted_any = True
                        time.sleep(4)
                    except telebot.apihelper.ApiTelegramException as te:
                        if te.error_code == 429: time.sleep(20)
                    except Exception: time.sleep(3)

            if not posted_any and (time.time() - last_post_time > 120) and isinstance(logs, list) and len(logs) > 0:
                for item in logs:
                    if isinstance(item, dict):
                        number = str(item.get("number") or item.get("range") or "").strip()
                        country = str(item.get("country") or "Global").strip()
                        service = str(item.get("service") or "OTP Service").strip()
                        if not number or len(number) < 4: continue
                        
                        raw_num = number.replace("+", "").strip()
                        range_str = raw_num[:8] + "XXX" if len(raw_num) > 8 else raw_num + "XXX"
                        
                        post_text = (
                            f"⚡ <b>HOT ACTIVE LIVE RANGE</b> ⚡\n\n"
                            f"📱 <b>Range:</b> <code>{range_str}</code>\n"
                            f"🎯 <b>Service:</b> {service}\n"
                            f"🌐 <b>Country:</b> {country}\n"
                            f"🔥 <b>Status:</b> Highly Active Range ⭐\n\n"
                            f"👇 <b>১-ক্লিকে এই রেঞ্জ দিয়ে নাম্বার নিতে নিচে চাপ দিন:</b>"
                        )
                        markup = types.InlineKeyboardMarkup()
                        markup.add(types.InlineKeyboardButton("🤖 HotOtp Bot-এ এই নাম্বার নিন", url=f"https://t.me/{BOT_USERNAME}?start={range_str}"))
                        
                        try:
                            bot.send_message(range_group, post_text, reply_markup=markup, parse_mode="HTML")
                            last_post_time = time.time()
                        except Exception: pass
                        break

        except Exception as e: print(f"Loop error: {e}")
        time.sleep(10)

threading.Thread(target=auto_post_live_ranges, daemon=True).start()

# ----------------------------------------------------
# ৭. ১০০% গ্যারান্টেড ওটিপি ফিল্টার
# ----------------------------------------------------
def fetch_otp(num_id, number):
    headers = {"X-API-Key": NEXA_API_KEY}
    
    # পদ্ধতি ১: সকল ইঞ্জিনের সরাসরি নাম্বার ওটিপি চেক
    urls = [
        f"https://nexaotpservice.com/api/v1/numbers/{num_id}/sms",
        f"https://nexaotpservice.com/api/v1/numbers/p2/{num_id}/sms",
        f"https://nexaotpservice.com/api/v1/numbers/p3/{num_id}/sms",
        f"https://nexaotpservice.com/api/v1/sms/recent"
    ]
    
    for u in urls:
        try:
            res1 = requests.get(u, headers=headers, timeout=5).json()
            found = extract_otp_smart(res1)
            if found:
                return f"📩 <b>OTP Received:</b> <code>{found}</code>"
        except Exception: pass

    # পদ্ধতি ২: সাইটের অল-ইঞ্জিন লগস থেকে ফোন নম্বর বা আইডি ম্যাচিং
    try:
        logs = fetch_all_site_logs()
        clean_target_num = str(number).replace("+", "").strip()
        
        for item in logs:
            if isinstance(item, dict):
                item_num = str(item.get("number") or item.get("phone") or "").replace("+", "").strip()
                item_id = str(item.get("number_id") or item.get("id") or "").strip()
                
                if (clean_target_num and clean_target_num in item_num) or (num_id and num_id == item_id):
                    found = extract_otp_smart(item)
                    if found:
                        return f"📩 <b>OTP Received:</b> <code>{found}</code>"
    except Exception: pass
    
    return None

def auto_check_otp(chat_id, num_id, number):
    for _ in range(60): # ৩ মিনিট ব্যাকগ্রাউন্ডে চেক করবে
        time.sleep(3)
        otp = fetch_otp(num_id, number)
        if otp:
            db["total_otps"] = db.get("total_otps", 0) + 1
            save_data()
            
            # ১. ইউজারের ইনবক্সে সাথে সাথে মেসেজ পাঠানো
            bot.send_message(chat_id, f"🎉 <b>ওটিপি চলে এসেছে!</b>\n\n{otp}", parse_mode="HTML")
            
            # ২. ওটিপি গ্রুপে অটো ফরোয়ার্ড করা (নাম্বার মাস্ক সহ)
            try:
                otp_grp = get_setting("otp_group", "@hototpotp")
                raw_num = str(number).replace("+", "").strip()
                masked_num = mask_phone_number(raw_num)
                
                group_post = (
                    f"🎉 <b>NEW OTP SUCCESS HIT</b> 🎉\n\n"
                    f"📱 <b>Number:</b> <code>{masked_num}</code>\n"
                    f"{otp}\n\n"
                    f"⚡ <b>Status:</b> Delivered via HotOtp Bot ⭐"
                )
                
                markup = types.InlineKeyboardMarkup()
                btn_bot = types.InlineKeyboardButton("🤖 HotOtp Bot-এ নাম্বার নিন", url=f"https://t.me/{BOT_USERNAME}")
                markup.add(btn_bot)
                
                bot.send_message(otp_grp, group_post, reply_markup=markup, parse_mode="HTML")
            except Exception as ge: print(f"Group forward error: {ge}")
            return

# ----------------------------------------------------
# ৮. বট মেসেজ ও এডমিন প্যানেল হ্যান্ডলারস
# ----------------------------------------------------
@bot.message_handler(commands=['myid'])
def my_id_command(message):
    bot.reply_to(message, f"🆔 আপনার টেলিগ্রাম আইডি: <code>{message.chat.id}</code>", parse_mode="HTML")

@bot.message_handler(commands=['admin'])
def admin_panel_cmd(message):
    if not is_admin(message.chat.id):
        bot.reply_to(message, "❌ <b>Access Denied!</b> আপনি এই বটের এডমিন নন।", parse_mode="HTML")
        return

    supp = get_setting("support", "@hototpotp")
    rng = get_setting("range_group", "@hototprange")
    otp = get_setting("otp_group", "@hototpotp")
    
    msg = (
        "⚙️ <b>HOT OTP ADMIN PANEL</b> ⚙️\n\n"
        f"💬 <b>Current Support:</b> <code>{supp}</code>\n"
        f"📱 <b>Range Channel:</b> <code>{rng}</code>\n"
        f"🔔 <b>OTP Group:</b> <code>{otp}</code>\n\n"
        "📌 <b>বটের ভেতরে সেটিংস পরিবর্তন করার নিয়ম:</b>\n"
        "• সাপোর্ট আইডি বদলাতে: <code>/setsupport @username</code>\n"
        "• রেঞ্জ চ্যানেল বদলাতে: <code>/setrange @channel</code>\n"
        "• ওটিপি গ্রুপ বদলাতে: <code>/setgroup @group</code>"
    )
    bot.reply_to(message, msg, parse_mode="HTML")

@bot.message_handler(commands=['setsupport'])
def set_support_cmd(message):
    if not is_admin(message.chat.id): return
    text = message.text.replace('/setsupport', '').strip()
    if text:
        if not text.startswith('@'): text = '@' + text
        db["settings"]["support"] = text
        save_data()
        bot.reply_to(message, f"✅ সাপোর্ট ইউজারনেম সেট হয়েছে: <code>{text}</code>", parse_mode="HTML")
    else:
        bot.reply_to(message, "❌ ব্যবহার: <code>/setsupport @username</code>", parse_mode="HTML")

@bot.message_handler(commands=['setrange'])
def set_range_cmd(message):
    if not is_admin(message.chat.id): return
    text = message.text.replace('/setrange', '').strip()
    if text:
        if not text.startswith('@'): text = '@' + text
        db["settings"]["range_group"] = text
        save_data()
        bot.reply_to(message, f"✅ রেঞ্জ চ্যানেল সেট হয়েছে: <code>{text}</code>", parse_mode="HTML")
    else:
        bot.reply_to(message, "❌ ব্যবহার: <code>/setrange @channel</code>", parse_mode="HTML")

@bot.message_handler(commands=['setgroup'])
def set_group_cmd(message):
    if not is_admin(message.chat.id): return
    text = message.text.replace('/setgroup', '').strip()
    if text:
        if not text.startswith('@'): text = '@' + text
        db["settings"]["otp_group"] = text
        save_data()
        bot.reply_to(message, f"✅ ওটিপি গ্রুপ সেট হয়েছে: <code>{text}</code>", parse_mode="HTML")
    else:
        bot.reply_to(message, "❌ ব্যবহার: <code>/setgroup @group</code>", parse_mode="HTML")

@bot.message_handler(commands=['broadcast'])
def broadcast_command(message):
    if not is_admin(message.chat.id): return
    text = message.text.replace('/broadcast', '').strip()
    if not text:
        bot.reply_to(message, "❌ ব্যবহারের নিয়ম: <code>/broadcast আপনার মেসেজ</code>", parse_mode="HTML")
        return

    success_count = 0
    bot.reply_to(message, "⏳ সব ইউজারের কাছে মেসেজ পাঠানো হচ্ছে...")
    for user_id in db["users"]:
        try:
            bot.send_message(user_id, f"📢 <b>ADMIN ANNOUNCEMENT</b> 📢\n\n{text}", parse_mode="HTML")
            success_count += 1
            time.sleep(0.1)
        except: pass
    
    bot.send_message(message.chat.id, f"✅ ব্রডকাস্ট সম্পন্ন হয়েছে!\nমোট <code>{success_count}</code> জনের কাছে সফলভাবে পাঠানো হয়েছে।", parse_mode="HTML")

# ----------------------------------------------------
# ৯. সাধারণ ইউজার মেসেজ হ্যান্ডলারস
# ----------------------------------------------------
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    chat_str = str(chat_id)
    bot.clear_step_handler_by_chat_id(chat_id)

    if chat_id not in db["users"]:
        db["users"].append(chat_id)
        save_data()

    args = message.text.split()
    if len(args) > 1:
        deep_range = args[1].strip()
        db["ranges"][chat_str] = deep_range
        save_data()
        bot.send_message(chat_id, f"✅ <b>চ্যানেল থেকে রেঞ্জ সিলেক্ট হয়েছে:</b> <code>{deep_range}</code>", reply_markup=bottom_main_keyboard(), parse_mode="HTML")
        fetch_and_send_number(chat_id, deep_range)
        return

    db["ranges"].pop(chat_str, None)
    save_data()
    bot.send_message(chat_id, "👋 <b>Welcome back to HotOtp Bot</b>", reply_markup=bottom_main_keyboard(), parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "☎️ Get Number" or m.text == "/number")
def get_number_handler(message):
    chat_id = message.chat.id
    chat_str = str(chat_id)
    saved_r = db["ranges"].get(chat_str)
    if saved_r:
        fetch_and_send_number(chat_id, saved_r)
    else:
        msg = bot.send_message(chat_id, "আপনার পছন্দমতো রেঞ্জটি (Range) টাইপ করে পাঠান\n(যেমন: <code>224671808XXX</code>):", parse_mode="HTML")
        bot.register_next_step_handler(msg, process_save_range)

@bot.message_handler(func=lambda m: m.text == "⚙️ Change Range" or m.text == "/range")
def change_range_handler(message):
    msg = bot.send_message(message.chat.id, "আপনার পছন্দমতো রেঞ্জটি (Range) টাইপ করে পাঠান\n(যেমন: <code>224671808XXX</code>):", parse_mode="HTML")
    bot.register_next_step_handler(msg, process_save_range)

@bot.message_handler(func=lambda m: m.text == "📱 Range Group")
def range_group_handler(message):
    rg = get_setting("range_group", "@hototprange")
    clean_url = rg.replace('@', '')
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📱 লাইভ রেঞ্জ চ্যানেলে যান", url=f"https://t.me/{clean_url}"))
    bot.send_message(message.chat.id, f"📢 <b>আমাদের লাইভ রেঞ্জ চ্যানেল:</b> {rg}\n\nনিচের বাটনে চাপ দিয়ে চ্যানেলে যুক্ত হন:", reply_markup=markup, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "🔽 OTHER" or m.text == "/other")
def other_handler(message):
    bot.send_message(message.chat.id, "📋 <b>OTHER OPTIONS</b>\n\nনিচের অপশন থেকে সিলেক্ট করুন:", reply_markup=bottom_other_keyboard(), parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "🏠 Home" or m.text == "/home")
def home_handler(message):
    bot.send_message(message.chat.id, "👋 <b>Welcome to HotOtp Bot</b>", reply_markup=bottom_main_keyboard())

@bot.message_handler(func=lambda m: "Support" in m.text or "help" in m.text or m.text == "/help")
def support_handler(message):
    supp = get_setting("support", "@hototpotp")
    clean_supp = supp.replace('@', '')
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💬 এডমিন সাপোর্ট (Contact Admin)", url=f"https://t.me/{clean_supp}"))
    
    bot.send_message(
        message.chat.id, 
        f"💬 <b>সহায়তার জন্য এডমিন চ্যাট:</b> <code>{supp}</code>\n\nযেকোনো সমস্যায় এডমিনের সাথে যোগাযোগ করুন।", 
        reply_markup=markup, 
        parse_mode="HTML"
    )

@bot.message_handler(func=lambda m: m.text == "✉️ Get Tempmail" or m.text == "/tempmail")
def tempmail_handler(message):
    bot.send_message(message.chat.id, "✉️ <b>Tempmail Feature:</b> শীঘ্রই আসছে!", parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "🔐 2FA" or m.text == "/twofa")
def twofa_handler(message):
    bot.send_message(message.chat.id, "🔐 <b>2FA Code Generator:</b> শীঘ্রই আসছে!", parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "👤 Fake Name")
def fakename_handler(message):
    bot.send_message(message.chat.id, "👤 <b>Fake Name Generator:</b> John Doe", parse_mode="HTML")

# ----------------------------------------------------
# ১০. কলব্যাক হ্যান্ডলার (ইনলাইন বাটন)
# ----------------------------------------------------
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    chat_id = call.message.chat.id
    chat_str = str(chat_id)
    try: bot.answer_callback_query(call.id)
    except: pass

    if call.data == "copy_info":
        bot.answer_callback_query(call.id, text="উপরে বোল্ড বক্সে থাকা নাম্বারটির ওপর এক টাচ করলেই কপি হয়ে যাবে!", show_alert=True)

    elif call.data == "reset_all":
        db["ranges"].pop(chat_str, None)
        save_data()
        bot.clear_step_handler_by_chat_id(chat_id)
        bot.send_message(chat_id, "🔄 <b>সবকিছু রিসেট করা হয়েছে!</b>", reply_markup=bottom_main_keyboard(), parse_mode="HTML")
        
    elif call.data == "ask_range":
        msg = bot.send_message(chat_id, "আপনার পছন্দমতো রেঞ্জটি (Range) টাইপ করে পাঠান\n(যেমন: <code>224671808XXX</code>):", parse_mode="HTML")
        bot.register_next_step_handler(msg, process_save_range)

    elif call.data == "get_num_auto":
        saved_r = db["ranges"].get(chat_str)
        if saved_r: 
            fetch_and_send_number(chat_id, saved_r, message_id=call.message.message_id)
        else:
            msg = bot.send_message(chat_id, "আপনার কোনো রেঞ্জ সেট করা নেই। রেঞ্জ টাইপ করুন:")
            bot.register_next_step_handler(msg, process_save_range)

    elif call.data.startswith("check_otp_"):
        parts = call.data.replace("check_otp_", "").split("|")
        num_id = parts[0]
        number = parts[1] if len(parts) > 1 else ""
        
        otp = fetch_otp(num_id, number)
        if otp: 
            bot.send_message(chat_id, f"🎉 <b>ওটিপি চলে এসেছে!</b>\n\n{otp}", parse_mode="HTML")
        else: 
            bot.answer_callback_query(call.id, text="এখনো ওটিপি আসেনি! ২-৩ সেকেন্ড পর আবার চাপুন...", show_alert=True)

# স্মার্ট রেঞ্জ সেভার
def process_save_range(message):
    chat_id = message.chat.id
    chat_str = str(chat_id)
    text = message.text.strip() if message.text else ""
    
    if text in MENU_BUTTONS or text.startswith("/"):
        bot.clear_step_handler_by_chat_id(chat_id)
        if "Range Group" in text: range_group_handler(message)
        elif "Get Number" in text or text == "/number": get_number_handler(message)
        elif "Change Range" in text or text == "/range": change_range_handler(message)
        elif "OTHER" in text or text == "/other": other_handler(message)
        elif "Home" in text or text == "/home": home_handler(message)
        elif "Support" in text or "help" in text: support_handler(message)
        elif "Tempmail" in text: tempmail_handler(message)
        elif "2FA" in text: twofa_handler(message)
        elif "Fake Name" in text: fakename_handler(message)
        return

    db["ranges"][chat_str] = text
    save_data()
    bot.send_message(chat_id, f"✅ <b>রেঞ্জ সেভ হয়েছে:</b> <code>{text}</code>", reply_markup=bottom_main_keyboard(), parse_mode="HTML")
    fetch_and_send_number(chat_id, text)

# নাম্বার ফানেল
def fetch_and_send_number(chat_id, user_range, message_id=None):
    if not message_id:
        bot.send_message(chat_id, f"⏳ <code>{user_range}</code> রেঞ্জ দিয়ে নাম্বার নেওয়া হচ্ছে...", parse_mode="HTML")
    
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

            otp_grp = get_setting("otp_group", "@hototpotp").replace('@', '')
            rng_grp = get_setting("range_group", "@hototprange").replace('@', '')

            msg_text = (
                f"✅ <b>Number:</b> 🌐 {country}\n\n"
                f"👇 <b>নাম্বারটির ওপর এক চাপ দিলেই সরাসরি কপি হবে:</b>\n<code>{raw_num}</code>"
            )
            
            markup = types.InlineKeyboardMarkup(row_width=2)
            
            try:
                btn_num1 = types.InlineKeyboardButton(f"📋 📱 {raw_num}", copy_text=types.CopyTextButton(raw_num))
            except AttributeError:
                btn_num1 = types.InlineKeyboardButton(f"📋 📱 {raw_num}", callback_data="copy_info")

            btn_otp_group = types.InlineKeyboardButton("🔔 OTP GROUP", url=f"https://t.me/{otp_grp}")
            btn_range_group = types.InlineKeyboardButton("📱 RANGE GROUP", url=f"https://t.me/{rng_grp}")
            
            btn_change_num = types.InlineKeyboardButton("🔄 Change Number", callback_data="get_num_auto")
            btn_refresh = types.InlineKeyboardButton("🔄 Refresh", callback_data=f"check_otp_{num_id}|{number}")
            btn_back = types.InlineKeyboardButton("⬅️ Back", callback_data="reset_all")

            markup.add(btn_num1)
            markup.add(btn_otp_group, btn_range_group)
            markup.add(btn_change_num, btn_refresh)
            markup.add(btn_back)
            
            if message_id:
                try:
                    bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=msg_text, reply_markup=markup, parse_mode="HTML")
                except Exception:
                    bot.send_message(chat_id, msg_text, reply_markup=markup, parse_mode="HTML")
            else:
                bot.send_message(chat_id, msg_text, reply_markup=markup, parse_mode="HTML")
                
            threading.Thread(target=auto_check_otp, args=(chat_id, num_id, number), daemon=True).start()
        else:
            bot.send_message(chat_id, f"❌ সমস্যা: {res.get('error')}", reply_markup=bottom_main_keyboard())
    except Exception as e:
        bot.send_message(chat_id, f"❌ আসল সমস্যা: {e}")

# ----------------------------------------------------
# ১১. পোলিং চালু রাখা
# ----------------------------------------------------
try:
    bot.polling(none_stop=True, interval=0)
except Exception as e:
    print(f"Error: {e}")
