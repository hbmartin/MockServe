#!/usr/bin/env python3

"""Simple mock server, useful for QA """

__author__ = "H. Martin"
__version__ = "0.1.0"

import argparse
import pprint
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from optparse import OptionParser
from urllib.parse import urlparse, parse_qs


def RequestHandlerFactory(routes):
    class RequestHandler(BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.1'

        def send_not_found(self, msg):
            self.send_error(404, message=msg)

        def do_GET(self):
            r = urlparse(self.path)
            if r.path in routes:
                path_router_rules = routes[r.path]
                req_params = parse_qs(r.query)
                route = None
                for rule in path_router_rules:
                    for key, val in rule['only']['params'].items():
                        if not key in req_params:
                            self.send_not_found("didnt find required param " + key)
                            continue
                        elif req_params[key][0] != val:
                            self.send_not_found("required param " + key + " is not " + val + " but " + req_params[key][0])
                            continue
                    route = rule
                if route is None:
                    self.send_not_found("no matching rules")

                resp_body = bytes(route['response']['body'], "utf8")
                self.send_response(200)
                self.send_header('content-length', len(resp_body))
                for h, v in route['response']['headers'].items():
                    self.send_header(h, v)
                self.end_headers()
                self.wfile.write(resp_body)

            else:
                self.send_not_found("no matching path")

        do_POST = do_GET
        do_PUT = do_GET

    return RequestHandler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('route_config', type=argparse.FileType('r'))
    parser.add_argument('-p', '--port', type=int, default=8080)
    args = parser.parse_args()
    routes = json.load(args.route_config)
    Handler = RequestHandlerFactory(routes)
    server = HTTPServer(('', args.port), Handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
