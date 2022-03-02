from django import template

register = template.Library()

@register.filter
def get_value_in_qs(queryset, key):
    return queryset.questions(key)
