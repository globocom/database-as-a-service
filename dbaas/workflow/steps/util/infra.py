# -*- coding: utf-8 -*-
from dbaas_cloudstack.models import DatabaseInfraOffering
from physical.models import Instance
from base import BaseInstanceStep, BaseInstanceStepMigration


class Update(BaseInstanceStep):
    def __init__(self, instance):
        super(Update, self).__init__(instance)

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

    @property
    def target_offering(self):
        return self.resize.target_offer.offering

    @property
    def source_offering(self):
        return self.resize.source_offer.offering

    def change_infra_offering(self, offering):
        if not offering:
            return

        self.infra_offering.offering = offering
        self.infra_offering.save()

    def do(self):
        self.change_infra_offering(self.target_offering)

    def undo(self):
        self.change_infra_offering(self.source_offering)


class OfferingMigration(Offering):

    @property
    def target_offering(self):
        return self.infra_offering.offering.equivalent_offering


class Memory(Update):

    def __unicode__(self):
        return "Updating max_memory info..."

    def do(self):
        self.set_max_memory_for(self.resize.target_offer.offering)

    def undo(self):
        self.set_max_memory_for(self.resize.source_offer.offering)

    def set_max_memory_for(self, offering):
        new_max_memory = offering.memory_size_mb
        resize_factor = 0.5
        if new_max_memory > 1024:
            resize_factor = 0.75

        new_max_memory *= resize_factor
        self.infra.per_database_size_mbytes = int(new_max_memory)
        self.infra.save()


class MigrationCreateInstance(BaseInstanceStepMigration):

    def __unicode__(self):
        return "Creating new infra instance..."

    def do(self):
        if self.instance.future_instance:
            return

        for instance in self.instance.hostname.instances.all():
            new_instance = Instance.objects.get(id=instance.id)
            new_instance.id = None
            new_instance.address = self.host.address
            new_instance.hostname = self.host
            new_instance.save()

            instance.future_instance = new_instance
            instance.save()

            if self.instance.id == instance.id:
                self.instance.future_instance = new_instance
                self.instance.save()


class UpdateMigrateEnvironment(BaseInstanceStepMigration):

    def __unicode__(self):
        return "Updating environment..."

    def do(self):
        env = self.environment
        if env:
            self.infra.environment = env
            self.infra.save()

            self.database.environment = env
            self.database.save()


class UpdateMigratePlan(BaseInstanceStepMigration):

    def __unicode__(self):
        return "Updating plan..."

    def do(self):
        if self.plan:
            self.infra.plan = self.plan
            self.infra.save()
