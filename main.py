from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Connect to MongoDB
from pymongo import MongoClient

# Set up MongoDB client
MONGO_URL = os.environ.get("DB_URL")
mongo_client = MongoClient(MONGO_URL)
db = mongo_client["apmdada"]
started_users_collection = db["started_users"]

# Set up Pyrogram client
api_id = os.environ.get("API_ID")
api_hash = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=BOT_TOKEN)


# Function to handle /start command
@app.on_message(filters.command("start") & filters.group)
async def start_command(client, message):
    user_id = message.from_user.id
    started_users.add(user_id)
    started_users_collection.update_one({"_id": user_id}, {"$set": {"started": True}}, upsert=True)
    await message.reply_text("Thanks for starting the bot. You will be updated of your requests here.")


# Function to handle #request messages
@app.on_message(filters.regex("^#request"))
async def request_message(client, message):
    user_id = message.from_user.id
    if not started_users_collection.find_one({"_id": user_id}):
        await message.reply_text(
            "Please start the bot first.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Start Bot", url=f"t.me/{BOT_NAME}")]
            ])
        )
    else:
        anime_name = message.text.split("#request ")[-1]
        requests[user_id] = {"name": anime_name, "message_id": message.message_id}
        log_message = await client.send_message(
            chat_id=LOG,
            text=f"New request: {anime_name}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Approve", callback_data=f"approve_{user_id}"),
                 InlineKeyboardButton("Decline", callback_data=f"decline_{user_id}"),
                 InlineKeyboardButton("Unavailable", callback_data=f"unavailable_{user_id}")],
                [InlineKeyboardButton("Request Message", url=f"{GRP_LINK}/{message.message_id}")]
            ])
        )
        await message.reply_text("Okay, Your request has been sent to the admins to review. Please wait some days for it to be uploaded.")


# Function to handle button presses
@app.on_callback_query()
async def button(client, callback_query):
    query = callback_query
    user_id = query.data.split("_")[-1]
    log_channel_id = LOG  # Log channel ID

    if query.data.startswith("approve"):
        anime_name = requests.get(user_id, {}).get("name", "Unknown")
        old_message_text = query.message.text
        new_text = f"*Approved The*:\n{old_message_text}"
        await client.edit_message_text(chat_id=log_channel_id, message_id=query.message.message_id,
                                       text=new_text, parse_mode='Markdown')
        await client.send_message(chat_id=user_id, text="Your Request has been Approved.")
    elif query.data.startswith("decline"):
        anime_name = requests.get(user_id, {}).get("name", "Unknown")
        old_message_text = query.message.text
        new_text = f"*Declined The*:\n{old_message_text}:"
        await client.edit_message_text(chat_id=log_channel_id, message_id=query.message.message_id,
                                       text=new_text, parse_mode='Markdown')
        await client.send_message(chat_id=user_id, text="Unfortunately, your Request has been declined.")
    elif query.data.startswith("unavailable"):
        anime_name = requests.get(user_id, {}).get("name", "Unknown")
        old_message_text = query.message.text
        new_text = f"*Unavailable The*:\n{old_message_text}"
        await client.edit_message_text(chat_id=log_channel_id, message_id=query.message.message_id,
                                       text=new_text, parse_mode='Markdown')
        await client.send_message(chat_id=user_id, text="The requested Request is unavailable.")


# Function to handle errors
@app.on_error()
async def error(client, update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)


# Run the client
app.run()
