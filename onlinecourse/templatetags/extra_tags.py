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


@register.filter
def is_choice_correct(correct_answers, choice):
    if choice.is_correct != 1:
        type = 'none'
    else:
        if choice in correct_answers:
            type = 'success'
        else:
            type = 'warning'

    return type


@register.filter
def choice_status(correct_answers, choice):
    if choice.is_correct != 1:
        status = ''
    else:
        if choice in correct_answers:
            status = 'Correct Answer:'
        else:
            status = 'Not Selected:'

    return status
