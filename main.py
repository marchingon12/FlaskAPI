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
                        "name": version.text,
                        "tag_name": version.text.lstrip(
                            "ASDWadeghilnoprstuywv_-"
                        ).rstrip(".apk"),
                        "datetime": datetime.datetime.strptime(
                            date.text, "%Y-%m-%d %H:%M"
                        ),
                        "url": f"{link}api/",
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

    if subpath == "AuroraStore/Stable/api":
        link = url.STORE_STABLE
    elif subpath == "AuroraDroid/Stable/api":
        link = url.DROID_STABLE

    jsondata = get_data(subpath)
    latest_data = {}

    if link == url.STORE_STABLE:
        text = r.get(url.GITHUB_STORE).json()
    elif link == url.DROID_STABLE:
        text = r.get(url.GITHUB_DROID).json()

    # search for latest by using id?
    while f"{jsondata['data']['id']}" != len(jsondata["data"]):
        try:
            latest_data["latest"].append(
                {
                    "id": f"{jsondata['id']}",
                    "type": f"{jsondata['type']}",
                    "name": f"{jsondata['name']}",
                    "tag_name": f"{jsondata['tag_name']}",
                    "datetime": f"{jsondata['datetime']}",
                    "url": f"{subpath}api/latest/",
                    "download_url": f"{jsondata['download_url']}",
                    "body": f"{text['body']}",
                }
            )
        except ValueError:
            pass

    return latest_data


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
