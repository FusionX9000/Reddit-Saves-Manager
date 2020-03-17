import requests
from urllib.parse import urlencode

import uuid
from flask import Flask, render_template, request, redirect, url_for, current_app
from flask_cors import CORS

from config import GRANT_TYPE, SCOPE_STRING, DURATION, RESPONSE_TYPE, AUTH_ENDPOINT, TOKEN_ENDPOINT
from instance.config import CLIENT_ID, CLIENT_SECRET, URI, USER_AGENT
from models import RedditAPI
from models.InterfaceDB import InterfaceDB

app = Flask(__name__)

cors = CORS(app)

PLACEHOLDER_USERNAME = "username"

@app.route('/login')
def login():
    auth_url = make_auth_url()
    return redirect(auth_url)


@app.route("/")
def home():
    return render_template("index.html")


def make_auth_url():
    random_string = str(uuid.uuid4())
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": URI,
        "scope": SCOPE_STRING,
        "response_type": RESPONSE_TYPE,
        "duration": DURATION,
        "state": random_string
    }
    auth_url = f"{AUTH_ENDPOINT}?{urlencode(params)}"
    return auth_url


@app.route('/authorize_callback')
def reddit_callback():
    state = request.args.get("state")
    code = request.args.get("code")
    token = get_token(code)
    print(token)
    return redirect("/sync?token={}".format(token["access_token"]))


@app.route('/sync')
def sync():
    token = request.args.get("token")
    reddit = RedditAPI.Reddit(USER_AGENT, access_token=token)
    user = reddit.username
    with InterfaceDB() as idb:
        if not idb.userExists(user):
            idb.addUser(user)
        idb.sync(reddit, limit=1000)
    return redirect(f"/?token={token}")


def get_token(code):
    client_auth = (CLIENT_ID, CLIENT_SECRET)
    post_data = {
        "grant_type": GRANT_TYPE,
        "code": code,
        "redirect_uri": URI
    }
    response = requests.post(TOKEN_ENDPOINT, auth=client_auth,
                             data=post_data, headers={"User-Agent": USER_AGENT})
    return response.json()


@app.route("/api/get_saved")
def get_saved():
    filters = dict()
    user = request.args.get("user")
    if not user:
        return {}

    offset = request.args.get("offset")
    if not offset:
        offset = 0
    limit = request.args.get("limit")
    if limit:
        limit = min(int(limit), 100)
    else:
        limit = 50

    filters["search"] = request.args.get("search")
    filters["tags"] = request.args.get("tags")
    filters["save_type"] = request.args.get("save-type")
    filters["subreddit"] = request.args.get("subreddit")
    if filters["subreddit"]:
        filters["subreddit"] = [x.strip().lower()
                                for x in filters["subreddit"].split(",")]

    with InterfaceDB() as idb:
        saves = idb.get_saves(
            user, offset=offset, limit=limit, filters=filters)
        res = {"children": saves[0],
               "count": saves[1]}
    return res

@app.route("/api/add_tag", methods=['POST'])
def add_tag():
    print(request.form)
    tagName = request.form.get("tag-name")
    print(tagName)
    with InterfaceDB() as idb:
        idb.add_tag(PLACEHOLDER_USERNAME,tagName)
    return ('',204)


if __name__ == "__main__":
    app.run("localhost", port=8080, debug=True)