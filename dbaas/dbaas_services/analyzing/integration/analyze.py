# -*- coding: utf-8 -*-
import requests
from dbaas_services.analyzing.exceptions import ServiceNotAvailable


class AnalyzeService(object):
    def __init__(self, endpoint, healh_check_route, healh_check_string):
        self.endpoint = endpoint
        self.healh_check_route = healh_check_route
        self.healh_check_string = healh_check_string

        if self.__service_is_not__available():
            raise ServiceNotAvailable("Service not Working")

    def __service_is_not__available(self,):
        healh_check_endpoint = self.endpoint + self.healh_check_route
        response = requests.get(healh_check_endpoint)

        return not response.content == self.healh_check_string

    def run(self, **kwargs):
        response = requests.post(self.endpoint, json=kwargs)
        return response.json()
