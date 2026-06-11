from datetime import date
import hashlib
from pathlib import Path
import re

import requests
from icalendar import Calendar, Event, prop
from lunarcalendar import Converter, Lunar


BASE_DIR = Path(__file__).resolve().parent

APPLE_CN_ICS_PATH = BASE_DIR / "source_ics/apple_cn.ics"
APPLE_US_ICS_PATH = BASE_DIR / "source_ics/apple_us.ics"
CUSTOM_ICS_PATH = BASE_DIR / "custom_ics/apple_supplement.ics"
CUSTOM_ICS_PATH_WITH_ORIGINAL = BASE_DIR / "custom_ics/apple_supplement_with_original.ics"

APPLE_CALENDAR_CN_URL = "https://calendars.icloud.com/holidays/cn_zh.ics"
APPLE_CALENDAR_US_URL = "https://calendars.icloud.com/holidays/us_en-us.ics"

LUNAR_HOLIDAYS = (
    ("龙抬头", 2, 2),
    ("迎财神", 1, 5),
    ("腊八节", 12, 8),
    ("北方小年", 12, 23),
    ("南方小年", 12, 24),
    ("中元节", 7, 15),
)

US_HOLIDAY_TRANSLATIONS = {
    "Valentine’s Day": "情人节",
    "Father’s Day": "父亲节",
    "Mother’s Day": "母亲节",
    "Christmas Eve": "平安夜",
    "Christmas Day": "圣诞节",
    "Halloween": "万圣节",
}


def download_calendar(url, path):
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        file.write(response.text)

    print(f"网页已成功下载并保存为 {path}")


def date_property(value):
    result = prop.vDDDTypes(value)
    result.params["VALUE"] = "DATE"
    return result


def summary_property(value):
    result = prop.vText(value)
    result.params["LANGUAGE"] = "zh_CN"
    return result


def add_common_event_properties(event):
    event.add("DTSTAMP", date_property(date.today()))
    event.add("CLASS", "PUBLIC")
    event.add("TRANSP", "TRANSPARENT")
    event.add("CATEGORIES", "节慶")


def add_uid(event):
    event.add("UID", f"{hashlib.md5(str(event).encode()).hexdigest()}@jayden")


def create_holiday_event(name, start_date):
    event = Event()
    event.add("SUMMARY", summary_property(name))
    event.add("DTSTART", date_property(start_date))
    add_common_event_properties(event)
    add_uid(event)
    return event


def add_event_to_calendars(event, calendars):
    for calendar in calendars:
        calendar.add_component(event)


def create_custom_calendar():
    calendar = Calendar()
    calendar.add("VERSION", "2.0")
    calendar.add("PRODID", "icalendar-ruby")
    calendar.add("CALSCALE", "GREGORIAN")
    calendar.add("X-WR-CALNAME", "中国大陆节假日补充")
    calendar.add("X-APPLE-LANGUAGE", "zh")
    calendar.add("X-APPLE-REGION", "CN")
    return calendar


def add_teachers_day(calendars):
    event = create_holiday_event(
        "教师节",
        date(date.today().year - 5, 9, 10),
    )
    event.add("RRULE", prop.vRecur({"FREQ": "YEARLY", "COUNT": 10}))
    add_event_to_calendars(event, calendars)


def add_lunar_holidays(calendars):
    current_year = date.today().year

    for year in range(current_year - 5, current_year + 5):
        for name, month, day in LUNAR_HOLIDAYS:
            lunar = Lunar(year, month, day, isleap=False)
            solar = Converter.Lunar2Solar(lunar)
            event = create_holiday_event(name, solar.to_date())
            add_event_to_calendars(event, calendars)


def add_us_holidays(calendars):
    with open(APPLE_US_ICS_PATH, "rb") as file:
        apple_us_calendar = Calendar.from_ical(file.read())

    for event in apple_us_calendar.walk("VEVENT"):
        translated_summary = US_HOLIDAY_TRANSLATIONS.get(str(event.get("SUMMARY")))
        if translated_summary is None:
            continue

        event["SUMMARY"] = summary_property(translated_summary)
        event["DTSTAMP"] = date_property(date.today())
        event["CATEGORIES"] = "节慶"

        if "UID" in event:
            del event["UID"]
        if "X-APPLE-UNIVERSAL-ID" in event:
            del event["X-APPLE-UNIVERSAL-ID"]

        event["UID"] = f"{hashlib.md5(str(event).encode()).hexdigest()}@jayden"
        add_event_to_calendars(event, calendars)


def normalize_ical(ical_string):
    return re.sub(
        r"(DTSTAMP;VALUE|SUMMARY;LANGUAGE|DTSTART;VALUE|DTEND;VALUE|RRULE:FREQ):",
        r"\1=",
        ical_string,
    )


def write_calendar(calendar, path):
    ical_string = normalize_ical(calendar.to_ical().decode("utf-8"))
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as file:
        file.write(ical_string.encode("utf-8"))

    print(f"创建新的的 .ics 文件已保存为 {path}")


def main():
    download_calendar(APPLE_CALENDAR_CN_URL, APPLE_CN_ICS_PATH)
    download_calendar(APPLE_CALENDAR_US_URL, APPLE_US_ICS_PATH)

    custom_calendar = create_custom_calendar()
    with open(APPLE_CN_ICS_PATH, "rb") as file:
        custom_calendar_with_original = Calendar.from_ical(file.read())

    calendars = (custom_calendar, custom_calendar_with_original)
    add_teachers_day(calendars)
    add_lunar_holidays(calendars)
    add_us_holidays(calendars)

    write_calendar(custom_calendar, CUSTOM_ICS_PATH)
    write_calendar(custom_calendar_with_original, CUSTOM_ICS_PATH_WITH_ORIGINAL)


if __name__ == "__main__":
    main()
