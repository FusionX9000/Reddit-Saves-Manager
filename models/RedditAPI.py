import requests
import json
import pathlib
from .config import NOAUTH_URL, AUTH_URL, ACCESS_TOKEN_ENDPOINT, SAVES_JSON_PATH, CONFIG_PATH

# scope = "identity  edit  flair  history  modconfig  modflair  modlog  modposts  modwiki  mysubreddits  privatemessages  read  report  save  submit  subscribe  vote  wikiedit  wikiread"


class Reddit():

    url = NOAUTH_URL
    username = None

    def __init__(self, userAgent, config=None, access_token=None):
        self.session = requests.Session()

        self.config = config
        self.userAgent = userAgent
        self.access_token = access_token

        self.updateHeader({'User-Agent': self.userAgent})

        if(config != None):
            self.access_token = self.getAccessToken(self.config)

        if(self.isAuthenticated()):
            self.updateAccessToken(self.access_token)
            self.url = AUTH_URL
            self.username = self.getUsername()

    def getAccessToken(self, config):
        username = config["user-config"]["username"]
        password = config["user-config"]["password"]
        client_id = config["client-config"]["client-id"]
        client_secret = config["client-config"]["client-secret"]

        url = ACCESS_TOKEN_ENDPOINT

        params = {
            "grant_type": "password",
            "username": username,
            "password": password,
        }

        auth = (client_id, client_secret)
        access_token = self.session.post(url, params=params, auth=auth)

        assert (access_token.status_code == 200), "Invalid details"
        print(access_token.json())
        return access_token.json()["access_token"]

    def updateAccessToken(self, access_token):
        auth_header = {"Authorization": "bearer %s" %
                       access_token}
        self.session.headers.update(auth_header)

    def updateHeader(self, headers):
        self.session.headers.update(headers)

    def isAuthenticated(self):
        return self.access_token != None

    def getUsername(self):
        assert(self.isAuthenticated()), "OAuth needed"
        url_api = "/api/v1/me"
        return self.request_api(url_api).json()["name"]

    def request_api(self, url_api, params={}, method="GET"):
        if not url_api.startswith('/'):
            url_api = '/'+url_api
        params['raw_json'] = 1
        url_to = "%s%s" % (self.url, url_api)
        if method == "GET":
            result = self.session.get(
                url_to, params=params)
        else:
            result = self.session.post(
                url_to, params=params)

        assert (result.status_code ==
                200), "Invalid details, %s" % result.json()

        return result

    def get_saved(self, params={}, limit=25):
        assert(self.isAuthenticated()), "OAuth needed"

        if "limit" not in params:
            params["limit"] = limit

        url_api = '/user/%s/saved' % self.username
        result = self.request_api(url_api, params)

        # check if call was successful
        assert (result.status_code == 200), result

        return result.json()

    def download_saved(self, count=0, limit=100, path=SAVES_JSON_PATH, params=dict()):
        base = pathlib.Path(path)
        base.mkdir(exist_ok=True)
        all=False
        if(limit >= 1000):
            all = True
            print("Max limit for saved posts is 1000")

        # if(all == True):
        #     limit = 100
        #     remaining = 1000
        # else:
        remaining = limit

        params.update({
            "limit": min(100, limit),
            "count": count
        })

        downloaded_files = list()

        result_saved = list()

        while(True):
            # call api
            result = self.get_saved(params)

            new_count = params['count']+result['data']['dist']

            # write result to file
            path_to_file = base / f"result_{count}-{new_count}.json"
            cnt = 0
            while(path_to_file.exists()):
                cnt+=1
                path_to_file = base / f"result_{count}-{new_count} ({cnt}).json"

            with path_to_file.open('w') as f:
                json.dump(result, f)

            downloaded_files.append(str(path_to_file))

            # update count and after
            params['after'] = result['data']['after']
            params['count'] = new_count
            remaining -= params['limit']
            params['limit'] = min(params['limit'], remaining)

            result_saved.append(result)

            print(result['data']['after'], params['count'])


            # if limit=1000 reached, break
            if(result['data']['after'] == None or (all == False and remaining == 0)):
                print(params['count'])
                break

        return result_saved


if __name__ == "__main__":
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)

    # print(CONFIG_PATH, config)
    # reddit = Reddit(config["headers"]["User-Agent"], access_token="")
    # subs = []
    # for sub in subs[130:]:
    #     reddit.download_saved(all=True, params={'sr':sub})
    # reddit = Reddit(config["headers"]["User-Agent"], config=config)
    # reddit = Reddit(userAgent=config["headers"]
    #                 ["User-Agent"], access_token="token")
    # print(reddit.access_token)
    # reddit = Reddit(config["headers"]["User-Agent"])
    # pprint(reddit.get_saved(limit=1).json())
    # print(reddit.request_api('/search.json',
    #                          params={"limit": 1, "q": "none"}).json())
    # reddit.download_saved(all=True)
    # print(reddit.isAuthenticated())
