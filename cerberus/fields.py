# Standard Library
import random
import zlib
from functools import lru_cache, partial
from itertools import groupby
from operator import attrgetter

# Django
from django.forms.models import ModelChoiceIterator, ModelMultipleChoiceField

# Third Party
from django_sqids import SqidsField
from sqids import Sqids


@lru_cache
def shuffled_alphabet(model_name: str) -> str:
    rand = random.Random(model_name)
    alphabet = list(map(chr, [*range(65, 91), *range(97, 123)]))
    shuffled = rand.sample(alphabet, len(alphabet))
    return "".join(shuffled)


class SqidsModelField(SqidsField):
    _sqids_instance: Sqids | None = None

    @property
    def sqids_instance(self) -> Sqids:
        if self._sqids_instance is None:
            raise ValueError("sqids_instance is not set")
        return self._sqids_instance

    @sqids_instance.setter
    def sqids_instance(self, value: Sqids) -> None:
        self._sqids_instance = value

    def get_sqid_instance(self):
        if self.alphabet is None:
            self.alphabet = shuffled_alphabet(self.model._meta.object_name)
        return super().get_sqid_instance()

    def get_prep_value(self, value):
        decoded_values = self.sqids_instance.decode(value)
        if not decoded_values:
            return None

        if len(decoded_values) < 2:
            raise ValueError("Invalid SQID")

        crc32 = zlib.crc32(str(decoded_values[0]).encode())
        if crc32 != decoded_values[1]:
            raise ValueError("CRC32 mismatch")

        return decoded_values[0]

    def __get__(self, instance, name=None):
        if not instance:
            return self
        real_value = getattr(instance, self.real_field_name, None)
        # the instance is not saved yet?
        if real_value is None:
            return ""
        assert isinstance(real_value, int)
        crc32 = zlib.crc32(str(real_value).encode())
        return self.sqids_instance.encode([real_value, crc32])


class GroupedModelChoiceIterator(ModelChoiceIterator):
    def __init__(self, field, groupby):
        self.groupby = groupby
        super().__init__(field)

    def __iter__(self):
        if self.field.empty_label is not None:
            yield ("", self.field.empty_label)
        queryset = self.queryset
        # Can't use iterator() when queryset uses prefetch_related()
        if not queryset._prefetch_related_lookups:
            queryset = queryset.iterator()
        for group, objs in groupby(queryset, self.groupby):
            yield (group, [self.choice(obj) for obj in objs])


class GroupedMultipleModelChoiceField(ModelMultipleChoiceField):
    def __init__(self, *args, choices_groupby, **kwargs):
        if isinstance(choices_groupby, str):
            choices_groupby = attrgetter(choices_groupby)
        elif not callable(choices_groupby):
            raise TypeError("choices_groupby must either be a str or a callable accepting a single argument")
        self.iterator = partial(GroupedModelChoiceIterator, groupby=choices_groupby)
        super().__init__(*args, **kwargs)
