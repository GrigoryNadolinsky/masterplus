# myapp/templatetags/custom_tags.py
from django import template

register = template.Library()

@register.simple_tag
def get_user_full_name(user):
    return user.get_full_name() if user.get_full_name() else user.username

@register.filter(name='add_class')
def add_class(field, css_class):
    if hasattr(field, 'as_widget'):
        classes = field.field.widget.attrs.get('class', '')
        if field.errors:
            css_class += ' is-invalid'
        return field.as_widget(attrs={"class": f"{classes} {css_class}".strip()})
    return field
