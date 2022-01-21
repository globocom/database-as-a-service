UPDATE physical_diskofferingtype
SET identifier = 'HDD', is_default = 1
WHERE type in('default', 'pd-standard');

UPDATE physical_diskofferingtype
SET identifier = 'SSD' WHERE type = 'pd-ssd';

UPDATE physical_diskofferingtype
SET identifier = 'BALANCED' WHERE type in('pd-balanced');


