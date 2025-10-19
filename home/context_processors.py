import json
from django_countries import countries
from .country_phone_codes import COUNTRY_PHONE_CODES


def countries_list(request):
    # return list of country names for templates and a mapping name->alpha-2 code
    all_countries = [(code, name) for code, name in countries]
    # mapping from display name to alpha2 code (lowercase) for flag assets
    name_to_code = {name: code.lower() for code, name in all_countries}
    # mapping from display name to phone code
    name_to_phone = {name: COUNTRY_PHONE_CODES.get(code, '') for code, name in all_countries}
    return {
        'ALL_COUNTRIES': [name for code, name in all_countries],
        'ALL_COUNTRIES_MAP': name_to_code,
        'ALL_COUNTRIES_MAP_JSON': json.dumps(name_to_code),
        'ALL_COUNTRIES_PHONE_JSON': json.dumps(name_to_phone),
    }
