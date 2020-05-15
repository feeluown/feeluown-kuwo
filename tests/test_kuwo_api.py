from fuo_kuwo.api import KuwoApi


class TestKuwoApi:
    def test_kuwoapi_search(self):
        response = KuwoApi().search('Hello', 20, 1)
        assert isinstance(response, dict)
        assert response.get('code') == 200
        assert isinstance(response['data'], dict)
        assert isinstance(response['data']['list'], list)
        if len(response['data']['list']) > 0:
            first_song: dict = response['data']['list'][0]
            fields = ['artist', 'album', 'name']
            for f in fields:
                assert f in first_song

    def test_kuwoapi_song_detail(self):
        response = KuwoApi().get_song_detail(95828238)
        assert isinstance(response, dict)
        assert response.get('code') == 200
        assert isinstance(response['data'], dict)

    def test_kuwoapi_song_url(self):
        response = KuwoApi().get_song_url(95828238)
        assert isinstance(response, dict)
        assert response.get('code') == 200
        assert 'url' in response

    def test_kuwoapi_song_url_rates(self):
        response = KuwoApi().get_song_url_mobi(95828238, 'shq')
        assert isinstance(response, str)
        assert 'url' in response
