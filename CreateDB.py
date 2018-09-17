# coding=utf-8
import sqlite3


conn = sqlite3.connect('weixin.db')
c = conn.cursor()
c.execute("DROP TABLE IF EXISTS account;")
c.execute('''
CREATE TABLE account (
  id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  biz TEXT DEFAULT NULL UNIQUE,
  nickname TEXT DEFAULT NULL,
  description TEXT DEFAULT NULL,
  head_image TEXT DEFAULT NULL,
  weixin_id TEXT DEFAULT NULL,
  updated_time  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
''')
