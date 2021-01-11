import datetime
import logging
from admin import *
from basic import *
from envs import TELEGRAM_BOT_TOKEN, CRED_FILE, WORKBOOK_NAME, DATABASE_PATH, PORT, WEB_ADDRESS
import keyboards
from keyboards import Keyboard
from readSheets import Workbook
import readSQL
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler, CallbackQueryHandler, ConversationHandler
from users import users
from utils import *
from key import usage_code, admin_code

updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    handlers=[
                        logging.FileHandler("_info.log"),
                        logging.StreamHandler()])
logger = logging.getLogger(__name__)

wb = Workbook(cred_file=CRED_FILE, wb_name=WORKBOOK_NAME)

admin_chosen_date = None
user_map = users()
user_lst = users(as_dict=False)
user_lst_seg = users(as_dict=False, segmented_list=2)


def verify_user(update, context):
    """
    All /start commands call this function.
    User is asked to authenticate by sending the key code.
    """

    user = update.message.from_user
    user_id = user.id

    db = readSQL.Database(DATABASE_PATH, setup=True)
    user_id_lst = db.get_user_id_lst()

    if user_id not in user_id_lst:
        logger.info("User %s (@%s) started the conversation.", user.first_name, user.username)
        context.bot.send_message(chat_id=user_id,
                                 text="If you are authorised to use this bot, you would have been given a key code. "
                                      "Please send me the key code now for verification.\n\n"
                                      "EXIT IMMEDIATELY IF YOU ARE NOT AUTHORISED TO PROCEED! /quit")
        return 33

    start(update, context)


def verify_user_confirmation(update, context):
    user = update.message.from_user
    user_id = user.id
    given_code = update.message.text
    logger.info("User %s (@%s) tried to authorise with code: %s.", user.first_name, user.username, given_code)

    if given_code == usage_code():
        context.bot.send_message(chat_id=user_id,
                                 text="Verification successful!")
        initial(update, context)
        return 0

    else:
        context.bot.send_message(chat_id=user_id,
                                 text="The key code you have entered is incorrect. "
                                      "You are not an authorised to use this bot!\n\n"
                                      "PLEASE EXIT IMMEDIATELY! /quit")
        return ConversationHandler.END


def initial(update, context):
    """
    If user_id is known, continue to start; else, find out who it is.
    """

    user_id = update.message.from_user.id
    db = readSQL.Database(DATABASE_PATH)
    user_id_lst = db.get_user_id_lst()

    if user_id not in user_id_lst:
        kb = Keyboard(user_lst_seg)
        reply_markup = InlineKeyboardMarkup(kb.setup())
        context.bot.send_message(chat_id=user_id,
                                 text="Welcome to the whimsical world of AttdBot! "
                                      "It's my pleasure meeting you for the first time.\n\n"
                                      "To finish setting things up, which of the following is your name?",
                                 reply_markup=reply_markup)

    else:
        return start(update, context)


def register(update, context):
    """
    If user_id has not been registered, write to database. Then, continue to _start.
    """

    query = update.callback_query
    user_id = query.from_user.id
    first_name = query.from_user.first_name
    user_name = query.from_user.username
    name = query.data.lower()
    db = readSQL.Database(DATABASE_PATH)
    db.add_user(name, user_id, first_name, user_name)
    return _start(update, context)


def start(update, context):
    db = readSQL.Database(DATABASE_PATH)

    if update.message:
        user = update.message.from_user
        user_id = user.id
        user_is_admin = db.user_info(user_id)["is_admin"]
        if user_is_admin:
            kb = Keyboard(keyboards.start_admin)
        else:
            kb = Keyboard(keyboards.start_ordinary)
        reply_markup = InlineKeyboardMarkup(kb.setup())
        update.message.reply_text(f"Hello {user.first_name}, what would you like to do?", reply_markup=reply_markup)

    else:
        remove_inline(update, context)
        user_id = update.callback_query.from_user.id
        user_is_admin = db.user_info(user_id)["is_admin"]
        if user_is_admin:
            kb = Keyboard(keyboards.start_admin)
        else:
            kb = Keyboard(keyboards.start_ordinary)
        reply_markup = InlineKeyboardMarkup(kb.setup())
        context.bot.send_message(chat_id=user_id, text="What else would you like to do?", reply_markup=reply_markup)


def _start(update, context):
    """
    Modified start function for new users, as message should be edited and not replied to with new message.
    """

    query = update.callback_query

    kb = Keyboard(keyboards.start_ordinary)
    reply_markup = InlineKeyboardMarkup(kb.setup())

    user = query.from_user
    logger.info("User %s started the conversation.", user.first_name)
    query.edit_message_text(f"Hello {user.first_name}, what would you like to do?", reply_markup=reply_markup)


def admin_register(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    log_print(update, context)

    query.edit_message_text(text="Register admin...",
                            reply_markup=None)
    context.bot.send_message(chat_id=user_id,
                             text="If you are an admin, you'd have been given a key code. "
                                  "Please send me the key code now for verification.\n\n"
                                  "Contact your local administrator, or DM @dinggchao, for more information. /cancel")
    return 49


def admin_key_check(update, context):
    user_id = update.message.from_user.id
    given_code = update.message.text
    log_print(update, context)

    if given_code == admin_code():
        db = readSQL.Database(DATABASE_PATH)
        if db.register_as_admin(user_id):
            kb = keyboards.Keyboard(keyboards.admin_confirmed)
            reply_markup = InlineKeyboardMarkup(kb.setup())
            context.bot.send_message(chat_id=user_id,
                                     text="Congratulations, you are now an admin!",
                                     reply_markup=reply_markup)
        else:
            kb = keyboards.Keyboard(keyboards.admin_rejected)
            reply_markup = InlineKeyboardMarkup(kb.setup())
            context.bot.send_message(chat_id=user_id,
                                     text="Oops, something went wrong! Please try again later!",
                                     reply_markup=reply_markup)
    else:
        kb = keyboards.Keyboard(keyboards.admin_rejected)
        reply_markup = InlineKeyboardMarkup(kb.setup())
        context.bot.send_message(chat_id=user_id,
                                 text="The key code you have entered is incorrect. "
                                      "You are not an admin (ie to say, an *IMPOSTOR*)!\n\n"
                                      "If you suspect that there has been a mistake, "
                                      "please contact your local administrator, or DM @dinggchao.",
                                 reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    return 0


def end_sess_gracefully(update, context):
    query = update.callback_query
    log_print(update, context)

    user_id = query.from_user.id
    remove_inline(update, context)
    context.bot.send_message(chat_id=user_id, text="Thank you for using AttdBot!")

    return ConversationHandler.END


def end_sess_harsh(update, context):
    user = update.message.from_user
    user_id = user.id
    logger.info("User %s (@%s) left the conversation.", user.first_name, user.username)
    context.bot.send_message(chat_id=user_id, text="Thanks for co-operating, bye!")

    return ConversationHandler.END


def help_page(update, context):
    log_print(update, context)
    update.message.reply_text("Use /start to start this bot.")


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" \ncaused error "%s"', update, context.error)


def main():
    # Initialise and Verify user
    dispatcher.add_handler(ConversationHandler(
        entry_points=[CommandHandler('start', verify_user)],
        states={
            33: [MessageHandler(filters=Filters.text, callback=verify_user_confirmation)]
        },
        fallbacks=[CommandHandler('quit', end_sess_harsh)], allow_reentry=True))
    # Registration
    dispatcher.add_handler(CallbackQueryHandler(register, pattern="|".join([x.title() for x in user_lst])))
    # Main Page; all calls to end session handled here
    dispatcher.add_handler(CallbackQueryHandler(view_basic, pattern=keyboards.start_admin[0]))
    dispatcher.add_handler(CallbackQueryHandler(edit_main, pattern=keyboards.start_admin[1]))
    dispatcher.add_handler(CallbackQueryHandler(admin_start, pattern=keyboards.start_admin[2]))
    dispatcher.add_handler(CallbackQueryHandler(end_sess_gracefully, pattern=keyboards.start_admin[3]))
    # To register as admin
    dispatcher.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_register, pattern=keyboards.start_ordinary[2])],
        states={
            49: [MessageHandler(filters=Filters.text, callback=admin_key_check)]
        },
        fallbacks=[CommandHandler('cancel', start),
                   CommandHandler('stop', end_sess_gracefully)], allow_reentry=True))
    # Confirmed as admin, proceed to Admin: Main Page
    dispatcher.add_handler(CallbackQueryHandler(admin_start, pattern=keyboards.admin_confirmed[0]))
    # View status for more days; all returns to Main Page handled here
    dispatcher.add_handler(CallbackQueryHandler(view_more, pattern=keyboards.view_basic[0]))
    dispatcher.add_handler(CallbackQueryHandler(view_other, pattern=keyboards.view_basic[1]))
    dispatcher.add_handler(CallbackQueryHandler(start, pattern=keyboards.view_basic[2]))
    # Edit status for current or specified day
    dispatcher.add_handler(CallbackQueryHandler(edit_day, pattern=keyboards.edit_main[0]))
    dispatcher.add_handler(CallbackQueryHandler(edit_day, pattern=keyboards.edit_main[1]))
    dispatcher.add_handler(CallbackQueryHandler(edit_more, pattern=keyboards.edit_main[2]))
    # Updates status
    dispatcher.add_handler(CallbackQueryHandler(update_data, pattern="|".join(flatten(keyboards.edit_day)[:-1])))
    dispatcher.add_handler(CallbackQueryHandler(edit_main, pattern=flatten(keyboards.edit_day)[-1]))
    # Admin: Main Page
    dispatcher.add_handler(CallbackQueryHandler(admin_report_date, pattern=keyboards.admin_view[0][0]))
    dispatcher.add_handler(CallbackQueryHandler(admin_report_select_date, pattern=keyboards.admin_view[0][1]))
    dispatcher.add_handler(CallbackQueryHandler(admin_report_week, pattern=keyboards.admin_view[1][0]))
    dispatcher.add_handler(CallbackQueryHandler(admin_report_select_week, pattern=keyboards.admin_view[1][1]))
    dispatcher.add_handler(CallbackQueryHandler(admin_edit_user, pattern=keyboards.admin_view[2][0]))
    dispatcher.add_handler(CallbackQueryHandler(admin_edit_user_select, pattern=keyboards.admin_view[2][1]))
    dispatcher.add_handler(CallbackQueryHandler(admin_bat_edit_date, pattern=keyboards.admin_view[3][0]))
    dispatcher.add_handler(CallbackQueryHandler(admin_bat_edit_select_date, pattern=keyboards.admin_view[3][1]))
    # Admin: report next day, previous day, or select day
    dispatcher.add_handler(CallbackQueryHandler(admin_report_prev_date, pattern=keyboards.admin_more_day[0][0]))
    dispatcher.add_handler(CallbackQueryHandler(admin_report_next_date, pattern=keyboards.admin_more_day[0][1]))
    dispatcher.add_handler(CallbackQueryHandler(admin_report_select_date, pattern=keyboards.admin_more_day[1][0]))
    # Admin: report next week, previous week, select week
    dispatcher.add_handler(CallbackQueryHandler(admin_report_prev_week, pattern=keyboards.admin_more_week[0][0]))
    dispatcher.add_handler(CallbackQueryHandler(admin_report_next_week, pattern=keyboards.admin_more_week[0][1]))
    dispatcher.add_handler(CallbackQueryHandler(admin_report_select_week, pattern=keyboards.admin_more_week[1][0]))
    # Admin: edit user
    dispatcher.add_handler(CallbackQueryHandler(admin_edit_user_interm, pattern="|".join([x.upper() for x in user_lst])))
    dispatcher.add_handler(CallbackQueryHandler(admin_update_data, pattern="|".join(keyboards.admin_edit_day)))
    # Admin: batch edit all status for selected day; all calls to cancel batch edit handled here
    dispatcher.add_handler(CallbackQueryHandler(admin_bat_edit_date_interm, pattern="|".join(flatten(keyboards.for_admin_edit)[:-1])))
    dispatcher.add_handler(CallbackQueryHandler(admin_options, pattern=keyboards.admin_edit[-1][0]))
    # Admin: all calls to return to Admin Main Page and General Main Page handled here
    dispatcher.add_handler(CallbackQueryHandler(admin_options, pattern=keyboards.admin_back[0]))
    dispatcher.add_handler(CallbackQueryHandler(start, pattern=keyboards.admin_back[1]))
    # Calendar handler
    dispatcher.add_handler(CallbackQueryHandler(bot_calendar))
    # Help Page
    dispatcher.add_handler(CommandHandler('help', help_page))
    # Stop Gracefully
    dispatcher.add_handler(CommandHandler('stop', end_sess_gracefully))
    # Error handler
    dispatcher.add_error_handler(error)

    print(f"Initialised @ {datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")

    # Start the Bot
    updater.start_polling()

    # If hosting on Heroku
    # updater.start_webhook(listen='0.0.0.0', port=PORT, url_path=TELEGRAM_BOT_TOKEN)
    # updater.bot.set_webhook(WEB_ADDRESS + TELEGRAM_BOT_TOKEN)

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()


if __name__ == '__main__':
    main()
