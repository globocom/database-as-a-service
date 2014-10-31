from django import forms
from django.utils.safestring import mark_safe



class DatabaseOfferingWidget(forms.widgets.TextInput):

    def render(self, name, value, attrs=None):
       html = super(DatabaseOfferingWidget, self).render(name, value,attrs)

       html = html + """
             <a id="resizeDatabase" class="btn btn-primary" mytitle="Resize database" href="#">
                <i class="icon-resize-full icon-white"></i>
             </a >
            <style type="text/css">

                #resizeDatabase {
                    position: relative;
                }

                #resizeDatabase::after {
                    content: attr(mytitle);

                    position: absolute;

                    opacity: 0;
                    -webkit-transition: opacity .15s ease-in-out;
                    -moz-transition: opacity .15s ease-in-out;
                    -ms-transition: opacity .15s ease-in-out;
                    -o-transition: opacity .15s ease-in-out;
                    transition: opacity .15s ease-in-out;

                    font-size: 0px;
                }

                #resizeDatabase:hover::after {
                    opacity: 1;
                    position:absolute;
                    display:inline-block;
                    padding:5px;
                    font-size:12px;
                    filter:alpha(opacity=0)
                    text-align:right;
                    text-decoration:none;
                    background-color:#000;
                    -webkit-border-radius:4px;
                    -moz-border-radius:4px;
                    border-radius:4px
                    float: right;
                    overflow:hidden;
                    right:-100px;
                    top:0px;

                }
            </style>
         """
       return mark_safe(html);


