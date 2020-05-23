from html import unescape

from marshmallow import Schema, fields, post_load, EXCLUDE


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
        artists = [KuwoArtistModel(identifier=data.get('artistid'), name=data.get('artist'))] \
            if data.get('artistid') else []
        album = KuwoAlbumModel(identifier=data.get('albumid'), name=data.get('album'),
                               cover=data.get('albumpic', '')) if data.get('albumid') else None
        return KuwoSongModel(identifier=data.get('identifier'),
                             duration=data.get('duration') * 1000,
                             title=data.get('title'),
                             artists=artists,
                             album=album,
                             lossless=data.get('lossless', False),
                             hasmv=data.get('hasmv', 0),
                             formats=[])


class KuwoSongSchemaV2(Schema):
    musicrid = fields.Str(data_key='MUSICRID', required=True)
    duration = fields.Int(data_key='DURATION', required=True)
    title = fields.Str(data_key='NAME', required=True)
    mvrid = fields.Str(data_key='MVRID', required=False)
    artist = fields.Str(data_key='ARTIST', required=True)
    artistid = fields.Int(data_key='ARTISTID', required=True)
    album = fields.Str(data_key='ALBUM', required=False)
    albumid = fields.Int(data_key='ALBUMID', required=False)
    formats_str = fields.Str(data_key='MINFO', required=False)

    @post_load
    def create_model(self, data, **kwargs):
        lossless = False

        def trans_format(format):
            fields = format.split(',')
            data = dict()
            for field in fields:
                [k, v] = field.split(':')
                data[k] = v
                if k == 'format' and v in ['ape', 'flac']:
                    lossless = True
            return data

        formats_str = data.get('formats_str')
        if formats_str:
            formats = list(map(trans_format, formats_str.split(';')))
        artists = [KuwoArtistModel(identifier=data.get('artistid'), name=data.get('artist'))] \
            if data.get('artistid') else []
        album = KuwoAlbumModel(identifier=data.get('albumid'), name=data.get('album')) if data.get('albumid') else None
        return KuwoSongModel(identifier=int(data.get('musicrid').split('_')[-1]),
                             duration=data.get('duration') * 1000,
                             title=data.get('title'),
                             artists=artists,
                             album=album,
                             lossless=lossless,
                             hasmv=int(data.get('mvrid', 0)) != 0,
                             formats=formats or [])


class KuwoAlbumSchema(Schema):
    identifier = fields.Int(data_key='albumid', required=True)
    name = fields.Str(data_key='album', required=True)
    cover = fields.Str(data_key='pic', required=False)
    artist = fields.Str(data_key='artist', required=True)
    artistid = fields.Int(data_key='artistid', required=True)
    albuminfo = fields.Str(data_key='albuminfo', required=False)
    songs = fields.List(fields.Nested('KuwoSongSchema'), data_key='musicList', allow_none=True, required=False)

    @post_load
    def create_model(self, data, **kwargs):
        return KuwoAlbumModel(identifier=data.get('identifier'), name=unescape(data.get('name')),
                              artists=[KuwoArtistModel(identifier=data.get('artistid'), name=data.get('artist'))],
                              desc=unescape(data.get('albuminfo', '')).replace('\n', '<br>'), cover=data.get('cover'), songs=[],
                              _songs=data.get('songs'))


class KuwoArtistSchema(Schema):
    identifier = fields.Int(data_key='id', required=True)
    name = fields.Str(data_key='name', required=True)
    pic = fields.Str(data_key='pic', required=False)
    pic300 = fields.Str(data_key='pic300', required=False)
    desc = fields.Str(data_key='info', required=False)

    @post_load
    def create_model(self, data, **kwargs):
        return KuwoArtistModel(identifier=data.get('identifier'), name=unescape(data.get('name')), cover=data.get('pic300'),
                               desc=data.get('desc'), info=data.get('desc'))


class KuwoPlaylistSchema(Schema):
    identifier = fields.Int(data_key='id', required=True)
    cover = fields.Str(data_key='img', required=False)
    name = fields.Str(data_key='name', required=True)
    desc = fields.Str(data_key='info', required=False)
    songs = fields.List(fields.Nested('KuwoSongSchema'), data_key='musicList', allow_none=True, required=False)

    @post_load
    def create_model(self, data, **kwargs):
        return KuwoPlaylistModel(identifier=data.get('identifier'), name=data.get('name'), cover=data.get('cover'),
                                 desc=data.get('desc'), songs=data.get('songs'))


from .models import KuwoSongModel, KuwoArtistModel, KuwoAlbumModel, KuwoPlaylistModel
