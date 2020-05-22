import ctypes
from html import unescape
from typing import Optional, Any


def int_overflow(val):
    maxint = 2147483647
    if not -maxint-1 <= val <= maxint:
        val = (val + (maxint + 1)) % (2 * (maxint + 1)) - maxint - 1
    return val


def unsigned_right_shift(n, i):
    if n < 0:
        n = ctypes.c_uint32(n).value
    if i < 0:
        return -int_overflow(n << abs(i))
    return int_overflow(n >> i)


def parse_lrc_time(time: str) -> str:
    """ parse float time string to mm:ss.ms

    :param time: float time string
    :type time: str
    :return: mm:ss.ms
    :rtype: str
    """
    time = float(time)
    minute = int(time // 60)
    seconds = int(time - minute * 60)
    ms = int((time - int(time)) * 1000)
    minutes_str = str(minute).zfill(2)
    seconds_str = str(seconds).zfill(2)
    ms_str = str(ms).ljust(3, '0')
    return f'{minutes_str}:{seconds_str}.{ms_str}'


def parse_lyrics(lyrics: Optional[list]) -> Optional[str]:
    """ parse lyrics to lrc file content

    :param lyrics: lyrics list
    :type lyrics: list, optional
    :return: lrc file content
    :rtype: str, optional
    """
    if not lyrics:
        return None
    content = []
    for line in lyrics:
        time = line.get('time')
        ll = line.get('lineLyric')
        if not time:
            continue
        content.append(f'[{parse_lrc_time(time)}]{unescape(ll)}')
    return "\n".join(content)


def digest_encrypt(s: str) -> str:
    from hashlib import md5
    return md5(s.encode('UTF-8')).digest().hex()
