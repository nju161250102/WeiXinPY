# coding=utf-8


class Account(object):

    def __init__(self):
        self.biz = ''  # 公众号id
        self.nickname = ''  # 公众号名称
        self.description = ''  # 公众号描述
        self.head_image = ''  # 公众号头像
        self.weixin_id = None  # 公众号个性id
        self.updated_time = None  # 更新时间


class Msg(object):

    def __int__(self):
        self.title = ''  # 文章标题
        self.digest = ''  # 文章摘要
        self.author = ''  # 作者
        self.publish_time = ''  # 发布时间
        self.read_num = None  # 阅读量
        self.like_num = None  # 点赞量
        self.reward_num = None  # 赞赏量
        self.idx = 0  # 消息序号
        self.biz = ''  # 公众号id
        self.mid = ''  # 消息id
        self.sn = ''  # 随机加密字符串，对于每条消息是唯一的
        self.source_url = ''  # 阅读原文链接地址
        self.cover = ''  # 封面图片地址
        self.delete_flag = 0  # 是否被删除 0-已被删除
        self.copyright_stat = '',  # 版权信息
        self.updated_time = ''  # 记录更新时间
