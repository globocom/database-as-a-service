from ..base import BaseProvider
from physical.models import DatabaseInfra
from logical.models import Database, Credential
from util import make_db_random_password
import datetime
from drivers import factory_for
import logging



LOG = logging.getLogger(__name__)

class PreProvisionedProvider(BaseProvider):
    
    def create_instance(self, plan, environment):
        """ Choose the best DatabaseInfra for another database """
        datainfras = list(DatabaseInfra.get_active_for(plan=plan, environment=environment))
        if not datainfras:
            return None
        datainfras.sort(key=lambda di: -di.available)
        best_datainfra = datainfras[0]
        if best_datainfra.available <= 0:
            return None
        return best_datainfra

    def destroy_instance(self, database,*args, **kwargs):
        """
        Overrides the delete method so that a database can be put in quarantine and not removed
        """
        #do_something()
        if database.is_in_quarantine:
            LOG.warning("Database %s is in quarantine and will be removed" % database.name)
            for credential in database.credentials.all():
                instance = factory_for(database.databaseinfra)
                instance.remove_user(credential)
            super(Database, database).delete(*args, **kwargs)  # Call the "real" delete() method.
        else:
            LOG.warning("Putting database %s in quarantine" % database.name)
            if database.credentials.exists():
                for credential in database.credentials.all():
                    new_password = make_db_random_password()
                    new_credential = Credential.objects.get(pk=credential.id)
                    new_credential.password = new_password
                    new_credential.save()

                    instance = factory_for(database.databaseinfra)
                    instance.update_user(new_credential)

            else:
                LOG.info("There is no credential on this database: %s" % database.databaseinfra)

            database.is_in_quarantine = True
            database.quarantine_dt = datetime.datetime.now().date()
            database.save()