import logging
import time

from fuocore.media import Media
from fuocore.models import BaseModel, SongModel, ModelStage, SearchModel, ArtistModel, AlbumModel, MvModel, LyricModel, \
    SearchType, PlaylistModel

from .api import KuwoApi
from .provider import provider

logger = logging.getLogger(__name__)


def _deserialize(data, schema_class, gotten=True):
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
        return ['shq', 'sq', 'lq']

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
        logger.info(data)
        for d in data.split():
            if 'url' in d:
                logger.info(d)
                media = Media(d.split('=')[-1],
                              format=KuwoApi.FORMATS_BRS[quality],
                              bitrate=KuwoApi.FORMATS_RATES[quality] // 1000)
                self._media[str(self.identifier)] = {}
                self._media[str(self.identifier)][quality] = (media, int(time.time()) + 60 * 10)
                return media or None
        return None


class KuwoArtistModel(ArtistModel, KuwoBaseModel):
    class Meta:
        allow_get = True
        allow_create_albums_g = True
        fields = ['_songs', '_albums', 'info']

    @classmethod
    def get(cls, identifier):
        data = cls._api.get_artist_info(identifier)
        return _deserialize(data.get('data'), KuwoArtistSchema)

    def create_albums_g(self):
        limit = 20
        page = 1
        data = self._api.get_artist_albums(self.identifier, page=page, limit=limit)
        if data.get('code') != 200:
            yield from ()
        else:
            while True:
                for album in data.get('data', {}).get('albumList', []):
                    yield _deserialize(album, KuwoAlbumSchema)
                if len(data.get('data', {}).get('albumList', [])) >= limit:
                    page += 1
                    data = self._api.get_artist_albums(self.identifier, page=page, limit=limit)
                else:
                    break

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
        limit = 20
        page = 1
        data = self._api.get_playlist_info(self.identifier, page=page, limit=limit)
        if data.get('code') != 200:
            yield from ()
        else:
            while True:
                for album in data.get('data', {}).get('musicList', []):
                    yield _deserialize(album, KuwoSongSchema)
                if len(data.get('data', {}).get('musicList', [])) >= limit:
                    page += 1
                    data = self._api.get_playlist_info(self.identifier, page=page, limit=limit)
                else:
                    break


class KuwoSearchModel(SearchModel, KuwoBaseModel):
    pass


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
    KuwoSongSchema, KuwoAlbumSchema, KuwoArtistSchema, KuwoPlaylistSchema,
)
