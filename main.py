from flask import Flask
from bs4 import BeautifulSoup
from markupsafe import escape
import requests as r
import constants as url
import datetime
import json


app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False


@app.route("/<path:subpath>")
def get_data(subpath):
    """Get folder structure data in json."""

    if subpath == "AuroraStore/Stable/api/":
        link = url.STORE_STABLE
    elif subpath == "AuroraStore/Nightly/api/":
        link = url.STORE_NIGHLY
    elif subpath == "AuroraDroid/Stable/api/":
        link = url.DROID_STORE
    else:
        link = url.STORE_STABLE

    html_data = r.get(link).text
    soup = BeautifulSoup(html_data, features="html.parser")
    jsondata = {}
    jsondata.setdefault("data", [])
    count = 0

    for td in soup.find_all("tr"):
        # fb-n: <a href="/AuroraStore/Stable/AuroraStore_x.x.x.apk">AuroraStore_x.x.x.apk</a>
        # fb-d: YYYY-DD-MM HH:MM
        version = td.find("td", class_="fb-n")
        date = td.find("td", class_="fb-d")
        if version and date:
            try:
                jsondata["data"].append(
                    {
                        "id": f"{count}",
                        "filename": version.text,
                        "datetime": date.text,
                        "downloadUrl": f"{link}{version.text}",
                    }
                )
                count += 1
            except ValueError:
                pass

    return jsondata


@app.route("/<path:subpath>/latest/")
def get_latest(subpath):
    """Get latest version from jsondata"""

    jsondata = get_data(subpath)
    latest_data = json.loads(jsondata, sort_keys=True)

    while jsondata != len(jsondata["data"]):
        lastest_version = {
            "id": f"{latest_data['id']}",
            "filename": f"{latest_data['filename']}",
            "datetime": f"{latest_data['datetime']}",
            "downloadUrl": f"{latest_data['downloadUrl']}",
        }

    return lastest_version


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
