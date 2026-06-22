from hub_tools import convert_to_bytes, get_name_of_object


def test_convert_to_bytes():
    # Test with a string
    assert convert_to_bytes("Hello, World!") == b"Hello, World!"

    # Test with an integer
    assert convert_to_bytes(12345) == b"12345"

    # Test with a float
    assert convert_to_bytes(3.14) == b"3.14"

    # Test with a boolean
    assert convert_to_bytes(True) == b"True"

    # Test with a bytearray
    assert convert_to_bytes(bytearray(b"bytearray")) == bytearray(b"bytearray")

    # Test with a byte string
    assert convert_to_bytes(b"byte string") == b"byte string"

    # Test with None
    assert convert_to_bytes(None) == b""

    print("convert_to_bytes: All test cases pass")


def test_get_name_of_object():
    # Test with a string
    assert get_name_of_object("Hello, World!") == "str"

    # Test with an integer
    assert get_name_of_object(12345) == "int"

    # Test with a float
    assert get_name_of_object(3.14) == "float"

    # Test with a boolean
    assert get_name_of_object(True) == "bool"

    # Test with a bytearray
    assert get_name_of_object(bytearray(b"bytearray")) == "bytearray"

    # Test with a byte string
    assert get_name_of_object(b"byte string") == "bytes"

    # Test with None
    assert get_name_of_object(None) == "NoneType"

    print("get_name_of_object: All test cases pass")


test_convert_to_bytes()
test_get_name_of_object()
