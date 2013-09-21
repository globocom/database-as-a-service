from django_services import service
from ..models import Credential
from base.engine.factory import EngineFactory


class CredentialService(service.CRUDService):
    model_class = Credential

    def get_engine(self, credential):
        return EngineFactory.factory(credential.database.instance)

    def create(self, credential):
        super(CredentialService, self).create(credential)

        engine = self.get_engine(credential)
        engine.create_user(credential)

    def update(self, credential):
        old_credential = self.get(credential.pk)

        # FIXME
        engine = self.get_engine(old_credential)
        engine.remove_user(old_credential)

        super(CredentialService, self).update(credential)
        engine.create_user(credential)

    def delete(self, credential):
        engine = self.get_engine(credential)
        engine.remove_user(credential)

        super(CredentialService, self).delete(credential)
