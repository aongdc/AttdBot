import datetime
from dateutil import relativedelta
import sys
from envs import CRED_FILE, WORKBOOK_NAME, WORKBOOK_CODES_SHEETNAME
from gspread_formatting import *
import calendar
import holidays
import readSheets
import users


def num_to_letter(n):
    """
    Convert integer number n into corresponding letter, for A1 notation in worksheets.
    """
    string = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        string = chr(65 + remainder) + string
    return string


def get_last_recorded_month(wb):
    print("\nFetching current data...")

    # First recorded month
    print(f"First sheet: {wb.all_sheets()[0].title}")

    # Last recorded month
    last_sheet_idx = len(wb.all_sheets()) - 1
    last_name = wb.all_sheets()[last_sheet_idx].title
    if last_name == WORKBOOK_CODES_SHEETNAME:
        last_sheet_idx -= 1
        last_name = wb.all_sheets()[last_sheet_idx].title
    print(f"Last sheet: {last_name}\n")

    return last_sheet_idx, last_name


def get_bg_fmt_rules(wb):
    bg_fmts = dict()
    ws = wb.open_sheet(WORKBOOK_CODES_SHEETNAME)
    # Num columns determined by number of filled cells in row 1 until an empty cell
    bg_num_cols = len(list(filter(None, ws.row_values(1))))
    for col in range(1, bg_num_cols + 1):
        for row, val in enumerate(ws.col_values(col), start=1):
            bg_fmt = get_user_entered_format(ws, f'{num_to_letter(col)}{row}').backgroundColor
            bg_fmts[val] = bg_fmt

    return bg_fmts


def write_dates(ws, date_obj, num_days_in_month, last_col_letter):
    # Create calendar for month
    cal = calendar.Calendar().monthdays2calendar(date_obj.year, date_obj.month)

    # Add days for month
    days = []
    num_workdays = num_days_in_month
    sg_hols = holidays.SG()
    for week in cal:
        for _date, day in week:
            is_weekend, is_ph = False, False
            if _date == 0:
                continue
            else:
                _date = datetime.date(year=date_obj.year, month=date_obj.month, day=_date)
                if day == 5 or day == 6:
                    is_weekend = True
                if _date in sg_hols:
                    is_ph = sg_hols.get(_date)

                if is_weekend or is_ph:
                    num_workdays -= 1

                days.append([calendar.day_name[day], _date, is_weekend, is_ph])

    # Add days of month
    edit_list = ws.range(f'A1:{last_col_letter}1')
    edit = ["DAY"] + [pair[0] for pair in days]
    k = 0
    while k < len(edit):
        edit_list[k].value = edit[k]
        k += 1
    ws.update_cells(edit_list)

    # Add dates for month
    edit_list = ws.range(f'A2:{last_col_letter}2')
    edit = ["NAME / DATE"] + [f"{pair[1]}/{date_obj.month}/{date_obj.strftime('%y')}" for pair in days]
    k = 0
    while k < len(edit):
        edit_list[k].value = edit[k]
        k += 1
    ws.update_cells(edit_list)

    return days, num_workdays


def write_users(ws, num_users):
    last_user_row = num_users + 2
    edit_list = ws.range(f'A3:A{last_user_row}')
    edit = [x.title() for x in users.users(as_dict=False)]
    k = 0
    while k < len(edit):
        edit_list[k].value = edit[k]
        k += 1
    ws.update_cells(edit_list)

    return last_user_row


def write_hols_and_data_validation(ws, bg_fmts, last_user_row, days):
    edit_list_wkend = []
    edit_list_ph = []
    exclude = ['WEEKEND', 'PH', 'HL', 'WFH', 'ATT', 'CSE', 'OL (AM)', 'OL (PM)', 'OL (AMPM)']
    valid_vals = ['1'] + [k for k in bg_fmts.keys()]
    for val in exclude:
        valid_vals.remove(val)
    val_rule = DataValidationRule(BooleanCondition('ONE_OF_LIST', valid_vals), showCustomUi=True, strict=True)

    for j in range(len(days)):
        cur_col = num_to_letter(j + 2)
        if days[j][2]:
            if days[j][3]:
                ph = days[j][3]
            else:
                ph = None
            edit_list_wkend.append((ws.range(f'{cur_col}3:{cur_col}{last_user_row}'), ph))
        elif days[j][3]:
            ph = days[j][3]
            edit_list_ph.append((ws.range(f'{cur_col}3:{cur_col}{last_user_row}'), ph))
        else:
            # Set data validation rules
            set_data_validation_for_cell_range(ws, f'{cur_col}3:{cur_col}{last_user_row}', val_rule)

    for edit_range, val in edit_list_wkend:
        for edit in edit_range:
            edit.value = "WEEKEND"
            if val:
                edit.value += f", PH\n({val})"

    for edit_range, val in edit_list_ph:
        for edit in edit_range:
            edit.value = f"PH\n({val})"

    edit_list_wkend = [edit[0] for edit in edit_list_wkend]
    edit_list_ph = [edit[0] for edit in edit_list_ph]

    ws.update_cells([edit for edits in edit_list_wkend for edit in edits])
    if edit_list_ph:
        ws.update_cells([edit for edits in edit_list_ph for edit in edits])


def write_proj_total_str(ws, header, edit_row, last_user_row, num_days, count_start_row=3):
    edit_list = ws.range(f'A{edit_row}:{num_to_letter(num_days + 1)}{edit_row}')
    edit_list[0].value = header
    k = 1
    while k < num_days + 1:
        col = num_to_letter(k + 1)
        edit_list[k].value = f'=COUNTBLANK({col}{count_start_row}:{col}{last_user_row})+' \
                             f'SUM({col}{count_start_row}:{col}{last_user_row}))'
        k += 1
    ws.update_cells(edit_list, value_input_option="USER_ENTERED")


def write_workdays_col(ws, last_row, num_days, num_workdays, num_void_rows_from_back=3):
    last_col_letter = num_to_letter(num_days + 2)
    edit_list = ws.range(f'{last_col_letter}1:{last_col_letter}{last_row}')
    edit_list[0].value = "WORKDAYS"
    edit_list[1].value = num_workdays
    for p in range(1, num_void_rows_from_back + 1):
        edit_list[-p].value = "X"
    k = 2
    while k < last_row - num_void_rows_from_back:
        edit_list[k].value = f'=SUM(B{k + 1}:{num_to_letter(num_days + 1)}{k + 1})+' \
                             f'COUNTIF(B{k + 1}:{num_to_letter(num_days + 1)}{k + 1}, "=OTHER (W)")+' \
                             f'COUNTIF(B{k + 1}:{num_to_letter(num_days + 1)}{k + 1}, "=MA*")'
        k += 1
    ws.update_cells(edit_list, value_input_option="USER_ENTERED")


def create_new(cred_file, wb_name):
    # Load in workbook
    wb = readSheets.Workbook(cred_file, wb_name)
    # Fetch current data and get last recorded month
    last_sheet_idx, last_name = get_last_recorded_month(wb)
    # Convert latest worksheet month into datetime object
    last_month, last_year = last_name.split(' ')
    last_month = datetime.datetime.strptime(last_month, '%b').strftime('%m')
    last_date = datetime.date(year=int(last_year), month=int(last_month), day=1)

    # Ask how many months to add
    to_add = None
    while to_add is None:
        to_add = input("How many months to add?\n")
        try:
            to_add = int(to_add)
            if to_add < 0:
                print("Enter positive integer number only!")
                to_add = None
            elif to_add == 0:
                print("Nothing to add, exiting now.")
                sys.exit(2)
        except (TypeError, ValueError) as e:
            print(f"Input integer number only!\n"
                  f"({e})\n")
            to_add = None

    print("\nInitialising...")

    # Get number of users to add into worksheet
    num_users = len(users.users())
    # Get background formatting rules from sheet as defined by WORKBOOK_CODES_SHEETNAME
    bg_fmts = get_bg_fmt_rules(wb)

    # Start adding month sheets
    added = 0
    while added < to_add:
        new_date = last_date + relativedelta.relativedelta(months=1)
        first_day, num_days = calendar.monthrange(new_date.year, new_date.month)
        title = new_date.strftime('%b %Y')
        print(f"[{added + 1}/{to_add}] Creating sheet for {title}")

        # Add sheet
        last_sheet_idx += 1
        wb.add_sheet(title,
                     rows=num_users + 5,
                     cols=num_days + 2,
                     idx=last_sheet_idx)

        # Open sheet for editing
        ws = wb.open_sheet(title)
        last_col_letter = num_to_letter(num_days + 2)

        # Add dates and days
        days, num_workdays = write_dates(ws, new_date, num_days, last_col_letter)

        # Add user names
        last_user_row = write_users(ws, num_users)

        # Write text weekends and public holidays, else validation rules
        write_hols_and_data_validation(ws, bg_fmts, last_user_row, days)

        # Write projected/total row for NSFs only
        edit_row = last_user_row + 1
        write_proj_total_str(ws, "PROJ / TTL 1", edit_row, last_user_row, num_days,
                             count_start_row=15)

        # Write projected/total row for on-site parade state
        edit_row = last_user_row + 2
        write_proj_total_str(ws, "PROJ / TTL 2", edit_row, last_user_row, num_days,
                             count_start_row=7)

        # Write projected/total row for all
        edit_row = last_user_row + 3
        write_proj_total_str(ws, "PROJ / TTL 3", edit_row, last_user_row, num_days,
                             count_start_row=3)

        # Write workdays column
        write_workdays_col(ws, edit_row, num_days, num_workdays, num_void_rows_from_back=3)

        # Freeze header rows and columns
        wb.freeze(ws, num_cols=1, num_rows=2)

        # Set basic formatting
        batch = batch_updater(ws.spreadsheet)
        header_col_fmt = CellFormat(textFormat=TextFormat(bold=True), horizontalAlignment='CENTER')
        header_row_fmt = CellFormat(textFormat=TextFormat(bold=True), horizontalAlignment='CENTER')
        basic_fmt = CellFormat(horizontalAlignment='CENTER', verticalAlignment='MIDDLE')
        batch.format_cell_range(ws, f'A:{last_col_letter}', basic_fmt)
        batch.format_cell_range(ws, '1:2', header_col_fmt)
        batch.format_cell_range(ws, 'A', header_row_fmt)
        batch.set_row_height(ws, f'3:{edit_row}', 35)
        batch.execute()

        # Set conditional formatting
        cond_fmt_rules = get_conditional_format_rules(ws)
        for val, bg_fmt in bg_fmts.items():
            if val in ('WEEKEND', 'PH'):
                cond = 'TEXT_STARTS_WITH'
            else:
                cond = 'TEXT_CONTAINS'
            cond_fmt_rules.append(
                ConditionalFormatRule(
                    ranges=[GridRange.from_a1_range(f"B:{last_col_letter}", ws)],
                    booleanRule=BooleanRule(
                        condition=BooleanCondition(cond, [val]),
                        format=CellFormat(backgroundColor=bg_fmt)
                    )
                )
            )
        cond_fmt_rules.save()

        added += 1
        last_date = new_date

    print("\nDone.")


def delete_sheets(cred_file, wb_name):
    wb = readSheets.Workbook(cred_file, wb_name)
    sheets = [sheet.title for sheet in wb.all_sheets()]
    print("Which sheet to delete? (Separate with commas to delete more than 1 sheet)")
    for i, sheet in enumerate(sheets):
        print(f"{i + 1}: {sheet}")

    to_delete = None
    while to_delete is None:
        to_delete = input("")
        try:
            to_delete = [int(to_del) for to_del in to_delete.split(',')]
            for to_del in to_delete:
                if not (1 <= to_del <= len(sheets)):
                    raise ValueError
        except (TypeError, ValueError) as e:
            print(f"Input only positive integer numbers!\n{(e)}\n")
            to_delete = None

    for to_del in to_delete:
        print(f"Deleting {sheets[to_del - 1]}")
        wb.delete_sheet(sheets[to_del - 1])

    print("Deleted.")


def main():
    print("What would you like to do?")

    action = None
    while action is None:
        action = input("1: Create new month sheets\n"
                       "2: Delete sheets\n")
        try:
            action = int(action)
            if not 0 < action <= 2:
                raise ValueError
        except (TypeError, ValueError) as e:
            print(f"Input only positive integer numbers!\n{(e)}\n")
            action = None

    if action == 1:
        create_new(CRED_FILE, WORKBOOK_NAME)

    elif action == 2:
        delete_sheets(CRED_FILE, WORKBOOK_NAME)


if __name__ == '__main__':
    main()
