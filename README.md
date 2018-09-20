# 微信文章抓取爬虫

## Introduction
基于mitmdump中间人代理工具，拦截微信客户端发送的http请求和响应，抓取微信公众号的数据、发布的文章内容、文章的相关数据，并保存至数据库中。  

## Dependence
[python 3.x](https://www.python.org/downloads/)  
[mitmproxy 4.0.4](https://mitmproxy.org/downloads/#4.0.4/)  

## Usage
* Step 1  
安装、配置数据库。本爬虫默认使用SQLlite数据库，如需使用其他数据库，请阅读下一小节。  
* Step 2  
使用pip安装mitmproxy，安装证书，设置代理，详见[mitmproxy文档](https://docs.mitmproxy.org/stable/)  
* Step 3  
在终端中将当前目录切换至本文件夹，输入命令:mitmdump -s Main.py  
* Step 4  
从微信客户端进入历史消息查看页面时抓取公众号基本信息，自动向下翻页抓取历史文章的基本信息。  
* Step 5  
点击任意一篇文章进入文章浏览页面，之后将根据步骤一中**已抓取的文章**依次跳转，完成对内容以及其他数据的抓取。

## Code
* Proxy  
mitmdump外接插件脚本，编写事件触发后的处理流程。  
* Rules  
编写过滤表达式和相应处理方法，最后导出为rules_dict。
* Data  
数据层，用于连接数据库。使用其他数据库请自行编写DataService接口的实现。  
* Model  
模型：默认情况下成员变量名与数据库字段名一致。  
* CreateDB  
在当前位置创建一个sqllite数据库，使用其他数据库请参考其中的字段命名。**如果数据库文件已存在则会被覆盖。**  

## Version
### v0.1 - update time: 2018.09.20
* 抓取微信公众号基本数据
* 抓取微信公众号文章内容等数据
* 使用插入队列进行数据库操作

## License
**不得用于闭源软件以及商业用途**  
[GNU GENERAL PUBLIC LICENSE v3](LICENSE)

## Support  
如果您觉得本项目对您有帮助，欢迎使用支付宝打赏作者以示支持。  
<img src="./doc/1.jpg" width="300" height="300"/>
