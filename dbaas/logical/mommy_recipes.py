from model_mommy.recipe import Recipe, seq
from logical.models import Credential


credential = Recipe(
    Credential,
    user=seq('fake_user'),
    password='123456'
)
