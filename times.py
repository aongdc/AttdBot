"""
Function to simply return required times and time objects from query time.
"""

import datetime

def times(ignore_weekend=False):
    today_obj = datetime.datetime.today()

    if not ignore_weekend:
        today = today_obj.strftime('%d/%m/%Y')
        today_day = today_obj.strftime('%A')
        tomorrow_obj = datetime.datetime.today() + datetime.timedelta(days=1)
        tomorrow = tomorrow_obj.strftime('%d/%m/%Y')
        tomorrow_day = tomorrow_obj.strftime('%A')
        week_day = today_obj.isoweekday()

    else:
        week_day = today_obj.isoweekday()
        if week_day == 6:
            today_obj += datetime.timedelta(days=2)
        elif week_day == 7:
            today_obj += datetime.timedelta(days=1)
        today = today_obj.strftime('%d/%m/%Y')
        today_day = today_obj.strftime('%A')
        tomorrow_obj = today_obj + datetime.timedelta(days=1)
        tomorrow = tomorrow_obj.strftime('%d/%m/%Y')
        tomorrow_day = tomorrow_obj.strftime('%A')
        week_day = today_obj.isoweekday()

    return today_obj, today, today_day, tomorrow_obj, tomorrow, tomorrow_day, week_day
