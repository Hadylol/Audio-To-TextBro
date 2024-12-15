import os
from dotenv import load_dotenv
import logging

from telegram import ForceReply, InlineKeyboardButton, Update,InlineKeyboardMarkup
from telegram.ext import Application, CallbackContext, CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters
load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

WAITING_FOR_AUDIO = 1
async def  start(update:Update, context: ContextTypes.DEFAULT_TYPE)-> None:
    user = update.effective_user
    if update.message and user :
        await update.message.reply_text(f"Hey {user.first_name} Welcome to Audio to Text Bot /help for more commands")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    if update.message:
            await update.message.reply_text("1- /AudioToText For Audio To Text!")

async def audio_to_text(update:Update, context: ContextTypes.DEFAULT_TYPE)->int:
    if update.message:
        await update.message.reply_text("PLease send the Audio I'll convert it to text Buddy")
    return WAITING_FOR_AUDIO

async def audio_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get the Audio file from  the user message."""
    if update.message:
        if  update.message.audio :
            audio = update.message.audio
            file_id=audio.file_id
            file =await context.bot.get_file(file_id)
            file_path = os.path.join("downloads",f"{file_id}.mp3")
            await file.download_to_drive(file_path)
            await update.message.reply_text(f"audio file  received and saved as {file_path}")
        else:
            await update.message.reply_text("No audio file received please try again")

async def cancel(update:Update,context: ContextTypes.DEFAULT_TYPE)->int:
    if update.message:
        await update.message.reply_text("Audio text Conversion has been canceled. sad..")
    return ConversationHandler.END

def main() -> None:
    """Start the bot."""
    BOT_KEY = os.getenv("BOT_KEY")
    if BOT_KEY is None:
        raise ValueError("BOT_KEY env var is not set or unreachable !")
    bot = Application.builder().token(BOT_KEY).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("AudioToText",audio_handler)],
        states={
            WAITING_FOR_AUDIO:[MessageHandler(filters.AUDIO,audio_handler)]
        },
        fallbacks=[CommandHandler('cancel',cancel)],
    )
    # on different commands - answer in Telegram
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("help", help_command))
    bot.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    bot.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
