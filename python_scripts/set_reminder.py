#------------------------------------------------------------------------------
# Set / update reminder sensor
#
# Data:
#   name: Sensor name (required)
#   icon_on: Remidner icon on state (optional, default mdi:calendar-alerrt)
#   icon_off: Remidner icon off state (optional, default mdi:calendar-star)
#   date: Reminder date time D/M/Y-H:M (required, time is optional)
#   title: Reminder title (optional)
#   recurrence: yearly, montly, daily, does not repeat (optional, default 'yearly')
#   every:
#   tag: (optional, default 'reminder')
#   notifier: (optional)
#   script: (optional)
#   message: (optional)
#   enable: Enable /disable the reminder (optional, default on)
#------------------------------------------------------------------------------

# Reminder name
name = data.get('name').replace(" ", "_")
# Icons
icon_off = data.get("icon_off", "mdi:calendar-star")
icon_on = data.get("icon_on", "mdi:calendar-alert")
# Days before to notify (not functional yet)
days_notice = data.get('days_notice', 0)
# Reminder recurrence
recurrence = data.get('recurrence', 'yearly').lower()
# Reminder duration in minutes. The time the reminder will be in 'on' state
duration = data.get('duration', 0)
# Reminder title (will be sensor friendly_name)
title = data.get('title', 'Reminder')
# Reminder tag
tag = data.get('tag', 'reminder')
# Every (recurrence every)
every = int(data.get('every', 1))
# Reminder action (notify / script)
notifier = data.get('notifier')
script = data.get('script')
# Action message
message = data.get('message', title)
# Split to date and time (input date should be in format: YYYY-MM-DD H:M)
date_time = data.get('date').split(' ')
# Enabled / disabled
enable = data.get('enable', 'on')

# Sensor name derived from name
sensor_name = "sensor.{}".format(name)

# Default values
new_state = 'off'
friendly_date = "-\-\-"
remaining = 0
remaining_days = 0
remaining_hours = 0
remaining_minutes = 0
remaining_seconds = 0

# Convert the date
date_split = date_time[0].split("-")
date_year = int(date_split[0])
date_month = int(date_split[1])
date_day = int(date_split[2])

# Check if time was specified
if len(date_time) == 2:
    all_day = False
    time_split = date_time[1].split(":")
    time_hour = int(time_split[0])
    time_minute = int(time_split[1])
else:
    all_day = True
    time_hour = 0
    time_minute = 0

# Helper function
def datebuild(year, month, day, hour = 8, minute = 0, offset = 0):
    date_str = "{}-{}-{} {}:{}".format(
        str(year), str(month), str(day),
        str(hour), str(minute),
    )
    return datetime.datetime.strptime(
        date_str, "%Y-%m-%d %H:%M"
    ) + datetime.timedelta(-offset)

# Helper function
def dateadd(t1, n, type):
    if type == 'yearly':
        t = t1.replace(t1.year + n)
    elif type == 'monthly':
        t = t1
        while n > 0:
            month = t.month + 1
            year = t.year
            if month > 12:
                month = 1
                year = year + 1
            t = t.replace(year=year, month=month)
            n = n - 1
    elif type == 'daily':
        t = t1 + datetime.timedelta(days=n)
    elif type == 'weekly':
        t = t1 + datetime.timedelta(days=7*n)
    else:
        logger.error("{} not supported".format(type))
    return t

# Helper function - diff in recurrence units
def datediff(t1, t2, type):
    diff = 0
    if t1 > t2:
        t1, t2 = t2, t1
    if type == 'monthly':
        while t1 < t2:
            month = t1.month + 1
            year = t1.year
            if month > 12:
                month = 1
                year = year + 1
            t1 = t1.replace(year=year, month=month)
            diff = diff + 1
    elif type == 'weekly':
        diff = int(((t2 - t1).days + 7) / 7)
    elif type == 'yearly':
        diff = t2.year - t1.year
        if t1.replace(t1.year + diff) < t2:
            diff = diff + 1
    elif type == 'daily':
        diff = (t2 - t1).days + 1
    else:
        logger.error("{} not supported".format(type))
    return diff

def datenext(t1, t2, n, type):
    diff = None
    if type == 'does not repeat':
        return None, diff
    if t1 < t2:
        diff = datediff(t1, t2, type)
        return dateadd(t1, int(n * (int((diff / n)) + (1 if (diff % n) else 0))), type), diff
    return t1, diff

# Reference date / time for reminder check (for now using sensor date time until
# the issue with datetime returning utc will be solved)
# calc_date = datetime.datetime.strptime(hass.states.get('sensor.date_time').state, "%Y-%m-%d, %H:%M")
calc_date = datetime.datetime.now().replace(second=0, microsecond=0)

# The remidner date set by user
set_date = datebuild(date_year, date_month, date_day, time_hour, time_minute)

# Reminder date this year (exclude if no reminder is no repeat)
if recurrence == 'yearly':
    reminder_date = datebuild(
        calc_date.year, date_month, date_day,
        time_hour, time_minute,
        days_notice
    )
elif recurrence == 'monthly':
    reminder_date = datebuild(
        calc_date.year, calc_date.month, date_day,
        time_hour, time_minute,
        days_notice
    )
elif recurrence == 'weekly':
    reminder_date = datebuild(
        date_year, date_month, date_day,
        time_hour, time_minute,
        days_notice
    )
elif recurrence == 'daily':
    reminder_date = datebuild(
        calc_date.year, calc_date.month, calc_date.day,
        time_hour, time_minute,
        days_notice
    )
elif recurrence == 'does not repeat':
    reminder_date = datebuild(
        date_year, date_month, date_day,
        time_hour, time_minute,
        days_notice
    )

# Next reminder
next_date, diff_date = datenext(set_date, calc_date, every, recurrence)

# sensor current state
current_state = hass.states.get(sensor_name).state

# Start / end of reference date
calc_date_start = calc_date.replace(hour=0, minute=0, second=0, microsecond=0)
calc_date_midnight = calc_date.replace(hour=23, minute=59, second=59, microsecond=0)
if duration == 0:
    calc_date_end = calc_date_midnight
else:
    calc_date_end = reminder_date + datetime.timedelta(minutes=duration)
    # By the end of the day we turn off all reminders
    if calc_date_end > calc_date_midnight:
        calc_date_end = calc_date_midnight

# Sensor new state.
if enable == 'on':
    # The first date the user set must be before the current date (otherwise first
    # reminder is in the future).
    if set_date < calc_date:
        # We check that every has being fullfiled
        if diff_date and (((diff_date - 1) % every) == 0):
            if calc_date_start <= reminder_date <= calc_date_end:
                if reminder_date <= calc_date <= calc_date_end:
                    new_state = 'on'

# Remaining days to next occurence
if next_date and new_state == 'off':
    delta = next_date - calc_date
    remaining_days = delta.days
    remaining_hours = int(delta.seconds / (60 * 60))
    remaining_minutes = int((delta.seconds - (remaining_hours * (60 * 60))) / 60)
    remaining_seconds = remaining_days * 60 * 60 * 24 + remaining_hours * 60 * 60 + remaining_minutes * 60
    if remaining_days > 0:
        remaining = remaining_days
    else:
        remaining = "{:02d}:{:02d}".format(remaining_hours, remaining_minutes)

# Format friendly next reminder date
if next_date:
    if all_day:
        date_time = "{:04d}-{:02d}-{:02d}".format(
            next_date.year, next_date.month, next_date.day)
    else:
        date_time = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}".format(
            next_date.year, next_date.month, next_date.day, next_date.hour, next_date.minute)

# Send the sensor to homeassistant
hass.states.set(sensor_name, new_state,
    {
        "icon" : icon_off if new_state == 'off' else icon_on,
        "friendly_name" : "{}".format(title),
        "next": date_time,
        "remaining": remaining,
        "days": remaining_days,
        "seconds": remaining_seconds,
        "enable": enable,
        "tag": tag
    }
)

# Actions
if new_state == 'on' and current_state == 'off':
    if notifier:
        hass.services.call('notify', notifier,
            {
                "title": "Reminder",
                "message": message
            }
        )
    if script:
        hass.services.call('script', script,
            {
                "message": message
            }
        )

# For debugging
# logger.warn("Reminder current:{} new:{} set:{} reminder:{} next:{} calc:{} start:{} end:{} diff:{} remaining:{} now:{}".format(
#     current_state, new_state, set_date, reminder_date, next_date,
#     calc_date, calc_date_start, calc_date_end, diff_date, remaining_time,
#     datetime.datetime.now())
#     )
