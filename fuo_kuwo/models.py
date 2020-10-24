import logging
import time

from fuocore.media import Media
from fuocore.models import BaseModel, SongModel, ModelStage, SearchModel, ArtistModel, AlbumModel, MvModel, LyricModel, \
    SearchType, PlaylistModel, UserModel, cached_field
from fuocore.reader import SequentialReader

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
    if gotten:
        obj.stage = ModelStage.gotten
    return obj


class KuwoBaseModel(BaseModel):
    _api: KuwoApi = provider.api

    class Meta:
        fields = ['rid']
        provider = provider


class KuwoLyricModel(LyricModel, BaseModel):
    pass


class KuwoMvModel(MvModel, KuwoBaseModel):
    pass


class KuwoSongModel(SongModel, KuwoBaseModel):
    _url: str
    _media: dict = {}
    _expired_at: int

    class Meta:
        allow_get = True
        fields = ['lossless', 'hasmv']
        support_multi_quality = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def get(cls, identifier):
        data = cls._api.get_song_detail(identifier)
        return _deserialize(data.get('data'), KuwoSongSchema)

    @property
    def url(self):
        if self._url is not None and self._expired_at > time.time():
            return self._url
        data = self._api.get_song_url(self.identifier)
        logger.info(data.get('url'))
        self._url = data.get('url', '')
        return self._url

    @url.setter
    def url(self, url):
        self._expired_at = int(time.time()) + 60 * 10
        self._url = url

    @property
    def mv(self):
        if self.hasmv != 1:
            return None
        cover = ''
        if self.album and self.album.cover:
            cover = self.album.cover
        return KuwoMvModel(name=self.title, desc='', cover=cover, artist=self.artists_name,
                           media=self._api.get_song_mv(self.identifier) or '')

    @mv.setter
    def mv(self, value):
        """Leave it empty"""
        pass

    @property
    def lyric(self):
        data = self._api.get_song_lyrics(self.identifier)
        lyrics: list = data.get('data', {}).get('lrclist', [])
        from fuo_kuwo.utils import parse_lyrics
        return KuwoLyricModel(identifier=self.identifier,
                              content=parse_lyrics(lyrics))

    @lyric.setter
    def lyric(self, value):
        """Leave it empty"""
        pass

    def list_quality(self):
        formats = ['shq', 'hq', 'lq']
        if not self.lossless:
            formats.remove('shq')
        logger.info(formats)
        return formats

    def get_media(self, quality):
        logger.info(quality)
        if quality == 'lq':
            return Media(self.url,
                         format=KuwoApi.FORMATS_BRS[quality],
                         bitrate=KuwoApi.FORMATS_RATES[quality] // 1000)
        if self._media.get(str(self.identifier)) and self._media.get(str(self.identifier)).get(quality)[0] is not None \
                and self._media.get(str(self.identifier)).get(quality)[1] > time.time():
            return self._media.get(str(self.identifier)).get(quality)[0]
        data = self._api.get_song_url_mobi(self.identifier, quality)
        bitrate = 0
        for d in data.split():
            if 'bitrate=' in d:
                bitrate = int(d.split('=')[-1])
            if 'url=' in d:
                if bitrate == 0:
                    bitrate = int(KuwoApi.FORMATS_RATES[quality] // 1000)
                media = Media(d.split('=')[-1],
                              format=KuwoApi.FORMATS_BRS[quality],
                              bitrate=bitrate)
                self._media[str(self.identifier)] = {}
                self._media[str(self.identifier)][quality] = (media, int(time.time()) + 60 * 10)
                return media or None
        return None


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
        return create_g(self._api.get_artist_songs, self.identifier, KuwoSongSchema)

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
                song = _deserialize(data_song, KuwoSongSchema)
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
            self._songs = list(map(lambda x: _deserialize(x, KuwoSongSchema), songs))
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
