from datetime import datetime
import lightbulb

plugin = lightbulb.Plugin(__name__)

def validate_deadline(deadline_date: str = None, deadline_hmp: str = None):
    """
    Validates if a string is good to be converted to a datetime object.
    Returns a datetime object based on the strings if it is
    :param deadline_date:
    :param deadline_hmp:
    :return: datetime object
    :return: string detailing error on a bad parsing
    """
    deadline_hmp_obj = None
    deadline_date_obj = None

    if deadline_hmp is not None:
        time_set = str(deadline_hmp[:-3]).replace(':', '')
        if not time_set.isnumeric() or len(time_set) != 4:
            return "Please enter a valid time in the format: HH:MM AM/PM, eg: 05:30 PM"
        elif " " not in deadline_hmp:
            return "There must be a space in-between HH:MM and AM/PM. Eg: 05:30 PM"
        elif not deadline_hmp[-2:].lower() in ['am', 'pm']:
            return "You did not enter AM or PM. Please use this example: 05:30 PM"
        elif not deadline_hmp[:-3].replace(':', '').isnumeric():
            return "Please enter a valid time in the format: HH:MM AM/PM, eg: 05:30 PM"
        elif int(time_set) > 1259 or int(time_set) < 100:
            return "The range for the time is between 01:00 AM and 12:59 PM. Please enter a valid time."
        deadline_hmp_obj = datetime.strptime(deadline_hmp, "%I:%M %p")

    if deadline_date is not None:
        date_set = deadline_date.replace('/', '')
        if not date_set.isnumeric():
            return "Please enter a valid date in the format: DD/MM/YYYY, eg 05/11/2025"
        elif len(date_set) != 8:
            return "Please enter a valid date in the format: DD/MM/YYYY, eg 05/11/2025"
        elif str(date_set)[:2] not in [
            "01", "02", "03", "04", "05", "06", "07", "08", "09", "10",
            "11", "12", "13", "14", "15", "16", "17", "18", "19", "20",
            "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31"
        ]:
            return f"Please enter a valid day between 01 and 31. You entered, {str(date_set)[:2]}"
        elif str(date_set)[2:4] not in ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]:
            return f"Please enter a valid month between 01 and 12. You entered, {str(date_set)[2:4]}"
        deadline_date_obj = datetime.strptime(deadline_date, "%d/%m/%Y")

    if deadline_hmp_obj and deadline_date_obj:
        deadline_obj = deadline_date_obj.replace(hour=deadline_hmp_obj.hour, minute=deadline_hmp_obj.minute, second=deadline_hmp_obj.second)
    elif deadline_date_obj:
        deadline_obj = deadline_date_obj
    elif deadline_hmp_obj:
        return "Please enter a date to go with the time."
    else:
        deadline_obj = None

    return deadline_obj

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
