import logging

from fuocore.models import BaseModel, SongModel

from . import provider


logger = logging.getLogger(__name__)


class KuwoBaseModel(BaseModel):
    class Meta:
        fields = ['rid']
        provider = provider

    _api = provider.api


class KuwoSongModel(SongModel, KuwoBaseModel):
    class Meta:
        allow_get = True
        fields = ['rid']
