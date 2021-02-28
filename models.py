import datetime
import json


def get_formatted_date(timestamp):
    date_time = datetime.datetime.fromtimestamp(timestamp)
    return date_time.strftime('%d-%m-%Y %H:%M:%S')


class Build:
    def __init__(self, id, name, timestamp, size, download_url):
        self.id = id
        self.name = name
        self.timestamp = timestamp * 1000
        self.datetime = get_formatted_date(timestamp)
        self.size = size
        self.download_url = download_url

    def __repr__(self):
        return json.dumps({"name": self.name, "timestamp": self.timestamp})

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "timestamp": self.timestamp,
            "datetime": self.datetime,
            "size": self.size,
            "download_url": self.download_url,
        }
