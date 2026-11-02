from django import template
from django.utils.html import format_html

register = template.Library()


@register.filter(name="highlight_after_semicolon")
def highlight_after_semicolon(value):
    """Wrap everything after the first semicolon in a highlight span."""
    text = "" if value is None else str(value)
    if ":" not in text:
        return text

    prefix, suffix = text.split(":", 1)
    if not suffix:
        return text

    return format_html(
        '{}:<span class="title-semicolon-highlight">{}</span>',
        prefix,
        suffix,
    )
