from django_services import service
from ..models import AccountUser


class UserService(service.CRUDService):
    model_class = AccountUser
