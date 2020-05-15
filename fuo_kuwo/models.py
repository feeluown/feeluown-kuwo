import logging
import time

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
    _expired_at: int

    class Meta:
        allow_get = True
        fields = ['rid']

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
