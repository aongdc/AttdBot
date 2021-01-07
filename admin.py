from telegram import InlineKeyboardMarkup
from botCalendar import Calendar
from envs import DATE_FORMAT, CRED_FILE, WORKBOOK_NAME
import keyboards
from keyboards import Keyboard
from readSheets import Workbook
from times import times
from utils import *

admin_chosen_date = None
wb = Workbook(cred_file=CRED_FILE, wb_name=WORKBOOK_NAME)
user_lst = users(as_dict=False)
cur_weekday = None


def admin_start(update, context):
    query = update.callback_query
    log_print(update, context)

    query.edit_message_text("Administration Mode")
    # send = context.bot.send_message(chat_id=update.callback_query.from_user.id,
    #                                 text=f"Administration")

    admin_options(update, context)


def admin_options(update, context):
    global admin_chosen_date

    query = update.callback_query
    admin_chosen_date = datetime.datetime.today().strftime(DATE_FORMAT)

    if query.data == '< Back to Admin' or query.data == 'Cancel Batch Edit':
        log_print(update, context)
        remove_inline(update, context)
        admin_chosen_date = datetime.datetime.today().strftime(DATE_FORMAT)

    kb = Keyboard(keyboards.admin_view)
    reply_markup = InlineKeyboardMarkup(kb.setup())
    context.bot.send_message(chat_id=query.from_user.id,
                             text="Hello admin, what would you like to do?",
                             reply_markup=reply_markup)


def admin_report_date(update, context, date=None, for_week=False, batch_edit=False):
    global admin_chosen_date

    def _admin_report_date(date, batch_edit=False):
        ws, row, col = coords(wb, 1, date)

        stats = dict()
        total_num = len(users())
        present_num = total_num
        for i in range(total_num):
            name = ws.cell(row + i, 1).value
            stat = ws.cell(row + i, col).value
            if not (stat == 1 or stat == '1' or stat == ''):
                present_num -= 1
                stats[name] = stat
            i += 1

        stats = sorted(stats.items(), key=lambda key: (key[1], key[0]))
        stats = [f'{x[0]} {x[1]}' for x in stats]
        stats = '\n'.join(stats)
        nl = '\n'

        if not batch_edit:
            header = f"SCVU PARADE STATE\n" \
                     f"{date}\n" \
                     f"{datetime.datetime.strptime(date, DATE_FORMAT).strftime('%A')}\n\n" \
                     f"{f'Current' if date == datetime.datetime.today().strftime(DATE_FORMAT) else 'Expected'} Strength: {present_num} / {total_num}\n" \
                     f"{nl*2 if total_num != present_num else ''}"
        else:
            header = f"{date}\n" \
                     f"{datetime.datetime.strptime(date, DATE_FORMAT).strftime('%A')}\n\n" \
                     f"{f'Current' if date == datetime.datetime.today().strftime(DATE_FORMAT) else 'Expected'} Strength: {present_num} / {total_num}\n" \
                     f"{nl * 2 if total_num != present_num else ''}"

        full = header + stats

        return full

    query = update.callback_query
    if date is None:
        date_obj, week_day = times()[0], times()[-1]
        # If today is a weekend, skip to next weekday
        if week_day == 6:
            date_obj += datetime.timedelta(days=2)
        elif week_day == 7:
            date_obj += datetime.timedelta(days=1)

        date = date_obj.strftime(DATE_FORMAT)
        day = date_obj.strftime('%A')
    admin_chosen_date = date

    query.edit_message_text(text=f"Fetching statuses for {admin_chosen_date if not for_week else 'the week'}...")
    log_print(update, context)

    if for_week:
        date_obj = datetime.datetime.strptime(date, DATE_FORMAT)
        day_num = date_obj.isoweekday()

        if day_num == 6:
            # Show upcoming week if today is a Saturday
            new_date = date_obj + datetime.timedelta(days=2)
        elif day_num == 7:
            # Show upcoming week if today is a Sunday
            new_date = date_obj + datetime.timedelta(days=1)
        else:
            new_date = date_obj - datetime.timedelta(days=day_num)

        full = [f"SCVU PARADE STATE (PROJECTED)\n"
                f"for week starting {new_date.strftime(DATE_FORMAT)}\n"
                f"retrieved {datetime.datetime.today().strftime('%d/%m/%Y %H%MH')}\n"
                f"============="]
        i = 0
        while i < 5:
            part = _admin_report_date(new_date.strftime(DATE_FORMAT), batch_edit=True)
            full.append(part)
            if i < 5:
                full.append("-------------")
            new_date += datetime.timedelta(days=1)
            i += 1

        full = "\n".join(full)
    else:
        full = _admin_report_date(date)

    if batch_edit:
        kb = Keyboard(keyboards.admin_edit, for_admin_bat_edit=True)
        reply_markup = InlineKeyboardMarkup(kb.setup())
        query.edit_message_text(f"{full}" + "\n\nWhat do you wish to update all statuses to?",
                                reply_markup=reply_markup)
    else:
        kb = Keyboard(keyboards.admin_more_day)
        reply_markup = InlineKeyboardMarkup(kb.setup())
        query.edit_message_text(f"{full}", reply_markup=reply_markup)


def admin_report_next_date(update, context):
    global admin_chosen_date

    ori_date = datetime.datetime.strptime(admin_chosen_date, DATE_FORMAT)
    new_date = ori_date + datetime.timedelta(days=1)
    admin_chosen_date = new_date.strftime(DATE_FORMAT)

    admin_report_date(update, context, date=admin_chosen_date)


def admin_report_prev_date(update, context):
    global admin_chosen_date

    ori_date = datetime.datetime.strptime(admin_chosen_date, DATE_FORMAT)
    new_date = ori_date - datetime.timedelta(days=1)
    admin_chosen_date = new_date.strftime(DATE_FORMAT)

    admin_report_date(update, context, date=admin_chosen_date)


def admin_report_select_date(update, context):
    query = update.callback_query
    log_print(update, context)

    reply_markup = Calendar(for_report=True, for_week=False).setup()
    query.edit_message_text("For which date do you wish to view status report?",
                            reply_markup=reply_markup)


def admin_report_week(update, context, date=datetime.datetime.today().strftime(DATE_FORMAT)):
    query = update.callback_query
    log_print(update, context)

    admin_report_date(update, context, date=date, for_week=True)


def admin_report_select_week(update, context):
    query = update.callback_query
    log_print(update, context)

    reply_markup = Calendar(for_report=True, for_week=True).setup()
    query.edit_message_text("For which week do you wish to view status report?\n"
                            "You may select any weekday of the week to view that week.",
                            reply_markup=reply_markup)


def admin_report_next_week(update, context):
    global admin_chosen_date

    query = update.callback_query
    log_print(update, context)

    date_obj = datetime.datetime.strptime(admin_chosen_date, DATE_FORMAT)
    day_num = date_obj.weekday()
    ori_week = date_obj - datetime.timedelta(days=day_num)
    new_week = ori_week + datetime.timedelta(weeks=1)
    admin_chosen_date = new_week.strftime(DATE_FORMAT)

    admin_report_date(update, context, date=admin_chosen_date, for_week=True)


def admin_report_prev_week(update, context):
    global admin_chosen_date

    query = update.callback_query
    log_print(update, context)

    date_obj = datetime.datetime.strptime(admin_chosen_date, DATE_FORMAT)
    day_num = date_obj.weekday()
    ori_week = date_obj - datetime.timedelta(days=day_num)
    new_week = ori_week - datetime.timedelta(weeks=1)
    admin_chosen_date = new_week.strftime(DATE_FORMAT)

    admin_report_date(update, context, date=admin_chosen_date, for_week=True)


def admin_bat_edit_date(update, context, date=datetime.datetime.today().strftime(DATE_FORMAT)):
    query = update.callback_query
    log_print(update, context)

    admin_report_date(update, context, date=date, for_week=False, batch_edit=True)


def admin_bat_edit_date_interm(update, context):
    global admin_chosen_date

    query = update.callback_query
    log_print(update, context)
    ws, row, col = coords(wb, 1, date=admin_chosen_date)

    stat_new = keyboards._for_admin_edit.get(query.data)
    stat_update = stat_new

    if stat_update == "Present":
        stat_update = "1" if admin_chosen_date == datetime.datetime.today().strftime(DATE_FORMAT) else ""

    num_users = len(user_lst)
    i = 0
    while i < num_users:
        ws.update_cell(row + i, col, stat_update)
        i += 1

    query.edit_message_text(f"All statuses for {admin_chosen_date} updated successfully: {stat_new}\n")

    kb = Keyboard(keyboards.admin_view)
    reply_markup = InlineKeyboardMarkup(kb.setup())
    user_id = update.callback_query.from_user.id
    context.bot.send_message(chat_id=user_id,
                             text="What else do you want to do, admin?",
                             reply_markup=reply_markup)


def admin_bat_edit_select_date(update, context):
    query = update.callback_query
    log_print(update, context)

    reply_markup = Calendar(for_report=True, for_week=False, batch_edit=True).setup()
    query.edit_message_text("For which date do you wish to batch edit everyone's status report?",
                            reply_markup=reply_markup)


def admin_edit_user(update, context, date=datetime.datetime.today().strftime(DATE_FORMAT)):
    global admin_chosen_date

    query = update.callback_query
    log_print(update, context)
    admin_chosen_date = date

    users_lst = [x.upper() for x in user_lst]

    kb = Keyboard(users_lst)
    reply_markup = InlineKeyboardMarkup(kb.setup())

    query.edit_message_text(f"For whose status report do you wish to make changes?",
                            reply_markup=reply_markup)


def admin_edit_user_spec(update, context, user_name, user_num, date=datetime.datetime.today().strftime(DATE_FORMAT)):
    global cur_weekday

    query = update.callback_query
    log_print(update, context)

    cur_weekday = date
    week_day = datetime.datetime.strptime(date, DATE_FORMAT).strftime('%A')
    query.edit_message_text(text=f"Fetching status for {user_name.title()} on {week_day}, {cur_weekday}...")

    ws, row, col = coords(wb, user_num, date=date)
    stat = ws.cell(row, col).value

    if stat == 1 or stat == '1' or stat == '':
        stat = 'Present'

    kb = Keyboard(keyboards.edit_day, for_admin_edit=True, user_num=user_num)
    reply_markup = InlineKeyboardMarkup(kb.setup())

    query.edit_message_text(f"Current status for {user_name.title()} on {week_day}, {cur_weekday}: {stat}\n"
                            "What do you want to update it to?",
                            reply_markup=reply_markup)


def admin_edit_user_interm(update, context):
    global admin_chosen_date

    query = update.callback_query
    log_print(update, context)
    date = admin_chosen_date
    user_name = query.data.lower()
    user_num = users()[user_name]

    return admin_edit_user_spec(update, context, user_name, user_num, date=date)


def admin_edit_user_select(update, context):
    query = update.callback_query
    log_print(update, context)

    reply_markup = Calendar(for_report=True, specific_edit=True).setup()
    query.edit_message_text("For which date do you wish to edit status report?",
                            reply_markup=reply_markup)


def admin_update_data(update, context):
    global cur_weekday

    query = update.callback_query
    log_print(update, context)
    user_num = int(query.data.split(', ')[1])

    ws, row, col = coords(wb, user_num, date=cur_weekday)

    stat_new = keyboards._admin_edit_day[query.data.split(', ')[0]]
    stat_update = stat_new

    if stat_update == "Present":
        stat_update = "1" if (datetime.datetime.strptime(cur_weekday, DATE_FORMAT) == datetime.datetime.today()) else ""

    ws.update_cell(row, col, stat_update)

    kb = Keyboard(keyboards.edit_back)
    reply_markup = InlineKeyboardMarkup(kb.setup())
    query.edit_message_text(f"Status for {user_lst[user_num-1].capitalize()} on {cur_weekday} updated successfully: {stat_new}\n",
                            reply_markup=reply_markup)
