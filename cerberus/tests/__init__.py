# Standard Library
from decimal import Decimal
from random import randint

# Third Party
from model_bakery import baker

baker.generators.add("djmoney.models.fields.MoneyField", lambda: Decimal(randint(100, 9999) / 100))
baker.generators.add("django_sqids.field.SqidsField", lambda: None)
