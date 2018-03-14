import copy
THREE_TASKS_THREE_NEWS = [
    {
        u'task_id': 1,
        u'task_name': u'notification.fake.task_1',
        u'task_status': 'SUCCESS',
        u'user': 'admin',
        u'arguments': 'Database: fake_database_name_1, New Disk Offering: Micro',
        u'updated_at': 1501177162,
        u'is_new': 1,
        u'read': 0,
    },
    {
        u'task_id': 2,
        u'task_name': u'notification.fake.task_2',
        u'task_status': 'RUNNING',
        u'user': 'admin',
        u'arguments': 'Database: fake_database_name_2, New Disk Offering: Micro',
        u'database_name': 'fake_database_name_from_obj',
        u'updated_at': 1501177162,
        u'is_new': 1,
        u'read': 0,
    },
    {
        u'task_id': 3,
        u'task_name': u'notification.fake.task_3',
        u'task_status': 'ERROR',
        u'user': 'admin',
        u'arguments': 'Database: fake_database_name_3, New Disk Offering: Micro',
        u'updated_at': 1501177162,
        u'is_new': 1,
        u'read': 0,
    }
]

THREE_TASKS_TWO_NEWS = copy.deepcopy(THREE_TASKS_THREE_NEWS)
THREE_TASKS_TWO_NEWS[1]['is_new'] = 0

THREE_TASKS_ZERO_NEWS = copy.deepcopy(THREE_TASKS_THREE_NEWS)
THREE_TASKS_ZERO_NEWS[0]['is_new'] = 0
THREE_TASKS_ZERO_NEWS[1]['is_new'] = 0
THREE_TASKS_ZERO_NEWS[2]['is_new'] = 0
