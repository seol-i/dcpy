from datetime import datetime
from .session import *
from .functions import *
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import json as __json
from urllib.parse import urlparse, parse_qsl
import html
from .dl import DL, magic_test
from os.path import join, dirname, splitext
from hashlib import sha256
import datetime

from typing import Union

# TODO: 디시콘 정보 출력
class comment:
    def __init__(self, **kwargs) -> None:
        self.info = kwargs
        # 20: 고닉, 00: 유동, 반고닉
        gonick = True if kwargs['nicktype'] == '20' else False
        ip = None if kwargs['ip'] == '' else kwargs['ip']
        self.writer = User(nick=kwargs['name'], ip=ip, uid=kwargs['user_id'],
                           gonick=gonick)
        # 올해 (O)
        if len(kwargs['reg_date']) < 15:
            __reg_date = f"{datetime.date.today().year}.{kwargs['reg_date']}"
        else:
            __reg_date = kwargs['reg_date']
        self.date = datetime.datetime.strptime(__reg_date, '%Y.%m.%d %H:%M:%S')
        self.number = kwargs['no']
        self.parent = kwargs['parent']
        
    @property
    def text(self):
        return BeautifulSoup(self.info['memo'], 'html.parser').text

class comment_iterator:
    def __init__(self, **kwargs) -> None:
        # 댓글돌이 삭제
        if kwargs['comments'] is not None:
            del_index = []
            for i in range(len(kwargs['comments'])):
                if kwargs['comments'][i]['nicktype'] == 'COMMENT_BOY':
                    del_index.append(i)
            for i in del_index[::-1]:
                del kwargs['comments'][i]
            
        self.kwargs = kwargs
        self.total = kwargs['total_cnt']
        self.page = kwargs['page']
        self.current = 0
        
    def __len__(self):
        if self.kwargs['comments'] is not None:
            return len(self.kwargs['comments'])
        else:
            return 0
    
    def __iter__(self):
        return self
    
    def __getitem__(self, item):
        if isinstance(item, int):
            return comment(**self.kwargs['comments'][item])
        if isinstance(item, slice):
            start = 0 if item.start is None else item.start
            stop = len(item)-1 if item.stop is None else item.stop
            step = 1 if item.step is None else item.step
            return [comment(**data) for data in self.kwargs['comments'][start:stop:step]]
    
    def __next__(self):
        if self.current < len(self):
            __r = self.kwargs['comments'][self.current]
            self.current += 1
            return comment(**__r)
        else:
            raise StopIteration

class post:
    def __init__(self,
                 id=None,
                 number=None,
                 title=None,
                 writer=None,
                 date=None,
                 count=None,
                 recommend=None,
                 device: str='desktop',
                 user=AnonUser(),
                 ) -> None:
        self.user = user
        self.id = id
        self.number = number
        self.title = title
        self.writer = writer
        self.date = date
        self.count = count
        self.recommend = recommend
        self.device = device
        self.state = 'not open'
        self.content_text = None

    @staticmethod
    def fromURL(url: str, device='desktop'):
        isMobile = True if re.match('https://m.dcinside.com', url) else False
        parts = urlparse(url)
        if isMobile:
            id, number = re.search(r'/board/(\w+)/(\d+)', parts.path).groups()
        else:
            query = dict(parse_qsl(html.unescape(parts.query)))
            id = query['id']
            number = query['no']
        return post(id=id, number=number, device=device)
    
    def read(self):
        if self.device == 'mobile':
            response = self.user.session.get(f'https://m.dcinside.com/board/{self.id}/{self.number}')

            if '게시물이 존재하지 않거나 삭제되었습니다.' in response.text:
                self.state = 'deleted'
                return
            self.html = BeautifulSoup(response.text, 'html.parser').find_all(class_='grid')[2]   # 제목 - 본문 - 댓글
            
            # title
            self.title = re.sub(r'[\r\t\n]', '', self.html.find(class_='tit').text)
            
            # uid
            _uid = re.search(r'gallog/(\w+).*', self.html.find(class_='rt').find('a')['href'])
            uid = _uid if _uid is None else _uid.group(1)
            
            ginfo = ginfo2__(self.html.find_all(class_='ginfo2'))
            
            self.writer = User(nick=ginfo['nick'], ip=ginfo['ip'], uid=uid, gonick=ginfo['gonick'])
            __date = ginfo['date']
            self.date = datetime.datetime.strptime(__date, '%Y.%m.%d %H:%M')
            self.count = ginfo['count']
            self.recommend = ginfo['recommend']
            self.recommend_gonick = int(self.html.find(id='recomm_btn_member').text.replace(',', ''))
            if self.html.find(id='nonrecomm_btn'):
                self.nonrecommend = int(self.html.find(id='nonrecomm_btn').text.replace(',', ''))
            else:
                self.nonrecommend = 0
            self.comment_count = ginfo['comment_count']
            
            # 광고제거
            ads = self.html.find_all(class_=re.compile(r'^adv'))
            for ad in ads: ad.decompose()
            
        elif self.device == 'desktop':
            self.user.session.headers.update(
                {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.60 Safari/537.36',})
            response = self.user.session.get(f'https://m.dcinside.com/board/{self.id}/{self.number}')

            if '게시물이 존재하지 않거나 삭제되었습니다.' in response.text:
                self.state = 'deleted'
                return
            
            
            self.html = BeautifulSoup(response.text, 'html.parser')   # 제목 - 본문 - 댓글
            __html = self.html.find(class_='view_content_wrap')

            # title
            self.title = re.sub(r'[\r\t\n]', '', __html.find(class_='title_subject').text)
            
            __nick = __html.find(class_='gall_writer')['data-nick']
            __ip = __html.find(class_='gall_writer')['data-ip']
            __ip = __ip if __ip != '' else None
            __uid = __html.find(class_='gall_writer')['data-uid']
            
            gonick = False
            if __html.find(class_='fl').img:
                if __html.find(class_='fl').img['src'].split('/')[-1] == 'fix_nik.gif':
                    gonick = True

            p = re.compile(r'\d+')
            
            self.writer = User(nick=__nick, ip=__ip, uid=__uid, gonick=gonick)
            __date = __html.find(class_='gall_date').text
            self.date = datetime.datetime.strptime(__date, '%Y.%m.%d %H:%M:%S')
            self.count = int(p.search(__html.find(class_='gall_count').text).group())
            self.recommend = int(__html.find(id=f'recommend_view_up_{self.number}').text)
            self.recommend_gonick = int(__html.find(id=f'recommend_view_up_fix_{self.number}').text)
            if __html.find(id=f'recommend_view_down_{self.number}'):
                self.nonrecommend = int(__html.find(id=f'recommend_view_down_{self.number}').text)
            else:
                self.nonrecommend = 0
            self.comment_count = int(p.search(__html.find(class_='gall_comment').text).group())
            
            # 광고제거
            ads = self.html.find_all(class_=re.compile(r'^adv'))
            for ad in ads: ad.decompose()
            
        self.state = 'open'
            
    @property
    def content(self):
        if self.device == 'desktop':
            return self.html.find(class_='write_div')
        elif self.device == 'mobile':
            return self.html.find(class_='thum-txtin')
    
    @property
    def simple_content(self):
        __copy = BeautifulSoup(str(self.content), 'html.parser')
        self.simplify(__copy)
        __simple = json.loads(f"[{__copy.text}]".replace('\xa0', ' ').replace('}{', '},{'))
        self.content_text = ''.join([j['content'] for j in __simple]).strip('\n')
        return __simple
        
    @property
    def link(self):
        return f'https://m.dcinside.com/board/{self.id}/{self.number}'
    
    def get_video(self, url):
        parts = urlparse(url)
        params = dict(parse_qsl(html.unescape(parts.query)))
        params['mobile'] = 'M'
        
        headers = {
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Dest': 'iframe',
            'Accept-Language': 'ko-KR,ko;q=0.9',
            'Referer': f'https://m.dcinside.com/board/{self.id}/{self.number}',    ##
        }
        
        response = requests.get('https://m.dcinside.com/movie/player', headers=headers, params=params)

        return BeautifulSoup(response.text, 'html.parser').source['src']
        
    def replace(self, tag, last=False):
        j = {
            'content': '',
            'image': False,
            'video': False,
            'style': None,
            'link': None,
            'nummark': None,
        }
        if tag.name is None:
            j |= {
                'content': tag.text,
                # 'style': tag['style'],
            }
            if tag.parent.name == 'div' and last:
                j['content'] += '\n'
            tag.replace_with(json.dumps(j))
        if tag.name == 'br':
            j['content'] += '\n'
            tag.replace_with(json.dumps(j))
        if tag.name == 'img':
            j |= {
                'content': tag['src'] + '\n',
                'link': tag['src'],
                'image': True,
            }
            tag.replace_with(json.dumps(j))
        if tag.name == 'iframe':
            if urlparse(tag['src']).netloc == 'www.youtube.com':
                return
            src = self.get_video(tag['src'])
            if src is None: return
            j |= {
                'content': src + '\n',
                'link': src,
                'video': True,
            }
            tag.replace_with(json.dumps(j))
        if tag.name == 'a':
            j |= {
                'content': tag.text + '\n',
                'link': tag['href'],
            }
            tag.replace_with(json.dumps(j))
    
    def simplify(self, tag):
        for i, e in enumerate(tag.childGenerator()):
            self.replace(e, last=(i+1 == len(tag)))
            if 'childGenerator' in e.__dir__():
                self.simplify(e)
    
    def download(self, link: str, folder='./', name=None) -> bool:
        parts = urlparse(link)
        query = dict(parse_qsl(html.unescape(parts.query)))

        # 다운로드용 헤더
        headers = {
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="99", "Google Chrome";v="99"',
            'sec-ch-ua-mobile': '?0',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.82 Safari/537.36',
            'sec-ch-ua-platform': '"Windows"',
            'accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'sec-fetch-site': 'cross-site',
            'sec-fetch-mode': 'no-cors',
            'sec-fetch-dest': 'image',
            'referer': 'https://gall.dcinside.com/mgallery/board/view/',
            'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,th;q=0.6',
        } | {
            'authority': parts.netloc,
        }

        with requests.Session().get(link, headers=headers, params=query) as r:
            content = r.content  
            type_ = magic_test(content[:32])
            if name is None:
                if dict(r.headers).get('Content-Disposition'):
                    name = re.search(r'filename=(.+)', r.headers['Content-Disposition']).group(1)
                    name, type_ = splitext(name)
                    name = f'{self.id} - {self.number} - {name}'
                    type_ = type_.replace('.', '')
                else:
                    name = sha256((link).encode('ascii')).hexdigest()
            
            with open(join(folder, filename(f'{name}.{type_}')), 'wb') as f:
                f.write(content)
        
    @property
    def appending_files(self):
        if self.device == 'desktop':
            soup = self.html
        elif self.device == 'mobile':
            headers = {
                'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="99", "Google Chrome";v="99"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36',
            }
            params = params = {
                'id': self.id,
                'no': str(self.number),
                't': 'cv',              # 본문 생략
            }

            response = requests.get('https://gall.dcinside.com/mgallery/board/view/',
                                    headers=dict(self.user.session.headers) | headers, params=params)
            soup = BeautifulSoup(response.text, 'html.parser')
        
        appending_file_box = soup.find(class_='appending_file_box')
        if appending_file_box is None:
            return []
        else:
            return [e['href']
                    for e in appending_file_box.find_all('a', href=re.compile('http'))]
    
    def download_all(self, simple_content=None, appending_files=None):
        """원본 이미지 & 영상 저장 함수"""
        if simple_content is None:
            simple_content = self.simple_content
        if appending_files is None:
            appending_files = self.appending_files
        
        videos = [j['link'] for j in simple_content if j['video']]
        for link in appending_files + videos:
            self.download(link)

    def comments(self, page: int=1):
        cookies = {}

        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,th;q=0.6',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://gall.dcinside.com',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.60 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
        }

        data = {
            'id': self.id,
            'no': str(self.number),
            'cmt_id': self.id,
            'cmt_no': str(self.number),
            'focus_cno': '',
            'focus_pno': '',
            'e_s_n_o': '3eabc219ebdd65f23b',
            'comment_page': str(page),
            'sort': 'D',
            'prevCnt': '0',
            '_GALLTYPE_': 'M',
        }

        response = requests.post('https://gall.dcinside.com/board/comment/', headers=headers, cookies=cookies, data=data)
        json_data = json.loads(BeautifulSoup(response.text, 'html.parser').text)

        return comment_iterator(**(json_data | {'page': page}))
        
class gallary:
    def __init__(self,
                 id: str='dcbest',
                 user: Union[AnonUser, LoginedUser]=AnonUser()) -> None:
        self.user = user
        self.id = id

    def page(self,
             page: int=1,
             list_count: int=100,
             json=False,
             only_number=False,
             least_recommend: int=0,
             device='desktop',
             reverse=True):
        self.user.session.cookies.update({
            'list_count': str(list_count),  # 정수는 오류남
        })
        self.user.session.headers.update({
            'Referer': f'https://m.dcinside.com/',
        })
        params = {
            'page': page,
        }
        
        response = self.user.session.get(
            f'https://m.dcinside.com/board/{self.id}', params=params)

        soup = BeautifulSoup(response.text, 'html.parser')
        lst = soup.find(class_='gall-detail-lst').childGenerator()
        posts = [e for e in lst
                 if (e.name == 'li') and (e.get('class') is None)]

        datas = []
        p = re.compile(r'.+/([\d]+).*')
        for _post in posts:
            number = int(p.search(_post.find(class_='lt')['href']).group(1))
            if only_number:
                datas.append([number])
                continue
            title = _post.find(class_='subjectin').text
            writer = User.fromtag(_post.find(class_='blockInfo'))
            ginfo = ginfo__(_post.find(class_='ginfo'))
            count, recommend = ginfo['count'], ginfo['recommend']
            
            date_p1 = re.compile(r'\d{2}:\d{2}')    # 오늘
            date_p2 = re.compile(r'\d{2}\.\d{2}')   # 전날
            date_p3 = re.compile(r'\d{2}\.\d{2}\.\d{2}')   # 1년전
            
            td = datetime.datetime.today()
            if date_p3.search(ginfo['date']):
                date = datetime.datetime.strptime(ginfo['date'], '%y.%m.%d')
            elif date_p2.search(ginfo['date']):
                date = datetime.datetime.strptime(ginfo['date'], '%m.%d')
                date = date.replace(year=td.year)
            else:
                date = datetime.datetime.strptime(ginfo['date'], '%H:%M')
                date = date.replace(year=td.year, month=td.month, day=td.day)

            if recommend <= least_recommend:
                continue

            if json:
                data = [self.id, number, writer.nick, writer.ip, writer.uid, title, count, recommend]
            else:
                data = [self.id, number, writer, date, title, count, recommend]
            datas.append(data)

        # 게시글 정렬
        datas = list(sorted(datas, key=lambda data: data[0], reverse=reverse))
        
        # json 출력
        if json:
            data_types = ['id', 'number', 'nick', 'ip', 'uid', 'count', 'recommend']
            df = pd.DataFrame(data=datas, columns=data_types)
            return __json.loads(df.to_json(orient='records'))
        
        if only_number:
            numbers = np.array(datas)
            return (post(id=self.id, number=number[0], user=self.user, device=device) for number in numbers)
            
        data_types = ['id', 'number', 'writer', 'date', 'title', 'count', 'recommend']
        return (post(**dict(zip(data_types, data)), user=self.user, device=device) for data in datas)
        
    def write(self):
        pass
    
    