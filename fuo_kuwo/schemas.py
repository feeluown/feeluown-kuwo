import unicodedata
import html

from marshmallow import Schema, fields, post_load, EXCLUDE


def normalize_str(s):
    # String returned from kuwo server may contain charactor
    # which is supposed to normalized.
    #
    # For example, there may be '&nbsp' in album name, which is
    # expected to normalized to whitespace.
    return unicodedata.normalize('NFKC', html.unescape(s))


def normalize_field(s):
    if s is None:
        return ''
    return normalize_str(s)


class BaseSchema(Schema):
    class Meta:
        unknown = EXCLUDE


Schema = BaseSchema


class KuwoSongSchema(Schema):
    identifier = fields.Int(data_key='rid', required=True)
    duration = fields.Int(data_key='duration', required=True)
    title = fields.Str(data_key='name', required=True)
    artist = fields.Str(data_key='artist', required=True)
    artistid = fields.Int(data_key='artistid', required=True)
    album = fields.Str(data_key='album', required=False)
    albumid = fields.Int(data_key='albumid', required=False)
    albumpic = fields.Str(data_key='albumpic', required=False)
    lossless = fields.Bool(data_key='hasLossless', required=False)
    hasmv = fields.Int(data_key='hasmv', required=False)

    @post_load
    def create_model(self, data, **kwargs):
        if data.get('artistid'):
            artists = [
                KuwoArtistModel(
                    identifier=data.get('artistid'),
                    name=normalize_field(data.get('artist'))
                )
            ]
        else:
            artists = []
        if data.get('albumid'):
            album = KuwoAlbumModel(identifier=data.get('albumid'),
                                   name=normalize_field(data.get('album')),
                                   cover=data.get('albumpic', ''))
        else:
            album = None
        return KuwoSongModel(identifier=data.get('identifier'),
                             duration=data.get('duration') * 1000,
                             title=normalize_field(data.get('title')),
                             artists=artists,
                             album=album,
                             lossless=data.get('lossless', False),
                             hasmv=data.get('hasmv', 0))


class KuwoAlbumSchema(Schema):
    identifier = fields.Int(data_key='albumid', required=True)
    name = fields.Str(data_key='album', required=True)
    cover = fields.Str(data_key='pic', required=False)
    artist = fields.Str(data_key='artist', required=True)
    artistid = fields.Int(data_key='artistid', required=True)
    albuminfo = fields.Str(data_key='albuminfo', required=False)
    songs = fields.List(fields.Nested('KuwoSongSchema'),
                        data_key='musicList',
                        allow_none=True, required=False)

    @post_load
    def create_model(self, data, **kwargs):
        return KuwoAlbumModel(
            identifier=data.get('identifier'),
            name=normalize_field(data.get('name')),
            artists=[KuwoArtistModel(
                identifier=data.get('artistid'),
                name=normalize_field(data.get('artist')))],
            desc=normalize_field(data.get('albuminfo', '')).replace('\n', '<br>'),
            cover=data.get('cover'),
            songs=[],
            _songs=data.get('songs')
        )


class KuwoArtistSchema(Schema):
    identifier = fields.Int(data_key='id', required=True)
    name = fields.Str(data_key='name', required=True)
    pic = fields.Str(data_key='pic', required=False)
    pic300 = fields.Str(data_key='pic300', required=False)
    desc = fields.Str(data_key='info', required=False)

    @post_load
    def create_model(self, data, **kwargs):
        return KuwoArtistModel(
            identifier=data.get('identifier'),
            name=normalize_field(data.get('name')),
            cover=data.get('pic300'),
            desc=data.get('desc'), info=data.get('desc')
        )


class KuwoPlaylistSchema(Schema):
    identifier = fields.Int(data_key='id', required=True)
    cover = fields.Str(data_key='img', required=False)
    name = fields.Str(data_key='name', required=True)
    desc = fields.Str(data_key='info', required=False)
    songs = fields.List(fields.Nested('KuwoSongSchema'),
                        data_key='musicList',
                        allow_none=True,
                        required=False)

    @post_load
    def create_model(self, data, **kwargs):
        return KuwoPlaylistModel(
            identifier=data.get('identifier'),
            name=normalize_field(data.get('name')),
            cover=data.get('cover'),
            desc=data.get('desc'),
            songs=data.get('songs')
        )


class KuwoUserPlaylistSchema(Schema):
    identifier = fields.Int(data_key='id', required=True)
    cover = fields.Str(data_key='pic', required=False)
    name = fields.Str(data_key='title', required=True)

    @post_load
    def create_model(self, data, **kwargs):
        return KuwoPlaylistModel(
            identifier=data.get('identifier'),
            name=normalize_field(data.get('name')),
            cover=data.get('cover'),
            desc='',
            songs=None
        )


class KuwoUserSchema(Schema):
    identifier = fields.Str(data_key='id', required=True)

    @post_load
    def create_model(self, data, **kwargs):
        return KuwoUserModel(
            identifier=data.get('identifier', '')
        )


from .models import KuwoSongModel, KuwoArtistModel, KuwoAlbumModel, KuwoPlaylistModel, KuwoUserModel
