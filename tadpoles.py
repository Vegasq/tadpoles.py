import os
import requests
import json
import datetime


start_year = 2019
end_year = 2024


cookie = """"""  # <- Cookie header value
email = ""  # <- X-TADPOLES-UID header value


def get_headers():
    return {"cookie": cookie, "x-tadpoles-uid": email}


def mime_to_extension(mime_type: str) -> str:
    file_ext = ".jpg"
    if mime_type == "image/jpeg":
        file_ext = ".jpg"
    elif mime_type == "video/mp4":
        file_ext = ".mp4"
    elif mime_type == "application/pdf":
        file_ext = ".pdf"
    elif mime_type == "image/png":
        file_ext = ".png"
    return file_ext


def generate_dates(year_from: int, year_to: int) -> list[list[str]]:
    start_date = datetime.datetime(year_from, 1, 1)
    end_date = datetime.datetime(year_to + 1, 1, 1)
    dates = []

    while start_date < end_date:
        next_month = start_date + datetime.timedelta(days=32)  # Going safely into the next month
        first_of_next_month = datetime.datetime(next_month.year, next_month.month, 1)

        dates.append([start_date.strftime("%Y-%m-%d"), first_of_next_month.strftime("%Y-%m-%d")])

        start_date = first_of_next_month

    return dates


def get_events(start_date, end_date):
    # Convert to timestamp
    start_date_timestamp = int(datetime.datetime.strptime(start_date, "%Y-%m-%d").timestamp())
    end_date_timestamp = int(datetime.datetime.strptime(end_date, "%Y-%m-%d").timestamp())

    # Download all the events for this period
    url = f"https://www.tadpoles.com/remote/v1/events?direction=range&earliest_event_time={start_date_timestamp}&"\
          f"latest_event_time={end_date_timestamp}&num_events=300&client=dashboard"
    response = requests.get(url, headers=get_headers())
    events_data = json.loads(response.text)

    output_data = []
    for event in events_data.get("events", []):
        for attachment in event.get("new_attachments", []):
            output_data.append({
                "event_date": event["event_date"],
                "key": attachment["key"],
                "mime_type": attachment["mime_type"]
            })

    return output_data


def download_event(event, index, download_location):
    year_month = event['event_date'][:-3]
    path = os.path.join(download_location, year_month)
    os.makedirs(path, exist_ok=True)
    key = event['key']

    file_ext = mime_to_extension(event['mime_type'])
    filename = os.path.join(path, f"tadpoles_{key}_{index}{file_ext}")
    if not os.path.exists(filename):
        download_url = f"https://www.tadpoles.com/remote/v1/attachment?key={key}"
        response = requests.get(download_url, headers=get_headers(), stream=True)
        with open(filename, 'wb') as f_out:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f_out.write(chunk)


def download_images(download_location: str, start_date: str, end_date: str):
    tp_events = get_events(start_date, end_date)
    for index, data in enumerate(tp_events):
        download_event(data, index, download_location)


def main():
    download_location = "images"

    for start_date, end_date in generate_dates(start_year, end_year):
        print(f"Retrieving images between {start_date} and {end_date}")
        download_images(download_location, start_date, end_date)


if __name__ == "__main__":
    main()
