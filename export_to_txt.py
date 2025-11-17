import os
import re
import json
import time
import random
import logging
import sys
import requests
from urllib import parse
from fake_useragent import UserAgent

# 配置日志记录
logging.basicConfig(
    filename='app.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
# 去除网络请求警告
requests.packages.urllib3.disable_warnings()


class ArticleTxtExporter:
    """
    功能：
    1. 解析 access_token 获取请求参数
    2. 分页获取文章列表
    3. 根据日期筛选文章
    4. 将筛选后的文章列表（日期、标题、链接）导出到 TXT 文件
    """

    def __init__(self, access_token):
        self.headers = {'User-Agent': UserAgent().random}
        self.root_path = r'./all_data/'
        self.official_names_head = '公众号----'
        os.makedirs(self.root_path, exist_ok=True)
        
        self.biz = None
        self.uin = None
        self.key = None
        self.pass_ticket = None
        
        if not self._parse_token(access_token):
            # 如果解析失败，在 _parse_token 中已经打印了错误
            raise ValueError("Access token 格式无效，无法解析必要参数。")

    def _parse_token(self, access_token):
        """解析 Fiddler 获取的 URL，提取关键参数"""
        try:
            parsed_token = parse.urlparse(access_token)
            query_dict = parse.parse_qs(parsed_token.query)
            
            self.biz = query_dict['__biz'][0]
            self.uin = query_dict['uin'][0]
            self.key = query_dict['key'][0]
            self.pass_ticket = query_dict['pass_ticket'][0]
            
            if self.biz and self.uin and self.key and self.pass_ticket:
                print('Access token 解析成功。')
                return True
        except Exception as e:
            print(f'解析 access token 时出错: {e}')
            logging.error(f'解析 access token 时出错: {e}', exc_info=True)
            return False
        
        print('\n※※※ Access token 参数不全，请重新输入')
        return False

    def _get_next_list(self, page):
        """
        获取指定页码的文章列表。
        (此方法逻辑基本复制自 Access_articles.py 中的 get_next_list)
        """
        pages = int(page) * 10
        print('正在获取第 ' + str(page + 1) + ' 页文章列表')
        url = ('https://mp.weixin.qq.com/mp/profile_ext?action=getmsg&__biz=' + self.biz + '&f=json&offset='
               + str(pages) + '&count=10&is_ok=1&scene=124&uin=' + self.uin + '&key=' + self.key + '&pass_ticket='
               + self.pass_ticket + '&wxtoken=&appmsg_token=&x5=0&f=json')
        
        try:
            res = requests.get(url=url, headers=self.headers, timeout=10, verify=False)
        except Exception:
            print('失败！！！获取第 ' + str(page + 1) + ' 页文章列表失败！！！')
            print('请检查错误类型，详情记录在日志中')
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logging.error(f'发生异常: {exc_type.__name__}: {exc_value}', exc_info=True)
            return {'m_flag': 0, 'passage_list': []}  # 返回空列表

        if 'app_msg_ext_info' in res.text:
            try:
                get_page = json.loads(json.loads(res.text)['general_msg_list'])['list']
                passage_list = []
                for i in get_page:
                    # 时间戳转换
                    time_tuple = time.localtime(i['comm_msg_info']['datetime'])
                    create_time = time.strftime("%Y-%m-%d", time_tuple)
                    title = i['app_msg_ext_info']['title']
                    content_url = i['app_msg_ext_info']['content_url'].replace('#wechat_redirect', '')
                    local_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                    # 存储格式：[本地时间, 发布日期, 标题, 链接]
                    passage_list.append([local_time, create_time, title, content_url])
                    
                    if i['app_msg_ext_info']['is_multi'] == 1 and i['app_msg_ext_info']['multi_app_msg_item_list']:
                        for j in i['app_msg_ext_info']['multi_app_msg_item_list']:
                            title = j['title']
                            content_url = j['content_url'].replace('#wechat_redirect', '')
                            passage_list.append([local_time, create_time, title, content_url])
                
                print('该页包含 ' + str(len(passage_list)) + ' 篇文章')
                return {
                    'm_flag': 1,
                    'passage_list': passage_list,
                    'length': len(passage_list)
                }
            except json.JSONDecodeError as e:
                print(f'解析第 {page + 1} 页JSON数据时出错: {e}')
                logging.error(f'解析JSON出错: {e}', exc_info=True)
                return {'m_flag': 0, 'passage_list': []}
        elif '"home_page_list":[]' in res.text:
            print('\n出现：操作频繁，请稍后再试\n该号可能已被封禁，请解封后再来！！！\n')
            return {'m_flag': 0, 'passage_list': []}
        else:
            print('请求结束！未获取到第 ' + str(page + 1) + ' 页文章列表')
            return {'m_flag': 0, 'passage_list': []}

    def _get_nickname_from_url(self, article_url):
        """工具方法：从任意一篇文章链接中获取公众号名称"""
        try:
            clean_url = article_url.replace('amp;', '')
            res = requests.get(clean_url, headers=self.headers, verify=False, timeout=10)
            if res.status_code == 200 and 'var nickname' in res.text:
                nickname = re.search(r'var nickname.*"(.*?)".*', res.text).group(1)
                return nickname
        except Exception as e:
            print(f'获取公众号名称失败: {e}')
            logging.error(f'获取公众号名称失败: {e}', exc_info=True)
        return self.biz  # 如果失败，使用 biz 作为备用名称

    def export_list_to_txt(self, start_date_str, end_date_str):
        """主执行方法：获取、筛选并导出到TXT"""
        
        # 1. 处理日期
        start_date_str_file = start_date_str or 'all'
        end_date_str_file = end_date_str or 'all'
        
        start_date_str = start_date_str or '1970-01-01'
        end_date_str = end_date_str or '2099-12-31'
        
        try:
            start_date = time.strptime(start_date_str, "%Y-%m-%d")
            end_date = time.strptime(end_date_str, "%Y-%m-%d")
        except ValueError:
            print("日期格式错误，请输入 YYYY-MM-DD 格式，或留空。")
            return

        print(f"开始导出文章列表，日期范围：{start_date_str} 到 {end_date_str}")
        
        filtered_articles = []
        page = 0
        stop_paging = False
        nickname = None

        # 2. 分页和筛选
        while not stop_paging:
            p_data = self._get_next_list(page)
            
            if p_data['m_flag'] == 0 or not p_data.get('passage_list'):
                print('文章列表获取完毕或遇到错误。')
                break
            
            # 尝试在获取到第一页数据时，获取公众号名称
            if nickname is None:
                 nickname = self._get_nickname_from_url(p_data['passage_list'][0][3])
                 print(f"已确定公众号名称：{nickname}")

            for article in p_data['passage_list']:
                # article 格式: [local_time, create_time, title, content_url]
                publish_date_str = article[1]
                try:
                    publish_date = time.strptime(publish_date_str, "%Y-%m-%d")
                except ValueError:
                    logging.warning(f"文章 '{article[2]}' 日期格式异常: {publish_date_str}")
                    continue  # 跳过日期格式异常的文章

                # 优化：如果当前文章日期早于开始日期，停止翻页
                if publish_date < start_date:
                    stop_paging = True
                    print('文章已超出筛选日期范围，停止获取更早的文章。')
                    break
                
                # 如果文章在日期范围内，则添加
                if start_date <= publish_date <= end_date:
                    filtered_articles.append(article)
            
            if not stop_paging:
                page += 1
                delay_time = random.uniform(1.5, 3.5)  # 随机延时
                print(f'延时 {delay_time:.2f} 秒后获取下一页...')
                time.sleep(delay_time)

        # 3. 处理结果
        if not filtered_articles:
            print(f'在 {start_date_str} 到 {end_date_str} 范围内未找到任何文章。')
            return
        
        if nickname is None:  # 备用，防止第一页就失败
            nickname = self.biz
        
        # 4. 保存到 TXT
        official_path = os.path.join(self.root_path, self.official_names_head + nickname)
        os.makedirs(official_path, exist_ok=True)
        
        # 使用日期范围命名文件
        txt_filename = f'文章列表_{start_date_str_file}_to_{end_date_str_file}.txt'
        txt_path = os.path.join(official_path, txt_filename)
        
        try:
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(f"公众号：{nickname}\n")
                f.write(f"共 {len(filtered_articles)} 篇文章\n")
                f.write(f"筛选日期：{start_date_str} 到 {end_date_str}\n")
                f.write("=" * 30 + "\n\n")
                
                # 列表是按最新日期排序的，反转列表使输出按日期从旧到新
                filtered_articles.reverse()

                for article in filtered_articles:
                    # [local_time, create_time, title, content_url]
                    f.write(f"日期：{article[1]}\n")
                    f.write(f"标题：{article[2]}\n")
                    f.write(f"链接：{article[3].replace('amp;', '')}\n\n")
            
            print(f"成功导出 {len(filtered_articles)} 篇文章到：{txt_path}")
        
        except Exception as e:
            print(f"写入 TXT 文件时出错: {e}")
            logging.error(f"写入 TXT 文件时出错: {e}", exc_info=True)