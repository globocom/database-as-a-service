from slugify import slugify as slugify_function

def slugify(string):
    return slugify_function(string, separator="_")