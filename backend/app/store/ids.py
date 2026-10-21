"""UUIDv7 generation (RFC 9562). Python 3.12's uuid module has no uuid7."""

import os
import time
import uuid

_UNIX_TS_MS_BITS = 48
_RAND_A_MASK = 0x0FFF
_RAND_B_MASK = (1 << 62) - 1


def uuid7() -> uuid.UUID:
    """Return a time-ordered, random UUIDv7. Random IDs make objects hard to enumerate."""
    timestamp_ms = time.time_ns() // 1_000_000
    random_bits = int.from_bytes(os.urandom(10), "big")
    rand_a = random_bits & _RAND_A_MASK
    rand_b = (random_bits >> 12) & _RAND_B_MASK

    value = (timestamp_ms & ((1 << _UNIX_TS_MS_BITS) - 1)) << 80
    value |= 0x7 << 76  # version
    value |= rand_a << 64
    value |= 0b10 << 62  # RFC 4122 variant
    value |= rand_b
    return uuid.UUID(int=value)
