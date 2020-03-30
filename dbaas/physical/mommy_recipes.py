from model_mommy.recipe import Recipe, seq
from physical.models import DatabaseInfra


databaseinfra = Recipe(
    DatabaseInfra,
    user=seq('fake_user'),
    endpoint=seq('127.0.0.1:111')
)
