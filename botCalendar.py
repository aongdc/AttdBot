"""
Defines a Calendar class from which the InlineKeyboard calendar can be set up.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
import datetime
import calendar


class Calendar:
    def __init__(self,
                 startpoint=datetime.datetime.today(),
                 begin=None,
                 end=None,
                 view_only=False,
                 for_report=False,
                 for_week=False,
                 batch_edit=False,
                 specific_edit=False):

        self.startpoint = startpoint
        self.begin = begin
        self.end = end
        self.view_only = view_only
        self.for_report = for_report
        self.for_week = for_week
        self.batch_edit = batch_edit
        self.specific_edit = specific_edit
        self.today = self.startpoint.strftime('%d/%m/%Y')
        self.year = int(self.startpoint.strftime('%Y'))
        self.month = int(self.startpoint.strftime('%m'))
        self.calendar = []
        self.update = None
        self.context = None
        self.to_ignore = None

    def join_callback(self, action, year, month, day, view_only, for_report, for_week, batch_edit, specific_edit):
        return '~'.join([action, str(year), str(month), str(day), str(view_only),
                         str(for_report), str(for_week), str(batch_edit), str(specific_edit)])

    def segment_callback(self, joined_data):
        return joined_data.split('~')

    def setup(self):
        self.to_ignore = self.join_callback("IGNORE", self.year, self.month, 0,
                                            self.view_only, self.for_report,
                                            self.for_week, self.batch_edit,
                                            self.specific_edit)
        cur_month = InlineKeyboardButton(calendar.month_name[self.month] + " " + str(self.year),
                                         callback_data=self.to_ignore)
        self.calendar.append([cur_month])

        days = []
        for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
            days.append(InlineKeyboardButton(day, callback_data=self.to_ignore))
        self.calendar.append(days)

        month_cal = calendar.monthcalendar(self.year, self.month)
        for week in month_cal:
            weeks = []
            for day in week:
                if day == 0:
                    weeks.append(InlineKeyboardButton(" ", callback_data=self.to_ignore))
                else:
                    weeks.append(InlineKeyboardButton(str(day), callback_data=self.join_callback("DAY",
                                                                                                 self.year,
                                                                                                 self.month,
                                                                                                 day,
                                                                                                 self.view_only,
                                                                                                 self.for_report,
                                                                                                 self.for_week,
                                                                                                 self.batch_edit,
                                                                                                 self.specific_edit)))
            self.calendar.append(weeks)

        tog_previous = InlineKeyboardButton("<", callback_data=self.join_callback("PREV_MONTH",
                                                                                  self.year,
                                                                                  self.month,
                                                                                  1,
                                                                                  self.view_only, self.for_report,
                                                                                  self.for_week, self.batch_edit,
                                                                                  self.specific_edit))

        tog_next = InlineKeyboardButton(">", callback_data=self.join_callback("NEXT_MONTH", self.year, self.month, 1,
                                                                              self.view_only, self.for_report,
                                                                              self.for_week, self.batch_edit,
                                                                              self.specific_edit))

        self.calendar.append([tog_previous, tog_next])

        return InlineKeyboardMarkup(self.calendar)

    def process(self, update, context):
        self.update = update
        self.context = context

        query = self.update.callback_query
        (action, year, month, day,
         self.view_only, self.for_report, self.for_week, self.batch_edit, self.specific_edit) \
            = self.segment_callback(query.data)
        print(action, self.view_only)
        ret = (False, None, self.view_only, self.for_report, self.for_week, self.batch_edit, self.specific_edit)
        cur_date = datetime.datetime(int(year), int(month), 1)

        if action == "IGNORE":
            self.context.bot.answer_callback_query(callback_query_id=query.id)

        elif action == "PREV_MONTH":
            prev = cur_date - datetime.timedelta(days=1)
            self.year = int(prev.year)
            self.month = int(prev.month)
            query.edit_message_text("For which date do you wish to update your status?",
                                    reply_markup=self.setup())

        elif action == "NEXT_MONTH":
            nxt = cur_date + datetime.timedelta(days=31)
            self.year = int(nxt.year)
            self.month = int(nxt.month)
            query.edit_message_text("For which date do you wish to update your status?",
                                    reply_markup=self.setup())

        elif action == "DAY":
            to_date = datetime.datetime(int(year), int(month), int(day)).strftime('%d/%m/%Y')
            ret = True, f"{to_date}", self.view_only, self.for_report, \
                  self.for_week, self.batch_edit, self.specific_edit

        else:
            self.context.bot.answer_callback_query(callback_query_id=query.id, text="Something went wrong!")

        return ret
