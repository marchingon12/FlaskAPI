from flask import Flask
from bs4 import BeautifulSoup
import requests as r
import constants as url
import datetime


app = Flask(__name__)


@app.route("/")
def index():

    return "Congratulations, it's a web app!"


def get_data():
    """Get folder data in json."""

    if route == "/AuroraStore/Stable/api":
        link = url.STORE_STABLE
    elif route == "/AuroraStore/Nightly/api":
        link = url.STORE_NIGHLY
    elif route == "/AuroraDroid/Stable/api":
        link = url.DROID_STORE
    else:
        link = url.STORE_STABLE

    html_data = r.get(link).text
    soup = BeautifulSoup(html_data, features="html.parser")
    jsondata = [{}]

    for td in soup.find_all("tr"):
        # fb-n: <a href="/AuroraStore/Stable/AuroraStore_x.x.x.apk">AuroraStore_x.x.x.apk</a>
        # fb-d: 2021-01-08 03:36
        version = td.find("td", class_="fb-n")
        date = td.find("td", class_="fb-d")
        if version and date:
            try:
                count += 1
                jsondata = {
                    "id": count,
                    "filename": version.text,
                    "datetime": datetime.datetime.strptime(date.text, "%Y-%m-%d %H:%M"),
                    "downloadUrl": f"{link}{version.text}",
                }
            except ValueError:
                pass
    # latest_date = sorted(jsondata.keys(), reverse=True)[0]
    # latest_version = jsondata[latest_date]

    return jsondata


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
