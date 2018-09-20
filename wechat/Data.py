# coding=utf-8
from .Model import *
import sqlite3


class DataService(object):
    """
    数据层接口，不同数据库可分别实现
    """

    def save_account(self, account: Account):
        """
        保存一个公众号信息（若不存在则更新）
        :param account: 公众号对象
        """
        pass

    def save_msg(self, msg: Msg):
        """
        保存一篇文章（若不存在则更新）
        :param msg:
        """
        pass

    def get_account(self, biz):
        """
        根据biz号获取公众号
        :param biz: biz
        """
        pass

    def get_msg(self, sn):
        """
        根据sm号获取一篇文章
        :param sn: 文章url里的sn参数
        :return: 从数据库取出的文章
        """
        pass

    def get_blank_msg(self, biz):
        """
        获取公众号未抓取文章的sn列表
        :param biz: 公众号id
        :return: 文章的sn列表
        """
        pass


class SqlLiteImpl(DataService):

    def __init__(self):
        # 建立数据库连接
        self.conn = sqlite3.connect('weixin.db')
        self.conn.row_factory = sqlite3.Row

    @staticmethod
    def insert_sql(obj: object, table_name) -> (str, tuple):
        """
        返回插入语句及参数
        :param obj: 待插入对象
        :param table_name: 表名
        :return: (str, tuple) sql语句, 参数
        """
        attrs = [x for x in dir(obj) if x[0] != '_']
        sql = "INSERT INTO " + table_name + "(" + ",".join(attrs) + ")" + " VALUES (" + ",".join(
            ['?'] * len(attrs)) + ");"
        params = tuple((getattr(obj, x) for x in attrs))
        return sql, params

    @staticmethod
    def update_sql(obj: object, table_name, unique_key) -> (str, tuple):
        """
        返回更新语句及参数
        :param obj: 待更新对象
        :param table_name: 表名
        :param unique_key: 主键名
        :return: (str, tuple) sql语句, 参数
        """
        attrs = [x for x in dir(obj) if x[0] != '_']
        attrs.remove(unique_key)
        sql = "UPDATE " + table_name + " SET " + " = ?, ".join(attrs) + " = ? WHERE " + unique_key + " = (?);"
        attrs.append(unique_key)
        params = tuple((getattr(obj, x) for x in attrs))
        return sql, params

    def get_one_object(self, obj: object, table_name: str, unique_key: str, unique_value: str):
        """
        根据unique键值获取一个唯一的row对象
        :param obj: 等待填充的对象
        :param table_name: 表名
        :param unique_key: unique键
        :param unique_value: unique键值
        :return: 唯一对象（未找到返回None）
        """
        c = self.conn.cursor()
        c.execute("SELECT * FROM " + table_name + " WHERE " + unique_key + "=?;", (unique_value,))
        row = c.fetchone()
        if row is None:
            return None
        for key in row.keys():
            setattr(obj, key, row[key])

    def save_object(self, obj: object, table_name: str, unique_key: str) -> None:
        """
        根据一个主键保存一个对象
        :param obj: 待保存对象
        :param table_name:
        :param unique_key:
        :return:
        """
        c = self.conn.cursor()
        c.execute("SELECT * FROM " + table_name + " WHERE " + unique_key + "=?;", (getattr(obj, unique_key),))
        sql, params = self.insert_sql(obj, table_name) if c.fetchone() is None else self.update_sql(obj, table_name, unique_key)
        c.execute(sql, params)
        self.conn.commit()

    def save_account(self, account: Account):
        self.save_object(account, 'account', 'biz')

    def save_msg(self, msg: Msg):
        self.save_object(msg, 'msg', 'sn')

    def get_account(self, biz):
        account = Account()
        self.get_one_object(account, 'account', 'biz', biz)
        return account

    def get_msg(self, sn):
        msg = Msg()
        self.get_one_object(msg, 'msg', 'sn', sn)
        return msg

    def get_blank_msg(self, biz):
        c = self.conn.cursor()
        c.execute("SELECT sn FROM msg WHERE biz='" + biz + "' AND content ISNULL;")
        sn_list = []
        for row in c.fetchall():
            sn_list.append(row[0])
        return sn_list
