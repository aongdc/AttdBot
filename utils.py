import datetime
import logging
from envs import DATABASE_PATH
import readSQL
from users import users


def log_print(update, context):
    query = update.message if update.message else update.callback_query
    user_id = update.message.from_user.id if update.message else query.from_user.id
    name = update.message.from_user.first_name if update.message else query.from_user.first_name
    logging.getLogger('__main__').info(f"{name} ({user_id}): {query.text if update.message else query.data}")
    user_id_map = readSQL.Database(DATABASE_PATH).get_user_id_map()
    user_num = users()[user_id_map[user_id]]
    return user_num


def coords(wb, user_num, date):
    """Gets the coordinates of the cell for specified user for particular date."""

    day, month, year = date.split('/')
    day, month, year = int(day), int(month), int(year)
    month = datetime.date(year, month, day).strftime('%b')
    sheet_name = f"{month} {year}"

    ws = wb.open_sheet(sheet=sheet_name)

    row = int(user_num + 2)
    col = int(day + 1)

    return ws, row, col


def flatten(chunk):
    """Convert nested lists into a single list."""

    lst = [x for y in chunk for x in y]

    return lst


def remove_inline(update, context):
    """Removes inline reply markup of previous message."""

    query = update.callback_query
    # query.edit_message_text(f"Status for today, {envs.date_1}: {stat_1}\n"
    #                         f"Expected status for tomorrow, {envs.date_2}: {stat_2}")
    query.edit_message_reply_markup(reply_markup=None)
