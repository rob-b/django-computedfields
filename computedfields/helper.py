from itertools import tee
try:
    from django.utils.six.moves import zip
except ImportError:
    pass


def pairwise(iterable):
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def is_computedfield(model, field):
    return hasattr(model, '_computed_fields') and field in model._computed_fields


def modelname(model):
    return '%s.%s' % (model._meta.app_label, model._meta.verbose_name)


def is_sublist(needle, haystack):
    if not needle:
        return True
    if not haystack:
        return False
    max_k = len(needle) - 1
    k = 0
    for elem in haystack:
        if elem != needle[k]:
            k = 0
            continue
        if k == max_k:
            return True
        k += 1
    return False


def get_fk_fields_for_update(update_fields, model):
    # FIXME: to be precalc'ed and removed
    from django.db.models import ForeignKey
    fks = set(f.name for f in filter(lambda f: isinstance(f, ForeignKey), model._meta.get_fields()))
    return fks & update_fields if update_fields else fks
