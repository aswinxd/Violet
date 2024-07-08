import importlib
import re
import asyncio
from sys import argv
from typing import Optional

from telegram import Update, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, Filters, DispatcherHandlerStop
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from telegram.utils.helpers import escape_markdown

from tg_bot import (
    KInit,
    dispatcher,
    updater,
    TOKEN,
    WEBHOOK,
    OWNER_ID,
    CERT_PATH,
    PORT,
    URL,
    log,
    KigyoINIT
)
from tg_bot.modules import ALL_MODULES
from tg_bot.modules.helper_funcs.chat_status import is_user_admin
from tg_bot.modules.helper_funcs.decorators import ivory, ivorycallback, kigmsg, rate_limit
from tg_bot.modules.helper_funcs.misc import paginate_modules
from tg_bot.modules.language import gs

IMPORTED = {}
MIGRATEABLE = []
HELPABLE = {}
STATS = []
USER_INFO = []
DATA_IMPORT = []
DATA_EXPORT = []

CHAT_SETTINGS = {}
USER_SETTINGS = {}
privacy_responses = {
    "info_collect": "We collect the following user data:\n- First Name\n- Last Name\n- Username\n- User ID\n- Messages sent by users\n- User bio if it is visible to the public\n These are public Telegram details that everyone can see.",
    "why_collect": "The collected data is used solely for improving your experience with the bot and for processing the bot stats and to avoid spammers.",
    "what_we_do": "We use the data to personalize your experience and provide better services.",
    "what_we_do_not_do": "We do not share your data with any third parties.",
    "right_to_process": "You have the right to access, correct, or delete your data. [Contact us](t.me/drxew) for any privacy-related inquiries."
}

# Privacy command
@ivory(command='privacy')
async def privacy_command(update: Update, context: CallbackContext):
    privacy_button = [
        [InlineKeyboardButton("Privacy Policy", callback_data="privacy_policy")]
    ]
    await update.message.reply_text("Select one of the options below for more information about how the bot handles your privacy.", 
                                    reply_markup=InlineKeyboardMarkup(privacy_button))

@ivorycallback(pattern=r'privacy_policy')
async def handle_callback_query(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    if data == "privacy_policy":
        buttons = [
            [InlineKeyboardButton("What Information We Collect", callback_data="info_collect")],
            [InlineKeyboardButton("Why We Collect", callback_data="why_collect")],
            [InlineKeyboardButton("What We Do", callback_data="what_we_do")],
            [InlineKeyboardButton("What We Do Not Do", callback_data="what_we_do_not_do")],
            [InlineKeyboardButton("Right to Process", callback_data="right_to_process")]
        ]
        await query.message.edit_text("Our contact details\nName: MissIvoryBot \nTelegram: https://t.me/CodecArchive\nThe bot has been made to protect and preserve privacy as best as possible.\nOur privacy policy may change from time to time. If we make any material changes to our policies, we will place a prominent notice on https://t.me/CodecBots.", 
                                      reply_markup=InlineKeyboardMarkup(buttons))
    elif data in privacy_responses:
        back_button = [
            [InlineKeyboardButton("Back", callback_data="privacy_policy")]
        ]
        await query.message.edit_text(privacy_responses[data], reply_markup=InlineKeyboardMarkup(back_button))

async def worker(name, client, queue, user_cache, cache_duration):
    while True:
        event_batch = []
        for _ in range(100):  
            event = await queue.get()
            event_batch.append(event)
            queue.task_done()
            if queue.empty():
                break
        await asyncio.gather(*[check_user_bio(client, event, user_cache, cache_duration) for event in event_batch])

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("tg_bot.modules." + module_name)
    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__

    if imported_module.__mod_name__.lower() not in IMPORTED:
        IMPORTED[imported_module.__mod_name__.lower()] = imported_module
    else:
        raise Exception("Can't have two modules with the same name! Please change one")

    if hasattr(imported_module, "get_help") and imported_module.get_help:
        HELPABLE[imported_module.__mod_name__.lower()] = imported_module

    # Chats to migrate on chat_migrated events
    if hasattr(imported_module, "__migrate__"):
        MIGRATEABLE.append(imported_module)

    if hasattr(imported_module, "__stats__"):
        STATS.append(imported_module)

    if hasattr(imported_module, "__user_info__"):
        USER_INFO.append(imported_module)

    if hasattr(imported_module, "__import_data__"):
        DATA_IMPORT.append(imported_module)

    if hasattr(imported_module, "__export_data__"):
        DATA_EXPORT.append(imported_module)

    if hasattr(imported_module, "__chat_settings__"):
        CHAT_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__user_settings__"):
        USER_SETTINGS[imported_module.__mod_name__.lower()] = imported_module


# do not async
def send_help(chat_id, text, keyboard=None):
    """#TODO

    Params:
        chat_id  -
        text     -
        keyboard -
    """

    if not keyboard:
        kb = paginate_modules(0, HELPABLE, "help")
        # kb.append([InlineKeyboardButton(text='Support', url='https://t.me/YorkTownEagleUnion'),
        #           InlineKeyboardButton(text='Back', callback_data='start_back'),
        #           InlineKeyboardButton(text="Try inline", switch_inline_query_current_chat="")])
        keyboard = InlineKeyboardMarkup(kb)
    dispatcher.bot.send_message(
        chat_id=chat_id, text=text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard
    )


@ivory(command='text')
def test(update: Update, _: CallbackContext):
    """#TODO

    Params:
        update: Update           -
        context: CallbackContext -
    """
    # pprint(ast.literal_eval(str(update)))
    # update.effective_message.reply_text("Hola tester! _I_ *have* `markdown`", parse_mode=ParseMode.MARKDOWN)
    update.effective_message.reply_text("This person edited a message")
    print(update.effective_message)


@ivorycallback(pattern=r'start_back')
@ivory(command='start', pass_args=True)
@rate_limit(40, 60)
def start(update: Update, context: CallbackContext):  # sourcery no-metrics
    """#TODO

    Params:
        update: Update           -
        context: CallbackContext -
    """
    chat = update.effective_chat
    args = context.args

    if hasattr(update, 'callback_query'):
        query = update.callback_query
        if hasattr(query, 'id'):
            first_name = update.effective_user.first_name
            update.effective_message.edit_text(
                text=gs(chat.id, "pm_start_text").format(
                    escape_markdown(first_name),
                    escape_markdown(context.bot.first_name),
                    OWNER_ID,
                ),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            text="Add Me To Your chat!",
                            url=f"https://t.me/MissIvoryBot?startgroup=true",
                        ),
                    ],
                ])
            )
            context.bot.answer_callback_query(query.id)
            return

    if update.effective_chat.type == "private":
        if args and len(args) >= 1:
            if args[0].lower() == "help":
                send_help(update.effective_chat.id, (gs(chat.id, "pm_help_text")))
            elif args[0].lower().startswith("ghelp_"):
                query = update.callback_query
                mod = args[0].lower().split("_", 1)[1]
                if not HELPABLE.get(mod, False):
                    return
                help_list = HELPABLE[mod].get_help(chat.id)
                help_text = []
                help_buttons = []
                if isinstance(help_list, list):
                    help_text = help_list[0]
                    help_buttons = help_list[1:]
                elif isinstance(help_list, str):
                    help_text = help_list
                text = " *{}*\n".format(HELPABLE[mod].__mod_name__) + help_text
                help_buttons.append(
                    [InlineKeyboardButton(text="Back", callback_data="help_back"),
                     InlineKeyboardButton(text='Support', url='https://t.me/codecarchive')]
                )
                send_help(
                    chat.id,
                    text,
                    InlineKeyboardMarkup(help_buttons),
                )

                if hasattr(query, "id"):
                    context.bot.answer_callback_query(query.id)
            elif args[0].lower() == "markdownhelp":
                IMPORTED["extras"].markdown_help_sender(update)
            elif args[0].lower() == "nations":
                IMPORTED["nations"].send_nations(update)
            elif args[0].lower().startswith("stngs_"):
                match = re.match("stngs_(.*)", args[0].lower())
                chat = update.effective_chat
                user = update.effective_user
                if match:
                    curr_page = match.groups()[0]
                    send_settings(chat.id, user.id, curr_page, context.bot)
            elif args[0].isdigit() and update.effective_user.id == OWNER_ID:
                chat = update.effective_chat
                user_id = args[0]
                try:
                    user_id = int(user_id)
                except ValueError:
                    pass
                user_chat = context.bot.get_chat(user_id)
                name = "{}{}".format(
                    user_chat.first_name,
                    " " + user_chat.last_name if user_chat.last_name else "",
                )
                send_help(
                    chat.id,
                    gs(chat.id, "pm_help_text"),
                    InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help")),
                )

            else:
                send_help(
                    update.effective_chat.id,
                    gs(chat.id, "pm_help_text"),
                    InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help")),
                )

        else:
            send_help(
                update.effective_chat.id,
                gs(chat.id, "pm_help_text"),
                InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help")),
            )

    else:
        update.message.reply_text(
            gs(chat.id, "pm_group_start_text"),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="Help",
                    url="https://t.me/{}?start=help".format(context.bot.username),
                )],
            ]),
        )


@ivorycallback(pattern=r'help_back')
def help_button(update: Update, context: CallbackContext):
    """#TODO

    Params:
        update: Update           -
        context: CallbackContext -
    """
    query = update.callback_query
    bot = context.bot
    chat = update.effective_chat

    mod_match = re.match(r"help_module\((.+?)\)", query.data)
    prev_match = re.match(r"help_prev\((.+?)\)", query.data)
    next_match = re.match(r"help_next\((.+?)\)", query.data)
    back_match = re.match(r"help_back", query.data)

    top_text = gs(chat.id, "pm_help_text")

    if mod_match:
        module = mod_match.groups()[0]
        text = (
            f" *{HELPABLE[module].__mod_name__}*\n"
            + HELPABLE[module].get_help(chat.id)
        )
        query.message.edit_text(
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="help_back")]]
            ),
        )

    elif prev_match:
        curr_page = int(prev_match.groups()[0])
        query.message.edit_text(
            top_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                paginate_modules(curr_page - 1, HELPABLE, "help")
            ),
        )

    elif next_match:
        curr_page = int(next_match.groups()[0])
        query.message.edit_text(
            top_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                paginate_modules(curr_page + 1, HELPABLE, "help")
            ),
        )

    elif back_match:
        query.message.edit_text(
            top_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help")),
        )

    # ensure no spinny white circle
    bot.answer_callback_query(query.id)

def main() -> None:
    """#TODO
    """
    # Updater
    updater.start_polling(allowed_updates=Update.ALL_TYPES)
    log.info("Using long polling.")

    # If we have a webserver, we should use webhook!
    if WEBHOOK:
        updater.start_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            key=CERT_PATH,
            webhook_url=URL + TOKEN,
        )

    # Idle
    updater.idle()


if __name__ == '__main__':
    main()
