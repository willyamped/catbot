from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, ConversationHandler, CallbackQueryHandler, CommandHandler, MessageHandler, filters
import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
CAT_API_KEY = os.getenv('CAT_API_KEY')

BREED, NO_OF_PHOTOS, GIF = range(3)

# update contains user info
async def hello(update, context):
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')

async def getCat(update, context):
    user = update.message.from_user
    with open('users.json', 'r') as user_db:
        users = json.load(user_db)

    if str(user.id) in users:
        users_info = users[str(user.id)]
        breed = '' if users_info["breed"] == 'all' else 'breeds_ids=' + users_info['breed']
        no_of_photos = int(users_info["no_of_photos"])
        is_gif = "gif" if users_info["is_gif"] else "jpg,png"

        cats = requests.get(f'https://api.thecatapi.com/v1/images/search?api_key{CAT_API_KEY}&limit={no_of_photos}&{breed}&mime_types={is_gif}').json()

        if not cats:
            await update.message.reply_text("Sorry, there's no cats for your settings. Try changing them!")
            return

        for cat in cats:
            url = cat['url']
            if users_info["is_gif"]:
                await context.bot.send_animation(chat_id = update.effective_chat.id, animation = url)
            else:
                await context.bot.send_photo(chat_id = update.effective_chat.id, photo = url)
        if len(cats) < no_of_photos:
            await update.message.reply_text("Sorry, that's all the cats we could find")
    else:
        cats = requests.get(f'https://api.thecatapi.com/v1/images/search?api_key{CAT_API_KEY}').json()
        url = cats[0]['url']
        await context.bot.send_photo(chat_id = update.effective_chat.id, photo = url)

async def chooseBreed(update, context):
    #callback_data is like where all the info about the user choice is saved
    #i think that's the actual breed name used in the API
    keyboard = [
        [
            InlineKeyboardButton("British Shorthair", callback_data = "bsho"),
            InlineKeyboardButton("Bengal", callback_data = "beng"),
        ],
        [
            InlineKeyboardButton("Persian", callback_data = "pers"),
            InlineKeyboardButton("Munchkin", callback_data = "munc"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Please choose a breed:", reply_markup= reply_markup)

async def getCatWithBreed(update, context):
    query = update.callback_query
    await query.answer()
    breed = query.data

    cats = requests.get(f'https://api.thecatapi.com/v1/images/search?api_key{CAT_API_KEY}&breed_ids = {breed}').json()
    url = cats[0]['url']
    await context.bot.send_photo(chat_id = update.effective_chat.id, photo = url)

async def saveUser(update, context):
    user = update.message.from_user

    user_info = {
        'username': user.username,
        'name': user.first_name,
        'chat_id': update.effective_chat.id,
        'breed': 'all',
        'no_of_photos': '1',
        'is_gif': False
    }

    #user_db is alias
    with open('users.json', 'r') as user_db:
        users = json.load(user_db)

    users[user.id] = user_info

    with open('users.json', 'w') as user_db:
        json.dump(users, user_db)
    
    reply_keyboard = [
        ["All of them!", "Bengal", "Persian"],
        ["Munchkin", "Ragamuffin", "Burmese"],
        ["Russian Blue", "Maine Coon", "Abyssinian"]
    ]

    await update.message.reply_text(
        "Ok, what's your favourite breed?",
        reply_markup = ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard = True, input_field_placeholder = "Favourite Breed?"
        )
    )

    return BREED

async def saveBreed(update, context):
    user = update.message.from_user

    breed = update.message.text
    breed_id = ''

    if (breed == "All of them!"):
        breed_id = "all"
    elif (breed == "Bengal"):
        breed_id = "beng"
    elif (breed == "Persian"):
        breed_id = "pers"
    elif (breed == "Munchkin"):
        breed_id = "munc"
    elif (breed == "Ragamuffin"):
        breed_id = "raga"
    elif (breed == "Maine Coon"):
        breed_id = "mcoo"
    elif (breed == "Abyssinian"):
        breed_id = "abys"

    with open('users.json', 'r') as user_db:
        users = json.load(user_db)

    users[str(user.id)]['breed'] = breed_id

    with open('users.json', 'w') as  user_db:
        json.dump(users, user_db)

    await update.message.reply_text(
        "Good choice! how many photos would you like to get at once?",
        reply_markup = ReplyKeyboardRemove()
    )

    return NO_OF_PHOTOS

async def saveNoOfPhotos(update, context):
    user = update.message.from_user

    no_of_photos = update.message.text

    with open('users.json', 'r') as user_db:
        users = json.load(user_db)

    users[str(user.id)]['no_of_photos'] = no_of_photos

    with open('users.json', 'w') as user_db:
        json.dump(users, user_db)

    reply_keyboard = [["GIF", "JPG"]]

    await update.message.reply_text(
        "Got it! Now do you want gifs or jpgs?",
        reply_markup = ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard = True, input_field_placeholder = "Gif or Jpg?"
        )
    )
    
    return GIF

async def saveGif(update, context):
    user = update.message.from_user

    is_gif = update.message.text == "GIF"

    with open('users.json', 'r') as user_db:
        users = json.load(user_db)

    users[str(user.id)]['is_gif'] = is_gif

    with open('users.json', 'w') as user_db:
        json.dump(users, user_db)

    await update.message.reply_text(
        "Thanks! Your settings have been saved.",
        reply_markup = ReplyKeyboardRemove()
    )

    return ConversationHandler.END

async def cancel(update, context):
    await update.message.reply_text(
        "Ok, we'll stop saving your settings", reply_markup = ReplyKeyboardRemove()
    )
    return ConversationHandler.END

bot = ApplicationBuilder().token(BOT_TOKEN).build()

bot.add_handler(CommandHandler("hello", hello))
bot.add_handler(CommandHandler("cat", getCat))
bot.add_handler(CommandHandler("breed", chooseBreed))
bot.add_handler(CallbackQueryHandler(getCatWithBreed))

settings_handler = ConversationHandler(
    entry_points = [CommandHandler("settings", saveUser)],
    states = {
        BREED: [MessageHandler(filters.Regex("^(All of them!|Bengal|Persian|Munchkin|Ragamuffin|Burmese|Russian Blue|Maine Coon|Abyssinian)$"), saveBreed)],
        NO_OF_PHOTOS: [MessageHandler(filters.TEXT & filters.Regex("^\d$"), saveNoOfPhotos)],
        GIF: [MessageHandler(filters.TEXT & filters.Regex("^(GIF|JPG)$"), saveGif)],
    },
    fallbacks = [CommandHandler("cancel", cancel)],
)

bot.add_handler(settings_handler)

bot.run_polling()