from logical.models import Database

from dbaas.celery import app


@app.task
def purge_quarantine():
    Database.purge_quarantine()
    return
