from django import template

register = template.Library()

@register.filter
def field_value(obj, name):
    return getattr(obj, name, '')
