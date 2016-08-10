from datetime import datetime, timedelta
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
                del request.session['last_touch']
                return

        request.session['last_touch'] = datetime.now()
