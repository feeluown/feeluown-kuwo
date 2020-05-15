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
    album = fields.Str(data_key='album', required=True)

    @post_load
    def create_model(self, data, **kwargs):
        return KuwoSongModel(identifier=data.get('identifier'),
                             duration=data.get('duration') * 1000,
                             title=data.get('title'),
                             artists=[KuwoArtistModel(name=data.get('artist'))],
                             album=KuwoAlbumModel(name=data.get('album')))


from .models import KuwoSongModel, KuwoArtistModel, KuwoAlbumModel
