O dbaas é um serviço cadastrado no tsuru.

A App Tsuru no DBaaS utiliza o Django Rest Framework e a autenticação no ambiente de dev utiliza "Basic Authentication"


comente a seguinte linha no settings.py do seu ambiente local
#'django.middleware.csrf.CsrfViewMiddleware',


As URLS disponíveis para o projeto podem ser encontradas em:

dbaas/tsuru/urls.py

EX:
#utilize o mesmo USER  e PASS do login  dev
## criando database
curl --location --request POST 'localhost:8000/dev/tsuru/resources' \
-u [USER]:[PASS] \
--header 'Content-Type: application/json' \
--data-raw '{"name": "[DB_NAME]","team": "dbaas", "description": "test","plan":"redis-single-not-persisted-4-0-rjdev-dev", "user": "[DBAAS_USER]@g.globo"}'

## removendo database
curl --location --request DELETE 'localhost:8000/dev/tsuru/resources/[DB_NAME]' \
-u [USER]:[PASS] \
--header 'Content-Type: application/json'