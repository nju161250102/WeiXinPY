# coding=utf-8
import Model
import sqlite3
import datetime


class DataService(object):

    def save_account(self, account: Model.Account):
        """
        保存一个公众号信息（若不存在则更新）
        :param account: 公众号对象
        """
        pass


class SqlLiteImpl(DataService):

    def __init__(self):
        # 建立数据库连接
        self.conn = sqlite3.connect('weixin.db')

    def save_account(self, account: Model.Account):
        c = self.conn.cursor()
        cursor = c.execute("SELECT * FROM account WHERE biz = (?);", (account.biz,))
        if cursor.rowcount == 0:
            c.execute("INSERT INTO account(biz, nickname, description, head_image) VALUES (?, ?, ?, ?);"
                      , (account.biz, account.nickname, account.description, account.head_image))
        else:
            c.execute("UPDATE account SET nickname = ?, description = ?, head_image = ?, updated_time = ?;"
                      , (account.nickname, account.description, account.head_image, datetime.datetime.now()))
        self.conn.commit()
