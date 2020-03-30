from model_mommy.recipe import Recipe, seq, foreign_key
from account.models import Team, Role
from django.contrib.auth.models import User


user = Recipe(
    User,
    username=seq('fake_username'),
    email=seq('fake_user_mail')
)


role = Recipe(
    Role,
    name=seq('fake_role')
)


team = Recipe(
    Team,
    email=seq('fake_email'),
    contacts=seq('fake_contact'),
    role=foreign_key(role)
)
