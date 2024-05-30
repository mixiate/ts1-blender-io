"""Read and write The Sims 1 BCF files."""

import dataclasses
import math
import pathlib
import struct
import typing


from . import utils


def decode_delta(delta: int) -> float:
    """Decode a compressed delta to it's float value."""
    return 3.9676e-10 * math.pow(float(delta) - 126.0, 3) * abs(float(delta) - 126.0)


COMPRESSION_TYPE_FULL = 0xFF
COMPRESSION_TYPE_REPEAT = 0xFE


def decode_values(file: typing.BinaryIO, count: int) -> list[float]:
    """Decode count values from the file."""
    values: list[float] = []

    previous_value = 0.0

    while len(values) < count:
        compression_type = struct.unpack('<B', file.read(1))[0]

        if compression_type == COMPRESSION_TYPE_FULL:
            values.append(struct.unpack('<f', file.read(4))[0])
        elif compression_type == COMPRESSION_TYPE_REPEAT:
            repeat_count = struct.unpack('<H', file.read(2))[0]
            values.extend(previous_value for _ in range(repeat_count + 1))
        else:  # delta
            values.append(previous_value + decode_delta(compression_type))

        previous_value = values[-1]

    return values


def create_delta_table() -> list[float]:
    """Create a table of all delta values."""
    return [decode_delta(i) for i in range(253)]


def encode_value_full(value: float) -> bytes:
    """Encode a value as a single value in full."""
    return bytes([0xFF]) + struct.pack('<f', value)


def encode_value_repeat(repeat_count: int) -> bytes:
    """Encode a value as a repeat sequence."""
    return bytes([0xFE]) + struct.pack('<H', repeat_count - 1)


def encode_value_delta(delta: int) -> bytes:
    """Encode a value as a delta to the previous value."""
    return struct.pack('<B', delta)


UNUSED_DELTA_START = 120
UNUSED_DELTA_END = 133
DELTA_ZERO = 126
MAX_REPEAT_COUNT = 65535
DELTA_DIFFERENCE_THRESHOLD = 0.001


def encode_values(values: typing.Iterator[float], *, compress: bool) -> bytes:
    """Encode values to a list of bytes with or without compression."""
    delta_table = create_delta_table()

    encoded_bytes = b""

    previous_value = next(values)
    encoded_bytes += encode_value_full(previous_value)

    repeat_count = 0
    for value in values:
        difference = value - previous_value
        delta_index, delta = min(enumerate(delta_table), key=lambda x: abs(x[1] - difference))

        if compress:
            if delta_index >= UNUSED_DELTA_START and delta_index < UNUSED_DELTA_END and repeat_count < MAX_REPEAT_COUNT:
                # if the sign of the value changes, we need to make sure
                # that this change is outputted for the quaternions to work
                if delta_index != DELTA_ZERO and not (value * previous_value >= 0.0):
                    delta_index = UNUSED_DELTA_END if value >= 0.0 else UNUSED_DELTA_START - 1
                    delta = delta_table[delta_index]
                else:
                    repeat_count += 1
                    continue
        elif value == previous_value and repeat_count < MAX_REPEAT_COUNT:
            repeat_count += 1
            continue

        if repeat_count > 0:
            encoded_bytes += encode_value_repeat(repeat_count)
            repeat_count = 0

        delta_difference = abs(difference - delta)
        if not compress or delta_difference > DELTA_DIFFERENCE_THRESHOLD:
            encoded_bytes += encode_value_full(value)
            previous_value = value
        else:
            encoded_bytes += encode_value_delta(delta_index)
            previous_value += delta

    if repeat_count > 0:
        encoded_bytes += encode_value_repeat(repeat_count)

    return encoded_bytes


@dataclasses.dataclass
class Cfp:
    """Individual lists of all the CFP values."""

    positions_x: list[float]
    positions_y: list[float]
    positions_z: list[float]
    rotations_x: list[float]
    rotations_y: list[float]
    rotations_z: list[float]
    rotations_w: list[float]


def read_file(file_path: pathlib.Path, position_count: int, rotation_count: int) -> Cfp:
    """Read a file as a CFP."""
    try:
        with file_path.open(mode='rb') as file:
            decoded_values = decode_values(file, (position_count * 3) + (rotation_count * 4))

            if len(file.read(1)) != 0:
                raise utils.FileReadError

    except (OSError, struct.error) as exception:
        raise utils.FileReadError from exception

    positions_x = decoded_values[:position_count]
    positions_y = decoded_values[position_count : position_count * 2]
    positions_z = decoded_values[position_count * 2 : position_count * 3]

    rotation_offset = position_count * 3
    rotations_x = decoded_values[rotation_offset : rotation_offset + rotation_count]
    rotations_y = decoded_values[rotation_offset + rotation_count : rotation_offset + (rotation_count * 2)]
    rotations_z = decoded_values[rotation_offset + (rotation_count * 2) : rotation_offset + (rotation_count * 3)]
    rotations_w = decoded_values[rotation_offset + (rotation_count * 3) : rotation_offset + (rotation_count * 4)]

    return Cfp(
        positions_x,
        positions_y,
        positions_z,
        rotations_x,
        rotations_y,
        rotations_z,
        rotations_w,
    )


def write_file(
    file_path: pathlib.Path,
    cfp: Cfp,
    *,
    compress: bool,
) -> None:
    """Write a CFP to a file."""
    import itertools

    values = itertools.chain(cfp.positions_x, cfp.positions_y)
    values = itertools.chain(values, cfp.positions_z)
    values = itertools.chain(values, cfp.rotations_x)
    values = itertools.chain(values, cfp.rotations_y)
    values = itertools.chain(values, cfp.rotations_z)
    values = itertools.chain(values, cfp.rotations_w)

    with file_path.open('wb') as file:
        file.write(encode_values(values, compress=compress))
        file.close()
