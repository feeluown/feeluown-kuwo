import logging
from feeluown.excs import ProviderIOError

from feeluown.models import BaseModel, ModelStage, SearchModel, ArtistModel, AlbumModel, MvModel, LyricModel, \
    SearchType, PlaylistModel, UserModel, cached_field
from feeluown.utils.reader import SequentialReader

from .api import KuwoApi
from .provider import provider

logger = logging.getLogger(__name__)


def create_g(func, identifier, schema, list_key='list', v2_model=False):
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
                    obj = _deserialize(obj_data, schema, gotten=True, v2_model=v2_model)
                    yield obj
                page += 1
                data = func(identifier, page=page).get('data', {})

    return SequentialReader(g(), total)


def _deserialize(data, schema_class, gotten=True, v2_model=False):
    """ deserialize schema data to model

    :param data: data to be deserialize
    :param schema_class: schema class
    :param gotten:
    :return:
    """
    schema = schema_class()
    obj = schema.load(data)
    if v2_model is False and gotten:
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


class KuwoLyricModel(LyricModel, BaseModel):
    pass


class KuwoArtistModel(ArtistModel, KuwoBaseModel):
    class Meta:
        allow_get = True
        allow_create_albums_g = True
        allow_create_songs_g = True
        fields = ['_songs', '_albums', 'info']

    @classmethod
    def get(cls, identifier):
        data = cls._api.get_artist_info(identifier)
        return _deserialize(data.get('data'), KuwoArtistSchema)

    def create_songs_g(self):
        return create_g(self._api.get_artist_songs,
                        self.identifier,
                        KuwoSongSchemaV2,
                        v2_model=True)

    def create_albums_g(self):
        return create_g(self._api.get_artist_albums, self.identifier, KuwoAlbumSchema, 'albumList')

    @property
    def desc(self):
        if not self.info:
            artist: KuwoArtistModel = self.get(self.identifier)
            self.info = artist.info
        return self.info

    @desc.setter
    def desc(self, value):
        """ Leave it empty """
        pass

    @property
    def songs(self):
        if self._songs is None:
            data_songs = self._api.get_artist_songs(self.identifier)
            songs = []
            for data_song in data_songs.get('data', {}).get('list', []):
                song = _deserialize(data_song, KuwoSongSchemaV2, v2_model=True)
                songs.append(song)
            self._songs = songs
        return self._songs

    @property
    def albums(self):
        if self._albums is None:
            data_albums = self._api.get_artist_albums(self.identifier)
            albums = []
            for data_album in data_albums.get('data', {}).get('albumList', []):
                album = _deserialize(data_album, KuwoAlbumSchema)
                albums.append(album)
            self._albums = albums
        return self._albums

    @albums.setter
    def albums(self, value):
        """ Leave it empty """
        pass

    @songs.setter
    def songs(self, value):
        """ Leave it empty """
        pass


class KuwoAlbumModel(AlbumModel, KuwoBaseModel):
    class Meta:
        allow_get = True
        fields = ['_songs']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def get(cls, identifier):
        data_album = cls._api.get_album_info(identifier)
        return _deserialize(data_album.get('data'), KuwoAlbumSchema)

    @property
    def songs(self):
        if self._songs is None:
            data_album = self._api.get_album_info(self.identifier)
            songs = data_album.get('data', {}).get('musicList', [])
            self._songs = list(
                map(lambda x: _deserialize(x, KuwoSongSchemaV2, v2_model=True), songs))
        return self._songs

    @songs.setter
    def songs(self, value):
        self._songs = value


class KuwoPlaylistModel(PlaylistModel, KuwoBaseModel):
    class Meta:
        allow_get = True
        allow_create_songs_g = True

    @classmethod
    def get(cls, identifier):
        data_album = cls._api.get_playlist_info(identifier)
        return _deserialize(data_album.get('data'), KuwoPlaylistSchema)

    def create_songs_g(self):
        return create_g(self._api.get_playlist_info,
                        self.identifier,
                        KuwoSongSchemaV2,
                        list_key='musicList',
                        v2_model=True)


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


def search_song(keyword: str):
    data_songs = provider.api.search(keyword)
    songs = []
    for data_song in data_songs.get('data', {}).get('list', []):
        song = _deserialize(data_song, KuwoSongSchemaV2, v2_model=True)
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
    KuwoAlbumSchema, KuwoArtistSchema,
    KuwoPlaylistSchema, KuwoUserSchema, KuwoUserPlaylistSchema,
    KuwoSongSchemaV2,
)
