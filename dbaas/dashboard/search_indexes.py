from haystack import indexes
from logical.models import Database


class DatabaseIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.NgramField(document=True, use_template=True)
    name =  indexes.CharField(model_attr='name')

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def get_model(self):
        return Database
