from model_mommy.recipe import Recipe, seq
from physical.models import DatabaseInfra, Host


databaseinfra = Recipe(
    DatabaseInfra,
    user=seq('fake_user'),
    endpoint=seq('127.0.0.1:111')
)

host = Recipe(
    Host,
    user='fake_username',
    password='fake_password'
)
