import json
from urllib.parse import urlparse

from feeluown.library import SongModel, BriefAlbumModel, BriefArtistModel
from fuo_kuwo.provider import _deserialize
from fuo_kuwo.schemas import KuwoSongSchema, KuwoArtistSchema


class TestSchemas:
    def test_search_song_schema(self):
        with open('./examples/search.json', 'r') as f:
            data_songs = json.load(f)
            for data_song in data_songs.get('data', {}).get('list', []):
                song = _deserialize(data_song, KuwoSongSchema)
                assert isinstance(song, SongModel)
                assert isinstance(song.identifier, str)
                assert isinstance(song.title, str)
                assert isinstance(song.cache_get('lossless')[0], bool)
                hasmv = song.cache_get('hasmv')[0]
                assert isinstance(hasmv, int)
                assert hasmv in (True, False)
                assert isinstance(song.duration, int)
                if song.artists and len(song.artists) > 0:
                    assert isinstance(song.artists[0], BriefArtistModel)
                if song.album:
                    assert isinstance(song.album, BriefAlbumModel)

    def test_search_artist_schema(self):
        with open('./examples/search_artist.json', 'r') as f:
            data_artists = json.load(f)
            for data_artist in data_artists.get('data', {}).get('artistList', []):
                artist = _deserialize(data_artist, KuwoArtistSchema)
                assert isinstance(artist.identifier, str)
                assert isinstance(artist.name, str)
                assert isinstance(artist.pic_url, str)
                uri = urlparse(artist.pic_url)
                assert uri.hostname == 'star.kuwo.cn'
                uri.path.endswith('.jpg')
                assert isinstance(artist.description, str)
