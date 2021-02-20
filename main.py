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

    if subpath.startswith("AuroraStore/Stable"):
        link = url.STORE_STABLE
    elif subpath.startswith("AuroraStore/Nightly"):
        link = url.STORE_NIGHLY
    elif subpath.startswith("AuroraDroid/Stable"):
        link = url.DROID_STABLE
    elif subpath.startswith("AuroraDroid/Nightly"):
        link = url.DROID_NIGHTLY
    elif subpath.startswith("Warden/Stable"):
        link = url.WARDEN_STABLE
    elif subpath.startswith("Wallpapers"):
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
        if version and date.text != "":
            try:
                jsondata["data"].append(
                    {
                        "id": f"{count}",
                        "type": "downloads",
                        "name": version.text,
                        "tag_name": version.text.lstrip(
                            "ASDWadeghilnoprstuywv_-"
                        ).rstrip(".apk"),
                        "datetime": date.text,
                        "url": f"{link}api/",
                        "download_url": f"{link}{version.text}",
                    }
                )
                count += 1
            except ValueError:
                return "Unknown error occured"

    return jsondata


@app.route("/<path:subpath>/latest/")
def get_latest(subpath):
    """Get latest version from jsondata"""

    link = ""
    if subpath.startswith("AuroraStore/Stable"):
        link = url.STORE_STABLE
    elif subpath.startswith("AuroraStore/Nightly"):
        link = url.STORE_NIGHLY
    elif subpath.startswith("AuroraDroid/Stable"):
        link = url.DROID_STABLE
    elif subpath.startswith("AuroraDroid/Nightly"):
        link = url.DROID_NIGHTLY
    elif subpath.startswith("Warden"):
        link = url.WARDEN_STABLE
    elif subpath.startswith("Wallpapers"):
        link = url.WALLS_STABLE

    if link == url.STORE_STABLE:
        text = r.get(url.GITHUB_STORE).json()
    elif link == url.DROID_STABLE:
        text = r.get(url.GITHUB_DROID).json()
    else:
        text = {"body": "No changelog available"}

    # search for latest by using id?
    jsondata = get_data(subpath)["data"][-1]

    try:
        return {
            "url": f"{link}api/latest/",
            "name": "",
            "id": "0",
            "tag_name": jsondata["tag_name"],
            "assets": [
                {
                    "id": jsondata["id"],
                    "type": jsondata["type"],
                    "name": jsondata["name"],
                    "datetime": jsondata["datetime"],
                    "download_url": jsondata["download_url"],
                }
            ],
            "body": text["body"],
        }
    except ValueError:
        return {"message": "An error occured!"}


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
                        "name": script.text,
                        "tag_name": script.text.rstrip(".json"),
                        "datetime": datetime.datetime.strptime(
                            date.text, "%Y-%m-%d %H:%M"
                        ),
                        "url": f"{link}api/",
                        "download_url": f"{link}{script.text}",
                    }
                )
                count += 1
            except ValueError:
                pass

    return jsondata


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
