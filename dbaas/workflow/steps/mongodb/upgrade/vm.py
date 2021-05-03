# -*- coding: utf-8 -*-
from __future__ import absolute_import
from util import build_context_script
from workflow.steps.util.vm import VmStep
from workflow.steps.util import test_bash_script_error
from workflow.steps.mongodb.util import build_change_release_alias_script


class ChangeBinaryBase(VmStep):

    def __script(self):
        return test_bash_script_error() + build_change_release_alias_script()

    @property
    def so_version(self):
        version = "rhel62"
        if self.host.is_ol7:
            version = "rhel70"
        return version

    def change_binary(self, release):
        context_dict = {
            'TARGET_PATH': '/usr/local/',
            'MONGODB_RELEASE_FOLDER': 'mongodb-linux-x86_64-{}-{}'.format(
                self.so_version,
                release
            ),
        }

        script = build_context_script(
            context_dict, self.__script()
        )
        self.host.ssh.run_script(
            script
        )


class ChangeBinaryTo32(ChangeBinaryBase):

    def __unicode__(self):
        return "Changing binary to 3.2..."

    def do(self):
        self.change_binary('3.2.11')


class ChangeBinaryTo34(ChangeBinaryBase):

    def __unicode__(self):
        return "Changing binary to 3.4..."

    def do(self):
        self.change_binary('3.4.1')


class ChangeBinaryTo36(ChangeBinaryBase):

    def __unicode__(self):
        return "Changing binary to 3.6..."

    def do(self):
        self.change_binary('3.6.8')


class ChangeBinaryTo40(ChangeBinaryBase):

    def __unicode__(self):
        return "Changing binary to 4.0..."

    def do(self):
        self.change_binary('4.0.3')
