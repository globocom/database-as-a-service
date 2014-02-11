from logical.models import Database

from dbaas.celery import app


@app.task
@only_one(key="purgequarantinekey", timeout=20)
def purge_quarantine():
    Database.purge_quarantine()
    return
