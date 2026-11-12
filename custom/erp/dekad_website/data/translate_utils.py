# -*- coding: utf-8 -*-
"""Translation helpers for the static page catalogs (apps / industries /
services).

The catalogs are plain Python dicts, so their visitor-facing strings are
wrapped in ``_lt(...)`` (Odoo's LazyTranslate): that makes Odoo's
"Export Translation" pick them up into ``i18n/*.po`` like any other code
term, and resolves them in the current request language at render time.

``localize()`` turns a (nested) catalog value into plain ``str`` for the
current language right before it's handed to QWeb, so templates keep
working with normal strings (lazy terms can't be compared/split/hashed).
"""
from odoo.tools.translate import LazyGettext, LazyTranslate

_lt = LazyTranslate('dekad_website')


def localize(value):
    if isinstance(value, LazyGettext):
        return str(value)
    if isinstance(value, dict):
        return {k: localize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [localize(v) for v in value]
    if isinstance(value, tuple):
        return tuple(localize(v) for v in value)
    return value