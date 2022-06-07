import json
from urllib.parse import urlparse

from fuo_kuwo.models import _deserialize
from fuo_kuwo.schemas import KuwoArtistSchema, KuwoSongSchemaV2


class TestSchemas:
    def test_search_song_schema(self):
        with open('./examples/search.json', 'r') as f:
            data_songs = json.load(f)
            for data_song in data_songs.get('data', {}).get('list', []):
                song = _deserialize(data_song, KuwoSongSchemaV2, v2_model=True)
                assert isinstance(song.identifier, str)
                assert isinstance(song.title, str)
                assert isinstance(song.duration, int)

    def test_search_artist_schema(self):
        with open('./examples/search_artist.json', 'r') as f:
            data_artists = json.load(f)
            for data_artist in data_artists.get('data', {}).get('artistList', []):
                artist = _deserialize(data_artist, KuwoArtistSchema)
                assert isinstance(artist.identifier, int)
                assert isinstance(artist.name, str)
                assert isinstance(artist.cover, str)
                uri = urlparse(artist.cover)
                assert uri.hostname == 'star.kuwo.cn'
                uri.path.endswith('.jpg')
                assert isinstance(artist.desc, str)
                assert isinstance(artist.info, str)
