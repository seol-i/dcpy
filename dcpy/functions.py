"""기타 함수들"""
import time, os, re
from os.path import join, dirname, splitext
import threading
from typing import NewType, Any, Union
from types  import FunctionType as Function
from queue  import Queue

Path = NewType('Path', str) # 파일 경로임을 명확히 한다. 

# 시간 추출 (한글)
def TIME(t) -> str:
    # return time.strftime('%y%m%d %H시%M분%S초'.encode('unicode-escape').decode(), time.localtime(int(t))).encode().decode('unicode-escape')
    return time.strftime('%y%m%d %H시%M분%S초', time.localtime(int(t)))

# 시간 추출 (기호)
def TIME2(t) -> str:
    return time.strftime('%Y.%m.%d %H:%M:%S', time.localtime(int(t)))

# 변수 관리
def RSC(name, alt='_') -> str: # Remove_Special_Characters
    name = re.sub('[\/:*?"<>|]', alt, name)
    return name

# 파일 이름 관리
def filename(file_name) -> str:
    return RSC(file_name.strip())
def changeExt(file_name, outExt):
    return splitext(file_name)[0] + '.' + outExt

# 폴더 만들기
def make_dir(folder: Path) -> None:
    if not os.path.isdir(folder): os.makedirs(folder)

def hex_to_rgb(hex) -> tuple: # hex_to_rgb('FFA023') -> (255, 160, 35) # '#FF'는 16진수를 의미
  return tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))

class thread:
    """threading의 결괏값의 순서를 보장해주는 class입니다.
    
    ex.\n
    where thr is list of threadings,\n
        result = thread(*thr).run()"""
    def __init__(self, *threads: threading.Thread):
        self.threads = threads
        
    def result(self, i: int, target: Function, args: Any, kwargs: Any) -> None:
        r = target(*args, **kwargs)
        self.q.put({'order': i, 'result': r})
        
    def run(self, timeout: Union[int, float]=None) -> list:
        self.q = Queue()
        for i, thread_ in enumerate(self.threads):
            target = thread_._target
            args = thread_._args
            kwargs = thread_._kwargs
            
            thread_._args = [self, i, target, args, kwargs]
            thread_._target = thread.result
            
            thread_.start()
            
        # 스레드를 기다린다.
        for thread_ in self.threads:
            thread_.join(timeout=timeout)
        
        # queue를 order(=i)의 순서대로 정렬하고 리스트 형태로 반환한다.
        r = sorted(list(self.q.queue), key=(lambda x: x['order']))
        return [x['result'] for x in r]

def splitfullname(fullname):
    reg = re.search(r'(.+?)\((\d{1,3}\.\d{1,3})\)', fullname)
    nick, ip = (fullname, None) if reg is None else reg.groups()
    return nick, ip
    
def ginfo__(tag):
    fullname, date, count, recommend = [
        e.text for e in tag.childGenerator() if (e.name == 'li')]

    nick, ip = splitfullname(fullname)
    
    count = int(re.search(r'[\d]+$', count).group())
    recommend = int(re.search(r'[\d]+$', recommend).group())
    
    return {
        'nick': nick,
        'ip': ip,
        'date': date,
        'count': count,
        'recommend': recommend,
    }

def ginfo2__(tags):
    fullname, date = [e.text for e in tags[0].childGenerator() if (e.name == 'li')]
    count, recommend, comment_count = [e.text for e in tags[1].childGenerator() if (e.name == 'li')]

    nick, ip = splitfullname(fullname)
    if tags[0].find(class_='gonick'):
        gonick = True
    elif tags[0].find(class_='nogonick'):
        gonick = False
    else:
        gonick = False
    
    count = int(re.search(r'[\d]+$', count).group())
    recommend = int(re.search(r'[\d]+$', recommend).group())
    comment_count = int(re.search(r'[\d]+$', comment_count).group())
    
    return {
        'nick': nick,
        'gonick': gonick,
        'ip': ip,
        'date': date,
        'count': count,
        'recommend': recommend,
        'comment_count': comment_count,
    }
