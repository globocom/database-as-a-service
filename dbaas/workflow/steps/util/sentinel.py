from zabbix import CreateAlarms


class CreateAlarmsNewInfra(CreateAlarms):

    @property
    def is_valid(self):
        return not self.instance.is_database
