from datetime import datetime, timedelta
from threading import current_thread
from django.conf import settings
from django.contrib import auth


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
        raise exception
