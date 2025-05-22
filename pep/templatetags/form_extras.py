from django import template

register = template.Library()

@register.filter
def add_placeholder(field, text):
    return field.as_widget(attrs={"placeholder": text})
