import logging
import time
from feeluown.excs import ProviderIOError

from feeluown.models import BaseModel, ModelStage, SearchModel, \
    SearchType, PlaylistModel, UserModel, cached_field
from feeluown.utils.reader import SequentialReader

from .api import KuwoApi
from .provider import provider

logger = logging.getLogger(__name__)


def create_g(func, identifier, schema, list_key='list'):
    data = func(identifier, page=1).get('data')
    total = int(data['total'])

    def g():
        nonlocal data
        if data is None:
            yield from ()
        else:
            page = 1
            while data[list_key]:
                obj_data_list = data[list_key]
                for obj_data in obj_data_list:
                    obj = _deserialize(obj_data, schema, gotten=True)
                    yield obj
                page += 1
                data = func(identifier, page=page).get('data', {})

    return SequentialReader(g(), total)


def _deserialize(data, schema_class, gotten=True):
    """ deserialize schema data to model

    :param data: data to be deserialize
    :param schema_class: schema class
    :param gotten:
    :return:
    """
    schema = schema_class()
    obj = schema.load(data)
    if isinstance(obj, BaseModel) and gotten:
        obj.stage = ModelStage.gotten
    return obj


def _get_data_or_raise(js):
    """Get data from response json"""
    data = js.get('data')
    if not data:
        raise ProviderIOError(f"resp code is {js.get('code', -1000)}, expect 200")
    return data


class KuwoBaseModel(BaseModel):
    _api: KuwoApi = provider.api

    class Meta:
        fields = ['rid']
        provider = provider


class KuwoPlaylistModel(PlaylistModel, KuwoBaseModel):
    class Meta:
        allow_get = True
        allow_create_songs_g = True

    @classmethod
    def get(cls, identifier):
        data_album = cls._api.get_playlist_info(identifier)
        return _deserialize(data_album.get('data'), KuwoPlaylistSchema)

    def create_songs_g(self):
        return create_g(self._api.get_playlist_info, self.identifier, KuwoSongSchema, list_key='musicList')


class KuwoSearchModel(SearchModel, KuwoBaseModel):
    pass


class KuwoUserModel(UserModel, KuwoBaseModel):
    class Meta:
        fields_no_get = ['name', 'fav_playlists', 'fav_songs',
                         'fav_albums', 'fav_artists', 'rec_songs', 'rec_playlists']

    @classmethod
    def get(cls, identifier):
        return _deserialize({'id': identifier}, KuwoUserSchema)

    @cached_field(ttl=5)
    def playlists(self):
        data = self._api.get_user_playlists()
        data_playlists = data.get('plist', [])
        return [_deserialize(data_playlist, KuwoUserPlaylistSchema) for data_playlist in data_playlists]

    def get_rec_playlists(self) -> list:
        data_playlists = self._api.playlist_recommend(20, 1)
        return [_deserialize(data_playlist, KuwoPlaylistSchema) for data_playlist in data_playlists.get('data', {}).get('list', [])]


def search_song(keyword: str):
    data_songs = provider.api.search(keyword)
    songs = []
    for data_song in data_songs.get('data', {}).get('list', []):
        song = _deserialize(data_song, KuwoSongSchema)
        songs.append(song)
    return KuwoSearchModel(songs=songs)


def search_album(keyword: str):
    data_albums = provider.api.search_album(keyword)
    albums = []
    for data_album in data_albums.get('data', {}).get('albumList', []):
        album = _deserialize(data_album, KuwoAlbumSchema)
        albums.append(album)
    return KuwoSearchModel(albums=albums)


def search_artist(keyword: str) -> KuwoSearchModel:
    data_artists = provider.api.search_artist(keyword)
    artists = []
    for data_artist in data_artists.get('data', {}).get('artistList', []):
        artist = _deserialize(data_artist, KuwoArtistSchema)
        artists.append(artist)
    return KuwoSearchModel(artists=artists)


def search_playlist(keyword: str) -> KuwoSearchModel:
    data_playlists = provider.api.search_playlist(keyword)
    playlists = []
    for data_playlist in data_playlists.get('data', {}).get('list', []):
        playlist = _deserialize(data_playlist, KuwoPlaylistSchema)
        playlists.append(playlist)
    return KuwoSearchModel(playlists=playlists)


def search(keyword: str, **kwargs) -> KuwoSearchModel:
    type_ = SearchType.parse(kwargs['type_'])
    if type_ == SearchType.so:
        return search_song(keyword)
    if type_ == SearchType.al:
        return search_album(keyword)
    if type_ == SearchType.ar:
        return search_artist(keyword)
    if type_ == SearchType.pl:
        return search_playlist(keyword)


from .schemas import (
    KuwoSongSchema, KuwoAlbumSchema, KuwoArtistSchema, KuwoPlaylistSchema, KuwoUserSchema, KuwoUserPlaylistSchema,
)
