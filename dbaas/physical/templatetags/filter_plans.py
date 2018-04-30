from django import template

register = template.Library()

@register.inclusion_tag('plans/plans_cells.html')
def table_add_plans(environment, engine):

    active_plans = environment.active_plans().filter(engine=engine)

    return {
        'selected_plans': active_plans,
        'env_name': environment.name,
        'eng_name': engine.full_name
    }
