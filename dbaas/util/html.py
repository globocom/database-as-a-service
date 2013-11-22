# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.safestring import mark_safe, mark_for_escaping

def render_progress_bar(current, total=100, message="%", bar_type="auto", striped=False, active=False):
    """ Returns a html code to render a bootstrap progress bar.
    Params:
        current: current value
        total: total value
        bar_type: one of info/success/warning/danger or auto or None
        striped: if you want striped bars
        active: if you want animated bars
    """
    if total is None: # unlimited
        p = 0.0
        total = current
    else:
        p = int(current * 100 / total)

    html_classes = ["progress"]
    if striped:
        html_classes.append("progress-striped")
    if active:
        html_classes.append("active")

    if bar_type:
        if bar_type == "auto":
            if p < 50:
                bar_type = "info"
            elif p < 75:
                bar_type = "warning"
            else:
                bar_type = "danger"

        html_classes.append("progress-%s" % bar_type)

    if message == '%':
        message = "%(current)d of %(total)d" % {'current': current, 'total': total}

    if message:
        # wrapper message in paragraph
        message = "<p style='padding-left: 10px; position: absolute;'>%s</p>" % mark_for_escaping(message)

    html = """<div class="%(classes)s">%(message)s<div class="bar" style="width: %(p)d%%;"></div></div>""" % \
        {
            "classes": " ".join(html_classes),
            "message": message or "",
            "p": p,
        }
    return mark_safe(html)
