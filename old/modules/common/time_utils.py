import datetime


def get_timestamp_iso_utc_now() -> str:
    return datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()
