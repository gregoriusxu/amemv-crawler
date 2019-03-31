
import sys
import getopt
import codecs
import os
from douyin import DouYinParse
from download import DownloadQueue


def usage():
    print(
        "1. Please create file share-url.txt under this same directory.\n"
        "2. In share-url.txt, you can specify amemv share page url separated by "
        "comma/space/tab/CR. Accept multiple lines of text\n"
        "3. Save the file and retry.\n\n"
        "Sample File Content:\nurl1,url2\n\n"
        "Or use command line options:\n\n"
        "Sample:\npython amemv-video-ripper.py url1,url2\n\n\n")
    print(u"未找到share-url.txt文件，请创建.\n"
          u"请在文件中指定抖音分享页面URL，并以 逗号/空格/tab/表格鍵/回车符 分割，支持多行.\n"
          u"保存文件并重试.\n\n"
          u"例子: url1,url12\n\n"
          u"或者直接使用命令行参数指定链接\n"
          u"例子: python amemv-video-ripper.py url1,url2")


def parse_sites(fileName):
    with open(fileName, "rb") as f:
        txt = f.read().rstrip().lstrip()
        txt = codecs.decode(txt, 'utf-8')
        txt = txt.replace("\t", ",").replace("\r", ",").replace("\n",
                                                                ",").replace(
                                                                    " ", ",")
        txt = txt.split(",")
    numbers = list()
    for raw_site in txt:
        site = raw_site.lstrip().rstrip()
        if site:
            numbers.append(site)
    return numbers


noFavorite = False

if __name__ == "__main__":
    content, opts, args = None, None, []

    try:
        if len(sys.argv) >= 2:
            opts, args = getopt.getopt(sys.argv[1:], "hi:o:", ["no-favorite"])
    except Exception:
        usage()
        sys.exit(2)
        raise

    if not args:
        # check the sites file
        filename = "share-url.txt"
        if os.path.exists(filename):
            content = parse_sites(filename)
        else:
            usage()
            sys.exit(1)
    else:
        content = (args[0] if args else '').split(",")

    if len(content) == 0 or content[0] == "":
        usage()
        sys.exit(1)

    if opts:
        for o, val in opts:
            if o in ("-nf", "--no-favorite"):
                noFavorite = True
                break

    douyinparse = DouYinParse(content, noFavorite)
    DownloadQueue(douyinparse.getParseResult())
