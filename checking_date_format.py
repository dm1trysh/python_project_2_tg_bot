from datetime import datetime


def check_date_value(date_notify):   # checking whether date is correct or not
    current_date = str(datetime.now().date()).split('-')
    if not(int(date_notify[1]) >= 0 and int(date_notify[1]) <= 12):  # checking month value
        return False
    if date_notify[1] == '02':                                          # if month is February
        if int(date_notify[2]) % 4 != 0:                                # if leap year
            if not(int(date_notify[0]) >= 0 and int(date_notify[0]) <= 28):  # 28 days
                return False
        else:                                                           # if not leap year
            if not(int(date_notify[0]) >= 0 and int(date_notify[0]) <= 29):  # 29 days
                return False
    else:                                                               # not February
        if date_notify[1] == '01' or date_notify[1] == '03' or date_notify[1] == '05' or \
            date_notify[1] == '07' or date_notify[1] == '08' or date_notify[1] == '10' or \
            date_notify[1] == '12':                 # January, March, May, July, August, October, December
            if not(int(date_notify[0]) >= 0 and int(date_notify[0]) <= 31):  # 31 days
                return False
        else:                                                       # April, June, September, November
            if not(int(date_notify[0]) >= 0 and int(date_notify[0]) <= 30):   # 30 days
                return False

    if int(current_date[0]) > int(date_notify[2]):   # checking whether date is bigger than date today or not
        return False
    elif int(current_date[0]) == int(date_notify[2]):
        if int(current_date[1]) > int(date_notify[1]):
            return False
        elif int(current_date[1]) == int(date_notify[1]):
            if int(current_date[2]) > int(date_notify[0]):
                return False
    return True


def check_time_value(time_notify):   # checking whether time is correct or not
    current_time = str(datetime.now().time()).split(':')
    if not(int(time_notify[0]) >= 0 and int(time_notify[0]) <= 23):  # hours in [0:23]
        return False
    if not (int(time_notify[1]) >= 0 and int(time_notify[1]) <= 59):   # minutes in [0:59]
        return False

    if int(current_time[0]) > int(time_notify[0]):   # checking whether time is bigger than time now or not
        return False
    elif int(current_time[0]) == int(time_notify[0]):
        if int(current_time[1]) > int(time_notify[1]):
            return False
    return True


def check_today_schedule_date(date_in_notification):   # checking matching 2 dates for schedule for today
    current_date = str(datetime.now().date()).split('-')
    if int(date_in_notification[2]) == int(current_date[0]) \
            and int(date_in_notification[1]) == int(current_date[1]):
        return True
    return False


def check_whether_date_equals(event_date, event_time):  # checking matching time and date now with time and date
    time_now = str(datetime.now()).split(' ')           # in DB for this event
    current_date = time_now[0].split('-')
    current_time = time_now[1].split(':')
    current_time = current_time[0:2]

    for i in range(len(event_date)):
        if int(event_date[i]) != int(current_date[len(event_date) - 1 - i]):
            return False

    for i in range(len(event_time)):
        if int(event_time[i]) != int(current_time[i]):
            return False

    return True
