from django.core.exceptions import ValidationError
from physical import models
from collections import Counter
from django.core import validators


def validate_hosts_ids(hosts_ids):

    validators.validate_comma_separated_integer_list(hosts_ids)

    hosts_ids = [int(x) for x in hosts_ids.split(',')]
    hosts_ids_set = Counter(set(hosts_ids))

    hosts_ids = Counter(hosts_ids)

    if hosts_ids_set != hosts_ids:
        raise ValidationError(u'Some ids are repeated')

    real_hosts = Counter(models.Host.objects.filter(
        id__in=hosts_ids,
    ).values_list('id', flat=True))

    diff = real_hosts - hosts_ids
    diff2 = hosts_ids - real_hosts

    if diff or diff2:
        f_diff = diff | diff2
        raise ValidationError(
            u'Some ids do not exist: {}'.format(f_diff.keys()))
