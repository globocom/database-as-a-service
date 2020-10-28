from . import mongodb


class MongoDBk8s(mongodb.MongoDB):

    @classmethod
    def topology_name(cls):
        return ['mongodb_single_k8s']

    def build_new_infra_auth(self):
        init_user, init_password = self.get_initial_infra_credentials()
        return init_user, init_password, None


class MongoDBReplicaSetk8s(MongoDBk8s):

    @classmethod
    def topology_name(cls):
        return ['mongodb_replica_set_k8s']
