import contextlib
import html
import random
import re
import time
from functools import partial
from io import BytesIO
from tg_bot.modules.helper_funcs.decorators import rate_limit
import tg_bot.modules.sql.welcome_sql as sql
from tg_bot import (
    DEV_USERS,
    SYS_ADMIN,
    log,
    OWNER_ID,
    SUDO_USERS,
    SUPPORT_USERS,
    SARDEGNA_USERS,
    WHITELIST_USERS,
    # sw,
    dispatcher,
)
from tg_bot.modules.helper_funcs.chat_status import (
    is_user_ban_protected,
    user_admin as u_admin,
)
from tg_bot.modules.helper_funcs.misc import build_keyboard, revert_buttons
from tg_bot.modules.helper_funcs.msg_types import get_welcome_type
from tg_bot.modules.helper_funcs.string_handling import (
    escape_invalid_curly_brackets,
    markdown_parser,
)
from tg_bot.modules.log_channel import loggable
from tg_bot.modules.sql.antispam_sql import is_user_gbanned
from telegram import (
    ChatPermissions,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ParseMode,
    Update,
    User,
)
from telegram.error import BadRequest, TelegramError
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    ChatMemberHandler,
)
from telegram.utils.helpers import escape_markdown, mention_html, mention_markdown
import tg_bot.modules.sql.log_channel_sql as logsql
from ..modules.helper_funcs.anonymous import user_admin, AdminPerms
from .sibylsystem import sibylClient, does_chat_sibylban
from SibylSystem import GeneralException

VALID_WELCOME_FORMATTERS = [
    "first",
    "last",
    "fullname",
    "username",
    "id",
    "count",
    "chatname",
    "mention",
]

ENUM_FUNC_MAP = {
    sql.Types.TEXT.value: dispatcher.bot.send_message,
    sql.Types.BUTTON_TEXT.value: dispatcher.bot.send_message,
    sql.Types.STICKER.value: dispatcher.bot.send_sticker,
    sql.Types.DOCUMENT.value: dispatcher.bot.send_document,
    sql.Types.PHOTO.value: dispatcher.bot.send_photo,
    sql.Types.AUDIO.value: dispatcher.bot.send_audio,
    sql.Types.VOICE.value: dispatcher.bot.send_voice,
    sql.Types.VIDEO.value: dispatcher.bot.send_video,
}

VERIFIED_USER_WAITLIST = {}
CAPTCHA_ANS_DICT = {}

from multicolorcaptcha import CaptchaGenerator

WHITELISTED = (
    [OWNER_ID, SYS_ADMIN] + DEV_USERS + SUDO_USERS + SUPPORT_USERS + WHITELIST_USERS
)
WHITELISTED = (
    [OWNER_ID, SYS_ADMIN] + DEV_USERS + SUDO_USERS + SUPPORT_USERS + WHITELIST_USERS
)


# do not async
def send(update, message, keyboard, backup_message):
    chat = update.effective_chat
    try:
        msg = dispatcher.bot.send_message(
            chat.id,
            message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard,
            allow_sending_without_reply=True,
        )
    except BadRequest as excp:
        if excp.message == "Button_url_invalid":
            msg = dispatcher.bot.send_message(
                chat.id,
                markdown_parser(
                    (
                        backup_message
                        + "\nNote: the current message has an invalid url in one of its buttons. Please update."
                    )
                ),
                parse_mode=ParseMode.MARKDOWN,
            )

        elif excp.message == "Have no rights to send a message":
            return
        elif excp.message == "Reply message not found":
            msg = dispatcher.bot.send_message(
                chat.id,
                message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard,
                quote=False,
            )

        elif excp.message == "Unsupported url protocol":
            msg = dispatcher.bot.send_message(
                chat.id,
                markdown_parser(
                    (
                        backup_message
                        + "\nNote: the current message has buttons which use url protocols that are unsupported by "
                        "telegram. Please update. "
                    )
                ),
                parse_mode=ParseMode.MARKDOWN,
            )

        elif excp.message == "Wrong url host":
            msg = dispatcher.bot.send_message(
                chat.id,
                markdown_parser(
                    (
                        backup_message
                        + "\nNote: the current message has some bad urls. Please update."
                    )
                ),
                parse_mode=ParseMode.MARKDOWN,
            )

            log.warning(message)
            log.warning(keyboard)
            log.exception("Could not parse! got invalid url host errors")
        else:
            msg = dispatcher.bot.send_message(
                chat.id,
                markdown_parser(
                    (
                        backup_message
                        + "\nNote: An error occured when sending the custom message. Please update."
                    )
                ),
                parse_mode=ParseMode.MARKDOWN,
            )

            log.exception()
    return msg


@rate_limit(40, 60)
def welcomeFilter(update: Update, context: CallbackContext):
    if update.effective_chat.type not in ["group", "supergroup"]:
        return
    if nm := update.chat_member.new_chat_member:
        om = update.chat_member.old_chat_member
        if nm.status == nm.MEMBER and om.status in [nm.KICKED, nm.LEFT]:
            return new_member(update, context)
        if nm.status in [nm.KICKED, nm.LEFT] and om.status in [
            nm.MEMBER,
            nm.ADMINISTRATOR,
            nm.CREATOR,
        ]:
            return left_member(update, context)


@rate_limit(40, 60)
@loggable
def new_member(update: Update, context: CallbackContext):  # sourcery no-metrics
    bot, job_queue = context.bot, context.job_queue
    chat = update.effective_chat
    user = update.effective_user
    log_setting = logsql.get_chat_setting(chat.id)
    if not log_setting:
        logsql.set_chat_setting(
            logsql.LogChannelSettings(chat.id, True, True, True, True, True)
        )
        log_setting = logsql.get_chat_setting(chat.id)
    should_welc, cust_welcome, cust_content, welc_type = sql.get_welc_pref(chat.id)
    welc_mutes = sql.welcome_mutes(chat.id)
    human_checks = sql.get_human_checks(user.id, chat.id)
    raid, _, deftime = sql.getRaidStatus(str(chat.id))

    new_mem = update.chat_member.new_chat_member.user

    welcome_log = None
    res = None
    sent = None
    should_mute = True
    welcome_bool = True
    media_wel = False

    if raid and new_mem.id not in WHITELISTED:
        bantime = deftime
        with contextlib.suppress(BadRequest):
            chat.ban_member(new_mem.id, until_date=bantime)
        return

    data = None
    if sibylClient and does_chat_sibylban(chat.id):
        try:
            data = sibylClient.get_info(user.id)
        except GeneralException:
            pass
        except BaseException as e:
            log.error(e)
        if data and data.banned:
            return  # all modes handle it in different ways

    # if sw != None:
    #     sw_ban = sw.get_ban(new_mem.id)
    #     if sw_ban:
    #         return

    if should_welc:
        # Give the owner a special welcome
        if new_mem.id == OWNER_ID:
            bot.send_message(
                chat.id,
                "Oh hi, my creator.",
            )
            welcome_log = (
                f"{html.escape(chat.title)}\n"
                f"#USER_JOINED\n"
                f"Bot Owner just joined the chat"
            )
            return

        # Welcome Devs
        elif new_mem.id in DEV_USERS:
            bot.send_message(
                chat.id,
                "Whoa! A member of the Eagle Union just joined!",
            )
            return

        # Welcome Sudos
        elif new_mem.id in SUDO_USERS:
            bot.send_message(
                chat.id,
                "Huh! A Royal Nation just joined! Stay Alert!",
            )
            return

        # Welcome Support
        elif new_mem.id in SUPPORT_USERS:
            bot.send_message(
                chat.id,
                "Huh! Someone with a Sakura Nation level just joined!",
            )
            return

        # Welcome Whitelisted
        elif new_mem.id in SARDEGNA_USERS:
            bot.send_message(
                chat.id,
                "Oof! A Sadegna Nation just joined!",
            )
            return

        # Welcome SARDEGNA_USERS
        elif new_mem.id in WHITELIST_USERS:
            bot.send_message(
                chat.id,
                "Oof! A Neptuia Nation just joined!",
            )
            return

        # Welcome yourself
        elif new_mem.id == bot.id:
            bot.send_message(
                chat.id,
                "Thanks for adding me! Join @YorkTownEagleUnion for support.",
            )
            return

        else:
            buttons = sql.get_welc_buttons(chat.id)
            keyb = build_keyboard(buttons)

            if welc_type not in (sql.Types.TEXT, sql.Types.BUTTON_TEXT):
                media_wel = True

            first_name = (
                new_mem.first_name or "PersonWithNoName"
            )  # edge case of empty name - occurs for some bugs.

            if cust_welcome:
                if cust_welcome == sql.DEFAULT_WELCOME:
                    cust_welcome = random.choice(sql.DEFAULT_WELCOME_MESSAGES).format(
                        first=escape_markdown(first_name)
                    )

                if new_mem.last_name:
                    fullname = escape_markdown(f"{first_name} {new_mem.last_name}")
                else:
                    fullname = escape_markdown(first_name)
                count = chat.get_member_count()
                mention = mention_markdown(new_mem.id, escape_markdown(first_name))
                if new_mem.username:
                    username = "@" + escape_markdown(new_mem.username)
                else:
                    username = mention

                valid_format = escape_invalid_curly_brackets(
                    cust_welcome, VALID_WELCOME_FORMATTERS
                )
                res = valid_format.format(
                    first=escape_markdown(first_name),
                    last=escape_markdown(new_mem.last_name or first_name),
                    fullname=escape_markdown(fullname),
                    username=username,
                    mention=mention,
                    count=count,
                    chatname=escape_markdown(chat.title),
                    id=new_mem.id,
                )

            else:
                res = random.choice(sql.DEFAULT_WELCOME_MESSAGES).format(
                    first=escape_markdown(first_name)
                )
                keyb = []

            backup_message = random.choice(sql.DEFAULT_WELCOME_MESSAGES).format(
                first=escape_markdown(first_name)
            )
            keyboard = InlineKeyboardMarkup(keyb)

    else:
        welcome_bool = False
        res = None
        keyboard = None
        backup_message = None
        reply = None

    # User exceptions from welcomemutes
    if (
        is_user_ban_protected(update, new_mem.id, chat.get_member(new_mem.id))
        or human_checks
    ):
        should_mute = False
    # Join welcome: soft mute
    if new_mem.is_bot:
        should_mute = False

    if user.id == new_mem.id and should_mute:
        if welc_mutes == "soft":
            bot.restrict_chat_member(
                chat.id,
                new_mem.id,
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=False,
                    can_send_other_messages=False,
                    can_invite_users=False,
                    can_pin_messages=False,
                    can_send_polls=False,
                    can_change_info=False,
                    can_add_web_page_previews=False,
                ),
                until_date=(int(time.time() + 24 * 60 * 60)),
            )
            sql.set_human_checks(user.id, chat.id)
        if welc_mutes == "strong":
            welcome_bool = False
            if not media_wel:
                VERIFIED_USER_WAITLIST.update(
                    {
                        (chat.id, new_mem.id): {
                            "should_welc": should_welc,
                            "media_wel": False,
                            "status": False,
                            "update": update,
                            "res": res,
                            "keyboard": keyboard,
                            "backup_message": backup_message,
                        }
                    }
                )
            else:
                VERIFIED_USER_WAITLIST.update(
                    {
                        (chat.id, new_mem.id): {
                            "should_welc": should_welc,
                            "chat_id": chat.id,
                            "status": False,
                            "media_wel": True,
                            "cust_content": cust_content,
                            "welc_type": welc_type,
                            "res": res,
                            "keyboard": keyboard,
                        }
                    }
                )
            new_join_mem = (
                f"[{escape_markdown(new_mem.first_name)}](tg://user?id={user.id})"
            )
            message = bot.send_message(
                chat.id,
                f"{new_join_mem}, click the button below to prove you're human.\nYou have 120 seconds.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Yes, I'm human.",
                                callback_data=f"user_join_({new_mem.id})",
                            )
                        ]
                    ]
                ),
                parse_mode=ParseMode.MARKDOWN,
                allow_sending_without_reply=True,
            )
            bot.restrict_chat_member(
                chat.id,
                new_mem.id,
                permissions=ChatPermissions(
                    can_send_messages=False,
                    can_invite_users=False,
                    can_pin_messages=False,
                    can_send_polls=False,
                    can_change_info=False,
                    can_send_media_messages=False,
                    can_send_other_messages=False,
                    can_add_web_page_previews=False,
                ),
            )
            job_queue.run_once(
                partial(check_not_bot, new_mem, chat.id, message.message_id),
                120,
                name="welcomemute",
            )
        if welc_mutes == "captcha":
            btn = []
            # Captcha image size number (2 -> 640x360)
            CAPCTHA_SIZE_NUM = 2
            # Create Captcha Generator object of specified size
            generator = CaptchaGenerator(CAPCTHA_SIZE_NUM)

            # Generate a captcha image
            captcha = generator.gen_captcha_image(difficult_level=3)
            # Get information
            image = captcha["image"]
            characters = captcha["characters"]
            # print(characters)
            fileobj = BytesIO()
            fileobj.name = f"captcha_{new_mem.id}.png"
            image.save(fp=fileobj)
            fileobj.seek(0)
            CAPTCHA_ANS_DICT[(chat.id, new_mem.id)] = int(characters)
            welcome_bool = False
            if not media_wel:
                VERIFIED_USER_WAITLIST.update(
                    {
                        (chat.id, new_mem.id): {
                            "should_welc": should_welc,
                            "media_wel": False,
                            "status": False,
                            "update": update,
                            "res": res,
                            "keyboard": keyboard,
                            "backup_message": backup_message,
                            "captcha_correct": characters,
                        }
                    }
                )
            else:
                VERIFIED_USER_WAITLIST.update(
                    {
                        (chat.id, new_mem.id): {
                            "should_welc": should_welc,
                            "chat_id": chat.id,
                            "status": False,
                            "media_wel": True,
                            "cust_content": cust_content,
                            "welc_type": welc_type,
                            "res": res,
                            "keyboard": keyboard,
                            "captcha_correct": characters,
                        }
                    }
                )

            nums = [random.randint(1000, 9999) for _ in range(7)]
            nums.append(characters)
            random.shuffle(nums)
            to_append = []
            # print(nums)
            for a in nums:
                to_append.append(
                    InlineKeyboardButton(
                        text=str(a),
                        callback_data=f"user_captchajoin_({chat.id},{new_mem.id})_({a})",
                    )
                )
                if len(to_append) > 2:
                    btn.append(to_append)
                    to_append = []
            if to_append:
                btn.append(to_append)

            message = bot.send_photo(
                chat.id,
                fileobj,
                caption=f"Welcome [{escape_markdown(new_mem.first_name)}](tg://user?id={user.id}). Click the correct button to get unmuted!\n"
                f"You got 120 seconds for this.",
                reply_markup=InlineKeyboardMarkup(btn),
                parse_mode=ParseMode.MARKDOWN,
                allow_sending_without_reply=True,
            )
            bot.restrict_chat_member(
                chat.id,
                new_mem.id,
                permissions=ChatPermissions(
                    can_send_messages=False,
                    can_invite_users=False,
                    can_pin_messages=False,
                    can_send_polls=False,
                    can_change_info=False,
                    can_send_media_messages=False,
                    can_send_other_messages=False,
                    can_add_web_page_previews=False,
                ),
            )
            job_queue.run_once(
                partial(check_not_bot, new_mem, chat.id, message.message_id),
                120,
                name="welcomemute",
            )

    if welcome_bool:
        if media_wel:
            if ENUM_FUNC_MAP[welc_type] == dispatcher.bot.send_sticker:
                sent = ENUM_FUNC_MAP[welc_type](
                    chat.id,
                    cust_content,
                    reply_markup=keyboard,
                )
            else:
                sent = ENUM_FUNC_MAP[welc_type](
                    chat.id,
                    cust_content,
                    caption=res,
                    reply_markup=keyboard,
                    parse_mode="markdown",
                )
        else:
            sent = send(update, res, keyboard, backup_message)
        prev_welc = sql.get_clean_pref(chat.id)
        if prev_welc:
            try:
                bot.delete_message(chat.id, prev_welc)
            except BadRequest:
                pass

            if sent:
                sql.set_clean_welcome(chat.id, sent.message_id)

        if not log_setting.log_joins:
            return ""
        if welcome_log:
            return welcome_log

    return ""
    if u.effective_message.left_chat_member or u.effective_message.new_chat_members:
        return handleCleanService(u)


def handleCleanService(update: Update):
    if sql.clean_service(update.effective_
