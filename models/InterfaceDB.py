import json
from datetime import datetime
import os
from pathlib import Path

from . import RedditAPI
from .DB import DB
from .config import SAVES_JSON_PATH, SAVES_SYNC_PATH, CONFIG_PATH, JSON_DIR
from .dbconfig import database, user, password, host, port


class InterfaceDB:
    def __init__(self):
        self.db = None

    def connect(self):
        self.db = DB(database=database, user=user,
                     password=password, host=host, port=port)

    def close(self):
        self.db.close()
        self.db = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

    def getParams(self, res):
        kind = res["kind"]
        res = res["data"]

        result = dict()
        params = dict()
        result["saves"] = params
        params["name_id"] = res["id"]
        params["kind"] = kind
        params["link_title"] = res["title"] if kind == "t3" else res["link_title"]
        params["link_permalink"] = res["permalink"] if kind == "t3" else res["link_permalink"]
        params["author"] = res["author"]
        params["subreddit"] = res["subreddit"]
        params["score_hidden"] = res["hide_score"] if kind == "t3" else res["score_hidden"]
        params["score"] = res["score"]
        params["created_utc"] = datetime.utcfromtimestamp(
            int(res["created_utc"])).isoformat()
        params["over_18"] = res["over_18"]

        params = dict()
        result["links"] = params

        if kind == "t3":
            params["link_id"] = res["id"]
            params["domain"] = res["domain"]
            params["link_url"] = res["url"]
            params["is_self"] = res["is_self"]
            if "selftext" in res and res["selftext"]:
                params["selftext"] = res["selftext"]
            if "selftext_html" in res and res["selftext_html"]:
                params["selftext_html"] = res["selftext_html"]
            params["num_comments"] = res["num_comments"]
            params["is_video"] = res["is_video"]
            if "post_hint" in res and res["post_hint"]:
                params["post_hint"] = res["post_hint"]
            if "thumbnail" in res and res["thumbnail"]:
                params["thumbnail"] = json.dumps(res["thumbnail"])
            if "media" in res and res["media"]:
                params["media"] = json.dumps(res["media"])
            if "media_embed" in res and res["media_embed"]:
                params["media_embed"] = json.dumps(res["media_embed"])
            if "preview" in res and res["preview"]:
                params["preview"] = json.dumps(res["preview"])

        params = dict()
        result["comments"] = params

        if kind == "t1":
            params["body_html"] = res["body_html"]
            params["link_id"] = res["link_id"]
            params["comment_id"] = res["id"]

        return result

    def addListings(self, user_id, listings):
        for listing in reversed(listings):
            children = listing["data"]["children"]
            for child in reversed(children):
                save_params = self.getParams(child)

                # print(save_params["saves"]["link_title"])
                # unique key for save
                self.addSave(user_id, save_params)

    def getJsonList(self, path):
        return (x for x in os.listdir(path)[::-1] if x.endswith('.json'))

    def addSave(self, user_id, params):

        unique_key = {
            "name_id": params["saves"]["name_id"],
            "kind": params["saves"]["kind"]
        }

        save_id = str()

        if not self.db.recordExists("saves", unique_key):
            save_id = self.db.insert("saves", params["saves"], returning=True)
            kind = params["saves"]["kind"]

            table_type = str()

            if(kind == "t3"):
                table_type = "links"
                params[table_type]["save_id"] = save_id

            elif(kind == "t1"):
                table_type = "comments"
                params[table_type]["save_id"] = save_id

            self.db.insert(table_type, params[table_type])

        else:
            save_id = self.db.getID("saves", unique_key)

        unique_key = {"user_id": user_id, "save_id": save_id, "saved": True}

        if self.db.recordExists("user_saves", unique_key):
            # print("Already exists. Skipping...", end="\n\n")
            pass
        else:
            self.db.insert("user_saves", unique_key)

    def addDownloadedListings(self, user_id, path=SAVES_JSON_PATH, persist=True):

        assert(path == SAVES_SYNC_PATH or (path == SAVES_JSON_PATH and persist ==
                                           False)), f"Cannot remove files from {JSON_DIR}"

        base = Path(path)

        listings = list()
        for file in self.getJsonList(path):
            base_file = base / file
            with base_file.open('r') as f:
                listings.append(json.load(f))
            if not persist:
                base_file.remove()
        self.addListings(user_id, listings)

    def sync(self, reddit, limit=50, path=SAVES_SYNC_PATH, persist=False):
        user = reddit.username

        user_id = self.getUserID(user)

        assert(user_id != None), "User does not exist"

        if persist:
            self.downloaded_files = reddit.download_saved(
                limit=limit, path=path)
            self.addDownloadedListings(user_id, path=path, persist=persist)

        else:
            listings = list()
            if limit <= 100:
                listings = [reddit.get_saved(limit=limit)]
            else:
                listings = reddit.download_saved(limit=limit, path=path)
            self.addListings(user_id, listings)

    def userExists(self, user):
        table = "users"
        params = {"username": user}
        return self.db.recordExists(table, params)

    def getUserID(self, user):
        table = "users"
        params = {"username": user}
        return self.db.getID(table, params)

    def addUser(self, user):
        table = "users"
        params = {"username": user}
        user_id = self.db.insert(table, params, returning=True)
        return user_id

    def get_saves(self, user, offset=0, limit=50, filters={}):
        print(filters)
        return self.db.selectUserSaves(user, offset=offset, limit=limit, filters=filters)

    def add_tag(self, user, tag_name):
        table = "tags"
        params = {"tag_name":tag_name}
        self.db.insert(table,params)
