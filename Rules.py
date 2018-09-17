# coding=utf-8
import re
import json
from mitmproxy import http
from mitmproxy import ctx
from Data import *


class Rules(object):

    def __init__(self):
        # 打开用于替换的图片
        self._img = open("1.png", "rb").read()
        # 初始化数据层
        self._data_service: DataService = SqlLiteImpl
        # 过滤规则：过滤器表达式 -> function(self, flow)
        self.rules_dict = {
            '~u mmbiz.qpic.cn/mmbiz_jpg': self.replace_image,
            '~u /mp/profile_ext\?action=home & ~ts text/html': self.history_html,
            '~u /mp/profile_ext\?action=getmsg & ~ts application/json': self.history_json
        }

    # 替换历史消息列表中的图片
    def replace_image(self, flow: http.HTTPFlow) -> None:
        flow.response.content = self._img
        flow.response.headers["content-type"] = "image/png"

    # 处理历史消息列表（html格式）
    def history_html(self, flow: http.HTTPFlow) -> None:
        text = flow.response.text
        msg_list = re.search(r"var msgList = '(.+)';", text, re.M).group(1)
        replace_dict = {'lt': '<', 'gt': '>', 'nbsp': ' ', 'amp': '&', 'quot': '"'}
        msg_list = re.sub(r'&(lt|gt|nbsp|amp|quot);', lambda matched: replace_dict[matched.group(1)], msg_list)
        msg_list = msg_list.replace(r'\\/', '/')
        json_object = json.loads(msg_list)
        ctx.log(msg_list)
        scroll_js = '''<script type="text/javascript">
                            var end = document.createElement("p");
                            document.body.appendChild(end);
                            (function scrollDown(){
                                end.scrollIntoView();
                                var loadMore = document.getElementsByClassName("loadmore with_line")[0];
                                if (!loadMore.style.display) {
                                    document.body.scrollIntoView();
                                } else {
                                    setTimeout(scrollDown,Math.floor(Math.random()*2000+1000));
                                }
                            })();
                        </script>'''
        text = text.replace("</body>", scroll_js + "\n</body>")
        flow.response.set_text(text)

    # 处理历史消息列表（json格式）
    def history_json(self, flow: http.HTTPFlow) -> None:
        text = flow.response.text
        text = text.replace(r'\"', '"').replace(r'\\\/', '/')
        with open('s.txt', 'a+', encoding='utf-8') as f:
            f.write('\n')
            f.write(text)
