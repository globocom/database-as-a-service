from ..base import BaseProvider
from physical.models import DatabaseInfra

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

    def destroy_instance(self):
        pass