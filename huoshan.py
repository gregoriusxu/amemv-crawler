from six.moves import queue as Queue
from const import HEADERS
import requests
import re


def get_real_address(url):
    res = requests.get(url, headers=HEADERS, allow_redirects=True)
    return res.url if res.status_code == 302 else None


class HuoShanParse(object):
    def __init__(self, items):
        self.queue = Queue.Queue()

        for i in range(len(items)):
            res = requests.get(items[i], headers=HEADERS, allow_redirects=True)
            if res.status_code == 302:
                continue

            url = res.url

            number = re.findall(r'share/item/(\d+)/', url)
            if not len(number):
                return
          
            videoid = re.findall(r'http://hotsoon.snssdk.com/hotsoon/item/video/_playback/\?video_id=(.*)&amp;line=0&amp;', str(res.text))[0]

            downloadrul = self._get_download_url(videoid)
            self.queue.put(('video', number[0], downloadrul, number[0]))
            print(downloadrul)

    def _get_download_url(self, uri):
        download_url = "http://hotsoon.snssdk.com/hotsoon/item/video/_playback/?{0}"
        download_params = {
            'video_id': uri,
            'line': '0',
            'app_id': '1112',
            'watermark': '0',
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


if __name__ == '__main__':
    HuoShanParse(['http://reflow.huoshan.com/hotsoon/s/UKPEALHs700'])
