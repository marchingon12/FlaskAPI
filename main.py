import json
import os
import re

import requests
from flask import Flask
from flask import jsonify
from flask_cors import CORS

import constants
from models import Build

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
CORS(app)

gitlab_token = "API_KEY_GOES_HERE"


@app.route("/")
def status():
    return "Aurora OSS App distribution API"


@app.route("/<path:sub_path>")
def get_data(sub_path):
    build_list = get_all_builds(sub_path)
    # Serialize all builds
    build_list_serialized = []
    for build in build_list:
        build_list_serialized.append(build.serialize())

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
        return jsonify("Hupp!'}")

    changelog_ = get_changelog(project_id)
    asset = get_local_latest(subpath)

    result = {
        "id": project_id,
        "name": name,
        "changelog": changelog_,
        "asset": asset
    }

    return result


def get_changelog(project_id):
    request = requests.get(constants.COMMIT_ENDPOINT.format(project_id),
                           headers={"PRIVATE-TOKEN": gitlab_token})
    result = request.content
    response = json.loads(result)

    changelog = {
        "general": [],
        "bugfix": [],
        "translations": []
    }

    for node in response:
        title = str(node["title"])
        # Add all commits having keyword `fix` to `bugfixes`
        if re.search("fix", title, re.IGNORECASE):
            changelog["bugfix"].append(title)
        # Add all commits having keyword `POEditor` to `translations`
        elif re.search("POEditor.com", title, re.IGNORECASE):
            changelog["translations"].append(title)
        # Add otherwise to `general`
        else:
            changelog["general"].append(title)

    # Build a single-line changelog string
    body = "### General\r\n{}### BugFix\r\n{}### Translations{}".format(" * ".join(changelog["general"]),
                                                                        " * ".join(changelog["bugfix"]),
                                                                        " * ".join(changelog["translations"]))
    changelog["body"] = body

    return changelog


def get_local_latest(sub_path):
    # Get all available builds
    build_list = get_all_builds(sub_path)
    # Sort builds based on timestamp data
    build_list.sort(key=lambda x: x.timestamp, reverse=True)
    # Return latest serialized build
    return build_list[0].serialize()


def get_all_builds(subpath):
    path = "../www/" + subpath
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
                timestamp=timestamp,
                size=size,
                download_url="{}/{}/{}".format(constants.BASE_URL, subpath, filename)
            )

            i = i + 1

            # Add build to available build list
            build_list.append(build)

    return build_list


if __name__ == "__main__":
    # app.run()
    # app.run(host="0.0.0.0", port=5555, debug=False, ssl_context='adhoc')
    app.run(host="0.0.0.0", port=5555, debug=False, ssl_context=('cert.pem', 'key.pem'))
