update physical_plan join physical_engine on (physical_engine.engine_type_id = physical_plan.engine_type_id)
set physical_plan.engine_id = physical_engine.id;
