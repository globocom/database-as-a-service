
from django_services import service
from .models import Environment, Host, Instance, Database, Credential


class EnvironmentService(service.CRUDService):
    model_class = Environment


class HostService(service.CRUDService):
    model_class = Host


class InstanceService(service.CRUDService):
    model_class = Instance


class DatabaseService(service.CRUDService):
    model_class = Database


class CredentialService(service.CRUDService):
    model_class = Credential
