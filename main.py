import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Dictionary to store user requests
requests = {}

# Set to store users who have started the bot
started_users = set()
BOT_NAME = os.environ.get("BOT_NAME")
GRP_LINK = os.environ.get("GRP_LINK")
log = os.environ.get("LOG_CHANNEL")
BOT_TOKEN = os.environ.get("BOT_TOKEN")


# Function to handle /start command
def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    started_users.add(user_id)
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Thanks for starting the bot. You will be updated of your requests here.")


# Function to handle #request command
def request(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id not in started_users:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Please start the bot first.",
                                 reply_markup=InlineKeyboardMarkup([
                                     [InlineKeyboardButton("Start Bot", url=f"t.me/{BOT_NAME}")]
                                 ]))
    else:
        anime_name = update.message.text.split("#request ")[-1]
        requests[user_id] = {"name": anime_name, "message_id": update.message.message_id}
        log_message = context.bot.send_message(chat_id=log,
                                               text=f"New request: {anime_name}",
                                               reply_markup=InlineKeyboardMarkup([
                                                   [InlineKeyboardButton("Approve", callback_data=f"approve_{user_id}"),
                                                    InlineKeyboardButton("Decline", callback_data=f"decline_{user_id}"),
                                                    InlineKeyboardButton("Unavailable", callback_data=f"unavailable_{user_id}")],
                                                   [InlineKeyboardButton("Request Message", url=f"{GRP_LINK}/{update.message.message_id}")]
                                               ]))
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Okay, Your request has been sent to the admins to review. Please wait some days for it to be uploaded.")

def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.data.split("_")[-1]
    log_channel_id = log  # Log channel ID

    if query.data.startswith("approve"):
        anime_name = requests.get(user_id, {}).get("name", "Unknown")
        old_message_text = query.message.text
        new_text = f"*Approved*:\n{old_message_text}"
        context.bot.edit_message_text(chat_id=log_channel_id, message_id=query.message.message_id,
                                      text=new_text, parse_mode='Markdown')
        context.bot.send_message(chat_id=user_id, text="Your anime has been Approved.")
    elif query.data.startswith("decline"):
        anime_name = requests.get(user_id, {}).get("name", "Unknown")
        new_text = f"*Declined*:"
        context.bot.edit_message_text(chat_id=log_channel_id, message_id=query.message.message_id,
                                      text=new_text, parse_mode='Markdown')
        context.bot.send_message(chat_id=user_id, text="Unfortunately, your anime has been declined.")
    elif query.data.startswith("unavailable"):
        anime_name = requests.get(user_id, {}).get("name", "Unknown")
        new_text = f"*Unavailable*"
        context.bot.edit_message_text(chat_id=log_channel_id, message_id=query.message.message_id,
                                      text=new_text, parse_mode='Markdown')
        context.bot.send_message(chat_id=user_id, text="The requested anime is unavailable.")

# Function to handle errors
def error(update: Update, context: CallbackContext) -> None:
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    token = os.getenv("BOT_TOKEN")
    updater = Updater(token, use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.regex('^#request'), request))
    dp.add_handler(CallbackQueryHandler(button))

    dp.add_error_handler(error)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
