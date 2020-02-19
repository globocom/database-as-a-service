from account.models import Team, RoleEnvironment
from logical.models import Database


def databases_by_env(qs, teams):
    roles = [team.role for team in teams]
    role_environments = RoleEnvironment.objects.filter(
        role__in=[role.id for role in roles]
    ).distinct()

    environments = []
    for role_env in role_environments:
        environments.extend(role_env.environments.all())

    return qs.filter(environment__in=[env.id for env in environments])


def can_access_database(database, teams):
    qs = Database.objects.filter(id=database.id)
    return databases_by_env(qs, teams)
