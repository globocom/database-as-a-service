# -*- coding: utf-8 -*-
from workflow.steps.util.base import BaseInstanceStep
from util import exec_remote_command_host
import os


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

        script = """cd /usr/local/
        tar -xvf {patch_path}
        rm -f mongodb
        ln -s {dir_name} mongodb
        chown -R mongodb:mongodb mongodb/
        """.format(patch_path=patch_path, dir_name=dir_name)

        self.execute_script(script)
