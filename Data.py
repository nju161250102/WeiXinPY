# coding=utf-8
import Model
import sqlite3


class DataService(object):
    """
    数据层接口，不同数据库可分别实现
    """

    def save_account(self, account: Model.Account):
        """
        保存一个公众号信息（若不存在则更新）
        :param account: 公众号对象
        """
        pass

    def save_msg(self, msg: Model.Msg):
        """
        保存一篇文章（若不存在则更新）
        :param msg:
        """
        pass


class SqlLiteImpl(DataService):

    def __init__(self):
        # 建立数据库连接
        self.conn = sqlite3.connect('weixin.db')

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

    def save_account(self, account: Model.Account):
        self.save_object(account, 'account', 'biz')

    def save_msg(self, msg: Model.Msg):
        self.save_object(msg, 'msg', 'sn')
