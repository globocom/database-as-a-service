# -*- coding: utf-8 -*-
from workflow.steps.util.base import BaseInstanceStep
from util import exec_remote_command_host
#from physical.models import EnginePatch


class DatabaseUpgradePatchStep(BaseInstanceStep):
    def __init__(self, instance):
        super(DatabaseUpgradePatchStep, self).__init__(instance)
        self.target_patch = self.upgrade_patch.target_patch
        self.source_patch = self.upgrade_patch.source_patch

    @property
    def upgrade_patch(self):
        upgrade = self.database.upgrades_patch.last()
        if upgrade and upgrade.is_running:
            return upgrade

    def __unicode__(self):
        return "Changing database binaries..."

    def execute_script(self, script):
        output = {}
        return_code = exec_remote_command_host(self.host, script, output)
        if return_code != 0:
            error = 'Could not execute script {}: {}'.format(
                return_code, output)
            raise EnvironmentError(error)



class MongoDBCHGBinStep(DatabaseUpgradePatchStep):

    def do(self):
        patch_path = self.target_patch.patch_path
        script = """cd /usr/local/
        cp -u {patch_path} .
        tgzfile=$(basename {patch_path})
        dirname=$(basename {patch_path} .tgz)
        tar -xvf $tgzfile
        rm -f mongodb
        ln -s $dirname mongodb
        chown -R mongodb:mongodb mongodb/
        """.format(patch_path=patch_path)

        self.execute_script(script)

    def undo(self):
        pass