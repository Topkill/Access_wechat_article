from Access_articles import *
from export_to_txt import ArticleTxtExporter  


if __name__=="__main__":
    app = ArticleDetail()
    print('默认存储路径为：' + app.root_path)
    screen_text = '''请输入数字键！
        数字键1：获取公众号主页链接（输入公众号下任意一篇已发布的文章链接即可）
        数字键2：获取公众号下文章列表（每页约有文章几十篇）
        数字键3：下载文章内容，自动下载文章列表中所有文章内容
        数字键4：同功能3，下载文章内容，包括单个文章的文本内容 + 阅读量、点赞数等信息
                （请注意请求间隔，若请求太多太快可能会触发封禁！！）
        数字键5：导出文章列表到TXT，支持日期筛选
    输入其他任意字符退出！'''
    print('欢迎使用，' + screen_text)
    while True:
        text = str(input('请输入功能数字：'))

        if text == '1':
            random_url = (input('（默认公众号主页链接为“研招网资讯”，按回车键使用）\n请输入公众号下任意一篇已发布的文章链接：') or
                          'https://mp.weixin.qq.com/s/4r_LKJu0mOeUc70ZZXK9LA')
            app.get_article_link(random_url)
            print('\n' + screen_text)

        elif text == '2':
            access_token = input('\n以下内容需要用到fiddler工具！！！！！\n（1）在微信客户端打开步骤1获取到的链接，\n'
                  '（2）在fiddler中查看——主机地址为https://mp.weixin.qq.com，URL地址为：/mp/profile_ext?acti\n'
                  '（3）选中此项后按快捷键：Ctrl+U，复制此网址到剪贴板\n（4）将该内容粘贴到此处 (づ￣ 3￣)づ\n请输入复制的链接：')
            pages = input('\n########## 默认获取第 1 页文章（约15篇）。如需公众号下全部文章，请输入：0 ##########\n'
                          '请估算后输入需要下载的最新发布文章的页数(例：1)：') or 1
            app.access_origin_list(access_token, int(pages))
            print('\n' + screen_text)

        elif text == '3':   # 该功能不需要token
            text_names3 = input('请输入 已下载文章列表的公众号名称 或 公众号的一篇文章链接(例如：泰山风景名胜区)：')
            save_img = input('是否保存图片？是(输入任意值)，否(默认，直接按回车跳过)') or False
            app.get_list_article(text_names3, save_img)
            print('\n' + screen_text)

        elif text == '4':
            access_token = input('\n以下内容需要用到fiddler工具！！！！！\n（1）在微信客户端打开步骤1获取到的链接，\n'
                          '（2）在fiddler中查看——主机地址为https://mp.weixin.qq.com，URL地址为：/mp/profile_ext?acti\n'
                          '（3）选中此项后按快捷键：Ctrl+U，复制此网址到剪贴板\n（4）将该内容粘贴到此处 (づ￣ 3￣)づ\n请输入复制的链接：')
            app.get_detail_list(access_token)
            print('\n未成功获取的链接已保存到本地。' + '\n' + screen_text)

        elif text == '5':
            access_token = input('\n功能5需要fiddler工具！！！！！\n'
                                 '（1）在微信客户端打开步骤1获取到的链接，\n'
                                 '（2）在fiddler中查看——主机地址为https://mp.weixin.qq.com，URL地址为：/mp/profile_ext?acti\n'
                                 '（3）选中此项后按快捷键：Ctrl+U，复制此网址到剪贴板\n（4）将该内容粘贴到此处 (づ￣ 3￣)づ\n请输入复制的链接：')
            start_date = input('请输入筛选【开始日期】 (格式 YYYY-MM-DD，留空表示不限制)：')
            end_date = input('请输入筛选【结束日期】 (格式 YYYY-MM-DD，留空表示不限制)：')
            try:
                # 实例化新类并执行导出
                exporter = ArticleTxtExporter(access_token)
                exporter.export_list_to_txt(start_date, end_date)
            except ValueError as e:
                print(f'初始化失败: {e}')
            except Exception as e:
                print(f'执行功能5时发生未知错误: {e}')
            print('\n' + screen_text)

        else:
            print('\n已成功退出！')
            break


