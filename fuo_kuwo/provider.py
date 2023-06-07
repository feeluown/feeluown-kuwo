import logging
import time
from typing import List, Optional, Tuple

from feeluown.library import (
    AbstractProvider, ProviderV2, ModelType, BriefVideoModel, LyricModel,
    SupportsVideoMultiQuality, SupportsSongMultiQuality,
    SupportsAlbumGet, SupportsAlbumSongsReader,
    SupportsArtistGet, SupportsArtistAlbumsReader, SupportsArtistSongsReader,
    SupportsPlaylistGet, SupportsPlaylistSongsReader,
)
from feeluown.library.model_protocol import BriefArtistProtocol, BriefSongProtocol, BriefVideoProtocol, BriefAlbumProtocol
from feeluown.media import Media, MediaType, Quality

from .utils import parse_lyrics
from . import __identifier__, __alias__
from .api import KuwoApi

logger = logging.getLogger(__name__)
Audio = Quality.Audio
Video = Quality.Video


class KuwoProvider(
    AbstractProvider, ProviderV2,
    SupportsVideoMultiQuality,
    SupportsSongMultiQuality,
    SupportsAlbumGet, SupportsAlbumSongsReader,
    SupportsArtistGet, SupportsArtistAlbumsReader, SupportsArtistSongsReader,
    SupportsPlaylistGet, SupportsPlaylistSongsReader,
):
    api: KuwoApi

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

    def use_model_v2(self, model_type: ModelType) -> bool:
        return model_type in (ModelType.song, )

    def song_get(self, identifier):
        data = self.api.get_song_detail(identifier)
        return _deserialize(data.get('data'), KuwoSongSchema)

    def song_list_quality(self, song: BriefSongProtocol) -> List[Audio]:
        has_lossless = self._model_cache_get_or_fetch(song, 'lossless')
        l = [Quality.Audio.hq, Quality.Audio.lq]
        if has_lossless:
            l.append(Quality.Audio.shq)
        return l

    def song_get_media(self, song: BriefVideoProtocol, quality: Audio):
        quality = quality.value
        if quality == 'lq':
            js = self.api.get_song_url(song.identifier)
            data = _get_data_or_raise(js)
            url = data.get('url', '')
            if not url:
                logger.warning("no song url for 'lq' quality")
                return None
            return Media(url,
                         format=KuwoApi.FORMATS_BRS[quality],
                         bitrate=KuwoApi.FORMATS_RATES[quality] // 1000)

        cache_key = f'media_{quality}'
        media, exists = song.cache_get(cache_key)
        if exists:
            return media

        # Response example::
        #   format=ape
        #   bitrate=1000
        #   url=http://sq.sycdn.kuwo.cn/xx/yy/zz.ape
        #   sig=1111111111111
        text = self.api.get_song_url_mobi(song.identifier, quality)
        media_data = {}
        for line in text.split():
            key, value = line.split('=', 1)
            media_data[key] = value
        # Check field value before use it since I'm not sure if the field always exists.
        if not media_data.get('url'):
            return None

        bitrate = int(media_data.get('bitrate', 0))
        if bitrate == 0:
            bitrate = KuwoApi.FORMATS_RATES[quality] // 1000
        media = Media(media_data['url'],
                      format=KuwoApi.FORMATS_BRS[quality],
                      bitrate=bitrate)
        song.cache_set(cache_key, media, ttl=int(time.time()) + 60 * 10)
        return media

    def song_get_lyric(self, song):
        data = self.api.get_song_lyrics(song.identifier)
        lyrics: list = data.get('data', {}).get('lrclist', [])
        return LyricModel(
            source=__identifier__,
            identifier=song.identifier,
            content=parse_lyrics(lyrics) or '',
        )

    def song_get_mv(self, song):
        hasmv = self._model_cache_get_or_fetch(song, 'hasmv')
        if not hasmv:
            return None
        return BriefVideoModel(
            source=__identifier__,
            identifier=f'mv_{self.identifier}',
            title=song.title,
        )

    def video_list_quality(self, _: BriefVideoProtocol) -> List[Video]:
        return [Video.sd]

    def video_get_media(self, video, _):
        identifier = video.identifier
        assert identifier.startswith('mv_')
        song_id = identifier[3:]
        js = self.api.get_song_mv(song_id)
        data = _get_data_or_raise(js)
        url = data.get('url', '')
        if not url:
            # TODO: remove this logging.
            logger.warning("song has no valid mv url, but attr 'hasmv' is true")
            return None
        return Media(url, MediaType.video)

    def album_get(self, identifier):
        data_album = self.api.get_album_info(identifier)
        return _deserialize(data_album['data'], KuwoAlbumSchema)

    def album_create_songs_rd(self, album: BriefAlbumProtocol):
        u_album = self.album_get(album.identifier)
        return u_album.songs

    def artist_get(self, identifier):
        data = self.api.get_artist_info(identifier)
        return _deserialize(data['data'], KuwoArtistSchema)

    def artist_create_songs_rd(self, artist: BriefArtistProtocol):
        return create_g(self.api.get_artist_songs, artist.identifier, KuwoSongSchema)

    def artist_create_albums_rd(self, artist: BriefArtistProtocol):
        return create_g(self.api.get_artist_albums,
                        artist.identifier,
                        KuwoAlbumSchema,
                        'albumList')

    def playlist_get(self, identifier):
        data_album = self.api.get_playlist_info(identifier)
        return _deserialize(data_album['data'], KuwoPlaylistSchema)

    def playlist_create_songs_rd(self, playlist):
        return create_g(self.api.get_playlist_info,
                        playlist.identifier,
                        KuwoSongSchema,
                        list_key='musicList')


provider = KuwoProvider()

from .models import search, _deserialize, _get_data_or_raise, create_g
from .schemas import KuwoSongSchema, KuwoAlbumSchema, KuwoArtistSchema, KuwoPlaylistSchema

provider.search = search
