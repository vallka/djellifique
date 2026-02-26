from django import template
from django.templatetags.static import static

register = template.Library()

@register.simple_tag
def static_url(path: str) -> str:
    return static(path)

SYMBOLS = {"GBP":"£","USD":"$","CAD":"C$","AUD":"A$","NZD":"NZ$"}

@register.filter
def currency_symbol(code):
    return SYMBOLS.get(code, "")