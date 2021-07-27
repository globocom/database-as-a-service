DBaas is a service in tsuru.

The tsuru app in DBaaS is writed using Django rest framework and the auth system uses "Basic Auth"


# Test API in DEV
comment the following line in settings.py file to disable CSRF verification in local environment.

#'django.middleware.csrf.CsrfViewMiddleware',


The URLs used to receive Tsuru requests can be found in the following file
`dbaas/tsuru/urls.py`

EX:
#Use the same user and pass from dbaas dev login
## creating database
curl --location --request POST 'localhost:8000/dev/tsuru/resources' \
-u [USER]:[PASS] \
--header 'Content-Type: application/json' \
--data-raw '{"name": "[DB_NAME]","team": "dbaas", "description": "test","plan":"redis-single-not-persisted-4-0-rjdev-dev", "user": "[DBAAS_USER]@g.globo"}'

## destroying database
curl --location --request DELETE 'localhost:8000/dev/tsuru/resources/[DB_NAME]' \
-u [USER]:[PASS] \
--header 'Content-Type: application/json'