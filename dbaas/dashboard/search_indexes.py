from haystack import indexes
from logical.models import Database
from account.models import Team
from logical.models import Project


class DatabaseIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.EdgeNgramField(document=True, use_template=True)
    name =  indexes.CharField(model_attr='name')
    team = indexes.CharField(model_attr='team')
    project = indexes.CharField(model_attr='project', null=True)

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def get_model(self):
        return Database
