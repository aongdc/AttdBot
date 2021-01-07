"""
Define inline keyboard options for each stage here.
Every keyboard defined should be in a list or tuple.
Nested lists are allowed.

*_raw / _* keyboards are each a dict mapping the keyboard text to a callback query code.
This is used for cases where the same keyboard option leads to a different callback stage.

Class for Keyboard is declared here. Used for ease of setting up the InlineKeyboard for each stage.
"""
from _keyboards import *
from times import times
from telegram import InlineKeyboardButton, KeyboardButton

start_admin = start_admin
start_ordinary = start_ordinary
admin_confirmed = admin_confirmed
admin_rejected = admin_rejected

view_basic = "View Next 7 Days", "View Other Date", "<< Back to Main Page", "End Session"
view_basic_2 = "View Other Date", "<< Back to Main Page", "End Session"
view_more = "View Other Date", "<< Back to Main Page", "End Session"

times = times(ignore_weekend=True)
edit_main = f"{times[2]}, {times[1]}", f"{times[5]}, {times[4]}", \
            "More...", "<< Back to Main Page", "End Session"
edit_day = edit_day

_admin_edit_day = admin_edit_day_raw
admin_edit_day = [f"n{x}" for x in [i for i in range(1, len(admin_edit_day_raw)+1)]] + ["Cancel Update"]

edit_back = "<< Back to Main Page", "End Session"

admin_view = ["Report Day", "Report Other Day"], ["Report Week", "Report Other Week"], \
             ["Status Edit Today", "Status Edit Other"], ["Batch Edit Today", "Batch Edit Other"], \
             ["<< Exit Admin"], ["End Session"]

admin_more_day = ["< Previous Day", "Next Day >"], ["Other Date"], ["< Back to Admin"], \
                 ["<< Exit Admin"], ["End Session"]

admin_more_week = ["< Previous Week", "Next Week >"], ["Other Week"], ["< Back to Admin"], \
                  ["<< Exit Admin"], ["End Session"]

admin_edit = admin_edit
for_admin_edit = for_admin_edit
_for_admin_edit = for_admin_edit_raw
admin_back = "< Back to Admin", "<< Exit Admin", "End Session"

end = "/Start Attdbot",


class Keyboard:
    def __init__(self, options, inline=True, for_admin_bat_edit=False, for_admin_edit=False, user_num=None):
        self.options = options
        self.inline = inline
        self.for_admin_bat_edit = for_admin_bat_edit
        self.for_admin_edit = for_admin_edit
        self.user_num = user_num
        self.keyboard = []
        self.fn = InlineKeyboardButton if self.inline else KeyboardButton

    def setup(self):
        i = 0
        j = 0
        while i < len(self.options):
            # or each option -> str or int (or row of options -> list)

            if type(self.options[i]) is list and not self.for_admin_edit:
                # Have to iterate through the elements in the list and append as a sub _keyboard to keyboard
                # Callback data is the same as element text for most cases, except if self.for_admin_bat_edit is True
                _keyboard = []
                for elem in self.options[i]:
                    _keyboard.append(self.fn(f"{elem}",
                                             callback_data=f'{elem if not self.for_admin_bat_edit else [x for y in for_admin_edit for x in y][j]}'))
                    j += 1
                self.keyboard.append(_keyboard)

            elif self.for_admin_edit:
                # Special case for for_admin_edit keyboard callbacks
                _keyboard = []
                for elem in self.options[i]:
                    _keyboard.append(self.fn(f"{elem}",
                                             callback_data=f'{admin_edit_day[j]}, {self.user_num}'))
                    j += 1
                self.keyboard.append(_keyboard)

            else:
                # Simply append appropriately to keyboard
                self.keyboard.append([self.fn(f"{self.options[i]}",
                                              callback_data=f'{self.options[i]}')])

            i += 1

        return self.keyboard
