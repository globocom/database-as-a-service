# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from collections import OrderedDict
from rest_framework import renderers


class JSONHalRenderer(renderers.UnicodeJSONRenderer):

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render `data` into JSON.
        """
        if data is None:
            return bytes()

        if isinstance(data, dict):
            data = self.represent_as_hal(data, renderer_context)
        elif hasattr(data, "__iter__"):  # list
            data = [self.represent_as_hal(
                data_obj, renderer_context) for data_obj in data]
        else:
            raise RuntimeError(
                "Unknown type %s for rendering with json-hal. Acceptable types are list and dict")

        return super(JSONHalRenderer, self).render(data, accepted_media_type, renderer_context)

    def get_current_url(self, object_dict, renderer_context):
        url = object_dict.get("url", None)
        if not url and renderer_context:
            url = renderer_context["request"].build_absolute_uri()
        return url

    def get_default_base_name(self, viewset):
        """
        If `base_name` is not specified, attempt to automatically determine
        it from the viewset.
        """
        model_cls = getattr(viewset, 'model', None)
        queryset = getattr(viewset, 'queryset', None)
        if model_cls is None and queryset is not None:
            model_cls = queryset.model

        assert model_cls, '`base_name` argument not specified, and could ' \
            'not automatically determine the name from the viewset, as ' \
            'it does not have a `.model` or `.queryset` attribute.'

        return model_cls._meta.object_name.lower()

    def represent_as_hal(self, object_dict, renderer_context):
        hal = OrderedDict()

        # there is not way to insert key on first element on OrderedDict. So I need to create one
        # with "self" key first and after insert another keys
        if "count" in object_dict and "next" in object_dict and "previous" in object_dict and "results" in object_dict:
            # pagination
            hal["_links"] = {
                "self": self.get_current_url(object_dict, renderer_context),
                "next": object_dict["next"],
                "previous": object_dict["previous"],
                "count": object_dict["count"],
            }
            base_name = self.get_default_base_name(renderer_context["view"])
            hal[base_name] = [
                self.represent_as_hal(obj, renderer_context) for obj in object_dict["results"]]

        else:
            hal["_links"] = {
                "self": self.get_current_url(object_dict, renderer_context),
            }
            hal.update([(k, v)
                        for (k, v) in object_dict.iteritems() if k != "url"])

        return hal
