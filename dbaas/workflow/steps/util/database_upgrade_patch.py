# -*- coding: utf-8 -*-
from workflow.steps.util.base import BaseInstanceStep
from util import exec_remote_command_host
import os
import logging

LOG = logging.getLogger(__name__)


class CantUpgradePatch(Exception):
    pass


class DatabaseUpgradePatchStep(BaseInstanceStep):
    def __init__(self, instance):
        super(DatabaseUpgradePatchStep, self).__init__(instance)

        upgrade = self.database.upgrades_patch.last()
        if upgrade and upgrade.is_running:
            self.target_patch = upgrade.target_patch
            self.source_patch = upgrade.source_patch
        else:
            self.target_patch = self.infra.engine_patch
            self.source_patch = self.engine.default_engine_patch

    def __unicode__(self):
        return "Changing database binaries..."

    @property
    def is_valid(self):

        if self.source_patch == self.target_patch:
            return False

        if self.source_patch.engine != self.target_patch.engine:
            error = "Can not change the Engine."
            error += " Source engine={}, targe engine={}".format(
                self.source_patch.engine,
                self.target_patch.engine)
            raise CantUpgradePatch(error)

        if self.source_patch.patch_version > self.target_patch.patch_version:
            error = "Target patch must be bigger than source patch."
            error += " Source patch={}, targe patch={}".format(
                self.source_patch, self.target_patch)
            raise CantUpgradePatch(error)

        if not self.target_patch.patch_path:
            error = "Patch path can not be empty."
            raise CantUpgradePatch(error)

        return True

    def execute_script(self, script):
        output = {}
        return_code = exec_remote_command_host(self.host, script, output)
        if return_code != 0:
            error = 'Could not execute script {}: {}'.format(
                return_code, output)
            raise EnvironmentError(error)

    def undo(self):
        pass


class MongoDBCHGBinStep(DatabaseUpgradePatchStep):

    def do(self):
        if not self.is_valid:
            return

        patch_path = self.target_patch.patch_path
        dir_name = os.path.splitext(os.path.basename(patch_path))[0]

        if self.target_patch.patch_path.startswith('https'):
            download_script = 'curl {} | tar -xz'.format(patch_path)
        else:
            download_script = 'tar -xvf {}'.format(patch_path)

        script = """cd /usr/local/
        {download_script}
        rm -f mongodb
        ln -s {dir_name} mongodb
        chown -R mongodb:mongodb mongodb/
        """.format(download_script=download_script, dir_name=dir_name)

        self.execute_script(script)


class MongoDBCHGBinStepRollback(MongoDBCHGBinStep):

    def do(self):
        pass

    def undo(self):
        super(MongoDBCHGBinStepRollback, self).do()


class RedisCHGBinStep(DatabaseUpgradePatchStep):

    def do(self):
        if not self.is_valid:
            return

        patch_path = self.target_patch.patch_path
        path, file_name = os.path.split(patch_path)
        dir_name = file_name.rsplit('.', 2)[0]

        if self.target_patch.patch_path.startswith('https'):
            download_script = 'curl {} | tar -xz'.format(patch_path)
        else:
            download_script = 'tar -xvf {}'.format(patch_path)

        script = """cd /usr/local/
        {download_script}
        rm -f redis
        ln -s {dir_name} redis
        cd redis && make
        cp /mnt/software/db/redis/redis-trib-gcom.rb /usr/local/redis/src/redis-trib-gcom.rb
        cd ..
        chown -R redis:redis redis/
        """.format(download_script=download_script, dir_name=dir_name)

        self.execute_script(script)


class MySQLCHGBinStep(DatabaseUpgradePatchStep):

    def do(self):
        if not self.is_valid:
            return

        patch_path = self.target_patch.patch_path

        script = """cd {patch_path}
        yum -y localinstall --nogpgcheck *.rpm
        """.format(patch_path=patch_path)

        self.execute_script(script)
