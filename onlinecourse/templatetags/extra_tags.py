from django import template
from pprint import pprint

register = template.Library()


@register.filter
def is_button_available(questions, lesson):
    is_button = False
    for q_test in questions:
        for lesson_fetch in q_test.lesson_id.all():
            if lesson_fetch == lesson:
                is_button = True
    return is_button
