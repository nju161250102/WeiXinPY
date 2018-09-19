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
c.execute("DROP TABLE IF EXISTS msg;")
c.execute('''
CREATE TABLE msg (
  id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  title TEXT DEFAULT NULL,
  digest TEXT DEFAULT NULL,
  author TEXT DEFAULT NULL,
  publish_time TEXT DEFAULT NULL,
  read_num INTEGER DEFAULT NULL,
  like_num INTEGER DEFAULT NULL,
  reward_num INTEGER DEFAULT NULL,
  comment_num INTEGER DEFAULT NULL,
  reward_flag INTEGER DEFAULT NULL,
  comment_flag INTEGER DEFAULT NULL,
  idx INTEGER DEFAULT NULL,
  biz TEXT DEFAULT NULL,
  mid TEXT DEFAULT NULL,
  sn TEXT DEFAULT NULL UNIQUE,
  content TEXT DEFAULT NULL,
  source_url TEXT DEFAULT NULL,
  cover TEXT DEFAULT NULL, 
  copyright_stat INTEGER DEFAULT NULL,
  updated_time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
''')
