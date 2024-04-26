# Standard Library
import random
import zlib
from functools import lru_cache

# Third Party
from django_sqids import SqidsField


@lru_cache
def shuffled_alphabet(model_name: str) -> str:
    rand = random.Random(model_name)
    alphabet = list(map(chr, [*range(65, 91), *range(97, 123)]))
    shuffled = rand.sample(alphabet, len(alphabet))
    return "".join(shuffled)


class SqidsModelField(SqidsField):
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
