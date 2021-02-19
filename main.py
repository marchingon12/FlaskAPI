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
        link = url.DROID_STABLE
    elif subpath == "AuroraDroid/Nightly/api/":
        link = url.DROID_NIGHTLY
    elif subpath == "Warden/Stable/api/":
        link = url.WARDEN_STABLE
    elif subpath == "Wallpapers/Stable/api/":
        link = url.WALLS_STABLE
    else:
        return "Unknown path"

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
                        "type": "downloads",
                        "filename": version.text,
                        "tag_name": version.text.lstrip("ASDadeghilnorstuy_-").rstrip(
                            ".apk"
                        ),
                        "datetime": datetime.datetime.strptime(
                            date.text, "%Y-%m-%d %H:%M"
                        ),
                        "download_url": f"{link}{version.text}",
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

    # search for latest by using id?
    while jsondata["id"]["data"] != len(jsondata["data"]):
        try:
            lastest_version = {
                "id": f"{latest_data['id']}",
                "type": f"{latest_data['type']}",
                "filename": f"{latest_data['filename']}",
                "tag_name": f"{latest_data['tag_name']}",
                "datetime": f"{latest_data['datetime']}",
                "download_url": f"{latest_data['download_url']}",
            }
        except ValueError:
            pass

    return lastest_version


@app.route("/Warden/Scripts/api/")
def get_scripts():
    """Get Warden scripts"""

    link = url.WARDEN_SCRIPTS
    html_data = r.get(link).text
    soup = BeautifulSoup(html_data, features="html.parser")
    jsondata = {}
    jsondata.setdefault("data", [])
    count = 0

    for td in soup.find_all("tr"):
        # fb-n: <a href="/Warden/Scripts/-.json">-.json</a>
        # fb-d: YYYY-DD-MM HH:MM
        script = td.find("td", class_="fb-n")
        date = td.find("td", class_="fb-d")
        if script and date:
            try:
                jsondata["data"].append(
                    {
                        "id": f"{count}",
                        "type": "scripts",
                        "filename": script.text,
                        "tag_name": script.text.rstrip(".json"),
                        "datetime": datetime.datetime.strptime(
                            date.text, "%Y-%m-%d %H:%M"
                        ),
                        "download_url": f"{link}{script.text}",
                    }
                )
                count += 1
            except ValueError:
                pass

    return jsondata


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
