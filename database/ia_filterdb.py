import logging from struct import pack import re import base64 from pyrogram.file_id import FileId from pymongo.errors import DuplicateKeyError from umongo import Instance, Document, fields from motor.motor_asyncio import AsyncIOMotorClient from marshmallow.exceptions import ValidationError from info import CAPTION_LANGUAGES, DATABASE_URI, DATABASE_URI2, DATABASE_NAME, COLLECTION_NAME, USE_CAPTION_FILTER, MAX_B_TN, MOVIE_UPDATE_CHANNEL, OWNERID from utils import get_settings, save_group_settings, temp, get_status from database.users_chats_db import add_name from .Imdbposter import get_movie_details, fetch_image from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(name) logger.setLevel(logging.INFO) #--------------------------------------------------------- tempDict = {'indexDB': DATABASE_URI}

client = AsyncIOMotorClient(DATABASE_URI) db = client[DATABASE_NAME] instance = Instance.from_db(db)

client2 = AsyncIOMotorClient(DATABASE_URI2) db2 = client2[DATABASE_NAME] instance2 = Instance.from_db(db2)

@instance.register class Media(Document): file_id = fields.StrField(attribute='_id') file_ref = fields.StrField(allow_none=True) file_name = fields.StrField(required=True) file_size = fields.IntField(required=True) file_type = fields.StrField(allow_none=True) mime_type = fields.StrField(allow_none=True) caption = fields.StrField(allow_none=True)

class Meta:
    indexes = ('$file_name', )
    collection_name = COLLECTION_NAME

@instance2.register class Media2(Document): file_id = fields.StrField(attribute='_id') file_ref = fields.StrField(allow_none=True) file_name = fields.StrField(required=True) file_size = fields.IntField(required=True) file_type = fields.StrField(allow_none=True) mime_type = fields.StrField(allow_none=True) caption = fields.StrField(allow_none=True)

class Meta:
    indexes = ('$file_name', )
    collection_name = COLLECTION_NAME

async def send_msg(bot, filename, caption): try: filename = re.sub(r'||\b@\S+|\bwww.\S+', '', filename).strip() caption = re.sub(r'||\b@\S+|\bwww.\S+', '', caption).strip()

season, episodes = '', ''
    match = re.findall(r"[Ss](\d+)[Ee](\d+)", filename)
    if match:
        season = f"s{match[0][0].zfill(2)}"
        episodes = f"episode {match[0][1].zfill(2)}"
    elif re.search(r"[Ss](\d+)", filename):
        season = f"s{re.search(r'[Ss](\d+)', filename).group(1).zfill(2)}"
    if "E" in filename and "&" in filename:
        ep_text = filename.split("E")[-1]
        if ep_text:
            episodes = f"episodes {ep_text.strip()}"

    imdb = await get_movie_details(filename)
    imdb_title = imdb.get("title") if imdb else None
    rating = imdb.get("rating") if imdb else None
    ott = imdb.get("ott") if imdb else None
    poster_url = imdb.get("poster_url") if imdb else None
    resized_poster = await fetch_image(poster_url) if poster_url else None

    qualities = ["ORG", "org", "hdcam", "HDCAM", "HQ", "hq", "HDRip", "hdrip", "camrip", "CAMRip", "hdtc", "predvd", "DVDscr", "dvdscr", "dvdrip", "dvdscr", "HDTC", "dvdscreen", "HDTS", "hdts"]
    quality = await get_qualities(caption.lower(), qualities) or "HDRip"

    language = ""
    for lang in CAPTION_LANGUAGES:
        if lang.lower() in caption.lower():
            language += f"{lang}, "
    language = language[:-2] if language else "Not idea 😄"

    filename = re.sub(r"[\{\}:;'\-!]", "", filename)

    main_title = f"✅ {filename} {season} #𝚃𝚊𝚖𝚒𝚕"
    text = f"{main_title}\n\n"

    if episodes:
        text += f"🍥 {episodes.capitalize()} Added\n\n"
    text += f"👼 ɴᴀᴍᴇ: {filename}\n\n"
    text += f"🫧 Qᴜᴀʟɪᴛʏ: {quality}\n\n"
    text += f"🦋 ᴀᴜᴅɪᴏ: {language}\n\n"
    if imdb_title:
        text += f"✨ IMDB Info\n"
    if ott:
        text += f"📺 OTT: {ott}\n"

    filenames = filename.replace(" ", '-')
    btn = [[InlineKeyboardButton("🌸 ᴄʟɪᴄᴋ ᴛᴏ ꜱᴇᴀʀᴄʜ 🌸", url=f"https://telegram.me/{temp.U_NAME}?start=getfile-{filenames}")]]

    if await add_name(OWNERID, filename):
        if resized_poster:
            await bot.send_photo(chat_id=MOVIE_UPDATE_CHANNEL, photo=resized_poster, caption=text, reply_markup=InlineKeyboardMarkup(btn))
        else:
            await bot.send_message(chat_id=MOVIE_UPDATE_CHANNEL, text=text, reply_markup=InlineKeyboardMarkup(btn))
except Exception as e:
    logger.error(f"Error sending message: {e}")

async def get_qualities(text, qualities: list): quality = [q for q in qualities if q in text] quality = ", ".join(quality) return quality[:-2] if quality.endswith(", ") else quality

