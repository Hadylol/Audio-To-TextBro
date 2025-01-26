from ast import keyword
from contextvars import Context
from genericpath import exists
import os
from pickle import STRING
from posix import times
from dotenv import load_dotenv
import logging
import warnings
import asyncio
from telegram._games.callbackgame import CallbackGame
import whisper
from telegram import CallbackQuery, File, ForceReply, InlineKeyboardButton, Message, Update,InlineKeyboardMarkup
from telegram.ext import Application, CallbackContext, CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters
from warnings import filterwarnings
from telegram.warnings import PTBUserWarning
import speech_recognition as sr
from pydub import AudioSegment
load_dotenv()

filterwarnings(action="ignore",message=r".*CallbackQueryHandler",category=PTBUserWarning)

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

DOWNLOAD_DIR = "DownloadsAudio"
WAITING_FOR_AUDIO = 3
WAITING_FOR_LANG=1
WAITING_FOR_METHOD =2
CONFIRM_METHOD=5
TRANSFER_TO_TEXT = 4
TO_TEXT_METHOD ="a_method"
CHOSEN_LANG ="a_lang"
async def  start(update:Update, context: ContextTypes.DEFAULT_TYPE)-> None:
    user = update.effective_user
    if update.message and user :
        await update.message.reply_text(f"Hey {user.first_name} Welcome to Audio to Text Bot !  \n /help for more Commands!")


async def speech_reco_sphinx(file_path ):
    recognizer = sr.Recognizer()

    with sr.AudioFile("Converted.wav") as source :
        audio_data = recognizer.record(source)
        try:
            text =recognizer.recognize_sphinx(audio_data)
            print(text)
            return text
        except sr.UnknownValueError:
            print("couldnt understand the audio dude")
        except sr.RequestError:
            print("Error happened with sphinx recognizer ")

async def speech_whisper(file_path):
    model = whisper.load_model("base")
    try :
        loop = asyncio.get_event_loop()
        text = await loop.run_in_executor(None,model.transcribe,file_path)
        print(text)
        return text["text"]
    except Exception as e:
        return f"Error happen With openAI whisper {e}"

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    if update.message:
            await update.message.reply_text(
                "1- /AudioToText -Convert  Audio To Text! \n "
                "2. /cancel -Cancel the current operation."
            )

async def convert_audio_to_wav(input_file_path,output_file="Converted.wav")->str:
    try:
        audio = AudioSegment.from_file(input_file_path)
        audio.export(output_file,format="wav")
        return output_file
    except Exception as e:
        print(f"Error Converting file {e}")
        return ""
    finally:
        if input_file_path and os.path.exists(input_file_path):
            os.remove(input_file_path)
async def choose_lang(update:Update,context:ContextTypes.DEFAULT_TYPE):
    keyboard= [
        [
        InlineKeyboardButton("English",callback_data="english"),
        InlineKeyboardButton("Arabic",callback_data="arabic"),
        InlineKeyboardButton("French(tklh)",callback_data="french"),
        InlineKeyboardButton("Spanish",callback_data="spanish"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text("Choose Your Langauge :",reply_markup=reply_markup)
        return WAITING_FOR_LANG
    return ConversationHandler.END

async def to_text_method(update:Update, context: ContextTypes.DEFAULT_TYPE)->int:
# User choosing the Transcription AKA the method to convert the Audio to Text
    keyboard=[
        [
        InlineKeyboardButton("SpeechRecognition",callback_data="speech_recognition"),
        InlineKeyboardButton("Whisper",callback_data="whisper"),
        InlineKeyboardButton("Vosk",callback_data="vosk"),
        InlineKeyboardButton("Wav2Vec2.0",callback_data="Wav2Vec2.0")
        ],
        [InlineKeyboardButton("Details About each one.",callback_data="details")]
    ]
    reply_markup =InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text("Chosse Your preferable Method : ",reply_markup=reply_markup)
        return CONFIRM_METHOD
    return ConversationHandler.END
async def chosen_lang(update:Update,context:ContextTypes.DEFAULT_TYPE):
    global CHOSEN_LANG
    query =update.callback_query
    if query:
        await query.answer()
        if query.data:
            CHOSEN_LANG= query.data
            await query.edit_message_text(text=f"Your Audio will be in : {query.data} \n /yes to confirm , /cancel to cancel the operation")
            return WAITING_FOR_METHOD
        else:
            await query.edit_message_text(text="Something Went worng \n /cancel and Retry !")
            return WAITING_FOR_LANG

async def chosen_method(update:Update , context: ContextTypes.DEFAULT_TYPE):
#Saving User chosen method
    global TO_TEXT_METHOD
    query= update.callback_query
    if query :
        await query.answer()
        if query.data:
            TO_TEXT_METHOD=query.data
            await query.edit_message_text(text=f"Turning your Audio to Text Using : {query.data} \n /yes to confirm , /cancel to cancel the operation")
        else:
            await query.edit_message_text(text="Something Went wrong while Chossin your Method.\n /cancel and Retry !")
            return WAITING_FOR_METHOD
        return WAITING_FOR_AUDIO

async def audio_to_text(update:Update, context: ContextTypes.DEFAULT_TYPE)->int:
    if update.message:
        await update.message.reply_text("Provide your Audio file in these formats: Mp3, AAC, Ogg, WAV\n Send /cancel to Cancel the operation")
    return WAITING_FOR_AUDIO

async def audio_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get the Audio file from  the user message."""
    if update.message :
        if update.message.audio :
            try:
                user_audio = update.message.audio
                file_id = user_audio.file_id
                file = await context.bot.get_file(file_id)
                os.makedirs(DOWNLOAD_DIR,exist_ok=True)
                file_path= os.path.join(DOWNLOAD_DIR,f"{user_audio.file_id}.wav")
                print("This is the file path ",file_path)
                await file.download_to_drive(file_path)
                converted_audio= await convert_audio_to_wav(file_path)
                print(TO_TEXT_METHOD)
                text = " "
                if TO_TEXT_METHOD =="speech_recognition":
                    text = await speech_reco_sphinx(converted_audio)
                if TO_TEXT_METHOD =="whisper":
                    text = await speech_whisper(converted_audio)
                if text :
                    await update.message.reply_text(f"The Transcript :\n {text}")
                else:
                    await update.message.reply_text("Failed to process the audio file")
            except Exception as e :
                logger.error(f"Error Downloading audio file :{e}")
                await update.message.reply_text("An error occurred while processing the audio file Please try agian !")
            return ConversationHandler.END
        else:
            await update.message.reply_text("No audio file received please try again \n /cancel if you wanna cancel the operation !")
            return WAITING_FOR_AUDIO
    print("FINSHED")
    return ConversationHandler.END


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
    #Conversation Handler with states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("AudioToText",choose_lang)],
        states={
            WAITING_FOR_LANG:[
             CallbackQueryHandler(chosen_lang)
            ],
            WAITING_FOR_METHOD:[
                MessageHandler(filters.ALL,to_text_method)
            ],
            CONFIRM_METHOD:[
             CallbackQueryHandler(chosen_method)
            ],
            WAITING_FOR_AUDIO:[
                MessageHandler(filters.AUDIO,audio_handler),
                CommandHandler("yes",audio_to_text),
                ],
                TRANSFER_TO_TEXT:[

                ]

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
