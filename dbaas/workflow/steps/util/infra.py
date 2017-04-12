# -*- coding: utf-8 -*-
from dbaas_cloudstack.models import DatabaseInfraOffering
from workflow.steps.util.base import BaseInstanceStep


class Update(BaseInstanceStep):
    def __init__(self, instance):
        super(Update, self).__init__(instance)

        self.infra = self.instance.databaseinfra
        self.database = self.infra.databases.last()
        self.infra_offering = DatabaseInfraOffering.objects.get(
            databaseinfra=self.infra
        )

    def do(self):
        raise NotImplementedError

    def undo(self):
        pass


class Offering(Update):
    def __unicode__(self):
        return "Updating offering info..."

    def do(self):
        last_resize = self.database.resizes.last()
        self.infra_offering.offering = last_resize.target_offer.offering
        self.infra_offering.save()

    def undo(self):
        pass


class Memory(Update):
    def __unicode__(self):
        return "Updating max_memory info..."

    def do(self):
        new_max_memory = self.infra_offering.offering.memory_size_mb
        resize_factor = 0.5
        if new_max_memory > 1024:
            resize_factor = 0.75

        new_max_memory *= resize_factor
        self.infra.per_database_size_mbytes = int(new_max_memory)
        self.infra.save()

    def undo(self):
        pass
