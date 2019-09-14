"""
Luxafor usb controller via the Python hid wrapper around libusb/hidapi.

apmorton/pyhidapi: https://github.com/apmorton/pyhidapi
libusb/hidapi: https://github.com/libusb/hidapi

"""
import hid
from .common import LED_ALL, LED_BACK, LED_FRONT, LED_VALID

__version__ = '0.1'

__all__ = ('LuxFlag', 'LED_ALL', 'LED_BACK', 'LED_FRONT')

LUXAFOR_VENDOR = 0x04d8
LUXAFOR_PRODUCT = 0xf372

COLOR_MAP = {
    "red": (255, 0, 0),
    "orange": (255, 69, 0),
    "yellow": (255, 255, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "magenta": (255, 0, 255),
    "indigo": (75, 0, 130),
    "cyan": (0, 255, 255),
    "white": (255, 255, 255),
    "off": (0, 0, 0)
}

COLOR_SIMPLE = {"R", "G", "B", "C", "M", "Y", "W", "O"}

MODE_BASIC = 0x00
MODE_STATIC = 0x01
MODE_FADE = 0x02
MODE_STROBE = 0x03
MODE_WAVE = 0x04
MODE_PATTERN = 0x6

# Message that is sent when a command, that cannont be completed immediatey,
# complets (such as fade).
MSG_NON_IMMEDIATE_COMPLETE = b'\x00\x01\x00\x00\x00\x00\x00\x00'
MSG_NONE = b''
MSG_SIZE = 8

CMD_REPORT_NUM = 0


def clamp(value, mn=0, mx=255):
    """Clamp the value to the the given minimum and maximum."""

    return max(min(value, mx), mn)


def resolve_color(color):
    """Resolve color."""

    if color.startswith('#') and len(color) == 7:
        color = (
            int(color[1:3], 16),
            int(color[3:5], 16),
            int(color[5:7], 16)
        )
    else:
        color = COLOR_MAP[color.lower()]

    return color


def validate_wave(wave):
    """Validate wave."""

    if not (1 <= wave <= 5):
        raise ValueError('Wave must be a positive integer between 1-5, {} was given'.format(wave))


def validate_speed(speed):
    """Validate speed."""

    if not (0 <= speed <= 255):
        raise ValueError('Speed channel must be a positive integer between 0-255, {} was given'.format(speed))


def validate_repeat(repeat):
    """Validate repeat."""

    if not (0 <= repeat <= 255):
        raise ValueError('Repeat channel must be a positive integer between 0-255, {} was given'.format(repeat))


def validate_pattern(pattern):
    """Validate pattern."""

    if not (1 <= pattern <= 8):
        raise ValueError('Pattern must be a positive integer between 1-9, {} was given'.format(pattern))


def validate_led(led):
    """Validate led."""

    if led not in LED_VALID:
        raise ValueError("LED must either be an integer 1-6, 0x41, 0x42, or 0xFF, {} was given".format(led))


def validate_simple_color(color):
    """Validate simple color code."""

    if color not in COLOR_SIMPLE:
        raise ValueError("Accepted color codes are R, G, B, C, M, Y, W, and O, {} was given".format(color))


class LuxFlag:
    """
    Class to controll luxflag.

    This is not implemented.

    - Productivity

      Byte 0: Report number: 0 (Luxafor flag only has 0)
      Byte 1: Command Mode: 10
      Byte 2: Command: E (enable), D (Disable), R, G, B, C, Y, M, W, O (colors)

    """

    def __init__(self):
        """Initialize."""

        self._device = hid.Device(vid=LUXAFOR_VENDOR, pid=LUXAFOR_PRODUCT)

    def __enter__(self):
        """Enter."""

        return self

    def __exit__(self, type, value, traceback):  # noqa: A002
        """Exit."""

        return self.close()

    def close(self):
        """Close luxafor device."""

        return self._device.close()

    def off(self):
        """Set all LEDs to off."""

        self.basic_color('O')

    def basic_color(self, color):
        """
        Build basic color command.

        Byte 0: Report number (Luxafor flag only has 0)
        Byte 1: Color: R, G, B, C, M, Y, W, O
        Byte 2: NA
        Byte 3: NA
        Byte 4: NA
        Byte 5: NA
        Byte 6: NA
        Byte 7: NA
        Byte 8: NA

        """

        color = color.upper()
        validate_simple_color(color)
        self._execute([CMD_REPORT_NUM, MODE_BASIC, ord(color)])

    def color(self, color, *, led=LED_ALL):
        """
        Build static color command.

        Byte 0: Report number: 0 (Luxafor flag only has 0)
        Byte 1: Command Mode: 1
        Byte 2: LED: 1-6, 0x42 (back), 0x41 (tab), 0xFF (all)
        Byte 3: Red channel: 0-255
        Byte 4: Green channel: 0-255
        Byte 5: Blue channel: 0-255
        Byte 6: NA
        Byte 7: NA
        Byte 8: NA

        """

        if isinstance(color, str) and len(color) == 1:
            self.basic_color(color)
        else:
            red, green, blue = resolve_color(color)
            validate_led(led)
            self._execute([CMD_REPORT_NUM, MODE_STATIC, led, red, green, blue, 0, 0, 0])

    def fade(self, color, *, led=LED_ALL, duration=1, wait=False):
        """
        Build fade command.

        Byte 0: Report number: 0 (Luxafor flag only has 0)
        Byte 1: Command Mode: 2
        Byte 2: LED: 1-6, 0x42 (back), 0x41 (tab), 0xFF (all)
        Byte 3: Red channel: 0-255
        Byte 4: Green channel: 0-255
        Byte 5: Blue channel: 0-255
        Byte 6: Fade speed: 0-255
        Byte 7: NA
        Byte 8: NA

        """

        red, green, blue = resolve_color(color)
        validate_led(led)
        validate_speed(duration)
        self._execute([CMD_REPORT_NUM, MODE_FADE, led, red, green, blue, duration, 0, 0], wait=wait)

    def wave(self, color, *, led=LED_ALL, wave=1, duration=0, repeat=0, wait=False):
        """
        Build wave command.

        Byte 0: Report number: 0 (Luxafor flag only has 0)
        Byte 1: Command Mode: 4
        Byte 2: Wave type: 1-5
        Byte 3: Red channel: 0-255
        Byte 4: Green channel: 0-255
        Byte 5: Blue channel: 0-255
        Byte 6: NA
        Byte 7: Repeat: 0-255
        Byte 8: Speed: 0-255

        """

        # We cannot wait when repeat is set to go on forever.
        if repeat == 0:
            wait = False
        red, green, blue = resolve_color(color)
        validate_led(led)
        validate_wave(wave)
        validate_speed(duration)
        validate_repeat(repeat)
        self._execute([CMD_REPORT_NUM, MODE_WAVE, wave, red, green, blue, 0, repeat, duration], wait=wait)

    def strobe(self, color, *, led=LED_ALL, speed=0, repeat=0, wait=False):
        """
        Build strobe command.

        Byte 0: Report number: 0 (Luxafor flag only has 0)
        Byte 1: Command Mode: 3
        Byte 2: LED: 1-6, 0x42 (back), 0x41 (tab), 0xFF (all)
        Byte 3: Red channel: 0-255
        Byte 4: Green channel: 0-255
        Byte 5: Blue channel: 0-255
        Byte 6: Speed: 0-255
        Byte 7: NA
        Byte 8: Repeat: 0-255

        """

        # We cannot wait when repeat is set to go on forever.
        if repeat == 0:
            wait = False
        red, green, blue = resolve_color(color)
        validate_led(led)
        validate_speed(speed)
        validate_repeat(repeat)
        self._execute([CMD_REPORT_NUM, MODE_STROBE, led, red, green, blue, speed, 0, repeat], wait=wait)

    def pattern(self, pattern, *, repeat=0, wait=False):
        """
        Build pattern command.

        Byte 0: Report number: 0 (Luxafor flag only has 0)
        Byte 1: Command Mode: 6
        Byte 2: Pattern ID: 0-8
        Byte 3: Repeat: 0-255

        """

        # We cannot wait when repeat is set to go on forever.
        if repeat == 0:
            wait = False
        validate_pattern(pattern)
        validate_repeat(repeat)
        self._execute([CMD_REPORT_NUM, MODE_PATTERN, pattern, repeat, 0, 0, 0, 0, 0], wait=wait)

    def _execute(self, cmd, wait=False):
        """Set color."""

        self._device.write(bytes(cmd))

        # Wait for commands that take time to complete
        if wait:
            while self._device.read(MSG_SIZE, 100) != MSG_NON_IMMEDIATE_COMPLETE:
                pass
