# -*- coding: utf-8 -*-

import os
import urllib.parse
import urllib.request
import hashlib
import requests
import re
from six.moves import queue as Queue
import json
from const import HEADERS


def get_real_address(url):
    if url.find('v.douyin.com') < 0:
        return url
    res = requests.get(url, headers=HEADERS, allow_redirects=False)
    return res.headers['Location'] if res.status_code == 302 else None


def get_dytk(url):
    res = requests.get(url, headers=HEADERS)
    if not res:
        return None
    dytk = re.findall("dytk: '(.*)'", res.content.decode('utf-8'))
    if len(dytk):
        return dytk[0]
    return None


class DouYinParse(object):
    def __init__(self, items, noFavorite):
        self.numbers = []
        self.challenges = []
        self.musics = []
        self.queue = Queue.Queue()

        for i in range(len(items)):
            url = get_real_address(items[i])
            if not url:
                continue

            if re.search('share/video', url):
                number = re.findall(r'share/video/(\d+)/', url)
                if not len(number):
                    return

                rct = requests.get(url, headers=HEADERS)              
                videoid = re.findall(r'https://aweme.snssdk.com/aweme/v1/playwm/\?video_id=(.*)&amp;line=0', str(rct.text))[0]

                downloadrul = self._get_download_url(videoid)
                self.queue.put(('video', number[0], downloadrul, number[0]))
                print(downloadrul)
            if re.search('share/user', url):
                self.numbers.append(url)
            if re.search('share/challenge', url):
                self.challenges.append(url)
            if re.search('share/music', url):
                self.musics.append(url)

        self.scheduling(noFavorite)

    def getParseResult(self):
        return self.queue

    @staticmethod
    def generateSignature(value):
        p = os.popen('node fuck-byted-acrawler.js %s' % value)
        return p.readlines()[0]

    @staticmethod
    def calculateFileMd5(filename):
        hmd5 = hashlib.md5()
        fp = open(filename, "rb")
        hmd5.update(fp.read())
        return hmd5.hexdigest()

    def scheduling(self, noFavorite):
        for url in self.numbers:
            self.download_user_videos(url, noFavorite)
        for url in self.challenges:
            self.download_challenge_videos(url)
        for url in self.musics:
            self.download_music_videos(url)

    def download_user_videos(self, url, noFavorite):
        number = re.findall(r'share/user/(\d+)', url)
        if not len(number):
            return
        dytk = get_dytk(url)
        hostname = urllib.parse.urlparse(url).hostname
        if hostname != 't.tiktok.com' and not dytk:
            return
        user_id = number[0]

        video_count = self._download_user_media(user_id, dytk, url, noFavorite)
        self.queue.join()
        print("\nAweme number %s, video number %s\n\n" % (user_id,
                                                          str(video_count)))
        print("\nFinish Downloading All the videos from %s\n\n" % user_id)

    def download_challenge_videos(self, url):
        challenge = re.findall('share/challenge/(\d+)', url)
        if not len(challenge):
            return
        challenges_id = challenge[0]
        video_count = self._download_challenge_media(challenges_id, url)
        self.queue.join()
        print("\nAweme challenge #%s, video number %d\n\n" % (challenges_id,
                                                              video_count))
        print(
            "\nFinish Downloading All the videos from #%s\n\n" % challenges_id)

    def download_music_videos(self, url):
        music = re.findall('share/music/(\d+)', url)
        if not len(music):
            return
        musics_id = music[0]
        video_count = self._download_music_media(musics_id, url)
        self.queue.join()
        print("\nAweme music @%s, video number %d\n\n" % (musics_id,
                                                          video_count))
        print("\nFinish Downloading All the videos from @%s\n\n" % musics_id)

    def _get_download_url(self, uri):
        download_url = "https://aweme.snssdk.com/aweme/v1/play/?{0}"
        download_params = {
            'video_id': uri,
            'line': '0',
            'ratio': '720p',
            'media_type': '4',
            'vr_type': '0',
            'test_cdn': 'None',
            'improve_bitrate': '0',
            'iid': '35628056608',
            'device_id': '46166618999',
            'os_api': '18',
            'app_name': 'aweme',
            'channel': 'App%20Store',
            'idfa': '00000000-0000-0000-0000-000000000000',
            'device_platform': 'iphone',
            'build_number': '27014',
            'vid': '2ED380A7-F09C-6C9E-90F5-862D58F3129C',
            'openudid': '21dae85eeac1da35a69e2a0ffeaeef61c78a2e98',
            'device_type': 'iPhone8%2C2',
            'app_version': '2.7.0',
            'version_code': '2.7.0',
            'os_version': '12.0',
            'screen_width': '1242',
            'aid': '1128',
            'ac': 'WIFI'
        }

        return download_url.format('&'.join(
            [key + '=' + download_params[key] for key in download_params]))

    def _get_old_dowload_url(self, uri):
        download_url = 'http://api.tiktokv.com/aweme/v1/play/?{0}'
        download_params = {
            'video_id': uri,
            'line': '0',
            'ratio': '720p',
            'media_type': '4',
            'vr_type': '0',
            'test_cdn': 'None',
            'improve_bitrate': '0',
            'version_code': '1.7.2',
            'language': 'en',
            'app_name': 'trill',
            'vid': 'D7B3981F-DD46-45A1-A97E-428B90096C3E',
            'app_version': '1.7.2',
            'device_id': '6619780206485964289',
            'channel': 'App Store',
            'mcc_mnc': '',
            'tz_offset': '28800'
        }

        return download_url.format('&'.join(
            [key + '=' + download_params[key] for key in download_params]))

    def _join_download_queue(self, aweme, target_folder):
        try:
            uri = aweme['video']['play_addr']['uri']
            url = ''

            if aweme.get('video', None):
                url = self._get_download_url(uri)
                share_info = aweme.get('share_info', {})
                self.queue.put(('video', share_info.get('share_desc', uri), url, target_folder))
            elif aweme.get('hostname') == 't.tiktok.com':
                url = self._get_old_dowload_url(uri)
                share_info = aweme.get('share_info', {})
                self.queue.put(('video', share_info.get('share_desc', uri), url, target_folder))
            else:
                if aweme.get('image_infos', None):
                    image = aweme['image_infos']['label_large']
                    self.queue.put(('image', image['uri'],
                                    image['url_list'][0], target_folder))

        except KeyError:
            return
        except UnicodeDecodeError:
            print("Cannot decode response data from DESC %s" % aweme['desc'])
            return

    def __download_favorite_media(self, user_id, dytk, hostname, signature,
                                  favorite_folder, video_count):
        # if not os.path.exists(favorite_folder):
        #     os.makedirs(favorite_folder)
        favorite_video_url = "https://%s/aweme/v1/aweme/favorite/" % hostname
        favorite_video_params = {
            'user_id': str(user_id),
            'count': '21',
            'max_cursor': '0',
            'aid': '1128',
            '_signature': signature,
            'dytk': dytk
        }
        max_cursor = None
        while True:
            if max_cursor:
                favorite_video_params['max_cursor'] = str(max_cursor)
            res = requests.get(
                favorite_video_url,
                headers=HEADERS,
                params=favorite_video_params)
            contentJson = json.loads(res.content.decode('utf-8'))
            favorite_list = contentJson.get('aweme_list', [])
            for aweme in favorite_list:
                video_count += 1
                aweme['hostname'] = hostname
                self._join_download_queue(aweme, favorite_folder)
            if contentJson.get('has_more'):
                max_cursor = contentJson.get('max_cursor')
            else:
                break
        return video_count

    def _download_user_media(self, user_id, dytk, url, noFavorite):
        if not user_id:
            print("Number %s does not exist" % user_id)
            return
        hostname = urllib.parse.urlparse(url).hostname
        signature = self.generateSignature(str(user_id))
        user_video_url = "https://%s/aweme/v1/aweme/post/" % hostname
        user_video_params = {
            'user_id': str(user_id),
            'count': '21',
            'max_cursor': '0',
            'aid': '1128',
            '_signature': signature,
            'dytk': dytk
        }
        if hostname == 't.tiktok.com':
            user_video_params.pop('dytk')
            user_video_params['aid'] = '1180'

        max_cursor, video_count = None, 0
        while True:
            if max_cursor:
                user_video_params['max_cursor'] = str(max_cursor)
            res = requests.get(
                user_video_url, headers=HEADERS, params=user_video_params)
            contentJson = json.loads(res.content.decode('utf-8'))
            aweme_list = contentJson.get('aweme_list', [])
            for aweme in aweme_list:
                video_count += 1
                aweme['hostname'] = hostname
                self._join_download_queue(aweme, user_id)
            if contentJson.get('has_more'):
                max_cursor = contentJson.get('max_cursor')
            else:
                break
        if not noFavorite:
            favorite_folder = user_id + '/favorite'
            video_count = self.__download_favorite_media(
                user_id, dytk, hostname, signature, favorite_folder,
                video_count)

        if video_count == 0:
            print("There's no video in number %s." % user_id)

        return video_count

    def _download_challenge_media(self, challenge_id, url):
        if not challenge_id:
            print("Challenge #%s does not exist" % challenge_id)
            return

        hostname = urllib.parse.urlparse(url).hostname
        signature = self.generateSignature(str(challenge_id) + '9' + '0')

        challenge_video_url = "https://%s/aweme/v1/challenge/aweme/" % hostname
        challenge_video_params = {
            'ch_id': str(challenge_id),
            'count': '9',
            'cursor': '0',
            'aid': '1128',
            'screen_limit': '3',
            'download_click_limit': '0',
            '_signature': signature
        }

        cursor, video_count = None, 0
        while True:
            if cursor:
                challenge_video_params['cursor'] = str(cursor)
                challenge_video_params['_signature'] = self.generateSignature(
                    str(challenge_id) + '9' + str(cursor))
            res = requests.get(
                challenge_video_url,
                headers=HEADERS,
                params=challenge_video_params)
            try:
                contentJson = json.loads(res.content.decode('utf-8'))
            except Exception:
                print(res.content)
                raise
            aweme_list = contentJson.get('aweme_list', [])
            if not aweme_list:
                break
            for aweme in aweme_list:
                aweme['hostname'] = hostname
                video_count += 1
                self._join_download_queue(aweme, challenge_id)
                print("number: ", video_count)
            if contentJson.get('has_more'):
                cursor = contentJson.get('cursor')
            else:
                break
        if video_count == 0:
            print("There's no video in challenge %s." % challenge_id)
        return video_count

    def _download_music_media(self, music_id, url):
        if not music_id:
            print("Challenge #%s does not exist" % music_id)
            return

        hostname = urllib.parse.urlparse(url).hostname
        signature = self.generateSignature(str(music_id))
        music_video_url = "https://%s/aweme/v1/music/aweme/?{0}" % hostname
        music_video_params = {
            'music_id': str(music_id),
            'count': '9',
            'cursor': '0',
            'aid': '1128',
            'screen_limit': '3',
            'download_click_limit': '0',
            '_signature': signature
        }
        if hostname == 't.tiktok.com':
            for key in ['screen_limit', 'download_click_limit', '_signature']:
                music_video_params.pop(key)
            music_video_params['aid'] = '1180'

        cursor, video_count = None, 0
        while True:
            if cursor:
                music_video_params['cursor'] = str(cursor)
                music_video_params['_signature'] = self.generateSignature(
                    str(music_id) + '9' + str(cursor))

            url = music_video_url.format('&'.join([
                key + '=' + music_video_params[key]
                for key in music_video_params
            ]))
            res = requests.get(url, headers=HEADERS)
            contentJson = json.loads(res.content.decode('utf-8'))
            aweme_list = contentJson.get('aweme_list', [])
            if not aweme_list:
                break
            for aweme in aweme_list:
                aweme['hostname'] = hostname
                video_count += 1
                self._join_download_queue(aweme, music_id)
            if contentJson.get('has_more'):
                cursor = contentJson.get('cursor')
            else:
                break
        if video_count == 0:
            print("There's no video in music %s." % music_id)
        return video_count
