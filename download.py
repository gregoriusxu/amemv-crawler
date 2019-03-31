# Setting timeout
import urllib.request
import urllib.parse
import copy
from threading import Thread
import os
import time
from six.moves import queue as Queue
import requests
from const import HEADERS, RETRY, TIMEOUT, THREADS


def getRemoteFileSize(url, proxy=None):
    '''
    通过content-length头获取远程文件大小
    '''
    try:
        request = urllib.request.Request(url)
        request.get_method = lambda: 'HEAD'
        response = urllib.request.urlopen(request)
        response.read()
    except urllib.error.HTTPError as e:
        # 远程文件不存在
        print(e.code)
        print(e.read().decode("utf8"))
        return 0
    else:
        fileSize = dict(response.headers).get('Content-Length', 0)
        return int(fileSize)


def download(medium_type, uri, medium_url, target_folder):
    headers = copy.copy(HEADERS)
    file_name = uri
    if medium_type == 'video':
        file_name += '.mp4'
        headers['user-agent'] = 'Aweme/27014 CFNetwork/974.2.1 Darwin/18.0.0'
    elif medium_type == 'image':
        file_name += '.jpg'
        file_name = file_name.replace("/", "-")
    else:
        return

    file_path = os.path.join(target_folder, file_name)
    if os.path.isfile(file_path):
        remoteSize = getRemoteFileSize(medium_url)
        localSize = os.path.getsize(file_path)
        if remoteSize == localSize:
            return
    print("Downloading %s from %s.\n" % (file_name, medium_url))
    retry_times = 0
    while retry_times < RETRY:
        try:
            resp = requests.get(
                medium_url, headers=headers, stream=True, timeout=TIMEOUT)
            if resp.status_code == 403:
                retry_times = RETRY
                print("Access Denied when retrieve %s.\n" % medium_url)
                raise Exception("Access Denied")
            with open(file_path, 'wb') as fh:
                for chunk in resp.iter_content(chunk_size=1024):
                    fh.write(chunk)
            break
        except Exception:
            pass
            raise
        retry_times += 1
    else:
        try:
            os.remove(file_path)
        except OSError:
            pass
        print("Failed to retrieve %s from %s.\n" % (uri, medium_url))
    time.sleep(1)


class DownloadWorker(Thread):
    def __init__(self, queue):
        Thread.__init__(self)
        self.queue = queue

    def _createdownloaddir(self, dirname):
        current_folder = os.getcwd()
        target_folder = os.path.join(current_folder, 'download/%s' % dirname)
        if not os.path.isdir(target_folder):
            os.mkdir(target_folder)
        return target_folder

    def run(self):
        while True:
            medium_type, uri, download_url, folder_id = self.queue.get()
            target_folder = self._createdownloaddir(folder_id)
            download(medium_type, uri, download_url, target_folder)
            self.queue.task_done()


class DownloadQueue(Queue.Queue):
    def __init__(self, queue):
        Thread.__init__(self)
        self.queue = queue

        for x in range(THREADS):
            worker = DownloadWorker(self.queue)
            worker.daemon = True
            worker.start()
