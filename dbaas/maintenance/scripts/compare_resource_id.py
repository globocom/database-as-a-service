from faasclient.client import Client


credential = get_credentials_for(
    Environment.objects.get(name='dev'),
    CredentialType.FAAS
)
faas_client = Client(
  authurl=credential.endpoint,
  user=credential.user, key=credential.password,
  tenant_name=credential.project,
  insecure=False
)
for vol in Volume.objects.filter(
        host__instances__databaseinfra__environment__name='dev'):
    p = VolumeProviderBase(vol.host.instances.first())
    database_resource = p.get_volume(vol).get('resource_id')
    faas_resource = faas_client.export_get(vol.identifier)[1].get(
        'resource_id'
    )

    if database_resource != faas_resource:
        print "volume {} com resource diferente dbaas: {} faas: {}".format(
            vol.identifier, database_resource, faas_resource
        )
    else:
        print "Volume {} OK".format(vol.identifier)
