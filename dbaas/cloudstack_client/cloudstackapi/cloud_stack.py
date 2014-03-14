import hashlib, hmac, string, base64, urllib
import json, urllib
from base_api_call import BaseApiCall

class CloudStack(BaseApiCall):
    def __getattr__(self, name):
        def handlerFunction(*args, **kwargs):
            if kwargs:
                return self._make_request(name, kwargs)
            return self._make_request(name, args[0])
        return handlerFunction
 
    def _http_get(self, url):
        response = urllib.urlopen(url)
        return response.read()
 
    def _make_request(self, command, args):
        args['response'] = 'json'
        args['command'] = command
        self.request(args)
        data = self._http_get(self.value)
        # The response is of the format {commandresponse: actual-data}
        key = command.lower() + "response"
        return json.loads(data)[key]
