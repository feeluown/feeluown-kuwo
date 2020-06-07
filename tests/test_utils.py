import json

from fuo_kuwo.utils import parse_lrc_time, parse_lyrics, digest_encrypt


class TestUtils:
    def test_parse_lrc_time(self):
        assert parse_lrc_time("0.00") == "00:00.000"
        assert parse_lrc_time("6.71") == "00:06.710"
        assert parse_lrc_time("69.87") == "01:09.870"

    def test_parse_lyrics(self):
        with open('./examples/song_lyrics.json', 'r') as f:
            data = json.load(f)
            content = parse_lyrics(data.get('data').get('lrclist'))
            assert isinstance(content, str)

    def test_digest_encrypt(self):
        s = 'This is a test string'
        res = digest_encrypt(s)
        assert isinstance(s, str)
        assert res == 'c639efc1e98762233743a75e7798dd9c'
