# Standard Library
from decimal import Decimal
from random import random

# Third Party
from model_bakery import baker

baker.generators.add("djmoney.models.fields.MoneyField", lambda: Decimal((random() * 10) + 5))
