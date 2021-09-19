UPDATE physical_vip v, physical_databaseinfra d
SET v.vip_ip = ''
WHERE d.id = v.infra_id;