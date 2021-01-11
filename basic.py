from admin import *
from botCalendar import Calendar
from envs import DATE_FORMAT, CRED_FILE, WORKBOOK_NAME, CD_MAP_DE, CD_MAP_EN
import keyboards
from keyboards import Keyboard
from readSheets import Workbook
from telegram import InlineKeyboardMarkup
from times import times
from utils import *


wb = Workbook(cred_file=CRED_FILE, wb_name=WORKBOOK_NAME)
cur_weekday = None


def view_basic(update, context, date=None, edit_start=True):
    """View status for current day and next day.
    If today is a weekend, status for Sat, Sun, Mon, Tues would be displayed."""
    query = update.callback_query
    if edit_start:
        query.edit_message_text(text=f"Checking status...")
    user_num = log_print(update, context)

    week_day = 1
    if date is None:
        date_1_obj, date_1, _, date_2_obj, date_2, _, week_day = times()

        # If today is a weekend, skip to next 2 week days
        if week_day == 6:
            date_1_obj += datetime.timedelta(days=2)
        elif week_day == 7:
            date_1_obj += datetime.timedelta(days=1)
        date_2_obj = date_1_obj + datetime.timedelta(days=1)
    else:
        date_1_obj = datetime.datetime.strptime(date, DATE_FORMAT)
        date_2_obj = date_1_obj + datetime.timedelta(days=1)

    date_1 = date_1_obj.strftime(DATE_FORMAT)
    day_1 = date_1_obj.strftime('%A')
    date_2 = date_2_obj.strftime(DATE_FORMAT)
    day_2 = date_2_obj.strftime('%A')

    ws, row, col = coords(wb, user_num, date_1)
    stat_1 = ws.cell(row, col).value

    ws, row, col = coords(wb, user_num, date_2)
    stat_2 = ws.cell(row, col).value

    if stat_1 == 1 or stat_1 == '1' or stat_1 == '':
        stat_1 = 'PRESENT'

    if stat_2 == 1 or stat_2 == '1' or stat_2 == '':
        stat_2 = 'PRESENT'

    # Convert cds
    stat_1 = CD_MAP_DE.get(stat_1, stat_1)
    stat_2 = CD_MAP_DE.get(stat_2, stat_2)

    # assume if edit_start is False, view_basic was called from view other date
    kb = Keyboard(keyboards.view_basic) if edit_start else Keyboard(keyboards.view_basic_2)
    reply_markup = InlineKeyboardMarkup(kb.setup())
    if edit_start:
        query.edit_message_text(
            f"{'Status' if (week_day < 6) else 'Expected status'} for {'today,' if (week_day < 6) else f'{day_1},'} {date_1}: {stat_1}\n"
            f"Expected status for {'tomorrow,' if (week_day < 6) else f'{day_2},'} {date_2}: {stat_2}",
            reply_markup=reply_markup)
    else:
        query.edit_message_text(
            f"(Expected) Status for {day_1}, {date_1}: {stat_1}\n"
            f"(Expected) Status for {day_2}, {date_2}: {stat_2}",
            reply_markup=reply_markup)


def view_more(update, context):
    """View status for next 7 weekdays."""

    query = update.callback_query
    query.edit_message_text(f"Fetching status for next 7 weekdays...")
    user_num = log_print(update, context)
    today_obj = times()[0]

    dates = []
    cur_date = today_obj
    while True:
        if len(dates) == 7:
            break

        if cur_date.isoweekday() == 6 or cur_date.isoweekday() == 7:
            cur_date = cur_date + datetime.timedelta(days=1)
        else:
            dates.append(cur_date)
            cur_date = cur_date + datetime.timedelta(days=1)

    dates = [(x.strftime(DATE_FORMAT), x.strftime('%A')) for x in dates]

    i = 0
    stats = []
    while i < len(dates):
        ws, row, col = coords(wb, user_num, date=dates[i][0])
        stat = ws.cell(row, col).value
        if stat == 1 or stat == '1' or stat == '':
            stat = "PRESENT"
        stat = CD_MAP_DE.get(stat, stat)
        stats.append(f"Status for {dates[i][1]}, {dates[i][0]}: {stat}")
        i += 1

    kb = Keyboard(keyboards.view_more)
    reply_markup = InlineKeyboardMarkup(kb.setup())
    query.edit_message_text(f"{stats[0]}\n{stats[1]}\n{stats[2]}\n{stats[3]}\n{stats[4]}\n{stats[5]}\n{stats[6]}",
                            reply_markup=reply_markup)


def view_other(update, context):
    """View status for other date.
    This will call calendar function to select particular date."""

    query = update.callback_query
    log_print(update, context)

    reply_markup = Calendar(view_only=True).setup()
    remove_inline(update, context)
    context.bot.send_message(chat_id=update.callback_query.from_user.id,
                             text="For which date do you wish to view your status?",
                             reply_markup=reply_markup)


def edit_main(update, context):
    query = update.callback_query
    log_print(update, context)
    # if update.message.chat.type is 'group':
    # context.bot.answer_inline_query(query.id, ["a"], switch_pm_text=True)
    kb = Keyboard(keyboards.edit_main)
    reply_markup = InlineKeyboardMarkup(kb.setup())
    query.edit_message_text(f"For which date do you wish to update your status?\n\n",
                            reply_markup=reply_markup)


def edit_day(update, context, full_date=None, view_only=False, for_report=False, for_week=False, batch_edit=False, specific_edit=False):
    """Allows user to edit status for particular day."""
    global cur_weekday

    query = update.callback_query

    if specific_edit:
        # user_name = query.data
        # user_num = user_map.get(user_name.lower())
        return admin_edit_user(update, context, date=full_date)

    else:
        user_num = log_print(update, context)

    if not full_date:
        full_date = query.data

    cur_weekday = full_date
    if ", " in cur_weekday:
        cur_weekday = cur_weekday.split(', ')[1]
    cur_weekday_name = datetime.datetime.strptime(cur_weekday, DATE_FORMAT).strftime('%A')

    if view_only and (not for_report or not for_week or not batch_edit):
        query.edit_message_text(text=f"Fetching status for {cur_weekday_name}, {cur_weekday}...")
        return view_basic(update, context, full_date, edit_start=False)

    if for_report:
        if for_week:
            admin_report_week(update, context, date=full_date)
        elif batch_edit:
            admin_bat_edit_date(update, context, date=full_date)
        else:
            admin_report_date(update, context, date=full_date)

    else:
        query.edit_message_text(text=f"Fetching status for {cur_weekday_name}, {cur_weekday}...")

        ws, row, col = coords(wb, user_num, date=cur_weekday)
        stat = ws.cell(row, col).value

        if stat == 1 or stat == '1' or stat == '':
            stat = 'PRESENT'
        stat = CD_MAP_DE.get(stat, stat)

        kb = Keyboard(keyboards.edit_day)
        reply_markup = InlineKeyboardMarkup(kb.setup())
        query.edit_message_text(f"Current status for {cur_weekday}: {stat}\n"
                                "What do you want to update it to?",
                                reply_markup=reply_markup)


def edit_more(update, context):
    """Allows user to select particular date to edit status.
    Calls calendar function to select particular date."""

    query = update.callback_query
    log_print(update, context)

    reply_markup = Calendar().setup()
    query.edit_message_text("For which date do you wish to update your status?",
                            reply_markup=reply_markup)


def update_data(update, context):
    """Update data on Google Sheets using API."""
    global cur_weekday

    query = update.callback_query
    user_num = log_print(update, context)

    ws, row, col = coords(wb, user_num, date=cur_weekday)

    stat_new = query.data
    stat_update = stat_new

    if stat_update == "PRESENT":
        stat_update = "1" # if (cur_weekday == datetime.datetime.today().strftime(DATE_FORMAT)) else ""
    else:
        stat_update = CD_MAP_EN.get(stat_update, stat_update)

    ws.update_cell(row, col, stat_update)

    kb = Keyboard(keyboards.edit_back)
    reply_markup = InlineKeyboardMarkup(kb.setup())
    query.edit_message_text(f"Status for {cur_weekday} updated successfully: {stat_new}\n",
                            reply_markup=reply_markup)


def bot_calendar(update, context):
    """Handler for calendar reply markup"""

    calendar = Calendar()
    selected, date, _, _, _, _, _ = calendar.process(update, context)
    view_only, for_report, for_week, batch_edit, specific_edit = update.callback_query.data.split('~')[-5:]

    if selected:
        edit_day(update, context, date, eval(view_only), eval(for_report),
                 eval(for_week), eval(batch_edit), eval(specific_edit))
