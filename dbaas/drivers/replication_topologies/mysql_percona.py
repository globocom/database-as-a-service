# -*- coding: utf-8 -*-
import logging

from .mysql import MySQLSingle, MySQLFoxHA, MySQLFoxHAAWS
from physical.models import Instance
from base import InstanceDeploy

LOG = logging.getLogger(__name__)


class MySQLPerconaSingle(MySQLSingle):

    @property
    def driver_name(self):
        return 'mysql_percona_single'

    def deploy_instances(self):
        return [[InstanceDeploy(Instance.MYSQL_PERCONA, 3306)]]


class MySQLPerconaFoxHA(MySQLFoxHA):

    @property
    def driver_name(self):
        return 'mysql_percona_foxha'

    def deploy_instances(self):
        return [
            [InstanceDeploy(Instance.MYSQL_PERCONA, 3306)],
            [InstanceDeploy(Instance.MYSQL_PERCONA, 3306)]
        ]


class MySQLPerconaFoxHAAWS(MySQLFoxHAAWS):

    @property
    def driver_name(self):
        return 'mysql_percona_foxha'

    def deploy_instances(self):
        return [
            [InstanceDeploy(Instance.MYSQL_PERCONA, 3306)],
            [InstanceDeploy(Instance.MYSQL_PERCONA, 3306)]
        ]
