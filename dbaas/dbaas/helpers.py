from email_extras.utils import send_mail_template
from django.contrib.sites.models import Site

from system.models import Configuration


class EmailHelper(object):

    extra_explanation_action_map = {
        'restart_database': ("Restart is necessary to change the database's "
                             "log path.")
    }
    task_warning_title_action_map = {
        'restart_database': ("The Restart of {} will be executed "
                             "within 24 hours."),
        'update_ssl': ("Update of {}'s SSL certificate will be executed "
                       "within 24 hours.")
    }
    @staticmethod
    def get_domain():
        domain = Site.objects.get(id=1).domain
        if not domain.startswith('http'):
            return "http://" + domain

        return domain

    @staticmethod
    def email_from():
        return Configuration.get_by_name("email_addr_from")

    @staticmethod
    def email_to(database):
        if database and database.team and database.team.email:
            return list(set([
                database.team.email,
                Configuration.get_by_name("new_user_notify_email")
            ]))
        return Configuration.get_by_name("new_user_notify_email")

    @classmethod
    def send_mail(cls, subject, template_name, template_context, action,
                  database=None, fail_silently=False, attachments=None):
        action_extra_explanation = cls.extra_explanation_action_map.get(action)
        if (template_context.get('extra_explanation') is None
                and action_extra_explanation):
            template_context['extra_explanation'] = action_extra_explanation
        task_warning_title = cls.task_warning_title_action_map.get(action)
        if task_warning_title:
            template_context['task_warning_title'] = task_warning_title.format(
                database.name
            )
        send_mail_template(
            subject, template_name, cls.email_from(), cls.email_to(database),
            fail_silently=fail_silently, attachments=attachments,
            context=template_context
        )
