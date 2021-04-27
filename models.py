import datetime
import json


def get_formatted_date(timestamp):
    date_time = datetime.datetime.fromtimestamp(timestamp)
    return date_time.strftime('%Y-%m-%dT%H:%M:%SZ')


class Build:
    def __init__(self, id, name, tag_name, timestamp, size, md5_hash, sha256_hash, download_url, gitlab_url):
        self.id = id
        self.name = name
        self.tag_name = tag_name
        self.timestamp = int(timestamp * 1000)
        self.datetime = get_formatted_date(timestamp)
        self.size = size
        self.md5_hash = md5_hash
        self.sha256_hash = sha256_hash
        self.download_url = download_url
        self.gitlab_url = gitlab_url

    def __repr__(self):
        return json.dumps({"name": self.name, "timestamp": self.timestamp})

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "tag_name": self.tag_name,
            "timestamp": self.timestamp,
            "datetime": self.datetime,
            "size": self.size,
            "md5": self.md5_hash,
            "sha256": self.sha256_hash,
            "download_url": self.download_url,
            "gitlab_url": self.gitlab_url,
        }
