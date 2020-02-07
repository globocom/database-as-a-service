from django.contrib.auth.models import User
from copy import deepcopy


def _migrate(file_path):
    arq = open(file_path)
    for line in arq.readlines():
        old_email, new_email = line.strip().split(',')
        old_email = old_email.strip()
        new_email = new_email.strip()
        try:
            old_user = User.objects.get(email=old_email)
        except User.DoesNotExist:
            continue
        new_user = User.objects.filter(email=new_email)
        if new_user:
            new_user = new_user[0]
            print new_user
            map(new_user.team_set.add, old_user.team_set.all())
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


def _validate(search_str, file_path):
    arq = open(file_path)
    for line in arq.readlines():
        old_email, new_email = line.strip().split(',')
        old_email = old_email.strip()
        new_email = new_email.strip()
        try:
            User.objects.get(email=old_email)
        except User.DoesNotExist:
            continue
        try:
            User.objects.get(email=new_email)
        except User.DoesNotExist:
            print "{}|{}".format(old_email, new_email)
    arq.close()

    users = User.objects.filter(email__contains=search_str)
    for user in users:
        try:
            User.objects.get(
                email=user.email.replace(search_str, "@g.globo")
            )
        except User.DoesNotExist:
            print "Nao encontrado {}".format(user.email)


def validate_corp():
    _validate("@corp.globo.com", '/tmp/corp.csv')


def validate_tvglobo():
    _validate("@tvglobo.com.br", '/tmp/tvglobo.csv')
