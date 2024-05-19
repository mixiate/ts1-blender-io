import math
import struct

def decode_values(file, count):
    values = list()

    previous_value = 0.0

    while len(values) < count:
        compression_type = struct.unpack('<B', file.read(1))[0]

        if compression_type == 0xFF: # full 4 byte float
            values.append(struct.unpack('<f', file.read(4))[0])
        elif compression_type == 0xFE: # repeat previous
            repeat_count = struct.unpack('<H', file.read(2))[0]
            for i in range(repeat_count + 1):
                values.append(previous_value)
        else: # delta
            values.append(previous_value + 3.9676e-10 * math.pow(float(compression_type) - 126.0, 3) * abs(float(compression_type) - 126.0))

        previous_value = values[-1]

    return values


def encode_value_full(value):
    return bytes([0xFF]) + struct.pack('<f', value)


def encode_value_repeat(repeat_count):
    return bytes([0xFE]) + struct.pack('<H', repeat_count - 1)


def encode_values(values, compress):
    encoded_bytes = bytes()

    if compress:
        previous_value = float('inf')
        repeat_count = 0
        for value in values:
            if value == previous_value and repeat_count < 65535:
                repeat_count += 1
                continue

            if repeat_count > 0:
                encoded_bytes += encode_value_repeat(repeat_count)
                repeat_count = 0

            encoded_bytes += encode_value_full(value)

            previous_value = value

        if repeat_count > 0:
            encoded_bytes += encode_value_repeat(repeat_count)
    else:
        for value in values:
            encoded_bytes += encode_value_full(value)

    return encoded_bytes


def read_file(file_path, position_count, rotation_count):
    values = {}

    file = open(file_path, mode='rb')

    values["positions_x"] = decode_values(file, position_count)
    values["positions_y"] = decode_values(file, position_count)
    values["positions_z"] = decode_values(file, position_count)

    values["rotations_x"] = decode_values(file, rotation_count)
    values["rotations_y"] = decode_values(file, rotation_count)
    values["rotations_z"] = decode_values(file, rotation_count)
    values["rotations_w"] = decode_values(file, rotation_count)

    try:
        file.read(1)
        raise Exception("data left unread at end of cfp file")
    except:
        pass

    return values


def write_file(
    file_path,
    compress,
    positions_x,
    positions_y,
    positions_z,
    rotations_x,
    rotations_y,
    rotations_z,
    rotations_w
):
    import itertools
    values = itertools.chain(positions_x, positions_y)
    values = itertools.chain(values, positions_z)
    values = itertools.chain(values, rotations_x)
    values = itertools.chain(values, rotations_y)
    values = itertools.chain(values, rotations_z)
    values = itertools.chain(values, rotations_w)

    file = open(file_path, "wb")
    file.write(encode_values(values, compress))
