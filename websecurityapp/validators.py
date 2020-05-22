from django.core.exceptions import ValidationError

from datetime import datetime, date



def past_validator(value):
    if isinstance(value, date):
        datetime_value = datetime(value.year, value.month, value.day)
    else:
        datetime_value = value
    now = datetime.now()
    if (now - datetime_value).total_seconds() < 0:
        raise ValidationError('La fecha debe ser pasada')