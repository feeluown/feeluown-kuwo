import logging
from urllib.parse import urlencode

from feeluown.library import (
    AbstractProvider, ProviderV2, ModelType, ProviderFlags as PF,
    LyricModel, BriefVideoModel,
)
from feeluown.media import Media, Quality

from . import __identifier__, __alias__
from .api import KuwoApi
from .utils import parse_lyrics

logger = logging.getLogger(__name__)


class KuwoProvider(AbstractProvider, ProviderV2):
    api: KuwoApi

    class meta:
        identifier = __identifier__
        name = __alias__
        flags = {
            ModelType.song: (PF.model_v2 | PF.get | PF.multi_quality |
                             PF.lyric | PF.mv),
            ModelType.video: (PF.model_v2 | PF.multi_quality)
        }

    def __init__(self):
        super().__init__()
        self.api = KuwoApi()
        self._user = None

    @property
    def user(self):
        return self._user

    @user.setter
    def user(self, user):
        self._user = user

    @property
    def name(self) -> str:
        return __alias__

    @property
    def identifier(self) -> str:
        return __identifier__

    def song_get(self, identifier):
        js = self.api.get_song_detail(identifier)
        data = _get_data_or_raise(js)
        return deserialize_v2(data, KuwoSongSchemaV2)

    def song_get_lyric(self, song):
        js = self.api.get_song_lyrics(song.identifier)
        data = _get_data_or_raise(js)
        lyrics: list = data.get('lrclist', [])
        return LyricModel(identifier=self.identifier,
                          source=__identifier__,
                          content=parse_lyrics(lyrics))

    def song_get_mv(self, song):
        hasmv = self._model_cache_get_or_fetch(song, 'hasmv')
        if hasmv is False:
            return None

        return BriefVideoModel(
            identifier=f'mv_{song.identifier}',
            source=__identifier__,
            title=song.title,
            artists_name=song.artists_name,
            duration_ms='0',  # No duration info.
        )

    def song_list_quality(self, song):
        return list(self._song_get_q_media_mapping(song))

    def song_get_media(self, song, quality):
        q_media_mapping = self._song_get_q_media_mapping(song)
        if quality not in q_media_mapping:
            return None

        media = q_media_mapping[quality]
        quality_str = quality.value

        # Media is cached.
        if media is not None:
            return media

        if quality is Quality.Audio.lq:
            js = self.api.get_song_url(song.identifier)
            data = _get_data_or_raise(js)
            url = data.get('url', '')
            if not url:
                logger.warning("no song url for 'lq' quality")
                media = None
            else:
                media = Media(
                    url,
                    format=KuwoApi.FORMATS_BRS[quality],
                    bitrate=KuwoApi.FORMATS_RATES[quality] // 1000
                )
        else:
            # Response example::
            #   format=ape
            #   bitrate=1000
            #   url=http://sq.sycdn.kuwo.cn/xx/yy/zz.ape
            #   sig=1111111111111
            text = self.api.get_song_url_mobi(song.identifier, quality_str)
            media_data = {}
            for line in text.split():
                key, value = line.split('=', 1)
                media_data[key] = value
            # Check field value before use it since I'm not sure if the field always exists.
            if not media_data.get('url'):
                logger.error(f"the song '{str(song)}' does not have '{quality_str}' quality")
                media = None
            else:
                bitrate = int(media_data.get('bitrate', 0))
                if bitrate == 0:
                    bitrate = KuwoApi.FORMATS_RATES[quality_str] // 1000
                media = Media(media_data['url'],
                              format=KuwoApi.FORMATS_BRS[quality_str],
                              bitrate=bitrate)
        # Save it.
        q_media_mapping[quality] = media
        return media

    def _song_get_q_media_mapping(self, song):
        q_media_mapping, exists = song.cache_get('q_media_mapping')
        if exists is True:
            return q_media_mapping

        # All song have hq and lq.
        q_media_mapping = {
            Quality.Audio.hq: None,
            Quality.Audio.lq: None,
        }
        lossless = self._model_cache_get_or_fetch(song, 'lossless')
        if lossless:
            q_media_mapping[Quality.Audio.shq] = None
        song.cache_set('q_media_mapping', q_media_mapping, 60*10)
        return q_media_mapping

    def video_list_quality(self, video):
        return [Quality.Video.sd]

    def video_get_media(self, video, quality):
        media, exists = video.cache_get('media')
        if exists is True:
            return media

        assert video.identifier.startswith('mv_')
        song_identifier = video.identifier[3:]
        js = self.api.get_song_mv(song_identifier)
        data = _get_data_or_raise(js)
        url = data.get('url', '')
        if not url:
            logger.warning(f"video {video.identifier} is invalid")
        media = Media(url)
        video.cache_set('media', media, ttl=60*10)
        return media


provider = KuwoProvider()

from functools import partial
from fuo_kuwo.schemas import KuwoSongSchemaV2
from .models import search, _get_data_or_raise, _deserialize

provider.search = search
deserialize_v2 = partial(_deserialize, gotten=False, v2_model=True)
