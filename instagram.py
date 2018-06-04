# -*- coding: utf-8 -*-
from __future__ import print_function

import json
import re
import sys
import time

import requests
from lxml import html


class User(object):
    def __init__(self, **kwargs):
        self.id = kwargs["id"]
        self.username = kwargs["username"]
        self.full_name = ""
        self.is_private = False
        self.is_verified = False
        self.follows = []
        # self.followed = 0
        # self.following = 0

    def __repr__(self):
        return "User %s<%s>" % (self.id, self.username)

    def add(self, user):
        self.follows.append(user)
        print (user)


class InstagramAPI(object):
    def __init__(self, **kwargs):
        self.fan = kwargs["fan"]
        self.brand = kwargs["brand"]
        self.endpoint = "https://www.instagram.com"
        self.queryid = ""
        self.session = requests.Session()
        headers = {
            'authority': 'www.instagram.com',
            'pragma': 'no-cache',
            'cache-control': 'no-cache',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.9',
            'cookie': 'csrftoken=dCCrgXTqkaSIlhK0ZxSqyBCc0IotNr8w; ds_user_id=7109575542; rur=FTW; mid=Wwrb1wAEAAEHnDTDqZqdZPvXf1HL; mcd=3; sessionid=IGSC91ee39d8409b3d9cfb4b1fd420067d9a25c29de8b73f2239f9752d0d64202d2c%3ApOCcw16OUIkCbAmxNNwXCGZYU2txIho1%3A%7B%22_auth_user_id%22%3A7109575542%2C%22_auth_user_backend%22%3A%22accounts.backends.CaseInsensitiveModelBackend%22%2C%22_auth_user_hash%22%3A%22%22%2C%22_platform%22%3A4%2C%22_token_ver%22%3A2%2C%22_token%22%3A%227109575542%3ApiS6NSoutAxNBvpi9ndUcGituvmgfN5f%3Aa0d6f0342f654f3fc8e45133b4bee03360b6adb528cd2fe09368fa929886793e%22%2C%22last_refreshed%22%3A1527757532.9577643871%7D; urlgen="{\\"time\\": 1527757533\\054 \\"23.27.206.3\\": 18779\\054 \\"209.58.130.129\\": 7203}:1fOdOJ:8g8iYMESSWplj6YMRchKzCJvIG8"',
        }
        self.session.headers.update(headers)

    def run(self):
        fan_url = "%s/%s/" % (self.endpoint, self.fan)
        brand_url = "%s/%s/" % (self.endpoint, self.brand)
        r = self.session.get(fan_url)
        if r.status_code != 200:
            return {"status":None, "message": "Bad Response for Fan User."}
        self.queryid = self.find_following_query_id(r)
        if self.queryid is None:
            return {"status": None, "message": "Invalid Fan Query Hash."}
        fan_user = self.get_profile(r)
        if fan_user is None:
            return {"status": None, "message": "Cookies/Response Error at Fan processing."}
        
        if fan_user.is_private is True:
            print ("private fan profile")
            r = self.session.get(brand_url)
            if r.status_code != 200:
                return {"status":None, "message": "Bad Response for Brand User."}
            self.queryid = self.find_followed_query_id(r)
            # print (self.queryid)
            if self.queryid is None:
                return {"status": None, "message": "Invalid Brand Query Hash."}
            brand_user = self.get_profile(r)
            if brand_user is None:
                return {"status": None, "message": "Cookies/Response Error at Brand processing."}
            if brand_user.is_private is True:
                return {"status": None, "message": "Fan & Brand profiles are private"}
            return self.is_followed(brand_user)
        
        return self.is_following(fan_user)

    def is_following(self, user):
        params = {
            'query_hash': self.queryid,
            'variables': '{"id":"%s","first":50}' % (user.id)
        }
        while True:
            r = self.session.get('https://www.instagram.com/graphql/query/', params=params)
            edges = r.json()
            if edges["status"] == "fail":
                return {"status": False, "message": edges["message"]}
            
            for edge in edges["data"]["user"]["edge_follow"]["edges"]:
                u = User(id=edge["node"]["id"], username=edge["node"]["username"])
                u.full_name = edge["node"]["full_name"]
                u.is_verified = edge["node"]["is_verified"]
                u.full_name = edge["node"]["full_name"]
                u.is_verified = edge["node"]["is_verified"]

                user.add(u)
                if self.brand == u.username:
                    return {"status":True, "message":"Success"}
            
            has_next_page = edges["data"]["user"]["edge_follow"]["page_info"]["has_next_page"]
            if has_next_page:
                end_cursor = edges["data"]["user"]["edge_follow"]["page_info"]["end_cursor"]
                params = {
                    'query_hash': self.queryid,
                    'variables': '{"id":"%s","first":25,"after":"%s"}' % (user.id, end_cursor)
                }
            else:
                break
            time.sleep(3)
        return {"status": False, "message": "No following."}
    
    def is_followed(self, user):
        params = {
            'query_hash': self.queryid,
            'variables': '{"id":"%s","first":50}' % (user.id)
        }
        while True:
            r = self.session.get(
                'https://www.instagram.com/graphql/query/', params=params)
            edges = r.json()
            if edges["status"] == "fail":
                return {"status": False, "message": edges["message"]}

            for edge in edges["data"]["user"]["edge_followed_by"]["edges"]:
                u = User(id=edge["node"]["id"],
                         username=edge["node"]["username"])
                u.full_name = edge["node"]["full_name"]
                u.is_verified = edge["node"]["is_verified"]
                user.add(u)
                if self.fan == u.username:
                    return {"status": True, "message": "Success"}

            has_next_page = edges["data"]["user"]["edge_followed_by"]["page_info"]["has_next_page"]
            if has_next_page:
                end_cursor = edges["data"]["user"]["edge_followed_by"]["page_info"]["end_cursor"]
                params = {
                    'query_hash': self.queryid,
                    'variables': '{"id":"%s","first":25,"after":"%s"}' % (user.id, end_cursor)
                }
            else:
                break
            time.sleep(3)
        
        return {"status": False, "message": "No following."}
    
    
    def find_followed_query_id(self, r):
        js_url = re.search(
            "/static/bundles/base/Consumer.js/(.*?).js", r.text, re.S | re.M)

        if js_url:
            js_link = "%s%s" % (self.endpoint, js_url.group(0))
            res = self.session.get(js_link)
            query_filter = re.search(
                "\)\,u=\"(.*?)\"\,s=", res.text, re.S | re.M)
            if query_filter:
                qid = query_filter.group(1)
                return qid
            else:
                return None
        else:
            return None
    
    def find_following_query_id(self, r):
        js_url = re.search(
            "/static/bundles/base/Consumer.js/(.*?).js", r.text, re.S | re.M)

        if js_url:
            js_link = "%s%s" % (self.endpoint, js_url.group(0))
            res = self.session.get(js_link)
            query_filter = re.search(
                "\,s\=\"(.*?)\"\,l\=1\;", res.text, re.S | re.M)
            if query_filter:
                qid = query_filter.group(1)
                return qid
            else:
                return None
        else:
            return None

    def get_profile(self, r):
        sharedData = self.parse_shared_data(r.text)
        if sharedData == {}:
            return None
        
        t = html.fromstring(r.text)
        userid = sharedData["entry_data"]["ProfilePage"][0]["graphql"]["user"]["id"]
        username = sharedData["entry_data"]["ProfilePage"][0]["graphql"]["user"]["username"]
        full_name = sharedData["entry_data"]["ProfilePage"][0]["graphql"]["user"]["full_name"]
        is_verified = sharedData["entry_data"]["ProfilePage"][0]["graphql"]["user"]["is_verified"]
        is_private = sharedData["entry_data"]["ProfilePage"][0]["graphql"]["user"]["is_private"]
        # following = sharedData["entry_data"]["ProfilePage"][0]["graphql"]["user"]["edge_follow"]["count"]
        # followed = sharedData["entry_data"]["ProfilePage"][0]["graphql"]["user"]["edge_followed_by"]["count"]

        user = User(id=userid, username=username)
        user.full_name = full_name
        user.is_private = is_private
        user.is_verified = is_private
        # user.followed = followed
        # user.following = following

        return user

    def parse_shared_data(self, html_string):
        res = re.search("\>window\.\_sharedData = (.*?)\;\<",
                        html_string, re.S | re.M | re.I)
        if res:
            return json.loads(res.group(1))
        else:
            return {}


def main(fan, brand):
    # fan = sys.argv[1]
    # brand = sys.argv[2]
    api = InstagramAPI(fan=fan, brand=brand)
    result = api.run()
    return result
    # print (result)


# if __name__ == '__main__':
#     main()
