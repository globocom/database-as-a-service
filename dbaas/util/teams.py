import requests
from dbaas_credentials.models import CredentialType
from util import get_credentials_for, get_credentials_in_any_env
from slugify import slugify


class TeamNotFoundError(Exception):
    pass


class TeamAPIError(Exception):
    pass


class Teams(object):
    def __init__(self, env=None):
        self.env = env
        self._credential = None

    def slugify(self, name):
        return slugify(
            name,
            regex_pattern=r'[^\w\S-]'
        )

    @property
    def credential(self):
        _get_credential = get_credentials_for
        if not self.env:
            _get_credential = get_credentials_in_any_env

        if not self._credential:
            self._credential = _get_credential(
                credential_type=CredentialType.TEAMS_API,
                environment=self.env)
        return self._credential

    def _make_team_api_url(self):
        return '{}/slug/'.format(
            self.credential.endpoint,
        )

    def validate(self, team_name=""):
        team_name = team_name.strip()
        if not team_name:
            raise TeamAPIError("Invalid team name")

        slugify_name = self.slugify(team_name)
        url = '{}{}'.format(self._make_team_api_url(), slugify_name)
        res = requests.get(url)
        if res.ok:
            return True

        if res.status_code == 404:
            raise TeamNotFoundError("Team not found in cost API")

        raise TeamAPIError(res.content)
