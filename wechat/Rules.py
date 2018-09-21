# coding=utf-8
import re
import json
import queue
import random
import datetime
import requests
import threading
from mitmproxy import http
from requests.cookies import RequestsCookieJar
from .Data import *


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
        # 存储需要跳转抓取的文章sn列表
        self.sn_list = []
        # sn列表游标
        self.sn_p = -1
        # 抓取历史列表json的cookie
        self.cookie_jar = RequestsCookieJar()
        # 抓取历史列表json的查询参数
        self.query_param = {}
        # 过滤规则：过滤器表达式 -> function(self, flow)
        self.rules_dict = {
            '~u mmbiz.qpic.cn/mmbiz_jpg': self.replace_image,
            '~u /mp/profile_ext\?action=home & ~ts text/html': self.history_html,
            '~u /mp/profile_ext\?action=urlcheck': self.url_check,
            # '~u /mp/profile_ext\?action=getmsg & ~ts application/json': self.history_json,
            '~u /mp/getappmsgext': self.article_info,
            '~u mp.weixin.qq.com/s\?__': self.article_content
        }

    def replace_image(self, flow: http.HTTPFlow) -> None:
        """
        替换历史消息列表中的图片
        :param flow: http流
        """
        flow.response.content = self._img
        flow.response.headers["content-type"] = "image/png"

    def url_check(self, flow: http.HTTPFlow) -> None:
        """
        拦截urlcheck的参数
        :param flow: http流
        """
        request_url = flow.request.url
        self.query_param['uin'] = re.search(r'uin=(.*?)&', request_url).group(1)
        self.query_param['key'] = re.search(r'key=(.*?)&', request_url).group(1)
        self.query_param['appmsg_token'] = re.search(r'appmsg_token=(.*?)&', request_url).group(1)
        self.query_param['pass_ticket'] = re.search(r'pass_ticket=(.*?)&', request_url).group(1)
        self.query_param['action'] = 'getmsg'
        self.query_param['f'] = 'json'
        self.query_param['count'] = 10
        self.query_param['offset'] = 10
        t = threading.Thread(target=self._get_msg_json)
        t.start()

    def history_html(self, flow: http.HTTPFlow) -> None:
        """
        处理历史消息列表（html格式）
        :param flow: http流
        """
        text = flow.response.text
        # 公众号信息处理
        account = Account()
        account.biz = re.search(r'var __biz = "(.+)";', text, re.M).group(1)
        account.nickname = re.search(r'var nickname = "(.+)" ', text, re.M).group(1)
        account.description = re.search(r'<p class="profile_desc">(\s*)(.*)(\s*)</p>', text, re.M).group(2).strip()
        account.head_image = re.search(r'var headimg = "(.+)" ', text, re.M).group(1)
        account.updated_time = datetime.datetime.now()
        self._data_service.save_account(account)
        # cookie与查询参数保存
        c = flow.response.cookies
        self.cookie_jar.set('wap_sid2', c['wap_sid2'][0])
        self.cookie_jar.set('wxuin', c['wxuin'][0])
        self.cookie_jar.set('pass_ticket', c['pass_ticket'][0])
        self.cookie_jar.set('wxtokenkey', '777')
        self.query_param['__biz'] = account.biz
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
        # text = text.replace("</body>", scroll_js + "\n</body>")
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

    def article_info(self, flow: http.HTTPFlow) -> None:
        """
        提取文章其余信息
        :param flow: http流
        """
        request_url = flow.request.headers["Referer"]
        sn = re.search(r'sn=([a-z0-9]+)', request_url).group(1)
        msg: Msg = self._data_service.get_msg(sn)
        text = flow.response.text
        json_object = json.loads(text, encoding='utf-8')
        msg.like_num = json_object["appmsgstat"]["like_num"]
        msg.read_num = json_object["appmsgstat"]["read_num"]
        msg.reward_num = json_object["reward_total_count"] if len(json_object["reward_head_imgs"]) > 0 else 0
        msg.comment_num = json_object["comment_count"]
        msg.reward_flag = json_object["user_can_reward"] if "user_can_reward" in json_object.keys() else 0
        msg.comment_flag = json_object["comment_enabled"]
        self._data_service.save_msg(msg)

    def article_content(self, flow: http.HTTPFlow) -> None:
        """
        提取文章内容
        :param flow: http流
        """
        text = flow.response.text
        request_url = flow.request.url
        if len(self.sn_list) == 0:
            biz = re.search(r'__biz=([a-zA-Z0-9|=]+)', request_url).group(1)
            self.sn_list = self._data_service.get_blank_msg(biz)
            self.sn_p = -1
            weixin_id = re.search(r'<span class="profile_meta_value">(.*?)</span>', text).group(1)
            account = self._data_service.get_account(biz)
            account.weixin_id = weixin_id
            account.updated_time = datetime.datetime.now()
            self._data_service.save_account(account)
        else:
            # 取出文章并更新内容
            content = ""
            for t in re.findall(r'<p(.*?)>(.*?)</p>', text):
                line = self._remove_escapes(t[1])
                if re.match(r'<br(.*?)>', line) is not None:
                    line = '\n'
                elif re.match(r'<img(.*?)/>', line) is not None:
                    line = re.search(r'data-src="(.*?)" ', line).group(1) + '\n'
                else:
                    line = re.sub(r'<(.*?)>', '', line) + '\n'
                content += line
            msg: Msg = self._data_service.get_msg(self.sn_list[self.sn_p])
            msg.content = content
            msg.updated_time = datetime.datetime.now()
            self._put_msg(msg)
        self.sn_p += 1
        # 如果还有等待抓取的文章，则设置下一跳的js
        if self.sn_p < len(self.sn_list):
            msg: Msg = self._data_service.get_msg(self.sn_list[self.sn_p])
            next_link = "https://mp.weixin.qq.com/s?__biz=%s&mid=%s&idx=%s&sn=%s#wechat" \
                        % (msg.biz, msg.mid, msg.idx, msg.sn)
            delay_time = int(random.random() * 2 + 1)
            insert_meta = '<meta http-equiv="refresh" content="' + str(delay_time) + ';url=' + next_link + '" />'
            text = text.replace('</title>', '</title>' + insert_meta)
        flow.response.set_text(text)

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
            if "app_msg_ext_info" not in obj.keys():  # 排除其他消息
                continue
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
        msg = Msg()
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
        msg.copyright_stat = app_msg["copyright_stat"]
        msg.updated_time = datetime.datetime.now()
        return msg

    def _run(self):
        """
        数据库存储进程，用于存储抓取的历史消息
        """
        data_service = SqlLiteImpl()  # SQLlite连接只能在创建的线程中使用
        while True:
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

    def _get_msg_json(self):
        while True:
            r = requests.get('http://mp.weixin.qq.com/mp/profile_ext', cookies=self.cookie_jar, params=self.query_param)
            text = self._remove_escapes(r.text)
            text = text.replace(r'"{', '{').replace(r'}"', '}')
            json_object = json.loads(text, encoding='utf-8')
            self._parse_article_list(json_object["general_msg_list"]["list"])
            if json_object["can_msg_continue"] == 0:
                break
            self.query_param['offset'] += 10
