import logging

import time
import requests
from requests.cookies import RequestsCookieJar
from fuo_kuwo.enc.DES import base64_encrypt
from .utils import digest_encrypt

logger = logging.getLogger(__name__)


class Singleton(type):
    """ singleton metaclass """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class KuwoApi(object, metaclass=Singleton):
    """ kuwo music API class """
    API_BASE: str = 'http://www.kuwo.cn/api/www'
    HTTP_HOST: str = 'http://kuwo.cn'
    MOBI_HOST: str = 'http://mobi.kuwo.cn'
    M_HOST: str = 'http://m.kuwo.cn'
    SEARCH_HOST: str = 'http://search.kuwo.cn'
    LOGIN_HOST: str = 'http://ar.i.kuwo.cn/US_NEW/kuwo'
    token: str
    cookie: RequestsCookieJar

    FORMATS_RATES = {
        'shq': 2000000,
        'hq': 320000,
        'sq': 192000,
        'lq': 128000
    }

    FORMATS_BRS = {
        'shq': '2000kflac',
        'hq': '320kmp3',
        'sq': '192kmp3',
        'lq': '128kmp3'
    }

    FORMATS = {
        'shq': 'AL',
        'hq': 'MP3H',
        'sq': 'MP3192',
        'lq': 'MP3128'
    }

    def __init__(self):
        """ class initializer """
        self.timeout = 30
        self.headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip,deflate',
            'Accept-Language': 'zh-CN,zh;q=0.8,gl;q=0.6,zh-TW;q=0.4',
            'Referer': 'http://kuwo.cn',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/81.0.4044.138 Safari/537.36',
            'Host': 'kuwo.cn',
        }
        self.mobi_headers = {'User-Agent': 'okhttp/3.10.0'}
        self.get_cookie_token()
        self.headers['csrf'] = self.token

    def get_cookie_token(self):
        """get kuwo token & set cookie jar"""
        token_uri = KuwoApi.HTTP_HOST + '/search/list?key=hello'
        with requests.Session() as session:
            response = session.get(token_uri, headers=self.headers)
            token = response.cookies.get('kw_token')
            self.token = token
            self.cookie = response.cookies

    def search(self, keyword: str, limit=20, page=1) -> dict:
        """kuwo web search API

        :param keyword: keyword of song/artist/album
        :type keyword: str
        :param limit: numbers per page, defaults to 20
        :type limit: int
        :param page: current page, defaults to 1
        :type page: int
        :return: response data
        :rtype: dict
        """
        uri = KuwoApi.API_BASE + f'/search/searchMusicBykeyWord?key={keyword}&pn={page}&rn={limit}'
        with requests.Session() as session:
            response = session.get(uri, cookies=self.cookie, headers=self.headers)
            data = response.json()
            return data

    def search_album(self, keyword: str, limit=20, page=1) -> dict:
        """kuwo search album API

        :param keyword: keyword of album
        :type keyword: str
        :param limit: numbers per page, defaults to 20
        :type limit: int
        :param page: current page
        :type page: int
        :return: response data
        :rtype: dict
        """
        uri = KuwoApi.API_BASE + f'/search/searchAlbumBykeyWord?key={keyword}&pn={page}&rn={limit}'
        with requests.Session() as session:
            response = session.get(uri, cookies=self.cookie, headers=self.headers)
            data = response.json()
            return data

    def search_artist(self, keyword: str, limit=20, page=1) -> dict:
        """kuwo search artist list

        :param keyword: keyword of artist
        :type keyword: str
        :param limit: numbers per page, defaults to 20
        :type limit: int
        :param page: current page
        :type page: int
        :return: response data
        :rtype: dict
        """
        uri = KuwoApi.API_BASE + f'/search/searchArtistBykeyWord?key={keyword}&pn={page}&rn={limit}'
        with requests.Session() as session:
            response = session.get(uri, cookies=self.cookie, headers=self.headers)
            data = response.json()
            return data

    def search_playlist(self, keyword: str, limit=20, page=1) -> dict:
        """kuwo search playlist API

        :param keyword: keyword of playlist
        :type keyword: str
        :param limit: numbers per page, defaults to 20
        :type limit: int
        :param page: current page
        :type page: int
        :return: response data
        :rtype: dict
        """
        uri = KuwoApi.API_BASE + f'/search/searchPlayListBykeyWord?key={keyword}&pn={page}&rn={limit}'
        with requests.Session() as session:
            response = session.get(uri, cookies=self.cookie, headers=self.headers)
            data = response.json()
            return data

    def get_song_detail(self, rid: int) -> dict:
        """get song detail by rid

        :param rid: musicrid
        :type rid: int
        :return: song detail data
        :rtype: dict
        """
        uri = KuwoApi.API_BASE + f'/music/musicInfo?mid={rid}'
        with requests.Session() as session:
            response = session.get(uri, cookies=self.cookie, headers=self.headers)
            data = response.json()
            return data

    def get_song_url(self, rid: int) -> dict:
        """get song url for web (128kmp3)

        :param rid: musicrid
        :type rid: int
        :return: song url data
        :rtype: dict
        """
        uri = KuwoApi.HTTP_HOST + f'/url?format=mp3&rid={rid}&response=url&type=convert_url3&br=128kmp3&from=web&t' \
                                  '=1589364222048'
        with requests.Session() as session:
            response = session.get(uri, cookies=self.cookie, headers=self.headers)
            data = response.json()
            return data

    def get_song_url_mobi(self, rid: int, quality: str) -> str:
        """get song url for app (128/192/320kmp3, flac, app, ...)

        :param rid: musicrid
        :type rid: int
        :param quality: quality of song, choices are lq, sq, shq
        :type quality: str
        :return: song url, bitrate, format
        :rtype: str
        """
        if quality == 'shq':
            logger.info(f'Querying lossless: {rid} ({quality})')
            formats = 'ape|flac|mp3|aac'
        else:
            logger.info(f'Querying best mp3: {rid} ({quality})')
            formats = 'mp3|aac'
        payload = f'corp=kuwo&p2p=1&type=convert_url2&sig=0&format={formats}&rid={rid}'
        uri = KuwoApi.MOBI_HOST + '/mobi.s?f=kuwo&q=' + base64_encrypt(payload)
        with requests.Session() as session:
            response = session.get(uri, headers=self.mobi_headers)
            return response.text

    def get_album_info(self, aid: int, limit=20, page=1) -> dict:
        """ kuwo album info API

        :param aid: album id
        :type aid: int
        :param limit: song list numbers per page, defaults to 20
        :type limit: int
        :param page: song list current page
        :type page: int
        :return: response data
        :rtype: dict
        """
        uri = KuwoApi.API_BASE + f'/album/albumInfo?albumId={aid}&pn={page}&rn={limit}'
        with requests.Session() as session:
            response = session.get(uri, cookies=self.cookie, headers=self.headers)
            data = response.json()
            return data

    def get_artist_info(self, aid: int, limit=20, page=1) -> dict:
        """ kuwo artist info API

        :param aid: album id
        :type aid: int
        :param limit: song list numbers per page, defaults to 20
        :type limit: int
        :param page: song list current page
        :type page: int
        :return: response data
        :rtype: dict
        """
        uri = KuwoApi.API_BASE + f'/artist/artist?artistid={aid}&pn={page}&rn={limit}'
        with requests.Session() as session:
            response = session.get(uri, cookies=self.cookie, headers=self.headers)
            data = response.json()
            return data

    def get_playlist_info(self, pid: int, limit=20, page=1) -> dict:
        """ kuwo playlist info API

        :param pid: playlist id
        :type pid: int
        :param limit: song list numbers per page, defaults to 20
        :type limit: int
        :param page: song list current page
        :type page: int
        :return: response data
        :rtype: dict
        """
        uri = KuwoApi.API_BASE + f'/playlist/playListInfo?pid={pid}&pn={page}&rn={limit}'
        with requests.Session() as session:
            response = session.get(uri, cookies=self.cookie, headers=self.headers)
            data = response.json()
            return data

    def get_artist_songs(self, aid: int, limit=20, page=1) -> dict:
        """ kuwo artist song list

        :param aid: album id
        :type aid: int
        :param limit: song list numbers per page, defaults to 20
        :type limit: int
        :param page: song list current page
        :type page: int
        :return: artist info response data
        :rtype: dict
        """
        uri = KuwoApi.API_BASE + f'/artist/artistMusic?artistid={aid}&pn={page}&rn={limit}'
        with requests.Session() as session:
            response = session.get(uri, cookies=self.cookie, headers=self.headers)
            data = response.json()
            return data

    def get_artist_albums(self, aid: int, limit=20, page=1) -> dict:
        """ kuwo artist album list

        :param aid: album id
        :type aid: int
        :param limit: album list numbers per page, defaults to 20
        :type limit: int
        :param page: album list current page
        :type page: int
        :return: response data
        :rtype: dict
        """
        uri = KuwoApi.API_BASE + f'/artist/artistAlbum?artistid={aid}&pn={page}&rn={limit}'
        with requests.Session() as session:
            response = session.get(uri, cookies=self.cookie, headers=self.headers)
            data = response.json()
            return data

    def get_song_mv(self, rid: int) -> str:
        """ kuwo mv url API

        :param rid: musicrid
        :type rid: int
        :return: song mv url
        :rtype: str
        """
        uri = KuwoApi.HTTP_HOST + f'/url?rid={rid}&response=url&format=mp4%7Cmkv&type=convert_url&t=1589586895402'
        with requests.Session() as session:
            response = session.get(uri, cookies=self.cookie, headers=self.headers)
            return response.text

    def get_song_lyrics(self, rid: int) -> dict:
        """ kuwo song lyrics url

        :param rid: musicrid
        :type rid: int
        :return: song lyrics response data
        :rtype: dict
        """
        uri = KuwoApi.M_HOST + f'/newh5/singles/songinfoandlrc?musicId={rid}'
        with requests.Session() as session:
            response = session.get(uri, cookies=self.cookie, headers=self.headers)
            return response.json()

    def get_mobile_verify_code(self, mobile: str, type_: int = 0):
        secret = digest_encrypt(digest_encrypt('imbadboy@!153').upper() + digest_encrypt(mobile + str(time.time()))
                                .upper()).upper()
        payload = f'mobile={mobile}&type={type_}&tm={str(time.time())}&secret={secret}'
        uri = KuwoApi.LOGIN_HOST + '/send_sms?f=ar&q=' + base64_encrypt(payload)
        with requests.Session() as session:
            response = session.post(uri, headers=self.mobi_headers)
            return response.text
