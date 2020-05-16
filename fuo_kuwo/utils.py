def parse_lrc_time(time) -> str:
    time = float(time)
    minute = int(time // 60)
    seconds = int(time - minute * 60)
    ms = int((time - int(time)) * 1000)
    minutes_str = str(minute).zfill(2)
    seconds_str = str(seconds).zfill(2)
    ms_str = str(ms).ljust(3, '0')
    return f'{minutes_str}:{seconds_str}.{ms_str}'


def parse_lyrics(lyrics: list) -> str:
    content = []
    for line in lyrics:
        time = line.get('time')
        ll = line.get('lineLyric')
        if not time:
            continue
        content.append(f'[{parse_lrc_time(time)}]{ll}')
    return "\n".join(content)
