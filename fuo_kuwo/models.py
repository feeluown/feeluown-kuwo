import logging
import time

from fuocore.media import Media
from fuocore.models import BaseModel, SongModel, ModelStage, SearchModel, ArtistModel, AlbumModel

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


class KuwoSongModel(SongModel, KuwoBaseModel):
    _url: str
    _media: dict = {
        'shq': (None, 0),
        'sq': (None, 0),
        'hq': (None, 0),
        'lq': (None, 0)
    }
    _expired_at: int

    class Meta:
        allow_get = True
        fields = ['rid', 'lossless']
        support_multi_quality = True

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

    def list_quality(self):
        formats = ['shq', 'lq']
        if not self.lossless:
            formats.remove('shq')
        logger.info(formats)
        return formats

    def get_media(self, quality):
        logger.info(quality)
        if quality != 'shq':
            return self.get(self.identifier)
        if self._media.get(quality)[0] is not None and self._media.get(quality)[1] > time.time():
            return self._media.get(quality)[0]
        data = self._api.get_song_url_mobi(self.identifier, quality)
        logger.info(data)
        for d in data.split():
            if 'url' in d:
                logger.info(d)
                media = Media(d.split('=')[-1],
                              format=KuwoApi.FORMATS_BRS[quality],
                              bitrate=KuwoApi.FORMATS_RATES[quality] // 1000)
                self._media[quality] = (media, int(time.time()) + 60 * 10)
                return media or None
        return None


class KuwoArtistModel(ArtistModel, KuwoBaseModel):
    pass


class KuwoAlbumModel(AlbumModel, KuwoBaseModel):
    pass


class KuwoSearchModel(SearchModel, KuwoBaseModel):
    pass


def search(keyword, **kwargs):
    data_songs = provider.api.search(keyword)
    songs = []
    for data_song in data_songs.get('data').get('list'):
        song = _deserialize(data_song, KuwoSongSchema)
        songs.append(song)
    return KuwoSearchModel(songs=songs)


from .schemas import (
    KuwoSongSchema,
)
