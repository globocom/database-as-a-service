# -*- coding: utf-8 -*-


class BaseTopology(object):

    def get_deploy_steps(self):
        raise NotImplementedError()

    def get_clone_steps(self):
        raise NotImplementedError()

    def get_resize_steps(self):
        raise NotImplementedError()

    def get_restore_snapshot_steps(self):
        raise NotImplementedError()

    def get_volume_migration_steps(self):
        raise NotImplementedError()
