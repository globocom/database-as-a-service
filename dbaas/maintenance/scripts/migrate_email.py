from django.contrib.auth.models import User
from copy import deepcopy


def _migrate(file_path):
    arq = open(file_path)
    for line in arq.readlines():
        old_email, new_email = line.strip().split(',')
        old_email = old_email.strip()
        new_email = new_email.strip()
        try:
            old_user = User.objects.get(username=old_email)
        except User.DoesNotExist:
            continue
        new_user = User.objects.filter(username=new_email)
        if new_user:
            continue
        new_user = deepcopy(old_user)
        new_user.id = None
        new_user.username = new_email
        new_user.email = new_email
        new_user.save()
        map(new_user.team_set.add, old_user.team_set.all())
    arq.close()


def migrate_corp():
    _migrate('/tmp/corp.csv')


def migrate_prestadores():
    _migrate('/tmp/prestadores.csv')


def migrate_tvglobo():
    _migrate('/tmp/tvglobo.csv')


def update_username():
    from django.db.models import Q
    for user in User.objects.all().exclude(
            Q(username='admin')
            | Q(username='slack_bot')
            | Q(username='tsuru-dbaas')
            | Q(username='dbaas_app')):
        if user.email:
            user.username = user.email
            user.save()
