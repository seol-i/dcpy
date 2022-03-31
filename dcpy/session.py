import requests, re, json

def get_ip():
    req = requests.get("http://ipconfig.kr")
    ip = re.search(r'IP Address : (\d{1,3}\.\d{1,3})\.\d{1,3}\.\d{1,3}', req.text).group(1)
    return ip

class User:
    def __init__(self, nick='ㅇㅇ', ip=None, uid=None, gonick=None) -> None:
        self.nick = nick.strip()
        if ip is None:
            assert uid is not None
            self.ip = None
            self.uid = uid
            self.gonick = gonick
        else:
            assert ip is not None
            self.ip = ip
            self.uid = None
            self.gonick = False
        self.fullname = f'{self.nick}({self.ip})' if self.ip else f'{self.nick}({self.uid})'
        
    @property
    def isAnon(self):
        return self.uid is None
    
    @staticmethod
    def fromtag(tag):
        """class='blockInfo' tag에서 User 객체를 생성합니다."""
        nick = tag['data-name']
        if re.search(r'\d{0,3}\.\d{0,3}', tag['data-info']) is None:
            uid = tag['data-info']
            ip = None
        else:
            uid = None
            ip = tag['data-info']
        
        return User(nick=nick, ip=ip, uid=uid)

class AnonUser(User):
    def __init__(self, nick='ㅇㅇ') -> None:
        super().__init__(nick, get_ip(), None)
        self.cookies = {}
        self.headers = {
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document',
            'Accept-Language': 'ko-KR,ko;q=0.9',
        }
        self.params = {
            'boardtype': '',
        }

        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.cookies.update(self.cookies)
        
class LoginedUser(User):
    def __init__(self, nick='ㅇㅇ', ip=None, uid=None) -> None:
        super().__init__(nick, ip, uid)

