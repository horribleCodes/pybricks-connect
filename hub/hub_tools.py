from usys import stdin, stdout

# Strings of characters allowed for input.
ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ "
NUM_NATURAL = "0123456789"
NUM_DECIMAL = NUM_NATURAL + "."
NUM_SIGNED = NUM_NATURAL + "-"
NUM_DECSIG = NUM_DECIMAL + "-"

# Control characters used for communication.
STX = b"\x02"  # Start of Text. Indicates the start of output.
ETX = b"\x03"  # End of Text. Indicates the end of a command.
ENQ = b"\x05"  # Enquiry. Indicates the program is ready for input.
NAK = b"\x15"  # Negative Acknowledge. Indicates the failure to execute a command.
EM = b"\x19"  # Start of Heading. Indicates the successful setup of the program.
SUB = b"\x1a"  # Substitute. Indicates the successful execution of a command. (x06 used by Bleak)
ESC = b"\x1b"  # Escape. Indicates the termination of the program.
FS = b"\x1c"  # File Separator. Indicates read mode toggle.

CONTROL_CHARS = {
    "STX": STX,
    "ETX": ETX,
    "ENQ": ENQ,
    "NAK": NAK,
    "EM": EM,
    "SUB": SUB,
    "ESC": ESC,
    "FS": FS,
}


def convert_to_bytes(data):
    """
    Converts data to a byte string if it isn't already.

    Args:
        data (Any): The data to convert.

    Returns:
        data (bytes): The data as a byte string.
    """
    if data is None:
        return b""
    if isinstance(data, bytes):
        return data
    elif isinstance(data, bytearray):
        return bytes(data)
    else:
        return bytes(str(data), "utf-8")


DEBUG_CONTROL_CHARS = {
    key: convert_to_bytes(key) + CONTROL_CHARS[key] for key in CONTROL_CHARS.keys()
}


def setup_chars(debug: bool = False):
    """
    Set up the control characters for communication.

    Args:
        debug (bool): Determines whether to use non-printable characters or their shortcuts.
        Defaults to False.
    """
    global_vars = globals()

    if debug:
        print("Debug mode enabled.")
        for key, value in DEBUG_CONTROL_CHARS.items():
            global_vars[key] = value
    else:
        for key, value in CONTROL_CHARS.items():
            global_vars[key] = value


def convert_to_int(data):
    """
    Converts data to an integer if it isn't already.

    Args:
        data (Any): The data to convert.

    Returns:
        data (int): The data as an integer.
    """
    output = None
    try:
        if isinstance(data, int):
            output = data
        else:
            output = int(data)
    except ValueError:
        print(f'ValueError: Invalid parameter "{data}".')
    finally:
        return output


def convert_to_float(data):
    """
    Converts data to a float if it isn't already.

    Args:
        data (Any): The data to convert.

    Returns:
        data (float): The data as a float.
    """
    output = None
    try:
        if isinstance(data, float):
            output = data
        else:
            output = float(data)
    except ValueError:
        print(f'ValueError: Invalid parameter "{data}".')
    finally:
        return output


def print_binary(char):
    stdout.buffer.write(char)


def read_indefinite(
    prompt=None, end_char=b"\r", allowed_chars=ALPHABET, prefix_enq=True
):
    """
    Reads input from the user until a specific end character is encountered.

    Args:
        prompt (str, optional): The prompt to display before reading input. Defaults to None.
        end_char (bytes, optional): The character that indicates the end of input. Defaults to \r.
        allowed_chars (bytes, optional): The set of allowed characters. Defaults to all letters.

    Returns:
        input (bytes): The input read from the user.
    """
    # Ensure there is always an end character.
    if end_char is None or end_char == b"":
        end_char = b"\r"
    else:
        end_char = convert_to_bytes(end_char)

    if allowed_chars is not None:
        allowed_chars = convert_to_bytes(allowed_chars)
    input = b""
    prompt_text = None
    if prompt:
        prompt_text = "%s: " % prompt
        print(prompt_text, end="")

    if prefix_enq:
        print_binary(ENQ)

    while True:
        new_byte = stdin.buffer.read(1)
        if new_byte == end_char:
            print()
            return input.lower().strip()
        if allowed_chars is not None:
            if new_byte not in allowed_chars:
                continue
        input += new_byte
        print_binary(new_byte)


def read_parameters(*prompts, end_char=None, allowed_chars=None):
    return [
        read_indefinite(prompt=prompt, end_char=end_char, allowed_chars=allowed_chars)
        for prompt in prompts
    ]


def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))


def abs_deg(angle):
    angle = angle % 360
    if angle < 0:
        angle -= 360
    return angle


def get_name_of_object(obj):
    """
    Get the name of an object.

    Args:
        obj (Any): The object to get the name of.
    Returns:
        name(str): The name of the object.
    """
    name = str(obj).split("'")[1].split(".")[-1]
    return name


setup_chars()
