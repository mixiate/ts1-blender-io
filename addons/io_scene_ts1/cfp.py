import math
import struct

def decode_delta(delta):
    return 3.9676e-10 * math.pow(float(delta) - 126.0, 3) * abs(float(delta) - 126.0)

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
            values.append(previous_value + decode_delta(compression_type))

        previous_value = values[-1]

    return values


def create_delta_table():
    delta_table = list()
    for i in range(253):
        delta_table.append(decode_delta(i))
    return delta_table


def encode_value_full(value):
    return bytes([0xFF]) + struct.pack('<f', value)


def encode_value_repeat(repeat_count):
    return bytes([0xFE]) + struct.pack('<H', repeat_count - 1)


def encode_value_delta(delta):
    return struct.pack('<B', delta)


def encode_values(values, compress):
    delta_table = create_delta_table()

    encoded_bytes = bytes()

    values = iter(values)
    previous_value = next(values)
    encoded_bytes += encode_value_full(previous_value)

    repeat_count = 0
    for value in values:
        difference = value - previous_value
        delta_index, delta = min(enumerate(delta_table), key=lambda x: abs(x[1] - difference))

        if compress:
            if delta_index >= 120 and delta_index < 133 and repeat_count < 65535:
                # if the sign of the value changes, we need to make sure
                # that this change is outputted for the quaternions to work
                if delta_index != 126 and not (value * previous_value >= 0.0):
                    delta_index = 133 if value >= 0.0 else 119
                    delta = delta_table[delta_index]
                else:
                    repeat_count += 1
                    continue
        else:
            if value == previous_value and repeat_count < 65535:
                repeat_count += 1
                continue

        if repeat_count > 0:
            encoded_bytes += encode_value_repeat(repeat_count)
            repeat_count = 0

        delta_difference = abs(difference - delta)
        if not compress or delta_difference > 0.001:
            encoded_bytes += encode_value_full(value)
            previous_value = value
        else:
            encoded_bytes += encode_value_delta(delta_index)
            previous_value += delta

    if repeat_count > 0:
        encoded_bytes += encode_value_repeat(repeat_count)

    return encoded_bytes


def read_file(file_path, position_count, rotation_count):
    file = open(file_path, mode='rb')

    decoded_values = decode_values(file, (position_count * 3) + (rotation_count * 4))

    try:
        file.read(1)
        raise Exception("data left unread at end of cfp file")
    except:
        pass

    values = {}

    values["positions_x"] = decoded_values[:position_count]
    values["positions_y"] = decoded_values[position_count:position_count * 2]
    values["positions_z"] = decoded_values[position_count * 2:position_count * 3]

    rotation_offset = position_count * 3
    values["rotations_x"] = decoded_values[rotation_offset:rotation_offset + rotation_count]
    values["rotations_y"] = decoded_values[rotation_offset + rotation_count:rotation_offset + (rotation_count * 2)]
    values["rotations_z"] = decoded_values[rotation_offset + (rotation_count * 2):rotation_offset + (rotation_count * 3)]
    values["rotations_w"] = decoded_values[rotation_offset + (rotation_count * 3):rotation_offset + (rotation_count * 4)]

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
