O dbaas é um serviço cadastrado no tsuru.

A App Tsuru no DBaaS utiliza o Django Rest Framework e a autenticação no ambiente de dev utiliza "Basic Authentication"

EX:

comente a seguinte linha no settings.py do seu ambiente local
#'django.middleware.csrf.CsrfViewMiddleware',

#utilize o mesmo USER  e PASS do login  dev

  curl --location --request POST 'localhost:8000/dev/tsuru/resources' \
-u [USER]:[PASS]
--header 'Content-Type: application/json' \
--data-raw '{}'