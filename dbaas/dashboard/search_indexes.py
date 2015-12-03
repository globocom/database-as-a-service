from haystack import indexes
from logical.models import Database


class DatabaseIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.EdgeNgramField(document=True, use_template=True)
    name = indexes.CharField(model_attr='name')
    team = indexes.CharField(model_attr='team')
    project = indexes.CharField(model_attr='project', default="")
    databaseinfra = indexes.CharField(model_attr='databaseinfra',)

    def prepare_databaseinfra(self, obj):
        return "%s" % (obj.databaseinfra.name)

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def get_model(self):
        return Database
