# coding=utf-8
from mitmproxy import http
from mitmproxy import flowfilter
from Rules import Rules


class Proxy(object):

    def __init__(self):
        # 导入过滤规则
        self.rules = Rules().rules_dict

    def response(self, flow: http.HTTPFlow) -> None:
        # 遍历过滤规则，执行相应函数
        for rule in self.rules.keys():
            if flowfilter.match(flowfilter.parse(rule), flow):
                self.rules[rule](flow)


addons = [
    Proxy()
]
