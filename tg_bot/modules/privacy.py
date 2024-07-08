import re
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler
rom tg_bot.modules.language import gs

privacy_responses = {
    "info_collect": "We collect the following user data:\n- First Name\n- Last Name\n- Username\n- User ID\n- Messages sent by users\n- User bio if it is visible to the public\nThese are public Telegram details that everyone can see.",
    "why_collect": "The collected data is used solely for improving your experience with the bot and for processing the bot stats and to avoid spammers.",
    "what_we_do": "We use the data to personalize your experience and provide better services.",
    "what_we_do_not_do": "We do not share your data with any third parties.",
    "right_to_process": "You have the right to access, correct, or delete your data. [Contact us](t.me/drxew) for any privacy-related inquiries."
}

def privacy_command(update: Update, context: CallbackContext) -> None:
    privacy_button = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Privacy Policy", callback_data="privacy_policy")]]
    )
    update.message.reply_text("Select one of the below options for more information about how the bot handles your privacy.", reply_markup=privacy_button)

def handle_callback_query(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    data = query.data
    if data == "privacy_policy":
        buttons = [
            [InlineKeyboardButton("What Information We Collect", callback_data="info_collect")],
            [InlineKeyboardButton("Why We Collect", callback_data="why_collect")],
            [InlineKeyboardButton("What We Do", callback_data="what_we_do")],
            [InlineKeyboardButton("What We Do Not Do", callback_data="what_we_do_not_do")],
            [InlineKeyboardButton("Right to Process", callback_data="right_to_process")]
        ]
        query.edit_message_text("Our contact details\nName: MissIvoryBot\nTelegram: https://t.me/CodecArchive\nThe bot has been made to protect and preserve privacy as best as possible.\nOur privacy policy may change from time to time. If we make any material changes to our policies, we will place a prominent notice on https://t.me/CodecBots.", reply_markup=InlineKeyboardMarkup(buttons))
    elif data in privacy_responses:
        back_button = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Back", callback_data="privacy_policy")]]
        )
        query.edit_message_text(privacy_responses[data], reply_markup=back_button)

__mod_name__ = "Federations"

def get_help(chat):
    return gs(chat, "admin_help")

def add_privacy_handlers(dispatcher) -> None:
    dispatcher.add_handler(CommandHandler("privacy", privacy_command))
    dispatcher.add_handler(CallbackQueryHandler(handle_callback_query))


