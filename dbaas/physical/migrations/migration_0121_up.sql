UPDATE physical_vip v, physical_databaseinfra d
SET v.vip_ip = SUBSTRING(d.endpoint, 1, position(':' IN d.endpoint) -1 )
WHERE d.id = v.infra_id;