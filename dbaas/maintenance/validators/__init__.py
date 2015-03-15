from django.core.exceptions import ValidationError






def validate_host_query(host_query):
    bad_statements = ['CREATE ', 'DROP ', 'DELETE ', 'UPDATE ', 'INSERT ']
    if any(statement in host_query.upper() for statement in bad_statements):
        raise ValidationError(u'Query has bad statements')
