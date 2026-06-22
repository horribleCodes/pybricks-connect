"""
Module to interface with the Pybricks Hub using the Bleak library.
Used to connect/disconnect to the hub, send messages, and receive responses.
"""

from asyncio import Event, Lock
import re
from bleak import BleakScanner, BleakClient

# UUIDs used by BLE devices
_PYBRICKS_COMMAND_EVENT_CHAR_UUID = "c5f50002-8280-46da-89f4-6d8051e4aeef"

NL = b"\n"
CRNL = b"\r\n"

# Control characters
SOH = 0x01  # Used by Bleak to indicate the start of output
STX = b"\x02"
ETX = b"\x03"
ENQ = b"\x05"
EOT = b"\x06"  # Used by Bleak to indicate the start of input
NAK = b"\x15"
EM = b"\x19"
SUB = b"\x1a"
ESC = b"\x1b"
FS = b"\x1c"
GS = b"\x1d"
RS = b"\x1e"
US = b"\x1f"
# List of control characters sent by the hub that we need to handle
CONTROL_CHARS = [STX, ETX, ENQ, SUB, NL, NAK, EM, ESC, FS, GS, RS, US]


def contains_any(string, char_list):
    return any(char in string for char in char_list)


def split_on_first_char(string, char_list):
    string = bytes(string)
    for i, char in enumerate(string):
        char = bytes([char])
        if char in char_list:
            j = i + 1
            return string[:j], string[j:]
    return string, b""


class BleakInterface:
    """
    Interface to the Pybricks Hub using the Bleak library.
    """

    def __init__(self, hub_name: str = "Pybricks Hub"):
        """
        Initializes the BleakInterface with the given hub name.

        Args:
            hub_name (str, optional): The name of the hub to connect to.
            This name will be used to search for the device using BLE. Defaults to "Pybricks Hub".
        """
        self._client: BleakClient = None
        self._device: BleakScanner = None
        self._VERBOSE: bool = False
        self._QUIET: bool = False
        self._READING: bool = False
        self._OUTPUT_BUFFER: bytearray = bytearray()
        self._BUFFER: bytearray = bytearray()
        self._ETX_EVENT: Event = Event()
        self._RUN_EVENT: Event = Event()
        self._SEND_LOCK: Lock = Lock()
        self._HUB_NAME: str = hub_name
        self._FLAGS: dict = {
            FS: self._toggle_read,
            ETX: self._etx_action,
            EM: self._RUN_EVENT.set,
        }

    # Public
    def hub_name(self, name: str = None):
        """
        Set and/or return the name of the hub.

        Raises:
            RuntimeError: The hub is currently running.
        Args:
            name (str): The new name of the hub.
        Returns:
            str: The current name of the hub.
        """
        if name:
            if self.is_running():
                raise RuntimeError("Cannot change hub name while running.")
            self._HUB_NAME = name
        return self._HUB_NAME

    def is_running(self):
        """
        Returns True if the hub is currently connected and running.
        """
        return self._RUN_EVENT.is_set()

    def is_locked(self):
        """
        Return True if the send function is  locked. This means that the hub is currently
        processing a command and will block any new commands until it is done.
        """
        return self._SEND_LOCK.locked()

    def verbose(self, verbose: bool = None):
        """
        Set and/or return the verbose mode of the interface.

        Args:
            verbose (bool): Whether to print all messages. Defaults to False.
        Raises:
            RuntimeError: The interface is currently locked.
        Returns:
            bool: The current verbose mode.
        """
        if verbose is not None:
            if self._SEND_LOCK.locked():
                raise RuntimeError("Cannot change verbose mode while locked.")
            self._VERBOSE = verbose
        return self._VERBOSE

    def quiet(self, quiet: bool = None):
        """
        Set and/or return the quiet mode of the interface.

        Args:
            quiet (bool): Whether to suppress print statements.
        Raises:
            RuntimeError: The interface is currently locked.
        Returns:
            bool: The current quiet mode.
        """
        if quiet is not None:
            if self._SEND_LOCK.locked():
                raise RuntimeError("Cannot change quiet mode while locked.")
            self._QUIET = quiet
        return self._QUIET

    # TODO: Add quiet mode to public functions
    async def connect(
        self,
        max_repeats: int = 1,
        hub_name: str = None,
        quiet: bool = None,
        verbose: bool = None,
    ):
        """
        Connect to the hub.

        Args:
            max_repeats (int, optional): The number of tries to connect before timing out.
            Defaults to 1.
            hub_name (str, optional): The name of the device to look for. Defaults to "".
            quiet (bool, optional): Whether to suppress the feed from the hub. Defaults to the
            current quiet mode setting.

        Raises:
            RuntimeError: The hub is already running.
            ValueError: The number of tries must be at least 0.

        Returns:
            bool: Whether the connection was successful and the hub is running.
        """
        if self.is_running():
            raise RuntimeError("Hub is already running.")

        if max_repeats < 0:
            raise ValueError("max_repeats must be greater than or equal to 0.")

        # Update settings
        self.hub_name(hub_name)
        self.quiet(quiet)
        self.verbose(verbose)

        # Find the device and initialize client.
        found = await self._find_device(max_repeats)

        if not found:
            self._print('Couldn\'t find a valid device named "%s".' % self._HUB_NAME)
            return self.is_running()

        self._print('Successfully connected to "%s".' % self._HUB_NAME)
        self._client = BleakClient(
            self._device, disconnected_callback=self._handle_disconnect
        )

        try:
            # Connect and get services.
            await self._client.connect()
            await self._client.start_notify(
                _PYBRICKS_COMMAND_EVENT_CHAR_UUID, self._handle_rx
            )

            # Tell user to start program on the hub.
            self._print(
                "Start the program on the hub now by pressing the center button.",
                hide_on_quiet=False,
            )

            await self._RUN_EVENT.wait()
            await self._setup_hub()
        except Exception as e:
            self._print(e, hide_on_quiet=False)

        return self.is_running()

    async def disconnect(self, quiet: bool = None):
        """
        Disconnect from the hub by sending a message. Will finish once the hub has replied with
        an ESC character.
        This sets the running flag to False and clears the start event and client.

        Arguments:
            quiet (bool, optional): Whether to suppress the feed from the hub. Defaults to the
            current quiet mode setting.
        """
        old_quiet = self.quiet()
        self.quiet(quiet)

        # Send a message to indicate stop.
        await self.send("bye")
        await self._client.disconnect()
        self._print('Disconnected from "%s".' % self._HUB_NAME)
        self._RUN_EVENT.clear()
        self._client = None
        self.quiet(old_quiet)

    async def send(self, *args, quiet: bool = None):
        """
        Send a message to the hub and return the response flagged with reading mode.

        Arguments:
            *args: Can be any number of arguments. Each argument will be converted to a string and
            sent as a separate line.
            quiet (bool, optional): Whether to suppress the feed from the hub. Defaults to the
            current quiet mode setting.

        Returns:
            output(list[list[str]]): A list of lists of strings containing the response
            from the hub marked with a read flag. Each list is seperated by a FS character and each
            sublist is seperated by a NL or GS character.
        """
        if self._client is None:
            raise Exception("Client is not connected.")
        if not args:
            raise ValueError("At least one argument is required.")

        old_quiet = self.quiet()
        self.quiet(quiet)

        input = self._build_input(args)
        output = None

        # Acquire the lock
        await self._SEND_LOCK.acquire()

        self._print(*[arg for arg in args], sep=" ")
        try:
            await self._client.write_gatt_char(
                _PYBRICKS_COMMAND_EVENT_CHAR_UUID,
                EOT + input,
                response=True,
            )
            # TODO: Add timeout, return response before OK event to read prompts.
            await self._ETX_EVENT.wait()
        except Exception as e:
            self._print(e, hide_on_quiet=False)
        finally:
            self._ETX_EVENT.clear()  # Reset event after response is received.
            output = self._build_output()  # Get all read values
            if output is not None:
                self._print(*output, sep="\n")
            # Release the lock
            self._SEND_LOCK.release()
            self.quiet(old_quiet)
            if output:
                return output

    # Private
    def _print(self, *args, **kwargs):
        hide_on_quiet = kwargs.pop("hide_on_quiet", True)
        show_on_verbose = kwargs.pop("show_on_verbose", False)
        print_args = True
        if self._QUIET and hide_on_quiet:
            print_args = False
        if not self._VERBOSE and show_on_verbose:
            print_args = False
        if print_args:
            print(*args, **kwargs)

    async def _handle_rx(self, _, data: bytearray):
        if data[0] == SOH:
            payload = data[1:]
            self._BUFFER += payload

        # If a control character is received, handle the response line by line.
        while contains_any(self._BUFFER, CONTROL_CHARS):
            chunk, self._BUFFER = split_on_first_char(self._BUFFER, CONTROL_CHARS)
            self._read_response(chunk)

    async def _find_device(self, max_repeats):
        tries = 0
        found = False
        try:
            while not found:
                self._print("Looking for Mindstorms Hub...")
                self._device = await BleakScanner.find_device_by_name(self._HUB_NAME)
                found = self._device is not None
                tries += 1
                if max_repeats >= 0:
                    if tries >= max_repeats:
                        break
        except OSError as e:
            self._print(e, hide_on_quiet=False)
        if found:
            self._HUB_NAME = self._device.name
        return found

    def _handle_disconnect(self, _):
        self._print("Hub was disconnected.")

    async def _setup_hub(self):
        # TODO: Run commands to set up the interface
        pass

    # Toggles reading mode, which writes every line into an output stack
    def _toggle_read(self):
        self._READING = not self._READING
        # If reading is toggled off, remove everything past the last FS character
        if not self._READING:
            self._OUTPUT_BUFFER = self._OUTPUT_BUFFER.rsplit(FS, 1)[0] + FS

    def _read_response(self, chunk: bytes):
        self._print(chunk.decode("utf-8"), end="", show_on_verbose=True)

        if self._READING:
            self._OUTPUT_BUFFER += chunk

        # Check if the message contains a flag
        flags = [flag for flag in self._FLAGS if flag in chunk]
        actions = [self._FLAGS.get(flag) for flag in flags if self._FLAGS.get(flag)]

        for action in actions:
            action()

    def _etx_action(self):
        if self._READING:
            self._toggle_read()
        self._ETX_EVENT.set()

    def _build_input(self, args):
        data = bytearray()
        for arg in args:
            # Convert the argument to a string and append it to the bytearray
            data += str(arg).encode()

            # Append the delimiter '\r' to the bytearray
            data += CRNL
        return data

    def _char_list_split(self, string, chars: list[bytes]):
        delimiters = [char.decode("utf-8") for char in chars]
        pattern = f"({'|'.join(delimiters)})"
        matches = re.split(pattern, string)
        return [
            match for match in matches if len(match) > 0 and match not in delimiters
        ]

    def _build_output(self):
        if len(self._OUTPUT_BUFFER) == 0:
            return None

        file_delimiters = [FS]
        group_delimiters = [NL, GS]
        output: list[list[str]] = []
        buffer_str = self._OUTPUT_BUFFER.replace(CRNL, NL).decode("utf-8")
        self._OUTPUT_BUFFER = bytearray()
        output_files = self._char_list_split(buffer_str, file_delimiters)
        for file in output_files:
            if not file:
                continue
            groups = self._char_list_split(file, group_delimiters)
            output.append(groups)
        return output
