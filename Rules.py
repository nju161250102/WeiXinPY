# coding=utf-8
import re
import json
import time
import queue
import datetime
import threading
from mitmproxy import http
from Data import *


class Rules(object):

    def __init__(self):
        # 历史消息队列
        self.msg_queue = queue.Queue()
        # 线程锁
        self.msg_lock = threading.Lock()
        # 数据库存储线程
        self.t = threading.Thread(target=self._run, daemon=True)
        self.t.start()
        # 打开用于替换的图片
        self._img = open("1.png", "rb").read()
        # 初始化数据层
        self._data_service: DataService = SqlLiteImpl()
        # 过滤规则：过滤器表达式 -> function(self, flow)
        self.rules_dict = {
            '~u mmbiz.qpic.cn/mmbiz_jpg': self.replace_image,
            '~u /mp/profile_ext\?action=home & ~ts text/html': self.history_html,
            '~u /mp/profile_ext\?action=getmsg & ~ts application/json': self.history_json
        }

    def replace_image(self, flow: http.HTTPFlow) -> None:
        """
        替换历史消息列表中的图片
        :param flow: http流
        """
        flow.response.content = self._img
        flow.response.headers["content-type"] = "image/png"

    def history_html(self, flow: http.HTTPFlow) -> None:
        """
        处理历史消息列表（html格式）
        :param flow: http流
        """
        text = flow.response.text
        # 公众号信息处理
        account = Model.Account()
        account.biz = re.search(r'var __biz = "(.+)";', text, re.M).group(1)
        account.nickname = re.search(r'var nickname = "(.+)" ', text, re.M).group(1)
        account.description = re.search(r'<p class="profile_desc">(\s*)(.*)(\s*)</p>', text, re.M).group(2).strip()
        account.head_image = re.search(r'var headimg = "(.+)" ', text, re.M).group(1)
        account.updated_time = datetime.datetime.now()
        self._data_service.save_account(account)
        # 历史消息处理
        msg_list = re.search(r"var msgList = '(.+)';", text, re.M).group(1)
        msg_list = self._remove_escapes(msg_list)
        json_object = json.loads(msg_list, encoding='utf-8')
        self._parse_article_list(json_object["list"])
        scroll_js = '''
        <script type="text/javascript">
            var end = document.createElement("p");
            document.body.appendChild(end);
            (function scrollDown(){
                end.scrollIntoView();
                var loadMore = document.getElementsByClassName("loadmore with_line")[0];
                if (!loadMore.style.display) {
                    document.body.scrollIntoView();
                } else {
                    setTimeout(scrollDown,Math.floor(Math.random()*1000+1000));
                }
            })();
        </script>'''
        text = text.replace("</body>", scroll_js + "\n</body>")
        flow.response.set_text(text)

    def history_json(self, flow: http.HTTPFlow) -> None:
        """
        处理历史消息列表（json格式）
        :param flow: http流
        """
        text = flow.response.text
        text = self._remove_escapes(text)
        text = text.replace(r'"{', '{').replace(r'}"', '}')
        json_object = json.loads(text, encoding='utf-8')
        self._parse_article_list(json_object["general_msg_list"]["list"])

    @staticmethod
    def _remove_escapes(s: str) -> str:
        """
        去除字符串中的各种转义字符
        :param s: 待处理字符串
        :return: 处理结果
        """
        replace_dict = {'lt': '<', 'gt': '>', 'nbsp': ' ', 'amp': '&', 'quot': '"'}
        s = re.sub(r'&(lt|gt|nbsp|amp|quot);', lambda matched: replace_dict[matched.group(1)], s)
        s = s.replace(r'\"', '"').replace(r'\\/', '/')
        return s

    def _parse_article_list(self, json_list):
        """
        解析文章列表的json
        :param json_list: 文章列表json
        """
        for obj in json_list:
            time_stamp = obj["comm_msg_info"]["datetime"]
            # 处理主图文消息
            app_msg = obj["app_msg_ext_info"]
            if 'del_flag' in app_msg.keys() and app_msg["del_flag"] == 1:
                self._put_msg(self._parse_article(app_msg, time_stamp))
            # 处理多图文消息
            if app_msg["is_multi"] == 1:
                for item in app_msg["multi_app_msg_item_list"]:
                    self._put_msg(self._parse_article(item, time_stamp))

    @staticmethod
    def _parse_article(app_msg, time_stamp):
        """
        解析一篇文章的json
        :param app_msg: 单条消息json
        :param time_stamp: 发布时间(时间戳)
        """
        msg = Model.Msg()
        msg.title = app_msg["title"]
        msg.digest = app_msg["digest"]
        msg.author = app_msg["author"]
        msg.publish_time = time_stamp
        url = app_msg["content_url"]
        msg.idx = re.search(r'idx=([0-9]+)', url).group(1)
        msg.biz = re.search(r'__biz=([a-zA-Z0-9|=]+)', url).group(1)
        msg.mid = re.search(r'mid=([0-9]+)', url).group(1)
        msg.sn = re.search(r'sn=([a-z0-9]+)', url).group(1)
        msg.source_url = app_msg["source_url"]
        msg.cover = app_msg["cover"]
        msg.delete_flag = app_msg["del_flag"]
        msg.copyright_stat = app_msg["copyright_stat"]
        msg.updated_time = datetime.datetime.now()
        return msg

    def _run(self):
        """
        数据库存储进程，用于存储抓取的历史消息
        """
        data_service = SqlLiteImpl()  # SQLlite连接只能在创建的线程中使用
        while True:
            time.sleep(0.1)
            while (not self.msg_queue.empty()) and self.msg_lock.acquire():
                data_service.save_msg(self.msg_queue.get())
                self.msg_lock.release()

    def _put_msg(self, msg):
        """
        向历史消息队列中增加消息
        :param msg: 等待放入历史消息队列的消息
        """
        if self.msg_lock.acquire():
            self.msg_queue.put(msg)
            self.msg_lock.release()
