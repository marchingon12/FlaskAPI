import os

# install the most important stuff
try:
    from flask import Flask
    from flask import jsonify
    from flask_cors import CORS
    from gevent.pywsgi import WSGIServer
except ImportError:
    os.system("pip3 install -r requirements.txt")
    from flask import Flask
    from flask import jsonify
    from flask_cors import CORS
    from gevent.pywsgi import WSGIServer

import json
import re
import requests
import constants

from models import Build

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True
CORS(app)

GITLAB_TOKEN = os.environ.get("API_KEY")


@app.route("/")
def status():
    return "Aurora OSS App distribution API"


@app.route("/<path:sub_path>")
def get_data(sub_path):
    try:
        build_list = get_all_builds(sub_path)
        # Serialize all builds
        build_list_serialized = []
        # if iter(build_list) is True:
        try:
            for build in build_list:
                build_list_serialized.append(build.serialize())
        except TypeError:
            return "Directory is empty"
    except FileNotFoundError:
        return "File or directory not found!"

    return jsonify(build_list_serialized)


@app.route("/<path:subpath>/Latest/")
def get_latest_build(subpath):
    if subpath.startswith("AuroraStore"):
        name = "AuroraStore"
        project_id = constants.AURORA_STORE_ID
    elif subpath.startswith("AuroraDroid"):
        name = "AuroraDroid"
        project_id = constants.AURORA_DROID_ID
    elif subpath.startswith("AuroraWallpaper"):
        name = "AuroraWallpaper"
        project_id = constants.AURORA_WALLPAPER
    elif subpath.startswith("AppWarden"):
        name = "AppWarden"
        project_id = constants.APP_WARDEN
    else:
        return jsonify("Non-existent path!")

    changelog_ = get_changelog(project_id)
    assets = get_local_latest(subpath)

    result = {
        "id": project_id,
        "name": name,
        "changelog": changelog_,
        "assets": [assets],
    }

    return result


def get_changelog(project_id):
    request = requests.get(
        constants.COMMIT_ENDPOINT.format(project_id),
        headers={"PRIVATE-TOKEN": GITLAB_TOKEN},
    )
    result = request.content
    response = json.loads(result)

    changelog = {"general": [], "bugfix": [], "translations": []}

    for node in response:
        title = str(node["title"])
        # Add all commits having keyword `fix` to `bugfixes`
        if re.search("fix", title, re.IGNORECASE):
            changelog["bugfix"].append(title)
        # Add all commits having keyword `Weblate` to `translations`
        elif re.search("Weblate", title, re.IGNORECASE):
            changelog["translations"].append(title)
        # Add otherwise to `general`
        else:
            changelog["general"].append(title)

    # If nothing changed, display appropriate message
    if not changelog["general"]:
        changelog["general"].append("Nothing was changed in general!")
    if not changelog["bugfix"]:
        changelog["bugfix"].append("No bugs were squashed this time!")
    if not changelog["translations"]:
        changelog["translations"].append("No translation updates!")

    # Build a single-line changelog string with bullet points
    body = (
        "### General\r\n- {}\r\n### BugFix\r\n- {}\r\n### Translations\r\n- {}".format(
            "\r\n- ".join(changelog["general"]) + "\r\n",
            "\r\n- ".join(changelog["bugfix"]) + "\r\n",
            "\r\n- ".join(changelog["translations"]) + "\r\n",
        )
    )
    changelog["body"] = body
    return changelog


def get_local_latest(sub_path):
    # Get all available builds
    build_list = get_all_builds(sub_path)
    # Sort builds based on timestamp data
    try:
        build_list.sort(key=lambda x: x.timestamp, reverse=True)
    except AttributeError:
        return f"Assets unavailable - unsortable list detected! Either files are non-existent in directory or files are in wrong path. Check data in parent url: {sub_path}"
    # Return latest serialized build
    return build_list[0].serialize()


def get_all_builds(subpath):
    path = "../h5ai/" + subpath
    build_list = []
    i = 0

    # Iterate through all builds & generate model list
    for filename in os.listdir(path):
        # Filter only APks, least like any other file type will appear, but still
        if filename.endswith(".apk"):
            relative_path = os.path.join(path, filename)
            timestamp = os.path.getmtime(relative_path)
            size = os.path.getsize(relative_path)

            # Parse file as build
            build = Build(
                id=i,
                name=filename,
                tag_name=re.findall("([0-9]+[.]+[0-9]+[.]+[0-9])", filename)[0],
                timestamp=timestamp,
                size=size,
                download_url="{}/{}/{}".format(constants.DL_URL, subpath, filename),
            )

            i = i + 1

            # Add build to available build list
            build_list.append(build)

    if not build_list:
        return jsonify("List is empty!")
    else:
        return build_list


if __name__ == "__main__":
    # app.run(host="0.0.0.0", port=8085, debug=True)
    app.debug = False
    http_server = WSGIServer(("", 8085), app)
    http_server.serve_forever()
    # app.run(host="0.0.0.0", port=5555, debug=False, ssl_context='adhoc')
    # app.run(host="0.0.0.0", port=5555, debug=False, ssl_context=('cert.pem', 'key.pem'))
