import os
import json
import re
import hashlib

"""
Import required modules otherwise install them using requirements.txt
"""
try:
    from flask import Flask
    from flask import jsonify
    from flask import abort
    from flask import redirect
    from flask import request
    from flask import url_for
    from flask_cors import CORS
    import requests
except ImportError:
    os.system("pip3 install -r requirements.txt")
    from flask import Flask
    from flask import jsonify
    from flask import abort
    from flask import redirect
    from flask import request
    from flask import url_for
    from flask_cors import CORS
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


#####################
#   Get Data List   #
#####################


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
        abort(404)

    return jsonify(build_list_serialized)


######################
#  Get Latest Build  #
######################


@app.route("/<path:subpath>/Latest/")
def get_latest_build(subpath):
    if subpath.startswith("AuroraStore"):
        name = "AuroraStore"
        project_id = constants.AURORA_STORE_ID
    elif subpath.startswith("AuroraDroid"):
        name = "AuroraDroid"
        project_id = constants.AURORA_DROID_ID
    elif subpath.startswith("Wallpapers"):
        name = "Wallpapers"
        project_id = constants.AURORA_WALLPAPER
    elif subpath.startswith("Warden"):
        name = "Warden"
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


"""
Get the changelog for each corresponding Aurora app from Gitlab releases.
"""


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


"""
Get the latest builds for corresponding Aurora app and show them in a list.
"""


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

            # Remove letter chars for tag names
            if path.endswith("Nightly"):
                tag = re.sub("[^0-9]", "", filename)
            else:
                tag = re.search("_(.*).apk", filename)[1]

            # Calculate hashes
            md5 = hasher("md5", filename, path)
            sha256 = hasher("sha256", filename, path)

            # Parse file as build
            build = Build(
                id=i,
                name=filename,
                tag_name=tag,
                timestamp=timestamp,
                size=size,
                md5_hash=md5,
                sha256_hash=sha256,
                download_url="{}/{}/{}".format(constants.DL_URL, subpath, filename),
            )

            i = i + 1

            # Add build to available build list
            build_list.append(build)

    if not build_list:
        return jsonify("List is empty!")
    else:
        return build_list


"""
Simple hashing digest for apk files. This is provided to verify if the files provided are legitimate or not.
"""


def hasher(algorithm, filename, path):

    apk_file = open(f"{path}/{filename}", "rb")

    if algorithm == "md5":
        md5_hash = hashlib.md5()
        content = apk_file.read()
        md5_hash.update(content)
        md5 = md5_hash.hexdigest()
        return md5

    if algorithm == "sha256":
        sha256_hash = hashlib.sha256()
        content = apk_file.read()
        sha256_hash.update(content)
        sha256 = sha256_hash.hexdigest()
        return sha256


#####################
#    Error Routes   #
#####################


@app.errorhandler(500)
def server_error(e):
    app.logger.error(f"Server error: {e}, route: {request.url}")
    return redirect("/", code=301)


@app.errorhandler(404)
def file_error(e):
    app.logger.error(f"Server error: {e}, route: {request.url}")
    return redirect("/", code=301)


@app.errorhandler(403)
def forbidden_error(e):
    app.logger.error(f"Server error: {e}, route: {request.url}")
    return redirect("/", code=301)


######################
#  Error Simulation  #
######################


# @app.route("/simulate500")
# def simulate500():
#     abort(500)


# @app.route("/simulate404")
# def simulate404():
#     abort(404)


# @app.route("/simulate403")
# def simulate403():
#     abort(403)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8085, debug=False)
    # app.run(host="127.0.0.1", port=8085, debug=False, ssl_context='adhoc')
    # app.run(host="127.0.0.1", port=8085, debug=False, ssl_context=('cert.pem', 'key.pem'))
