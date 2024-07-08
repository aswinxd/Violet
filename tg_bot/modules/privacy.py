import re
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler
from tg_bot.modules.language import gs
from tg_bot.modules.helper_funcs.decorators import ivory, kigmsg, ivorycallback, rate_limit

# Dictionary for privacy responses
privacy_responses = {
    "info_collect": "We currently collect and process the following information:\n• Telegram UserID, firstname, lastname, username (Note: These are your public telegram details. We do not know your real details.)\n• Chat memberships (The list of all chats you have been seen interacting in)\n• Settings or configurations as set through any commands (For example, welcome settings, notes, filters, etc)",
    "why_collect": "How we get the personal information and why we have it\nMost of the personal information we process is provided to us directly by you for one of the following reasons:\n• You've messaged the bot directly. This can be to read the complete a CAPTCHA, read the documentation, etc.\n• You've opted to save your messages through the bot.\nWe also receive personal information indirectly, from the following sources in the following scenarios\n:• You're part of a group, or channel, which uses this bot.",
    "what_we_do": "What we do with the personal information\nWe use the information that you have given us in order to support various bot features. This can include:\n• User ID/username pairing, which allows the bot to resolve usernames to valid user ids.\n• Chat memberships, which allows for federations to know where to ban from, and determine which bans are of importance to you.\n• Storing certain messages that have been explicitly saved. (eg through notes, filters, welcomes, etc)",
    "what_we_do_not_do": "What we DO NOT do with the personal information\nWe DO NOT:\n• store any messages, unless explicitly saved (eg through notes, filters, welcomes etc).\n• use technologies like beacons or unique device identifiers to identify you or your device.\n• knowingly contact or collect personal information from children under 13. If you believe we have inadvertently collected such information, please contact us so we can promptly obtain parental consent or remove the information.\n• share any sensitive information with any other organisations or individuals.",
    "right_to_process": "You have the right to access, correct, or delete your data. [Contact us](t.me/drxew) for any privacy-related inquiries."
}

# Command handler for the /privacy command
@ivory(command='privacy')
def privacy_command(update: Update, context: CallbackContext) -> None:
    privacy_button = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Privacy Policy", callback_data="privacy_policy")]]
    )
    update.message.reply_text("Select one of the below options for more information about how the bot handles your privacy.", reply_markup=privacy_button)

# Callback query handler for privacy-related queries
@ivorycallback(pattern=r"privacy_policy|info_collect|why_collect|what_we_do|what_we_do_not_do|right_to_process")
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
        query.edit_message_text(
            "Our contact details\nName: MissIvoryBot\nTelegram: @CodecArchive\nThe bot has been made to protect and preserve privacy as best as possible.\nOur privacy policy may change from time to time. If we make any material changes to our policies, we will place a prominent notice on @CodecBots.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    elif data in privacy_responses:
        back_button = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Back", callback_data="privacy_policy")]]
        )
        query.edit_message_text(privacy_responses[data], reply_markup=back_button)

__mod_name__ = "Privacy"

def get_help(chat):
    return gs(chat, "privacy_help")
