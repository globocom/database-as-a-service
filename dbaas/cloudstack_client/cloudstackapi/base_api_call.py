import hashlib, hmac, string, base64, urllib
import json, urllib
 
class BaseApiCall(object):
    def __init__(self, api_url, apiKey, secret):
        self.api_url = api_url
        self.apiKey = apiKey
        self.secret = secret
 
    def request(self, args):
        args['apiKey'] = self.apiKey
 
        self.params = []
        self._sort_request(args)
        self._create_signature()
        self._build_post_request()
 
    def _sort_request(self, args):
        keys = sorted(args.keys())
 
        for key in keys:
            self.params.append(key + '=' + urllib.quote_plus(args[key]))
 
    def _create_signature(self):
        self.query = '&'.join(self.params)
        digest = hmac.new(
            self.secret,
            msg=self.query.lower(),
            digestmod=hashlib.sha1).digest()
 
        self.signature = base64.b64encode(digest)
 
    def _build_post_request(self):
        self.query += '&signature=' + urllib.quote_plus(self.signature)
        self.value = self.api_url + '?' + self.query