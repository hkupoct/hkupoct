from multiprocessing import context
import os
import json
import asyncio
import logging
import profile
from database import (
    init_database,
    get_or_create_conversation,
    save_chat_message,
    mark_conversation_read,
    get_admin_conversations,
    get_admin_conversation_by_id
)
from telegram.error import RetryAfter, Forbidden
from sqlalchemy import update
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)


# ============================================================
# CONFIGURATION
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Your Telegram Admin ID
ADMIN_ID = 1638005081

# ============================================================
# PREMIUM PAYMENT
# ============================================================

PAYMENT_QR_ID = "AgACAgUAAxkBAAI6UGqLtUl3bG8wf02lRhzlXkork64DAALjEWsbmGdgVCDdAidcHTTqAQADAgADeQADPQQ"

PREMIUM_PRICE = "₹999"

# ============================================================
# PROFILE DATABASE
# ============================================================

PROFILES = {

    ("female", "younger"): [
        {
    		"name": "Aparna",
    		"age": 23,
    		"bio": "One night fun?? 😉",
    		"photo_id": "AgACAgUAAxkBAAIBA2qDWZjinkEkmxvFpw0liL6lBR22AALNEWsbYjEhVKRsjX15wQvDAQADAgADeQADPQQ"
	},
	{
    		"name": "Kushi",
    		"age": 22,
    		"bio": "Mere boobs dabao, meri chut chaato aur phir mujhe chodom yeh hai mera plan😉",
    		"photo_id": "AgACAgUAAxkBAAIB7GqDX2Zu12o0yulozDJGrS3ytCXcAALlEWsbYjEhVPO5hkR2E5w8AQADAgADeQADPQQ"
	},
	{
    		"name": "Yatri",
    		"age": 23,
    		"bio": "Sex and nothing more",
    		"photo_id": "AgACAgUAAxkBAAIBvmqDXk_czRKhUFde7AohdmY8hLdUAALhEWsbYjEhVC4fY_cAAYpF5AEAAwIAA3kAAz0E"
	},
	{
    		"name": "Anjali",
    		"age": 27,
    		"bio": "Small dick not interested 😂 . Only above 6 inches 🫦",
    		"photo_id": "AgACAgUAAxkBAAPXaoNYaNV02ogrEz2E6qMQVzfwGvcAAskRaxtiMSFUF6Cc44yIpOoBAAMCAAN5AAM9BA"
	},
	{
    		"name": "Janvi",
    		"age": 23,
    		"bio": "Let's 69 until we can't breathe anymore🥵",
    		"photo_id": "AgACAgUAAxkBAAIBRWqDWvxqPMlqHG0e_Yk8Kam1xS_iAALTEWsbYjEhVNQNYz6V1nB6AQADAgADeQADPQQ"
	},
	{
    		"name": "Janani",
    		"age": 24,
    		"bio": "Boobs press karne ka mann kar raha hai??",
    		"photo_id": "AgACAgUAAxkBAAIBkmqDXURFuknAOw5adGxwVOnSfoUFAALdEWsbYjEhVAVAw9uU3x_9AQADAgADeQADPQQ"
	},
	{
    		"name": "Shefali",
    		"age": 25,
    		"bio": "Just here for sex",
    		"photo_id": "AgACAgUAAxkBAAIBs2qDXh3WGnmZhg04aXGW838ezYVKAALgEWsbYjEhVJJ_WRlgeHBBAQADAgADeQADPQQ"
	},
	{
    		"name": "Arpita",
    		"age": 26,
    		"bio": "I bet you can't hold my boob in one hand😊",
    		"photo_id": "AgACAgUAAxkBAAIBGWqDWhP8lkNhumHwKM_jfr9gbONSAALPEWsbYjEhVAlb17T2olt3AQADAgADeAADPQQ"
	},
	{
    		"name": "Sakshi",
    		"age": 27,
    		"bio": "Mere boobs se khelna hai??",
    		"photo_id": "AgACAgUAAxkBAAP4aoNZLtnYxIs-QpdHnSctwU4P6OMAAswRaxtiMSFUaDH-MkvVSn4BAAMCAAN5AAM9BA"
	},
	{
    		"name": "Reshma",
    		"age": 26,
    		"bio": "My boobs are real and so my desire to fuck😍",
    		"photo_id": "AgACAgUAAxkBAAIBUGqDWzSLKJvRyYjiPLBJByvtk2RUAALUEWsbYjEhVJfpPrwa0iubAQADAgADeQADPQQ"
	},
	{
    		"name": "Prarthana",
    		"age": 25,
    		"bio": "Scared of bj. Looking for someone who can make me over come it ❣️",
    		"photo_id": "AgACAgUAAxkBAAPtaoNY7tvT_NgU6TDomab7A7t74K4AAssRaxtiMSFUOnsYoIJT0I0BAAMCAAN4AAM9BA"
	},
	{
    		"name": "Chandini",
    		"age": 26,
    		"bio": "Looking for a fuck buddy , not a soulmate",
    		"photo_id": "AgACAgUAAxkBAAIB4WqDXykd0z897vEhVBK-En7Nq134AALkEWsbYjEhVHLSMv2Jj1ZmAQADAgADeQADPQQ"
	},
	{
    		"name": "Athira",
    		"age": 27,
    		"bio": "Let's get naked and see where it goes😍",
    		"photo_id": "AgACAgUAAxkBAAIBJGqDWkjqYhhNCqYh3decdK5F4g1gAALQEWsbYjEhVJFBOYx3jLnRAQADAgADeQADPQQ"
	},
	{
    		"name": "Tara",
    		"age": 25,
    		"bio": "Main ek aisi ladki hun jo sirf ek raat ka maza chahti hai, koi rista nahi🙏",
    		"photo_id": "AgACAgUAAxkBAAO2aoNXtkNI-bhUmUz2DHc9FOVLqv0AAsYRaxtiMSFUG2foZEclabYBAAMCAAN4AAM9BA"
	},
	{
    		"name": "Aarthi",
    		"age": 26,
    		"bio": "Mujhe teri zarurat hai, andar se👀",
    		"photo_id": "AgACAgUAAxkBAAOHaoNWc4Edjsa4dz-jbljBhAft2R0AAsERaxtiMSFUyPFSFt1BguMBAAMCAAN5AAM9BA"
	},
	{
    		"name": "Monica",
    		"age": 24,
    		"bio": "I'm single and ready to mingle in bed 💗",
    		"photo_id": "AgACAgUAAxkBAANzaoNV0YO3Zu4ThaEdz0EpuiqAtPcAAr8RaxtiMSFUMprdb0nwSYUBAAMCAAN4AAM9BA"
	},
	{
    		"name": "Deepika",
    		"age": 29,
    		"bio": "Interested in Anal???",
    		"photo_id": "AgACAgUAAxkBAAPiaoNYsJUAAQxadm-wqI7Pdppm9r2OAALKEWsbYjEhVFM2fsST2LQJAQADAgADeQADPQQ"
	},
	{
    		"name": "Nidhi",
    		"age": 23,
    		"bio": "Looking for a cock that can satisfy my hungry pussy😍",
    		"photo_id": "AgACAgUAAxkBAAMQaoNSS0seUpG0VHQtJXC9EIkOSh8AArYRaxtiMSFUWCU7knyYQecBAAMCAAN5AAM9BA"
	},
	{
    		"name": "Greeshma",
   		"age": 27,
    		"bio": "Without condom ??😍",
    		"photo_id": "AgACAgUAAxkBAAICAmqDX_JGuTXndYbvYd9eLMMI8aaXAALoEWsbYjEhVEd6bwW2tD0xAQADAgADeQADPQQ"
	},
	{
    		"name": "Aishanya",
    		"age": 27,
    		"bio": "I want to feel your cock in every position",
    		"photo_id": "AgACAgUAAxkBAAMmaoNTuiCiXHD6PEtrFJjdGU3tSOQAArgRaxtiMSFUcahKOHu8h9wBAAMCAAN5AAM9BA"
	},
	{
    		"name": "Pooja",
    		"age": 29,
    		"bio": "Mere bed par aake maza lena",
    		"photo_id": "AgACAgUAAxkBAAIBh2qDXQcslqv-yzruSuv9Qw_1lZadAALcEWsbYjEhVDXtaVgEDWSQAQADAgADeQADPQQ"
	},
	{
    		"name": "Jiya",
    		"age": 24,
    		"bio": "Tera lund , meri chut, perfect combination",
    		"photo_id": "AgACAgUAAxkBAAMxaoNUCmrSOVpDg_QZL3FSOOQyCUgAArkRaxtiMSFUAfqIgVwVmoEBAAMCAAN5AAM9BA"
	},
	{
    		"name": "Mary d souza",
    		"age": 30,
    		"bio": "No commitments just orgasms . Sound good??",
    		"photo_id": "AgACAgUAAxkBAAIB1mqDXuDdLXPi0yD6ludbEFtNrr2iAALjEWsbYjEhVBG_dGye9BbjAQADAgADeQADPQQ"
	},
	{
    		"name": "Deepa",
    		"age": 29,
    		"bio": "Let's get dirty with my tits and your cock😜",
    		"photo_id": "AgACAgUAAxkBAANoaoNVj9j6Q75TQQIOASjdCDXWY9gAAr4RaxtiMSFUxEBLNhg3wdUBAAMCAAN5AAM9BA"
	},
	{
    		"name": "Ishani",
    		"age": 28,
    		"bio": "Kya tu meri pyaas bujha sakta hai?",
    		"photo_id": "AgACAgUAAxkBAAM8aoNURs_Ea3-R-6PkSbR6jnfwFrQAAroRaxtiMSFUsZaakBs0upMBAAMCAAN5AAM9BA"
	}
    ],

    ("female", "older"): [
        {
    		"name": "Sunita",
    		"age": 42,
    		"bio": "My pussy is wet and ready for you",
    		"photo_id": "AgACAgUAAxkBAAICLmqDYcn_kZ-TyIbIw2S3pbuY2cTFAALtEWsbYjEhVJuaNFJuzVcuAQADAgADeQADPQQ"
	},
	{
    		"name": "Nikitha sharma",
    		"age": 34,
    		"bio": "Mera husband ka chota hai😔",
    		"photo_id": "AgACAgUAAxkBAAPMaoNYM5RE7er2f03wr5EM9VdBpXsAAsgRaxtiMSFUVQEUZFOuq14BAAMCAAN5AAM9BA"
	},
	{
    		"name": "Archana",
    		"age": 41,
    		"bio": "Chudai ki raat hai soja nahi",
    		"photo_id": "AgACAgUAAxkBAAIBnWqDXX1tqR9AVz_6dfMkc73jWox3AALeEWsbYjEhVJ7FV2SdzCk0AQADAgADeQADPQQ"
	},
	{
    		"name": "Lakshmi",
    		"age": 53,
    		"bio": "Meri boobs bada hai, experience bhi Zyada hai",
    		"photo_id": "AgACAgUAAxkBAAOraoNXRuUtuMP5gEsTM4O6DtELhfQAAsURaxtiMSFUS8mLCnSre6cBAAMCAAN4AAM9BA"
	},
	{
    		"name": "Lalitha",
    		"age": 40,
    		"bio": "Pussy gili hai, aa jao na",
    		"photo_id": "AgACAgUAAxkBAAICI2qDYYLF5yP3wR2Xp2XbWApxFzzVAALsEWsbYjEhVEU564fmbm38AQADAgADeQADPQQ"
	},
	{
    		"name": "Neelam",
    		"age": 33,
    		"bio": "Aaj raat bas chudai ki baat hai , baaki sab baad mein. Interested??",
    		"photo_id": "AgACAgUAAxkBAAPBaoNX8qdWJwdC7f-c_KcWzVDG1hcAAscRaxtiMSFUOHRTQ5XLNx8BAAMCAAN5AAM9BA"
	},
	{
    		"name": "Meena",
    		"age": 39,
    		"bio": "Lund chahiye , jaldi se🥵",
    		"photo_id": "AgACAgUAAxkBAAOgaoNXBSszmXJcVW8CPdqlsK7bJtcAAsQRaxtiMSFUHk1NHFzZaDwBAAMCAAN5AAM9BA"
	},
	{
    		"name": "Naina yadav",
    		"age": 35,
    		"bio": "Chuchi dabane aur chut chatne ke liye ready?",
    		"photo_id": "AgACAgUAAxkBAANdaoNVSnLHIbiCwYMR9ARbbIPW5BEAAr0RaxtiMSFULwrByJOZsDwBAAMCAAN5AAM9BA"
	},
	{
    		"name": "Krutika",
    		"age": 30,
    		"bio": "Down for fuck",
    		"photo_id": "AgACAgUAAxkBAAIBqGqDXdlht3PlpcF47z8OiZDhlixhAALfEWsbYjEhVCfwFCjWiVVVAQADAgADeQADPQQ"
	},
	{
    		"name": "Kavita",
    		"age": 38,
    		"bio": "Meri gaand ki baat hi alag hai🍑",
    		"photo_id": "AgACAgUAAxkBAAICGGqDYURDsGLKBNlZ1QWvE3zCPuX4AALrEWsbYjEhVKS0qbL9NrXFAQADAgADeQADPQQ"
	},
	{
    		"name": "Shruthi",
    		"age": 35,
    		"bio": "Meri boobs itne bade hain ki Tera lund khada ho jayega🫦",
    		"photo_id": "AgACAgUAAxkBAAOVaoNWur_kqbmoPStgu-ioi6YLTSgAAsMRaxtiMSFUix05hlmN2uEBAAMCAAN5AAM9BA"
	},
	{
    		"name": "Rita",
    		"age": 32,
    		"bio": "Looking for someone to fuck my tits😋",
    		"photo_id": "AgACAgUAAxkBAANSaoNU9Vg2kqckjsPhNL_6FIgAAQ29AAK8EWsbYjEhVCDe7E2N2tPlAQADAgADeQADPQQ"
	},
	{
    		"name": "Usha",
    		"age": 39,
    		"bio": "Sirf ek raat ke liye boyfriend ban ja",
    		"photo_id": "AgACAgUAAxkBAAICDWqDYRAqyLl7kbKYxPIe8QLCSPNjAALqEWsbYjEhVGF-JYPffve2AQADAgADeQADPQQ"
	},
	{
    		"name": "Poonam",
    		"age": 33,
    		"bio": "Aaj raat hum dono nange honge aur ek dusre ko chodenge, koi objection?",
    		"photo_id": "AgACAgUAAxkBAANHaoNUrYHlbghm3XxwcWGrPaVZiQoAArsRaxtiMSFUUD8uIaKXtpQBAAMCAAN5AAM9BA"
	},
	{
    		"name": "Shambhavi",
    		"age": 31,
    		"bio": "Bas sex chahiye, baaki bakwas mat kar",
    		"photo_id": "AgACAgUAAxkBAAMbaoNTeSKZPeJbJfBsUJYEL-r1AAEEAAK3EWsbYjEhVGPgRJsguEnhAQADAgADeQADPQQ"
	},
	{
    		"name": "Maya",
    		"age": 33,
    		"bio": "I'm here for the physical only, nothing else😋",
    		"photo_id": "AgACAgUAAxkBAAIBDmqDWcAWLkbf0gP9zHUGCrDHGFGyAALOEWsbYjEhVINKQINwaQodAQADAgADeQADPQQ"
	},
	{
    		"name": "Shruthi",
    		"age": 37,
    		"bio": "My nipples get hard just thinking about cock☺️",
    		"photo_id": "AgACAgUAAxkBAAIBL2qDWojvWheGaxfsO6wY22oyK1_4AALREWsbYjEhVMNY4DlsoaD5AQADAgADeQADPQQ"
	},
	{
    		"name": "Geetha",
    		"age": 39,
    		"bio": "Chudai ke liye taiyar hun darling 😘",
    		"photo_id": "AgACAgUAAxkBAAN-aoNWMydQ6y-8winCk61_2hJQMm4AAsARaxtiMSFUJ2r18bYhr_oBAAMCAAN5AAM9BA"
	},
	{
    		"name": "Purnima",
    		"age": 37,
    		"bio": "My pussy's ready for wild night 😋",
    		"photo_id": "AgACAgUAAxkBAAIB92qDX7mua89ycm7RZztLjCwu_1i1AALnEWsbYjEhVKftnGjaFgWdAQADAgADeQADPQQ"
	},
	{
    		"name": "Rekha",
    		"age": 46,
    		"bio": "Mere gaand ki maalish karde",
    		"photo_id": "AgACAgUAAxkBAAIByWqDXoa9fA2MGcNPIhYrZscfSAABiQAC4hFrG2IxIVQrDrg26jaAJwEAAwIAA3kAAz0E"
	},
	{
    		"name": "Leena",
    		"age": 33,
    		"bio": "I'll play with my tits while you eat my pussy🫦",
    		"photo_id": "AgACAgUAAxkBAAIBOmqDWsQT9wt6QQvKO48KorMM-ZTwAALSEWsbYjEhVBtn-Vkq3rN7AQADAgADeQADPQQ"
	},
	{
    		"name": "Geeta",
    		"age": 33,
    		"bio": "Meri chut ka paani tumhare Lund ke liye nikal raha hai, aao ise piyo aur muje chodo",
    		"photo_id": "AgACAgUAAxkBAAIBcWqDXBmECaZN8unAYmiPmPX8JZYvAALZEWsbYjEhVOflJw7Ax7GSAQADAgADeQADPQQ"
	},
	{
    		"name": "Asha",
    		"age": 32,
    		"bio": "Newly married but my husband is not that good ☹️. I am looking for secret affair😍",
    		"photo_id": "AgACAgUAAxkBAAIBW2qDW4iowTC_4gk0Wf-hiNQUhEXzAALVEWsbYjEhVH45YpBvxMaBAQADAgADeQADPQQ"
	},
	{
    		"name": "Krupa",
    		"age": 31,
    		"bio": "Bored in marriage life . Thrill in affair😜",
    		"photo_id": "AgACAgUAAxkBAAIBfGqDXKZhr3enoK6WIMSDJlk4vUVvAALbEWsbYjEhVNDLAAH8zt7FWwEAAwIAA3kAAz0E"
	},
	{
    		"name": "Meena",
    		"age": 30,
    		"bio": "30 and still not married 😑. I don't want marriage I only want sex .😍",
    		"photo_id": "AgACAgUAAxkBAAIBZmqDW9JTNkNoTw3zRYKfbWUJ39vyAALXEWsbYjEhVDi9464-UfWyAQADAgADeQADPQQ"
	}
    ],

    ("female", "any_age"): [
        {
    		"name": "Aparna",
    		"age": 23,
    		"bio": "One night fun?? 😉",
    		"photo_id": "AgACAgUAAxkBAAIBA2qDWZjinkEkmxvFpw0liL6lBR22AALNEWsbYjEhVKRsjX15wQvDAQADAgADeQADPQQ"
	},
	{
    		"name": "Kushi",
    		"age": 22,
    		"bio": "Mere boobs dabao, meri chut chaato aur phir mujhe chodom yeh hai mera plan😉",
    		"photo_id": "AgACAgUAAxkBAAIB7GqDX2Zu12o0yulozDJGrS3ytCXcAALlEWsbYjEhVPO5hkR2E5w8AQADAgADeQADPQQ"
	},
	{
    		"name": "Yatri",
    		"age": 23,
    		"bio": "Sex and nothing more",
    		"photo_id": "AgACAgUAAxkBAAIBvmqDXk_czRKhUFde7AohdmY8hLdUAALhEWsbYjEhVC4fY_cAAYpF5AEAAwIAA3kAAz0E"
	},
	{
    		"name": "Anjali",
    		"age": 27,
    		"bio": "Small dick not interested 😂 . Only above 6 inches 🫦",
    		"photo_id": "AgACAgUAAxkBAAPXaoNYaNV02ogrEz2E6qMQVzfwGvcAAskRaxtiMSFUF6Cc44yIpOoBAAMCAAN5AAM9BA"
	},
	{
    		"name": "Janvi",
    		"age": 23,
    		"bio": "Let's 69 until we can't breathe anymore🥵",
    		"photo_id": "AgACAgUAAxkBAAIBRWqDWvxqPMlqHG0e_Yk8Kam1xS_iAALTEWsbYjEhVNQNYz6V1nB6AQADAgADeQADPQQ"
	},
	{
    		"name": "Leena",
    		"age": 33,
    		"bio": "I'll play with my tits while you eat my pussy🫦",
    		"photo_id": "AgACAgUAAxkBAAIBOmqDWsQT9wt6QQvKO48KorMM-ZTwAALSEWsbYjEhVBtn-Vkq3rN7AQADAgADeQADPQQ"
	},
	{
    		"name": "Geeta",
    		"age": 33,
    		"bio": "Meri chut ka paani tumhare Lund ke liye nikal raha hai, aao ise piyo aur muje chodo",
    		"photo_id": "AgACAgUAAxkBAAIBcWqDXBmECaZN8unAYmiPmPX8JZYvAALZEWsbYjEhVOflJw7Ax7GSAQADAgADeQADPQQ"
	},
	{
    		"name": "Asha",
    		"age": 32,
    		"bio": "Newly married but my husband is not that good ☹️. I am looking for secret affair😍",
    		"photo_id": "AgACAgUAAxkBAAIBW2qDW4iowTC_4gk0Wf-hiNQUhEXzAALVEWsbYjEhVH45YpBvxMaBAQADAgADeQADPQQ"
	},
	{
    		"name": "Krupa",
    		"age": 31,
    		"bio": "Bored in marriage life . Thrill in affair😜",
    		"photo_id": "AgACAgUAAxkBAAIBfGqDXKZhr3enoK6WIMSDJlk4vUVvAALbEWsbYjEhVNDLAAH8zt7FWwEAAwIAA3kAAz0E"
	},
	{
    		"name": "Meena",
    		"age": 30,
    		"bio": "30 and still not married 😑. I don't want marriage I only want sex .😍",
    		"photo_id": "AgACAgUAAxkBAAIBZmqDW9JTNkNoTw3zRYKfbWUJ39vyAALXEWsbYjEhVDi9464-UfWyAQADAgADeQADPQQ"
	},
	{
    		"name": "Janani",
    		"age": 24,
    		"bio": "Boobs press karne ka mann kar raha hai??",
    		"photo_id": "AgACAgUAAxkBAAIBkmqDXURFuknAOw5adGxwVOnSfoUFAALdEWsbYjEhVAVAw9uU3x_9AQADAgADeQADPQQ"
	},
	{
    		"name": "Shefali",
    		"age": 25,
    		"bio": "Just here for sex",
    		"photo_id": "AgACAgUAAxkBAAIBs2qDXh3WGnmZhg04aXGW838ezYVKAALgEWsbYjEhVJJ_WRlgeHBBAQADAgADeQADPQQ"
	},
	{
    		"name": "Arpita",
    		"age": 26,
    		"bio": "I bet you can't hold my boob in one hand😊",
    		"photo_id": "AgACAgUAAxkBAAIBGWqDWhP8lkNhumHwKM_jfr9gbONSAALPEWsbYjEhVAlb17T2olt3AQADAgADeAADPQQ"
	},
	{
    		"name": "Sakshi",
    		"age": 27,
    		"bio": "Mere boobs se khelna hai??",
    		"photo_id": "AgACAgUAAxkBAAP4aoNZLtnYxIs-QpdHnSctwU4P6OMAAswRaxtiMSFUaDH-MkvVSn4BAAMCAAN5AAM9BA"
	},
	{
    		"name": "Reshma",
    		"age": 26,
    		"bio": "My boobs are real and so my desire to fuck😍",
    		"photo_id": "AgACAgUAAxkBAAIBUGqDWzSLKJvRyYjiPLBJByvtk2RUAALUEWsbYjEhVJfpPrwa0iubAQADAgADeQADPQQ"
	},
	{
    		"name": "Maya",
    		"age": 33,
    		"bio": "I'm here for the physical only, nothing else😋",
    		"photo_id": "AgACAgUAAxkBAAIBDmqDWcAWLkbf0gP9zHUGCrDHGFGyAALOEWsbYjEhVINKQINwaQodAQADAgADeQADPQQ"
	},
	{
    		"name": "Shruthi",
    		"age": 37,
    		"bio": "My nipples get hard just thinking about cock☺️",
    		"photo_id": "AgACAgUAAxkBAAIBL2qDWojvWheGaxfsO6wY22oyK1_4AALREWsbYjEhVMNY4DlsoaD5AQADAgADeQADPQQ"
	},
	{
    		"name": "Geetha",
    		"age": 39,
    		"bio": "Chudai ke liye taiyar hun darling 😘",
    		"photo_id": "AgACAgUAAxkBAAN-aoNWMydQ6y-8winCk61_2hJQMm4AAsARaxtiMSFUJ2r18bYhr_oBAAMCAAN5AAM9BA"
	},
	{
    		"name": "Purnima",
    		"age": 37,
    		"bio": "My pussy's ready for wild night 😋",
    		"photo_id": "AgACAgUAAxkBAAIB92qDX7mua89ycm7RZztLjCwu_1i1AALnEWsbYjEhVKftnGjaFgWdAQADAgADeQADPQQ"
	},
	{
    		"name": "Rekha",
    		"age": 46,
    		"bio": "Mere gaand ki maalish karde",
    		"photo_id": "AgACAgUAAxkBAAIByWqDXoa9fA2MGcNPIhYrZscfSAABiQAC4hFrG2IxIVQrDrg26jaAJwEAAwIAA3kAAz0E"
	},
	{
    		"name": "Prarthana",
    		"age": 25,
    		"bio": "Scared of bj. Looking for someone who can make me over come it ❣️",
    		"photo_id": "AgACAgUAAxkBAAPtaoNY7tvT_NgU6TDomab7A7t74K4AAssRaxtiMSFUOnsYoIJT0I0BAAMCAAN4AAM9BA"
	},
	{
    		"name": "Chandini",
    		"age": 26,
    		"bio": "Looking for a fuck buddy , not a soulmate",
    		"photo_id": "AgACAgUAAxkBAAIB4WqDXykd0z897vEhVBK-En7Nq134AALkEWsbYjEhVHLSMv2Jj1ZmAQADAgADeQADPQQ"
	},
	{
    		"name": "Athira",
    		"age": 27,
    		"bio": "Let's get naked and see where it goes😍",
    		"photo_id": "AgACAgUAAxkBAAIBJGqDWkjqYhhNCqYh3decdK5F4g1gAALQEWsbYjEhVJFBOYx3jLnRAQADAgADeQADPQQ"
	},
	{
    		"name": "Tara",
    		"age": 25,
    		"bio": "Main ek aisi ladki hun jo sirf ek raat ka maza chahti hai, koi rista nahi🙏",
    		"photo_id": "AgACAgUAAxkBAAO2aoNXtkNI-bhUmUz2DHc9FOVLqv0AAsYRaxtiMSFUG2foZEclabYBAAMCAAN4AAM9BA"
	},
	{
    		"name": "Aarthi",
    		"age": 26,
    		"bio": "Mujhe teri zarurat hai, andar se👀",
    		"photo_id": "AgACAgUAAxkBAAOHaoNWc4Edjsa4dz-jbljBhAft2R0AAsERaxtiMSFUyPFSFt1BguMBAAMCAAN5AAM9BA"
	},
	{
    		"name": "Monica",
    		"age": 24,
    		"bio": "I'm single and ready to mingle in bed 💗",
    		"photo_id": "AgACAgUAAxkBAANzaoNV0YO3Zu4ThaEdz0EpuiqAtPcAAr8RaxtiMSFUMprdb0nwSYUBAAMCAAN4AAM9BA"
	},
	{
    		"name": "Deepika",
    		"age": 29,
    		"bio": "Interested in Anal???",
    		"photo_id": "AgACAgUAAxkBAAPiaoNYsJUAAQxadm-wqI7Pdppm9r2OAALKEWsbYjEhVFM2fsST2LQJAQADAgADeQADPQQ"
	},
	{
    		"name": "Nidhi",
    		"age": 23,
    		"bio": "Looking for a cock that can satisfy my hungry pussy😍",
    		"photo_id": "AgACAgUAAxkBAAMQaoNSS0seUpG0VHQtJXC9EIkOSh8AArYRaxtiMSFUWCU7knyYQecBAAMCAAN5AAM9BA"
	},
	{
    		"name": "Greeshma",
   		"age": 27,
    		"bio": "Without condom ??😍",
    		"photo_id": "AgACAgUAAxkBAAICAmqDX_JGuTXndYbvYd9eLMMI8aaXAALoEWsbYjEhVEd6bwW2tD0xAQADAgADeQADPQQ"
	},
	{
    		"name": "Aishanya",
    		"age": 27,
    		"bio": "I want to feel your cock in every position",
    		"photo_id": "AgACAgUAAxkBAAMmaoNTuiCiXHD6PEtrFJjdGU3tSOQAArgRaxtiMSFUcahKOHu8h9wBAAMCAAN5AAM9BA"
	},
	{
    		"name": "Pooja",
    		"age": 29,
    		"bio": "Mere bed par aake maza lena",
    		"photo_id": "AgACAgUAAxkBAAIBh2qDXQcslqv-yzruSuv9Qw_1lZadAALcEWsbYjEhVDXtaVgEDWSQAQADAgADeQADPQQ"
	},
	{
    		"name": "Jiya",
    		"age": 24,
    		"bio": "Tera lund , meri chut, perfect combination",
    		"photo_id": "AgACAgUAAxkBAAMxaoNUCmrSOVpDg_QZL3FSOOQyCUgAArkRaxtiMSFUAfqIgVwVmoEBAAMCAAN5AAM9BA"
	},
	{
    		"name": "Mary d souza",
    		"age": 30,
    		"bio": "No commitments just orgasms . Sound good??",
    		"photo_id": "AgACAgUAAxkBAAIB1mqDXuDdLXPi0yD6ludbEFtNrr2iAALjEWsbYjEhVBG_dGye9BbjAQADAgADeQADPQQ"
	},
	{
    		"name": "Deepa",
    		"age": 29,
    		"bio": "Let's get dirty with my tits and your cock😜",
    		"photo_id": "AgACAgUAAxkBAANoaoNVj9j6Q75TQQIOASjdCDXWY9gAAr4RaxtiMSFUxEBLNhg3wdUBAAMCAAN5AAM9BA"
	},
	{
    		"name": "Ishani",
    		"age": 28,
    		"bio": "Kya tu meri pyaas bujha sakta hai?",
    		"photo_id": "AgACAgUAAxkBAAM8aoNURs_Ea3-R-6PkSbR6jnfwFrQAAroRaxtiMSFUsZaakBs0upMBAAMCAAN5AAM9BA"
	},
	{
    		"name": "Sunita",
    		"age": 42,
    		"bio": "My pussy is wet and ready for you",
    		"photo_id": "AgACAgUAAxkBAAICLmqDYcn_kZ-TyIbIw2S3pbuY2cTFAALtEWsbYjEhVJuaNFJuzVcuAQADAgADeQADPQQ"
	},
	{
    		"name": "Nikitha sharma",
    		"age": 34,
    		"bio": "Mera husband ka chota hai😔",
    		"photo_id": "AgACAgUAAxkBAAPMaoNYM5RE7er2f03wr5EM9VdBpXsAAsgRaxtiMSFUVQEUZFOuq14BAAMCAAN5AAM9BA"
	},
	{
    		"name": "Archana",
    		"age": 41,
    		"bio": "Chudai ki raat hai soja nahi",
    		"photo_id": "AgACAgUAAxkBAAIBnWqDXX1tqR9AVz_6dfMkc73jWox3AALeEWsbYjEhVJ7FV2SdzCk0AQADAgADeQADPQQ"
	},
	{
    		"name": "Lakshmi",
    		"age": 53,
    		"bio": "Meri boobs bada hai, experience bhi Zyada hai",
    		"photo_id": "AgACAgUAAxkBAAOraoNXRuUtuMP5gEsTM4O6DtELhfQAAsURaxtiMSFUS8mLCnSre6cBAAMCAAN4AAM9BA"
	},
	{
    		"name": "Lalitha",
    		"age": 40,
    		"bio": "Pussy gili hai, aa jao na",
    		"photo_id": "AgACAgUAAxkBAAICI2qDYYLF5yP3wR2Xp2XbWApxFzzVAALsEWsbYjEhVEU564fmbm38AQADAgADeQADPQQ"
	},
	{
    		"name": "Neelam",
    		"age": 33,
    		"bio": "Aaj raat bas chudai ki baat hai , baaki sab baad mein. Interested??",
    		"photo_id": "AgACAgUAAxkBAAPBaoNX8qdWJwdC7f-c_KcWzVDG1hcAAscRaxtiMSFUOHRTQ5XLNx8BAAMCAAN5AAM9BA"
	},
	{
    		"name": "Meena",
    		"age": 39,
    		"bio": "Lund chahiye , jaldi se🥵",
    		"photo_id": "AgACAgUAAxkBAAOgaoNXBSszmXJcVW8CPdqlsK7bJtcAAsQRaxtiMSFUHk1NHFzZaDwBAAMCAAN5AAM9BA"
	},
	{
    		"name": "Naina yadav",
    		"age": 35,
    		"bio": "Chuchi dabane aur chut chatne ke liye ready?",
    		"photo_id": "AgACAgUAAxkBAANdaoNVSnLHIbiCwYMR9ARbbIPW5BEAAr0RaxtiMSFULwrByJOZsDwBAAMCAAN5AAM9BA"
	},
	{
    		"name": "Krutika",
    		"age": 30,
    		"bio": "Down for fuck",
    		"photo_id": "AgACAgUAAxkBAAIBqGqDXdlht3PlpcF47z8OiZDhlixhAALfEWsbYjEhVCfwFCjWiVVVAQADAgADeQADPQQ"
	},
	{
    		"name": "Kavita",
    		"age": 38,
    		"bio": "Meri gaand ki baat hi alag hai🍑",
    		"photo_id": "AgACAgUAAxkBAAICGGqDYURDsGLKBNlZ1QWvE3zCPuX4AALrEWsbYjEhVKS0qbL9NrXFAQADAgADeQADPQQ"
	},
	{
    		"name": "Shruthi",
    		"age": 35,
    		"bio": "Meri boobs itne bade hain ki Tera lund khada ho jayega🫦",
    		"photo_id": "AgACAgUAAxkBAAOVaoNWur_kqbmoPStgu-ioi6YLTSgAAsMRaxtiMSFUix05hlmN2uEBAAMCAAN5AAM9BA"
	},
	{
    		"name": "Rita",
    		"age": 32,
    		"bio": "Looking for someone to fuck my tits😋",
    		"photo_id": "AgACAgUAAxkBAANSaoNU9Vg2kqckjsPhNL_6FIgAAQ29AAK8EWsbYjEhVCDe7E2N2tPlAQADAgADeQADPQQ"
	},
	{
    		"name": "Usha",
    		"age": 39,
    		"bio": "Sirf ek raat ke liye boyfriend ban ja",
    		"photo_id": "AgACAgUAAxkBAAICDWqDYRAqyLl7kbKYxPIe8QLCSPNjAALqEWsbYjEhVGF-JYPffve2AQADAgADeQADPQQ"
	},
	{
    		"name": "Poonam",
    		"age": 33,
    		"bio": "Aaj raat hum dono nange honge aur ek dusre ko chodenge, koi objection?",
    		"photo_id": "AgACAgUAAxkBAANHaoNUrYHlbghm3XxwcWGrPaVZiQoAArsRaxtiMSFUUD8uIaKXtpQBAAMCAAN5AAM9BA"
	},
	{
    		"name": "Shambhavi",
    		"age": 31,
    		"bio": "Bas sex chahiye, baaki bakwas mat kar",
    		"photo_id": "AgACAgUAAxkBAAMbaoNTeSKZPeJbJfBsUJYEL-r1AAEEAAK3EWsbYjEhVGPgRJsguEnhAQADAgADeQADPQQ"
	}

	
    ],

    ("male", "younger"): [
        {
    		"name": "Ishaan",
    		"age": 25,
    		"bio": "I'm a fucking enthusiast",
    		"photo_id": "AgACAgUAAxkBAAICOWqG-LTYbn-Nrnmynos806eaDG9dAAJLF2sbn8s5VHblkpOFfoc2AQADAgADeQADPQQ"
	},
	{
    		"name": "Krish",
    		"age": 27,
    		"bio": "Chut aur Lund ka khel hai",
    		"photo_id": "AgACAgUAAxkBAAICRGqG-OGprICnFT0PzlnZiciZ5jP8AAJNF2sbn8s5VM-aaCw4oN2fAQADAgADeQADPQQ"
	},
	{
    		"name": "Rudra",
    		"age": 29,
    		"bio": "Your one-night-only boyfriend",
    		"photo_id": "AgACAgUAAxkBAAICT2qG-TN8IOSZVkwYCaGv8WdyeOgbAAJOF2sbn8s5VMMCBAihB_33AQADAgADeQADPQQ"
	},
	{
    		"name": "Raghav",
    		"age": 23,
    		"bio": "Ass or pussy? You choose darling 💋",
    		"photo_id": "AgACAgUAAxkBAAICWmqG-W4XGMgrejA7iqMm1WIaUAzRAAJPF2sbn8s5VOWM9mAnq_GcAQADAgADeQADPQQ"
	},
	{
    		"name": "Aditya",
    		"age": 24,
    		"bio": "Teach me how to fuck",
    		"photo_id": "AgACAgUAAxkBAAICZWqG-aaGAe22CnKN326U4NCHw17vAAJQF2sbn8s5VAHQ4yzRarb5AQADAgADeAADPQQ"
	},
	{
    		"name": "Aryan",
    		"age": 21,
    		"bio": "Meri Lund ki sawari karogi?",
    		"photo_id": "AgACAgUAAxkBAAICcGqG-c0Pq8vqkcrPuJ-c-DV_ysoLAAJRF2sbn8s5VIu5SMy5v_OBAQADAgADeQADPQQ"
	},
	{
    		"name": "Omkar",
    		"age": 28,
    		"bio": "Gonna fuck all night long",
    		"photo_id": "AgACAgUAAxkBAAICe2qG-glkWxQZ1Wpg3wRt-ENF_F5_AAJSF2sbn8s5VHiKDt63zG7rAQADAgADeQADPQQ"
	},
	{
    		"name": "Harshit",
    		"age": 24,
    		"bio": "Getting naked and fucking only",
    		"photo_id": "AgACAgUAAxkBAAIChmqG-j9W9XVjSrUXeopOxvPWZtoXAAJUF2sbn8s5VCxcnWgToDNyAQADAgADeQADPQQ"
	},
	{
    		"name": "Vedant",
    		"age": 26,
    		"bio": "Topic's tonight : fucking",
    		"photo_id": "AgACAgUAAxkBAAICkWqG-ngSSgqHNLmotePleBZ2C_V0AAJXF2sbn8s5VFaP7GfD1WTmAQADAgADeQADPQQ"
	},
	{
    		"name": "Pranav",
    		"age": 30,
    		"bio": "Bas sex aur kuchh nahi",
    		"photo_id": "AgACAgUAAxkBAAICnGqG-qKQIAFumQL6yvqlz0lGt6z-AAJYF2sbn8s5VI5dOZXrVeCOAQADAgADeAADPQQ"
	}
    ],

    ("male", "older"): [
	    {
    		"name": "Krishna roy",
    		"age": 43,
    		"bio": "Old enough to know better and young enough to do it anyway",
    		"photo_id": "AgACAgUAAxkBAAICp2qG-xBweF1Ov1r1KMZEJzjIpUv6AAJcF2sbn8s5VEoiu8s-D_rsAQADAgADeQADPQQ"
	},
	{
    		"name": "Abhishekh",
    		"age": 33,
    		"bio": "Age is just a number . My stamina is the real surprise",
    		"photo_id": "AgACAgUAAxkBAAICsmqG-4fpR4F1pP8ek0Ru69v38PcDAAJfF2sbn8s5VGKzfGEU9CgsAQADAgADeQADPQQ"
	},
	{
    		"name": "Amit",
    		"age": 31,
    		"bio": "I don't play games . Just here for great sex",
    		"photo_id": "AgACAgUAAxkBAAICvWqG-7k0WE82bWRFX6_7kPiKSsj4AAJgF2sbn8s5VAV9tN1j0Ce2AQADAgADeQADPQQ"
	},
	{
    		"name": "Rajesh",
    		"age": 40,
    		"bio": "Tired of boys? Try a man who knows how to satisfy",
    		"photo_id": "AgACAgUAAxkBAAICyGqG--FBvfV_wuoBk8hyrfDRtngQAAJhF2sbn8s5VFQppr7vjzfSAQADAgADeQADPQQ"
	},
	{
    		"name": "Shiv prakash",
    		"age": 55,
    		"bio": "Old is gold . Mera lund teri chut mein jaana chahta hai",
    		"photo_id": "AgACAgUAAxkBAAIC02qG_BoIgAX0bXlKigz8i91B6j2RAAJiF2sbn8s5VLJ8on-uaPxtAQADAgADeAADPQQ"
	},
	{
    		"name": "Sanjay",
    		"age": 35,
    		"bio": "Looking for fun night. I'll handle the rest",
    		"photo_id": "AgACAgUAAxkBAAIC3mqG_GFweeBX70P-DzVW2HI1IELkAAJjF2sbn8s5VNbuzjMe7jx1AQADAgADeQADPQQ"
	},
	{
    		"name": "Rajeev",
    		"age": 37,
    		"bio": "House, car , aur job hai. Bas chut chodne ko baaki hai",
    		"photo_id": "AgACAgUAAxkBAAIC6WqG_JlFei1N0uxIWPICMQbO_S-fAAJkF2sbn8s5VHa4qpYJDAU6AQADAgADeQADPQQ"
	},
	{
    		"name": "Santosh",
    		"age": 40,
    		"bio": "40 saal ka hoon, par stamina 20 ki. Teri chut fadne ke liye taiyar",
    		"photo_id": "AgACAgUAAxkBAAIC9GqG_Oy01HWaT890bh_MhoY0g8N1AAJmF2sbn8s5VJP00wkTCm04AQADAgADeQADPQQ"
	},
	{
    		"name": "Gulshan",
    		"age": 36,
    		"bio": "Family man hoon , par aaj raat teri chut ka servant banunga",
    		"photo_id": "AgACAgUAAxkBAAIC_2qG_Sd8f0-sT3m3YN6E9BJ-m2XKAAJnF2sbn8s5VB6cCVf7ZfhTAQADAgADeQADPQQ"
	},
	{
    		"name": "Rohit",
    		"age": 32,
    		"bio": "Matured man with wild desires",
    		"photo_id": "AgACAgUAAxkBAAIDCmqG_WXOXxg81sbUHLBX40K-Tp3-AAJtF2sbn8s5VAZxo1LtibAEAQADAgADeQADPQQ"
	}
    ],

    ("male", "any_age"): [
	{
    		"name": "Ishaan",
    		"age": 25,
    		"bio": "I'm a fucking enthusiast",
    		"photo_id": "AgACAgUAAxkBAAICOWqG-LTYbn-Nrnmynos806eaDG9dAAJLF2sbn8s5VHblkpOFfoc2AQADAgADeQADPQQ"
	},
	{
    		"name": "Krish",
    		"age": 27,
    		"bio": "Chut aur Lund ka khel hai",
    		"photo_id": "AgACAgUAAxkBAAICRGqG-OGprICnFT0PzlnZiciZ5jP8AAJNF2sbn8s5VM-aaCw4oN2fAQADAgADeQADPQQ"
	},
	{
    		"name": "Rudra",
    		"age": 29,
    		"bio": "Your one-night-only boyfriend",
    		"photo_id": "AgACAgUAAxkBAAICT2qG-TN8IOSZVkwYCaGv8WdyeOgbAAJOF2sbn8s5VMMCBAihB_33AQADAgADeQADPQQ"
	},
	{
    		"name": "Raghav",
    		"age": 23,
    		"bio": "Ass or pussy? You choose darling 💋",
    		"photo_id": "AgACAgUAAxkBAAICWmqG-W4XGMgrejA7iqMm1WIaUAzRAAJPF2sbn8s5VOWM9mAnq_GcAQADAgADeQADPQQ"
	},
	{
    		"name": "Aditya",
    		"age": 24,
    		"bio": "Teach me how to fuck",
    		"photo_id": "AgACAgUAAxkBAAICZWqG-aaGAe22CnKN326U4NCHw17vAAJQF2sbn8s5VAHQ4yzRarb5AQADAgADeAADPQQ"
	},
	{
    		"name": "Krishna roy",
    		"age": 43,
    		"bio": "Old enough to know better and young enough to do it anyway",
    		"photo_id": "AgACAgUAAxkBAAICp2qG-xBweF1Ov1r1KMZEJzjIpUv6AAJcF2sbn8s5VEoiu8s-D_rsAQADAgADeQADPQQ"
	},
	{
    		"name": "Abhishekh",
    		"age": 33,
    		"bio": "Age is just a number . My stamina is the real surprise",
    		"photo_id": "AgACAgUAAxkBAAICsmqG-4fpR4F1pP8ek0Ru69v38PcDAAJfF2sbn8s5VGKzfGEU9CgsAQADAgADeQADPQQ"
	},
	{
    		"name": "Amit",
    		"age": 31,
    		"bio": "I don't play games . Just here for great sex",
    		"photo_id": "AgACAgUAAxkBAAICvWqG-7k0WE82bWRFX6_7kPiKSsj4AAJgF2sbn8s5VAV9tN1j0Ce2AQADAgADeQADPQQ"
	},
	{
    		"name": "Rajesh",
    		"age": 40,
    		"bio": "Tired of boys? Try a man who knows how to satisfy",
    		"photo_id": "AgACAgUAAxkBAAICyGqG--FBvfV_wuoBk8hyrfDRtngQAAJhF2sbn8s5VFQppr7vjzfSAQADAgADeQADPQQ"
	},
	{
    		"name": "Shiv prakash",
    		"age": 55,
    		"bio": "Old is gold . Mera lund teri chut mein jaana chahta hai",
    		"photo_id": "AgACAgUAAxkBAAIC02qG_BoIgAX0bXlKigz8i91B6j2RAAJiF2sbn8s5VLJ8on-uaPxtAQADAgADeAADPQQ"
	},
	{
    		"name": "Aryan",
    		"age": 21,
    		"bio": "Meri Lund ki sawari karogi?",
    		"photo_id": "AgACAgUAAxkBAAICcGqG-c0Pq8vqkcrPuJ-c-DV_ysoLAAJRF2sbn8s5VIu5SMy5v_OBAQADAgADeQADPQQ"
	},
	{
    		"name": "Omkar",
    		"age": 28,
    		"bio": "Gonna fuck all night long",
    		"photo_id": "AgACAgUAAxkBAAICe2qG-glkWxQZ1Wpg3wRt-ENF_F5_AAJSF2sbn8s5VHiKDt63zG7rAQADAgADeQADPQQ"
	},
	{
    		"name": "Harshit",
    		"age": 24,
    		"bio": "Getting naked and fucking only",
    		"photo_id": "AgACAgUAAxkBAAIChmqG-j9W9XVjSrUXeopOxvPWZtoXAAJUF2sbn8s5VCxcnWgToDNyAQADAgADeQADPQQ"
	},
	{
    		"name": "Vedant",
    		"age": 26,
    		"bio": "Topic's tonight : fucking",
    		"photo_id": "AgACAgUAAxkBAAICkWqG-ngSSgqHNLmotePleBZ2C_V0AAJXF2sbn8s5VFaP7GfD1WTmAQADAgADeQADPQQ"
	},
	{
    		"name": "Pranav",
    		"age": 30,
    		"bio": "Bas sex aur kuchh nahi",
    		"photo_id": "AgACAgUAAxkBAAICnGqG-qKQIAFumQL6yvqlz0lGt6z-AAJYF2sbn8s5VI5dOZXrVeCOAQADAgADeAADPQQ"
	},
	{
    		"name": "Sanjay",
    		"age": 35,
    		"bio": "Looking for fun night. I'll handle the rest",
    		"photo_id": "AgACAgUAAxkBAAIC3mqG_GFweeBX70P-DzVW2HI1IELkAAJjF2sbn8s5VNbuzjMe7jx1AQADAgADeQADPQQ"
	},
	{
    		"name": "Rajeev",
    		"age": 37,
    		"bio": "House, car , aur job hai. Bas chut chodne ko baaki hai",
    		"photo_id": "AgACAgUAAxkBAAIC6WqG_JlFei1N0uxIWPICMQbO_S-fAAJkF2sbn8s5VHa4qpYJDAU6AQADAgADeQADPQQ"
	},
	{
    		"name": "Santosh",
    		"age": 40,
    		"bio": "40 saal ka hoon, par stamina 20 ki. Teri chut fadne ke liye taiyar",
    		"photo_id": "AgACAgUAAxkBAAIC9GqG_Oy01HWaT890bh_MhoY0g8N1AAJmF2sbn8s5VJP00wkTCm04AQADAgADeQADPQQ"
	},
	{
    		"name": "Gulshan",
    		"age": 36,
    		"bio": "Family man hoon , par aaj raat teri chut ka servant banunga",
    		"photo_id": "AgACAgUAAxkBAAIC_2qG_Sd8f0-sT3m3YN6E9BJ-m2XKAAJnF2sbn8s5VB6cCVf7ZfhTAQADAgADeQADPQQ"
	},
	{
    		"name": "Rohit",
    		"age": 32,
    		"bio": "Matured man with wild desires",
    		"photo_id": "AgACAgUAAxkBAAIDCmqG_WXOXxg81sbUHLBX40K-Tp3-AAJtF2sbn8s5VAZxo1LtibAEAQADAgADeQADPQQ"
	}	        
    ],
}

# ============================================================
# USER DATABASE
# ============================================================

USERS_FILE = os.path.join("data", "users.json")


def load_users():
    if not os.path.exists(USERS_FILE):
        return {}

    try:
        with open(
            USERS_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(file)

    except Exception as error:
        logger.error(
            "Could not load users.json: %s",
            error
        )
        return {}


def save_users(users):

    os.makedirs(
        os.path.dirname(USERS_FILE),
        exist_ok=True
    )

    with open(
        USERS_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            users,
            file,
            indent=4,
            ensure_ascii=False
        )

# ============================================================
# CHAT DATA
# ============================================================

USER_ACTIVE_CHAT = {}
USER_CHAT_COUNT = {}
USER_INTERESTED = {}

# ============================================================
# ADMIN CONVERSATION SYSTEM
# ============================================================

CONVERSATIONS = {}
ADMIN_INBOX_MESSAGE_ID = None

# ============================================================
# CONVERSATION KEY
# ============================================================

def get_conversation_key(user_id, profile_name):
    return f"{user_id}_{profile_name}"

# ============================================================
# ADMIN INBOX
# ============================================================

async def update_admin_inbox(
    context: ContextTypes.DEFAULT_TYPE
):
    global ADMIN_INBOX_MESSAGE_ID

    # Get conversations from PostgreSQL
    conversations = get_admin_conversations(20)

    inbox_text = (
        "📥 TRAUMA ADMIN INBOX\n\n"
        f"💬 Active conversations: {len(conversations)}\n\n"
    )

    keyboard = []

    # Show newest conversations first
    for conversation in conversations:

        user_name = conversation.get(
            "user_name",
            "Unknown"
        )

        city = conversation.get(
            "city",
            "Unknown"
        )

        profile_name = conversation.get(
            "profile_name",
            "Unknown"
        )

        latest_message = conversation.get(
            "latest_message",
            ""
        )

        unread = conversation.get(
            "unread_count",
            0
        )

        if len(latest_message) > 50:
            latest_message = (
                latest_message[:50]
                + "..."
            )

        if unread > 0:
            status = f"🔴 {unread} new"
        else:
            status = "🟢 Read"

        inbox_text += (
            f"👤 {user_name}\n"
            f"📍 {city}\n"
            f"❤️ {profile_name}\n"
            f"💬 {latest_message}\n"
            f"{status}\n\n"
        )

        keyboard.append([
            InlineKeyboardButton(
                f"💬 Open {user_name} × {profile_name}",
                callback_data=f"open_chat_{conversation['id']}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "🔄 Refresh Inbox",
            callback_data="refresh_admin_inbox"
        )
    ])

    markup = InlineKeyboardMarkup(keyboard)

    # --------------------------------------------------------
    # CREATE INBOX MESSAGE
    # --------------------------------------------------------

    if ADMIN_INBOX_MESSAGE_ID is None:

        message = await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=inbox_text,
            reply_markup=markup
        )

        ADMIN_INBOX_MESSAGE_ID = message.message_id

        return

    # --------------------------------------------------------
    # UPDATE EXISTING INBOX MESSAGE
    # --------------------------------------------------------

    try:

        await context.bot.edit_message_text(
            chat_id=ADMIN_ID,
            message_id=ADMIN_INBOX_MESSAGE_ID,
            text=inbox_text,
            reply_markup=markup
        )

    except Exception as error:

        logger.error(
            "Could not update admin inbox: %s",
            error
        )

# Admin reply system
ADMIN_REPLYING_TO = None
ADMIN_REPLYING_MODE = None
ADMIN_REPLYING_PROFILE = None

# ============================================================
# BROADCAST DATA
# ============================================================

BROADCAST_DATA = {}

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN is not set. Please set your BotFather token "
        "in the terminal before starting the bot."
    )


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# ============================================================
# REGISTRATION STATES
# ============================================================

(
    AGE_CHECK,
    NAME,
    GENDER,
    AGE,
    CITY,
    STATE,
    PHOTO,
    PHONE,
    BIO,
    TALK_GENDER,
    AGE_PREFERENCE,
    QUESTION_1,
    QUESTION_2,
    QUESTION_3,
    QUESTION_4,
    QUESTION_5,
    QUESTION_6,
    QUESTION_7,
    QUESTION_8,
) = range(19)


# ============================================================
# 8 QUESTIONNAIRE QUESTIONS
# ============================================================

QUESTIONS = [
    "Are you interested in having sex with more than one person at the same time (threesome/group sex)?",

    "Are you interested in having sex outdoors?",

    "Are you interested in tying up someone or being tied up during sex?",

    "Are you interested in using sex toys?",

    "Are you interested in having Anal sex?",

    "Are you interested in having oral sex?",

    "Are you interested to record while having sex?",

    "Are you interested to have sex with same gender (gay/lesbian) ?",
]


# ============================================================
# /START
# ============================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data.clear()

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ I'm 18+",
                callback_data="age_yes"
            )
        ]
    ]

    await update.message.reply_text(
        "👋 Welcome to HookupIndia.\n\n"
        "A place where people look for, "
        "people who only want physical connections "
        "not love and relationships.\n\n"
        "🔞 You must be 18 or older to use this bot.\n\n"
        "Please confirm that you are 18 or older.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return AGE_CHECK


# ============================================================
# AGE CHECK
# ============================================================

async def age_check(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    if query.data == "age_no":

        await query.edit_message_text(
            "❌ Sorry, you must be 18 or older "
            "to use this bot."
        )

        return ConversationHandler.END

    await query.edit_message_text(
        "✅ Age confirmed.\n\n"
        "Let's create your profile.\n\n"
        "👤 What is your name?"
    )

    return NAME


# ============================================================
# NAME
# ============================================================

async def get_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    name = update.message.text.strip()

    if len(name) < 2:

        await update.message.reply_text(
            "❌ Please enter a valid name."
        )

        return NAME

    if len(name) > 50:

        await update.message.reply_text(
            "❌ Name is too long. "
            "Please enter a shorter name."
        )

        return NAME

    context.user_data["name"] = name

    keyboard = [
        [
            InlineKeyboardButton(
                "👨 Male",
                callback_data="gender_male"
            ),
            InlineKeyboardButton(
                "👩 Female",
                callback_data="gender_female"
            ),
        ]
    ]

    await update.message.reply_text(
        "Choose your gender:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return GENDER


# ============================================================
# GENDER
# ============================================================

async def get_gender(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    if query.data == "gender_male":

        context.user_data["gender"] = "male"

    elif query.data == "gender_female":

        context.user_data["gender"] = "female"

    await query.edit_message_text(
        "🎂 What is your age?"
    )

    return AGE


# ============================================================
# AGE
# ============================================================

async def get_age(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    age_text = update.message.text.strip()

    if not age_text.isdigit():

        await update.message.reply_text(
            "❌ Please enter your age as a number."
        )

        return AGE

    age = int(age_text)

    if age < 18:

        await update.message.reply_text(
            "❌ You must be 18 or older to use this bot."
        )

        return ConversationHandler.END

    if age > 100:

        await update.message.reply_text(
            "❌ Please enter a valid age."
        )

        return AGE

    context.user_data["age"] = age

    await update.message.reply_text(
        "🏙️ What city do you live in?"
    )

    return CITY


# ============================================================
# CITY
# ============================================================

async def get_city(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    city = update.message.text.strip()

    if len(city) < 2:

        await update.message.reply_text(
            "❌ Please enter a valid city."
        )

        return CITY

    if len(city) > 100:

        await update.message.reply_text(
            "❌ Please enter a shorter city name."
        )

        return CITY

    context.user_data["city"] = city

    await update.message.reply_text(
        "📍 What state do you live in?"
    )

    return STATE


# ============================================================
# STATE
# ============================================================

async def get_state(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    state = update.message.text.strip()

    if len(state) < 2:

        await update.message.reply_text(
            "❌ Please enter a valid state."
        )

        return STATE

    if len(state) > 100:

        await update.message.reply_text(
            "❌ Please enter a shorter state name."
        )

        return STATE

    context.user_data["state"] = state

    await update.message.reply_text(
        "📸 Now send your profile photo."
    )

    return PHOTO


# ============================================================
# PROFILE PHOTO
# ============================================================

async def get_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message.photo:

        await update.message.reply_text(
            "❌ Please send a photo."
        )

        return PHOTO

    # Highest-resolution photo
    photo = update.message.photo[-1]

    # Telegram file_id
    context.user_data["photo_id"] = photo.file_id

    await update.message.reply_text(
        "📱 Enter your 10-digit phone number.\n\n"
        "Example: 9876543210"
    )

    return PHONE


# ============================================================
# PHONE
# ============================================================

async def get_phone(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    phone = update.message.text.strip()

    # Only numbers
    if not phone.isdigit():

        await update.message.reply_text(
            "❌ Please enter only numbers.\n\n"
            "Example: 9876543210"
        )

        return PHONE

    # Exactly 10 digits
    if len(phone) != 10:

        await update.message.reply_text(
            "❌ Please enter exactly 10 digits.\n\n"
            "Example: 9876543210"
        )

        return PHONE

    context.user_data["phone"] = phone

    await update.message.reply_text(
        "💬 Tell us a little about yourself.\n\n"
        "Write a short bio."
    )

    return BIO


# ============================================================
# BIO
# ============================================================

async def get_bio(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    bio = update.message.text.strip()

    if len(bio) < 5:

        await update.message.reply_text(
            "❌ Please write a little more about yourself."
        )

        return BIO

    if len(bio) > 500:

        await update.message.reply_text(
            "❌ Your bio is too long.\n\n"
            "Please keep it under 500 characters."
        )

        return BIO

    context.user_data["bio"] = bio

    keyboard = [
        [
            InlineKeyboardButton(
                "👨 Male",
                callback_data="talk_male"
            ),
            InlineKeyboardButton(
                "👩 Female",
                callback_data="talk_female"
            ),
        ]
    ]

    await update.message.reply_text(
        "💬 Who do you want to hookup with?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return TALK_GENDER


# ============================================================
# WHO THEY WANT TO TALK TO
# ============================================================

async def get_talk_gender(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    if query.data == "talk_male":

        context.user_data["talk_gender"] = "male"

    elif query.data == "talk_female":

        context.user_data["talk_gender"] = "female"

    keyboard = [
        [
            InlineKeyboardButton(
                "⬇️ Younger",
                callback_data="pref_younger"
            )
        ],
        [
            InlineKeyboardButton(
                "⬆️ Older",
                callback_data="pref_older"
            )
        ],
        [
            InlineKeyboardButton(
                "🔄 Any Age",
                callback_data="pref_any_age"
            )
        ],
    ]

    await query.edit_message_text(
        "🎂 What age group are you interested in to hookup?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return AGE_PREFERENCE


# ============================================================
# AGE PREFERENCE
# ============================================================

async def get_age_preference(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    if query.data == "pref_younger":

        preference = "younger"

    elif query.data == "pref_older":

        preference = "older"

    else:

        preference = "any_age"

    context.user_data["age_preference"] = preference

    # Start questionnaire
    context.user_data["question_index"] = 0
    context.user_data["answers"] = []

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Yes",
                callback_data="answer_yes"
            ),
            InlineKeyboardButton(
                "❌ No",
                callback_data="answer_no"
            ),
        ]
    ]

    await query.edit_message_text(
        "🧠 Let's answer 8 quick questions.\n\n"
        "There are no right or wrong answers.\n\n"
        "Question 1:\n\n"
        f"{QUESTIONS[0]}",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return QUESTION_1


# ============================================================
# QUESTION HANDLER
# ============================================================

async def handle_question(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    if query.data == "answer_yes":

        answer = "Yes"

    else:

        answer = "No"

    context.user_data["answers"].append(answer)

    current_index = context.user_data["question_index"]

    next_index = current_index + 1

    context.user_data["question_index"] = next_index

    # --------------------------------------------------------
    # ALL 8 QUESTIONS COMPLETED
    # --------------------------------------------------------

    if next_index >= len(QUESTIONS):

        await finish_registration(
            update,
            context
        )

        return ConversationHandler.END

    # --------------------------------------------------------
    # NEXT QUESTION
    # --------------------------------------------------------

    question_number = next_index + 1

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Yes",
                callback_data="answer_yes"
            ),
            InlineKeyboardButton(
                "❌ No",
                callback_data="answer_no"
            ),
        ]
    ]

    await query.edit_message_text(
        f"Question {question_number}:\n\n"
        f"{QUESTIONS[next_index]}",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    # QUESTION_1 = 11
    # QUESTION_2 = 12
    # ...
    # QUESTION_8 = 18

    return QUESTION_1 + next_index


# ============================================================
# REGISTRATION COMPLETE
# ============================================================

async def finish_registration(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    data = context.user_data

        # ========================================================
    # SAVE USER FOR FUTURE BROADCASTS
    # ========================================================

    user_id = update.effective_user.id

    users = load_users()

    users[str(user_id)] = {
        "name": data.get("name", ""),
        "phone": data.get("phone", ""),
        "age": data.get("age", ""),
        "city": data.get("city", ""),
        "state": data.get("state", ""),
    }

    save_users(users)

    # --------------------------------------------------------
    # ADMIN NOTIFICATION
    # --------------------------------------------------------

    caption = (
        "🆕 NEW USER REGISTRATION\n\n"
        f"👤 Name: {data['name']}\n"
        f"📱 Phone: {data['phone']}\n"
        f"🎂 Age: {data['age']}\n"
        f"🏙️ City: {data['city']}\n"
        f"📍 State: {data['state']}"
    )

    try:

        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=data["photo_id"],
            caption=caption,
        )

        logger.info(
            "Registration notification sent to admin."
        )

    except Exception as error:

        logger.error(
            "Failed to send registration notification: %s",
            error,
        )

        # --------------------------------------------------------
    # USER CONFIRMATION
    # --------------------------------------------------------

    query = update.callback_query

    await query.message.reply_text(
        "🎉 Registration Complete!\n\n"
        "Your profile has been saved successfully.\n\n"
        "Let's find people for you to hookup . 💙"
    )

    await show_profiles(
        update,
        context
    )

    logger.info(
        "Registration completed for user ID: %s",
        update.effective_user.id,
    )

# ============================================================
# PROFILE BROWSING
# ============================================================

async def show_profiles(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    Shows up to 10 profiles based on the user's
    gender and age preference.
    """

    user_data = context.user_data

    talk_gender = user_data.get("talk_gender")
    age_preference = user_data.get("age_preference")

    city = user_data.get("city")
    state = user_data.get("state")

    if not talk_gender or not age_preference:
        return

    category = (
        talk_gender,
        age_preference
    )

    profiles = PROFILES.get(category, [])

    if not profiles:

        await update.effective_message.reply_text(
            "😔 Sorry, there are currently no profiles "
            "available in this category."
        )

        return

    # --------------------------------------------------------
    # Store profile list and current position
    # --------------------------------------------------------

    context.user_data["profile_list"] = profiles
    context.user_data["profile_index"] = 0

    await send_next_profiles(
        update,
        context
    )


# ============================================================
# SEND NEXT 10 PROFILES
# ============================================================

async def send_next_profiles(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    profiles = context.user_data.get(
        "profile_list",
        []
    )

    current_index = context.user_data.get(
        "profile_index",
        0
    )

    if current_index >= len(profiles):

        await update.effective_message.reply_text(
            "😔 You've reached the end of the available profiles."
        )

        return

    # Show maximum 10 profiles
    end_index = min(
        current_index + 10,
        len(profiles)
    )

    profiles_to_show = profiles[
        current_index:end_index
    ]

    city = context.user_data.get("city")
    state = context.user_data.get("state")

    for profile in profiles_to_show:

        caption = (
            f"👤 {profile['name']}\n"
            f"🎂 Age: {profile['age']}\n"
            f"📍 {city}, {state}\n\n"
            f"💬 {profile['bio']}"
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "❤️ Interested",
                    callback_data=f"profile_interested_{profile['name']}"
                ),
                InlineKeyboardButton(
                    "💬 Chat",
                    callback_data=f"profile_chat_{profile['name']}"
                )
            ]
        ]

        try:

            await update.effective_message.reply_photo(
                photo=profile["photo_id"],
                caption=caption,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        except Exception as error:

            logger.error(
                "Could not send profile %s: %s",
                profile.get("name"),
                error
            )

    # Update index
    context.user_data["profile_index"] = end_index

    # --------------------------------------------------------
    # LOAD MORE BUTTON
    # --------------------------------------------------------

    if end_index < len(profiles):

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔽 Load More",
                    callback_data="load_more"
                )
            ]
        ]

        await update.effective_message.reply_text(
            "Want to see more profiles?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    else:

        await update.effective_message.reply_text(
            "✅ You've seen all available profiles."
        )


# ============================================================
# LOAD MORE
# ============================================================

async def load_more(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    await query.edit_message_reply_markup(
        reply_markup=None
    )

    await send_next_profiles(
        update,
        context
    )


# ============================================================
# INTERESTED BUTTON
# ============================================================

async def profile_interested(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    data = query.data

    # profile_interested_ProfileName
    profile_name = data[len("profile_interested_"):]

    user_id = update.effective_user.id

    if user_id not in USER_INTERESTED:
        USER_INTERESTED[user_id] = []

    if profile_name not in USER_INTERESTED[user_id]:
        USER_INTERESTED[user_id].append(profile_name)

        await query.message.reply_text(
            f"❤️ You marked {profile_name} as interested."
        )

    else:
        await query.message.reply_text(
            f"❤️ You already marked {profile_name} as interested."
        )


# ============================================================
# CHAT BUTTON
# ============================================================

async def profile_chat(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    data = query.data

    # Get profile name
    profile_name = data[len("profile_chat_"):]

    user_id = update.effective_user.id

    # --------------------------------------------------------
    # USER ALREADY HAS A FREE CHAT
    # --------------------------------------------------------

    if user_id in USER_ACTIVE_CHAT:

        current_profile = USER_ACTIVE_CHAT[user_id]

        keyboard = [
            [
                InlineKeyboardButton(
                    "⭐ Join HookupIndia Premium Club",
                    callback_data="join_premium"
                )
            ]
        ]

        await query.message.reply_text(
            f"⭐ You already have a free chat with "
            f"{current_profile}.\n\n"
            "Join Premium Club to chat with another profile.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return

    # --------------------------------------------------------
    # START FREE CHAT
    # --------------------------------------------------------

    USER_ACTIVE_CHAT[user_id] = profile_name

    USER_CHAT_COUNT[user_id] = 0

    await query.message.reply_text(
        f"💬 You selected {profile_name}.\n\n"
        "You can send your first message now."
    )

# ============================================================
# FREE CHAT MESSAGE HANDLER
# ============================================================

# ============================================================
# FREE CHAT MESSAGE HANDLER
# ============================================================

async def handle_chat_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
        # ========================================================
    # BROADCAST TEXT
    # ========================================================

    if update.effective_user.id == ADMIN_ID:

        broadcast_step = BROADCAST_DATA.get("step")

        if broadcast_step == "name":
            await broadcast_name(update, context)
            return

        elif broadcast_step == "age":
            await broadcast_age(update, context)
            return

        elif broadcast_step == "message":
            await broadcast_message(update, context)
            return

    # ========================================================
    # UTR SUBMISSION
    # ========================================================

    if context.user_data.get("waiting_for_utr"):

        await handle_utr(
            update,
            context
        )

        return
        
	# ========================================================
    # NEW ADMIN REPLY
    # ========================================================

    if update.effective_user.id == ADMIN_ID:

        reply_user_id = context.user_data.get(
            "new_reply_user_id"
        )

        reply_profile = context.user_data.get(
            "new_reply_profile"
        )

        reply_mode = context.user_data.get(
            "new_reply_mode"
        )

        if reply_user_id is not None:

            reply_text = update.message.text

            conversation_id = get_or_create_conversation(
                reply_user_id,
                reply_profile,
                context.user_data.get(
                    "new_reply_user_name",
                    "Unknown"
                ),
                context.user_data.get(
                    "new_reply_city",
                    "Unknown"
                ),
                context.user_data.get(
                    "new_reply_state",
                    "Unknown"
                )
            )

            if not conversation_id:
                await update.message.reply_text(
                "❌ Conversation not found."
            )
            return

            try:

                if reply_mode == "profile":

                    message_to_user = (
                        f"💬 {reply_profile}:\n\n"
                        f"{reply_text}"
                    )

                    sender_type = "profile"

                else:

                    message_to_user = (
                        "👑 Admin:\n\n"
                        f"{reply_text}"
                    )

                    sender_type = "admin"

                await context.bot.send_message(
                    chat_id=reply_user_id,
                    text=message_to_user
                )

                conversation["messages"].append({
                    "sender": sender_type,
                    "text": reply_text
                })

                await update.message.reply_text(
                    "✅ Reply sent."
                )

                context.user_data.pop(
                    "new_reply_user_id",
                    None
                )

                context.user_data.pop(
                    "new_reply_profile",
                    None
                )

                context.user_data.pop(
                    "new_reply_mode",
                    None
                )

            except Exception as error:

                logger.error(
                    "Could not send new admin reply: %s",
                    error
                )

                await update.message.reply_text(
                    "❌ Could not send the reply."
                )

            return
    user_id = update.effective_user.id
    # --------------------------------------------------------
    # CHECK ACTIVE CHAT
    # --------------------------------------------------------

    if user_id not in USER_ACTIVE_CHAT:

        await update.message.reply_text(
            "💬 Please select a profile and click "
            "\"Chat\" to start a conversation."
        )

        return

    # --------------------------------------------------------
    # CURRENT PROFILE
    # --------------------------------------------------------

    profile_name = USER_ACTIVE_CHAT[user_id]

    count = USER_CHAT_COUNT.get(
        user_id,
        0
    )

    # --------------------------------------------------------
    # THIRD MESSAGE → DELETE + PREMIUM
    # --------------------------------------------------------

    if count >= 2:

        # Delete the user's third message
        try:
            await update.message.delete()
        except Exception as error:
            logger.error(
                "Could not delete third message: %s",
                error
            )

        keyboard = [
            [
                InlineKeyboardButton(
                    "⭐ Join Premium Club",
                    callback_data="join_premium"
                )
            ]
        ]

        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "⭐ You've used your 2 free messages.\n\n"
                "Join Premium Club to continue this conversation."
            ),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return

    # --------------------------------------------------------
    # MESSAGE 1 OR MESSAGE 2
    # --------------------------------------------------------

    message_number = count + 1

    USER_CHAT_COUNT[user_id] = message_number

    user_name = context.user_data.get(
        "name",
        "Unknown"
    )

    city = context.user_data.get(
        "city",
        "Unknown"
    )

    state = context.user_data.get(
        "state",
        "Unknown"
    )

    message_text = update.message.text

    # --------------------------------------------------------
    # SAVE MESSAGE TO CONVERSATION
    # --------------------------------------------------------

    conversation_key = get_conversation_key(
        user_id,
        profile_name
    )

    conversation_id = get_or_create_conversation(
        user_id,
        profile_name,
        user_name,
        city,
        state
    )

    if conversation_id:
        save_chat_message(
            conversation_id,
            "user",
            message_text
        )

    await update_admin_inbox(context)

    # --------------------------------------------------------
    # SIMPLE USER CONFIRMATION
    # --------------------------------------------------------

    await update.message.reply_text(
        "💬 Message sent."
    )
# ============================================================
# OPEN ADMIN CHAT
# ============================================================

async def open_admin_chat(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    if update.effective_user.id != ADMIN_ID:
        return

    data = query.data

    
   # open_chat_CONVERSATION_ID
    conversation_id = int(
        data[len("open_chat_"):]
    )

    conversation = get_admin_conversation_by_id(
        conversation_id
    )

    if not conversation:
        await query.message.reply_text(
            "❌ Conversation not found."
        )
        return

    # Mark conversation as read
    # Mark conversation as read in PostgreSQL
    mark_conversation_read(conversation_id)

    conversation["unread_count"] = 0

    messages = conversation.get(
        "messages",
        []
    )

    user_name = conversation.get(
        "user_name",
        "Unknown"
    )

    city = conversation.get(
        "city",
        "Unknown"
    )

    state = conversation.get(
        "state",
        "Unknown"
    )
    profile_name = conversation.get(
        "profile_name",
        "Unknown"
    )

    user_id = conversation.get(
        "user_id"
    )

    chat_text = (
        f"💬 CHAT — {user_name}\n\n"
        f"📍 {city}, {state}\n"
        f"❤️ Profile: {profile_name}\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
    )

    for message in messages:

        sender = message.get(
            "sender",
            "user"
        )

        text = message.get(
            "text",
            ""
        )

        if sender == "user":

            chat_text += (
                f"👤 {user_name}:\n"
                f"{text}\n\n"
            )

        elif sender == "profile":

            chat_text += (
                f"💬 {profile_name}:\n"
                f"{text}\n\n"
            )

        else:

            chat_text += (
                "👑 Admin:\n"
                f"{text}\n\n"
            )

    keyboard = [
        [
            InlineKeyboardButton(
                f"↩️ Reply as {profile_name}",
                callback_data=(
                    f"new_reply_profile_{user_id}_"
                    f"{profile_name}"
                )
            )
        ],
        [
            InlineKeyboardButton(
                "👑 Reply as Admin",
                callback_data=(
                    f"new_reply_admin_{user_id}_"
                    f"{profile_name}"
                )
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Back to Inbox",
                callback_data="refresh_admin_inbox"
            )
        ]
    ]

    await query.message.reply_text(
        chat_text,
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )

    # Update inbox after marking as read
    await update_admin_inbox(context)

# ============================================================
# NEW REPLY AS PROFILE
# ============================================================

async def new_reply_as_profile(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    if update.effective_user.id != ADMIN_ID:
        return

    data = query.data

    remaining = data[len("new_reply_profile_"):]

    user_id_text, profile_name = remaining.split(
        "_",
        1
    )

    user_id = int(user_id_text)

    context.user_data["new_reply_user_id"] = user_id
    context.user_data["new_reply_profile"] = profile_name
    context.user_data["new_reply_mode"] = "profile"

    await query.message.reply_text(
        f"↩️ Replying as {profile_name}\n\n"
        f"Type your message to the user."
    )

# ============================================================
# NEW REPLY AS ADMIN
# ============================================================

async def new_reply_as_admin(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    if update.effective_user.id != ADMIN_ID:
        return

    data = query.data

    remaining = data[len("new_reply_admin_"):]

    user_id_text, profile_name = remaining.split(
        "_",
        1
    )

    user_id = int(user_id_text)

    context.user_data["new_reply_user_id"] = user_id
    context.user_data["new_reply_profile"] = profile_name
    context.user_data["new_reply_mode"] = "admin"

    await query.message.reply_text(
        "👑 Replying as Admin\n\n"
        "Type your message to the user."
    )
	
# ============================================================
# PREMIUM CLUB
# ============================================================

async def join_premium(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    await query.message.reply_photo(
        photo=PAYMENT_QR_ID,
        caption=(
            "⭐ PREMIUM CLUB\n\n"
            f"💰 Price: {PREMIUM_PRICE}\n\n"
            "Download the QR code and scan from any app to make the payment.\n\n"
            "After payment, click the button below "
            "and enter your UTR number."
        ),
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "💳 I've Made the Payment",
                    callback_data="payment_done"
                )
            ]
        ])
    )

async def payment_done(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "🔢 Please enter your UTR number."
    )

    context.user_data["waiting_for_utr"] = True

# ============================================================
# UTR HANDLER
# ============================================================

async def handle_utr(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not context.user_data.get(
        "waiting_for_utr"
    ):
        return

    utr = update.message.text.strip()

    if not utr.isdigit():

        await update.message.reply_text(
            "❌ Please enter a valid UTR number."
        )

        return

    if len(utr) < 10 or len(utr) > 20:

        await update.message.reply_text(
            "❌ Please enter a valid UTR number."
        )

        return

    context.user_data["waiting_for_utr"] = False

    # Registered name, NOT Telegram name
    user_name = context.user_data.get(
        "name",
        "Unknown"
    )

    # --------------------------------------------------------
    # ADMIN PAYMENT NOTIFICATION
    # --------------------------------------------------------

    admin_message = (
        "💳 PAYMENT\n\n"
        f"👤 Name: {user_name}\n"
        f"🔢 UTR: {utr}"
    )

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=admin_message
    )

    await update.message.reply_text(
        "✅ Payment details submitted.\n\n"
        "Your payment will be verified."
    )

# ============================================================
# BROADCAST START
# ============================================================

async def broadcast_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.effective_user.id != ADMIN_ID:
        return

    BROADCAST_DATA.clear()

    BROADCAST_DATA["step"] = "photo"

    await update.message.reply_text(
        "📢 BROADCAST\n\n"
        "Step 1/4\n\n"
        "📸 Send the profile photo."
    )

# ============================================================
# BROADCAST PHOTO
# ============================================================

async def broadcast_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.effective_user.id != ADMIN_ID:
        return

    if BROADCAST_DATA.get("step") != "photo":
        return

    if not update.message.photo:
        return

    photo_id = update.message.photo[-1].file_id

    BROADCAST_DATA["photo_id"] = photo_id
    BROADCAST_DATA["step"] = "name"

    await update.message.reply_text(
        "👤 Step 2/4\n\n"
        "Enter the profile name."
    )

# ============================================================
# BROADCAST PROFILE NAME
# ============================================================

async def broadcast_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.effective_user.id != ADMIN_ID:
        return

    if BROADCAST_DATA.get("step") != "name":
        return

    name = update.message.text.strip()

    if not name:
        await update.message.reply_text(
            "❌ Please enter a profile name."
        )
        return

    BROADCAST_DATA["name"] = name
    BROADCAST_DATA["step"] = "age"

    await update.message.reply_text(
        "🎂 Step 3/4\n\n"
        "Enter the profile age."
    )

# ============================================================
# BROADCAST PROFILE AGE
# ============================================================

async def broadcast_age(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.effective_user.id != ADMIN_ID:
        return

    if BROADCAST_DATA.get("step") != "age":
        return

    age_text = update.message.text.strip()

    if not age_text.isdigit():

        await update.message.reply_text(
            "❌ Please enter the age as a number."
        )

        return

    age = int(age_text)

    if age < 18 or age > 100:

        await update.message.reply_text(
            "❌ Please enter a valid age between 18 and 100."
        )

        return

    BROADCAST_DATA["age"] = age
    BROADCAST_DATA["step"] = "message"

    await update.message.reply_text(
        "💬 Step 4/4\n\n"
        "Enter the message you want to send.\n\n"
        "You can use:\n"
        "{user_name}\n"
        "{user_city}\n"
        "{user_state}"
    )

# ============================================================
# BROADCAST MESSAGE
# ============================================================

async def broadcast_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.effective_user.id != ADMIN_ID:
        return

    if BROADCAST_DATA.get("step") != "message":
        return

    message = update.message.text.strip()

    if not message:
        await update.message.reply_text(
            "❌ Please enter a message."
        )
        return

    BROADCAST_DATA["message"] = message
    BROADCAST_DATA["step"] = "preview"

    name = BROADCAST_DATA["name"]
    age = BROADCAST_DATA["age"]
    photo_id = BROADCAST_DATA["photo_id"]

    preview_message = (
        f"👤 {name}\n"
        f"🎂 Age: {age}\n\n"
        f"{name} is interested to hookup with you.\n\n"
        f"💬 Message from {name}:\n\n"
        f"\"{message}\""
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "💬 Chat",
                 callback_data=f"broadcast_chat_{name}"
            )
        ],
        [
            InlineKeyboardButton(
                "✅ Send Broadcast",
                callback_data="broadcast_send"
            ),
            InlineKeyboardButton(
                "❌ Cancel",
                callback_data="broadcast_cancel"
            )
        ]
    ]

    await update.message.reply_photo(
        photo=photo_id,
        caption=preview_message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )




# ============================================================
# /RESTART
# ============================================================

async def restart(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    context.user_data.clear()

    USER_ACTIVE_CHAT.pop(user_id, None)
    USER_CHAT_COUNT.pop(user_id, None)
    USER_INTERESTED.pop(user_id, None)

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ I'm 18+",
                callback_data="age_yes"
            )
        ]
    ]

    await update.message.reply_text(
        "🔄 Registration restarted.\n\n"
        "Please confirm that you are 18 or older.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return AGE_CHECK


# ============================================================
# /CANCEL
# ============================================================

async def cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data.clear()

    await update.message.reply_text(
        "❌ Registration cancelled.\n\n"
        "Use /start whenever you want to begin again."
    )

    return ConversationHandler.END


# ============================================================
# ERROR HANDLER
# ============================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):

    logger.error(
        "Exception while handling an update:",
        exc_info=context.error,
    )

# ============================================================
# BROADCAST TEXT CONTROLLER
# ============================================================

async def broadcast_text_controller(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.effective_user.id != ADMIN_ID:
        return

    step = BROADCAST_DATA.get("step")

    if step == "name":
        await broadcast_name(update, context)
        return

    elif step == "age":
        await broadcast_age(update, context)
        return

    elif step == "message":
        await broadcast_message(update, context)
        return

    # IMPORTANT:
    # If no broadcast is active, allow the normal
    # handle_chat_message handler to process the text.
    raise ApplicationHandlerStop

# ============================================================
# BROADCAST CHAT BUTTON
# ============================================================

async def broadcast_chat(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    data = query.data

    profile_name = data[len("broadcast_chat_"):]

    keyboard = [
        [
            InlineKeyboardButton(
                "⭐ Join Premium Club",
                callback_data="join_premium"
            )
        ]
    ]

    await query.message.reply_text(
        f"⭐ Premium Club\n\n"
        f"To continue chatting with {profile_name}, "
        "please join Premium Club.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ============================================================
# BROADCAST CANCEL
# ============================================================

async def broadcast_cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    if update.effective_user.id != ADMIN_ID:
        return

    BROADCAST_DATA.clear()

    await query.message.reply_text(
        "❌ Broadcast cancelled."
    )

# ============================================================
# BROADCAST SEND
# ============================================================

# ============================================================
# SEND BROADCAST
# ============================================================

async def broadcast_send(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    if update.effective_user.id != ADMIN_ID:
        return

    if not BROADCAST_DATA:
        await query.message.reply_text(
            "❌ No broadcast data found."
        )
        return

    # --------------------------------------------------------
    # LOAD USERS
    # --------------------------------------------------------

    users = load_users()

    if not users:
        await query.message.reply_text(
            "❌ No registered users found."
        )
        return

    # --------------------------------------------------------
    # BROADCAST INFORMATION
    # --------------------------------------------------------

    photo_id = BROADCAST_DATA.get("photo_id")
    profile_name = BROADCAST_DATA.get("name")
    profile_age = BROADCAST_DATA.get("age")
    message_template = BROADCAST_DATA.get("message")

    sent = 0
    failed = 0
    removed = 0

    await query.message.reply_text(
        "📢 Broadcast started.\n\n"
        f"👤 Profile: {profile_name}\n"
        f"👥 Users: {len(users)}\n\n"
        "Please wait..."
    )

    # --------------------------------------------------------
    # SEND TO USERS
    # --------------------------------------------------------

    for user_id, user_data in list(users.items()):

        # Skip users previously marked as blocked
        if user_data.get("blocked", False):
            continue

        # ----------------------------------------------------
        # PERSONALIZE MESSAGE
        # ----------------------------------------------------

        user_name = user_data.get(
            "name",
            ""
        )

        user_city = user_data.get(
            "city",
            ""
        )

        user_state = user_data.get(
            "state",
            ""
        )

        personalized_message = (
            message_template
            .replace(
                "{user_name}",
                user_name
            )
            .replace(
                "{user_city}",
                user_city
            )
            .replace(
                "{user_state}",
                user_state
            )
        )

        caption = (
            f"👤 {profile_name}\n"
            f"🎂 Age: {profile_age}\n\n"
            f"{profile_name} is interested to hookup with you.\n\n"
            f"💬 Message from {profile_name}:\n\n"
            f"\"{personalized_message}\""
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "💬 Chat",
                    callback_data=(
                        f"broadcast_chat_{profile_name}"
                    )
                )
            ]
        ]

        # ----------------------------------------------------
        # SEND WITH RETRY
        # ----------------------------------------------------

        success = False
        permanently_failed = False

        for attempt in range(3):

            try:

                await context.bot.send_photo(
                    chat_id=int(user_id),
                    photo=photo_id,
                    caption=caption,
                    reply_markup=InlineKeyboardMarkup(
                        keyboard
                    )
                )

                success = True
                sent += 1
                break

            except RetryAfter as error:

                wait_time = error.retry_after

                logger.warning(
                    "Rate limited. Waiting %s seconds.",
                    wait_time
                )

                await asyncio.sleep(
                    wait_time + 1
                )

            except Forbidden:

                user_data["blocked"] = True
                permanently_failed = True
                removed += 1
                break

            except Exception as error:

                logger.error(
                    "Broadcast attempt %s failed for %s: %s",
                    attempt + 1,
                    user_id,
                    error
                )

                if attempt < 2:
                    await asyncio.sleep(2)

        if not success and not permanently_failed:
            failed += 1

        # ----------------------------------------------------
        # CONTROLLED SEND RATE
        # ----------------------------------------------------

        await asyncio.sleep(0.1)

    # --------------------------------------------------------
    # SAVE UPDATED USER DATABASE
    # --------------------------------------------------------

    save_users(users)

    # --------------------------------------------------------
    # CLEAR BROADCAST DATA
    # --------------------------------------------------------

    BROADCAST_DATA.clear()

    # --------------------------------------------------------
    # FINAL REPORT
    # --------------------------------------------------------

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "📢 BROADCAST COMPLETE\n\n"
            f"✅ Sent: {sent}\n"
            f"❌ Failed: {failed}\n"
            f"🗑 Blocked/removed: {removed}\n"
            f"👥 Total users: {len(users)}"
        )
    )
# ============================================================
# MAIN
# ============================================================

def main():

    init_database()

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    registration_handler = ConversationHandler(

    entry_points=[
        CommandHandler("start", start),
        CommandHandler("restart", restart),
    ],

        states={

            # --------------------------------------------
            # AGE CHECK
            # --------------------------------------------

            AGE_CHECK: [
                CallbackQueryHandler(
                    age_check,
                    pattern=r"^age_(yes|no)$"
                )
            ],

            # --------------------------------------------
            # NAME
            # --------------------------------------------

            NAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_name
                )
            ],

            # --------------------------------------------
            # GENDER
            # --------------------------------------------

            GENDER: [
                CallbackQueryHandler(
                    get_gender,
                    pattern=r"^gender_(male|female)$"
                )
            ],

            # --------------------------------------------
            # AGE
            # --------------------------------------------

            AGE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_age
                )
            ],

            # --------------------------------------------
            # CITY
            # --------------------------------------------

            CITY: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_city
                )
            ],

            # --------------------------------------------
            # STATE
            # --------------------------------------------

            STATE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_state
                )
            ],

            # --------------------------------------------
            # PHOTO
            # --------------------------------------------

            PHOTO: [
                MessageHandler(
                    filters.PHOTO,
                    get_photo
                )
            ],

            # --------------------------------------------
            # PHONE
            # --------------------------------------------

            PHONE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_phone
                )
            ],

            # --------------------------------------------
            # BIO
            # --------------------------------------------

            BIO: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_bio
                )
            ],

            # --------------------------------------------
            # TALKING GENDER
            # --------------------------------------------

            TALK_GENDER: [
                CallbackQueryHandler(
                    get_talk_gender,
                    pattern=r"^talk_(male|female)$"
                )
            ],

            # --------------------------------------------
            # AGE PREFERENCE
            # --------------------------------------------

            AGE_PREFERENCE: [
                CallbackQueryHandler(
                    get_age_preference,
                    pattern=r"^pref_(younger|older|any_age)$"
                )
            ],

            # --------------------------------------------
            # QUESTIONS
            # --------------------------------------------

            QUESTION_1: [
                CallbackQueryHandler(
                    handle_question,
                    pattern=r"^answer_(yes|no)$"
                )
            ],

            QUESTION_2: [
                CallbackQueryHandler(
                    handle_question,
                    pattern=r"^answer_(yes|no)$"
                )
            ],

            QUESTION_3: [
                CallbackQueryHandler(
                    handle_question,
                    pattern=r"^answer_(yes|no)$"
                )
            ],

            QUESTION_4: [
                CallbackQueryHandler(
                    handle_question,
                    pattern=r"^answer_(yes|no)$"
                )
            ],

            QUESTION_5: [
                CallbackQueryHandler(
                    handle_question,
                    pattern=r"^answer_(yes|no)$"
                )
            ],

            QUESTION_6: [
                CallbackQueryHandler(
                    handle_question,
                    pattern=r"^answer_(yes|no)$"
                )
            ],

            QUESTION_7: [
                CallbackQueryHandler(
                    handle_question,
                    pattern=r"^answer_(yes|no)$"
                )
            ],

            QUESTION_8: [
                CallbackQueryHandler(
                    handle_question,
                    pattern=r"^answer_(yes|no)$"
                )
            ],
        },

        fallbacks=[
            CommandHandler("restart", restart),
            CommandHandler("cancel", cancel),
        ],

        allow_reentry=True,
    )

    application.add_handler(
        registration_handler
    )
    application.add_handler(
        CommandHandler(
            "broadcast",
            broadcast_start
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            load_more,
            pattern=r"^load_more$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            profile_interested,
            pattern=r"^profile_interested_.+$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            profile_chat,
            pattern=r"^profile_chat_.+$"
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            open_admin_chat,
            pattern=r"^open_chat_\d+$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            new_reply_as_profile,
            pattern=r"^new_reply_profile_\d+_.+$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            new_reply_as_admin,
            pattern=r"^new_reply_admin_\d+_.+$"
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            join_premium,
            pattern=r"^join_premium$"
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            payment_done,
            pattern=r"^payment_done$"
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            broadcast_chat,
            pattern=r"^broadcast_chat_.+$"
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            broadcast_send,
            pattern=r"^broadcast_send$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            broadcast_cancel,
            pattern=r"^broadcast_cancel$"
        )
    )
    application.add_handler(
        MessageHandler(
            filters.PHOTO,
            broadcast_photo
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_chat_message
        )
    )

    application.add_error_handler(
        error_handler
    )

    print("======================================")
    print("       TRAUMA BOT IS RUNNING")
    print("======================================")

    application.run_polling()


# ============================================================
# START PROGRAM
# ============================================================

if __name__ == "__main__":
    main()
