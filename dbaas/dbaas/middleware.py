from datetime import datetime, timedelta
from threading import current_thread
from django.conf import settings
from django.contrib import auth
from django.shortcuts import redirect

from system.models import Configuration


class AutoLogout:

    def process_request(self, request):
        if not request.user.is_authenticated():
            return

        if 'last_touch' in request.session:
            max_inactive = timedelta(0, settings.AUTO_LOGOUT_DELAY * 60, 0)
            current_inactive = datetime.now() - request.session['last_touch']

            if current_inactive > max_inactive:
                auth.logout(request)
                return

        request.session['last_touch'] = datetime.now()


class UserMiddleware(object):

    _requests = {}

    @classmethod
    def current_user(cls):
        current_request = cls._requests.get(current_thread().ident, None)
        if not current_request:
            return
        return current_request.user

    @classmethod
    def set_current_user(cls, user):
        current_request = cls._requests[current_thread().ident]
        current_request.user = user

    def process_request(self, request):
        self._requests[current_thread().ident] = request

    def process_response(self, request, response):
        self._requests.pop(current_thread().ident, None)
        return response

    def process_exception(self, request, exception):
        self._requests.pop(current_thread().ident, None)


class DeployMiddleware(object):
    """'
    Middleware to make pages unreachable when deploying new version
    Uses a Configuration `deploy_active` to validate and redirect the user accordingly
    """

    def process_request(self, request):
        configuration = Configuration.get_by_name_as_int('deploy_active', 0)

        path_info = request.META['PATH_INFO'].replace('/', '')
        available_urls = ['deploy', 'configuration', 'taskhistory']  # paths to be allowed when deploying
        matches = list(filter(lambda k: k in path_info, available_urls))  # matched allowed paths and current path

        if configuration != 0 and not matches and path_info != 'admin':  # check configuration and if not in main page
            return redirect('deploy')
