import sys
from http.server import BaseHTTPRequestHandler
import json
import os
import mimetypes
from code.util import auth
from urllib.parse import parse_qs
import traceback
import logging
import re
from datetime import datetime

logging.basicConfig(level=logging.INFO)


paths = {}


class endpoint:
    def __init__(self, url: str, method: str, userType: str, callback: callable, logdebug=False):
        self.url      = url
        self.method   = method
        self.userType = userType
        self.callback = callback
        self.logdebug = logdebug

def post(url: str, userType: str, callback: callable, logdebug=False):
    paths[url + "|POST"] = endpoint(url, "POST", userType, callback, logdebug)


def get(url: str, userType: str, callback: callable, logdebug=False):
    paths[url + "|GET"] = endpoint(url, "GET", userType, callback, logdebug)

webEndpoints = []
def web(url: str, userType: str, callback: callable):
    webEndpoints.append((url, userType, callback))

def fits(cookie, userType: str) -> bool:
    logging.debug(f"Checking cookie {cookie} against userType {userType}")
    if userType == "any":
        return True
    elif userType == "loggedin":
        return auth.getUser(cookie) is not None
    elif userType == "admin":
        return auth.isAdmin(cookie)
    elif userType == "participant":
        return auth.isParticipant(cookie)
    return False

def HTMLMatches(url):
    for (u, _, __) in webEndpoints:
        if re.match(u, url):
            return True
    return False

def serveHTML(cookie, url):
    endpoint = None
    for (u, t, c) in webEndpoints:
        x = re.match(u, url)
        if x:
            endpoint = (u, t, c, x)
            break
    
    logging.debug(endpoint)
    _, userType, callback, x = endpoint
    params = x.groups()
    user = auth.getUser(cookie)

    statusCode = 200
    headers = [("Content-type", "text/html")]
    if not fits(cookie, userType):
        statusCode = 302
        headers = [("Location", "/")]
        response = ""
        return statusCode, headers, response
    
    try:
        response = callback(params, user)
    except Exception as e:
        exc = traceback.format_exc()
        logging.error(exc)
        statusCode = 500
        response = "Internal error" 
    return statusCode, headers, response

def serveStatic(path):
    path = "/code/serve" + path
    logging.info("Serving {}".format(path))
    if os.path.abspath(path).startswith("/code/serve"):
        if not os.path.exists(path) or not os.path.isfile(path):
            return 404, [("Content-type", "text/plain")], "Not found"
        else:
            with open(path, "r") as f:
                return 200, [("Content-type", str(mimetypes.guess_type(path)))], f.read()
    else:
        return 403, [("Content-type", "text/plain")], "Not authorized"

def setHeader(headers, name, value):
    headers.append((name, value))

# class Server(BaseHTTPRequestHandler):
#     def handleRequest(self, method):
def serve(env):
    method = env["REQUEST_METHOD"]
    cookie = env.get("HTTP_COOKIE") or ""
    
    url = env["REQUEST_URI"]
    url = url.split("?")[0]
    url = url.split("#")[0]

    headers = []
    statusCode = 200
    response = ""

    if url.startswith("/static"):
        path = url[7:]
        return serveStatic(path)

    if f"{url}|{method}" in paths:
        endpoint = paths[f"{url}|{method}"]
        if not fits(cookie, endpoint.userType):
            if method == "POST":
                statusCode = 403
                headers.append(("Content-type", "text/plain"))
                response = f"Not authorized: {url}"
            else:
                statusCode = 302
                headers.append(("Location", "/login"))
        else:

            f = env["wsgi.input"].read().decode("utf-8")
            params = parse_qs(f)

            user = auth.getUser(cookie)
            username = f'[{user.username}]' if user else ''

            dolog = logging.debug if endpoint.logdebug else logging.info
            dolog(datetime.now().strftime('%H:%M:%S') + username + ":" + url + " -------------------------")
            dolog(params)
            for param in params:
                if len(params[param]) == 1:
                    params[param] = params[param][0]

            try:
                result = endpoint.callback(params, lambda x, y: setHeader(headers, x, y), user)
                if logging.getLogger().isEnabledFor(logging.DEBUG):
                    logging.debug(result)
                if isinstance(result, str):
                    headers.append(("Content-type", "text/plain"))
                    response = result
                elif isinstance(result, int):
                    statusCode = result
                elif isinstance(result, dict) or isinstance(result, list):
                    headers.append(("Content-type", "application/json"))
                    response = json.dumps(result)
                else:
                    headers.append(("Content-type", "application/json"))
                    response = "" # TODO: util.toString(result)
            except Exception as e:
                exc = traceback.format_exc()
                logging.error(f'Error processing {url}:\n{exc}')
                statusCode = 500
                headers.append(("Content-type", "text/plain"))
                response = f"Internal Error: {e}"
    elif HTMLMatches(url):
        statusCode, headers, response = serveHTML(cookie, url)
    else:
        statusCode = 404
        headers.append(("Content-type", "text/plain"))
        response = f"Not found: {url}"

    return statusCode, headers, response
    self.send_response(statusCode)
    for header, value in headers:
        self.send_header(header, value)
    self.end_headers()
    self.wfile.write(bytes(str(response), "utf-8"))

    # def do_GET(self):
    #     return self.handleRequest("GET")
    
    # def do_POST(self):
    #     return self.handleRequest("POST")
