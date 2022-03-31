import time, os, re, threading, pickle
from .magic_number  import magic_numbers
from .exception import FileTypeError, DownloadError
from .functions     import make_dir, filename
from typing             import NewType, Union
from requests.models    import Response
from requests.sessions  import Session

Path = NewType('Path', str) # 파일 경로임을 명확히 한다. 

def magic_test(b: bytes):
    """File Signature를 확인하여 확장자를 판별합니다.

    Args:
        b (bytes): 판별할 바이트.

    Returns:
        str | None: 확장자.
    """
    for type_, bytes_list in magic_numbers.items():
        for bytes_ in bytes_list:
            for bytes__ in bytes_:
                if bytes__ in b:
                    return type_
    return None
    
class DL:
    """파일을 분할 다운로드할 수 있도록 하는 class입니다.
    
    ex.\n
    with DL(url, session, partition=5) as file:\n
        file.save()"""
    def __init__(self,
                 url        : str,
                 session    : Session = None,
                 params     : dict    = {},
                 name       : str     = None,
                 folder     : Path    = './',
                 partition  : int     = 1,
                 chunk_size : int     = 1024,
                 rename     : bool    = True
                 ) -> None:
        self.url        = url
        self.session    = session if session != None else Session()
        self.params     = params
        name            = name if name != None else self.getName(self.url)  # 파일 이름을 정하지 않으면 url에서 가져온다.
        self.name       = name if (rename == False) else filename(name)     # 파일 이름에 맞게 수정한다.
        self.dir        = re.sub(r'\\', '/', folder).rstrip('/')
        self.response   = self.getResponse(self.url, self.session, params)
        self.size       = self.contentSize(self.response)
        self.type       = self.getType(self.response, self.session, params=self.params)
        self.setPartition(number=partition)
        self.filename   = self.dir + '/' + self.name + '.' + self.type
        self.state      = 'waiting'
        self.chunk_size = chunk_size    # (byte)
        
    def __enter__(self):
        """열 때, 다운로드 진행상황 기록이 있다면 확인한다."""
        pk_file = self.filename + '.pk'
        if os.path.exists(pk_file):
            with open(pk_file,"rb") as pk:
                self.partition = pickle.load(pk)
        elif os.path.exists(self.filename) and os.path.getsize(self.filename) == self.size:
                self.state = 'downloaded'
        else:
            # 폴더 만들기
            make_dir(self.dir)
            # print(pk_file, '\n\n', '\n\n')
            with open(pk_file,"wb") as pk:
                pickle.dump(self.partition, pk)
        return self
    
    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """닫을 때, 다운로드가 완료되지 못했다면, 파일(.pk)을 만들어 현재 진행상황을 남긴다."""
        if self.state == 'downloaded': return
        finished = True
        for partition in self.partition:
            if partition[1] != partition[2]:
                finished = False
                break
        pk_file = self.filename + '.pk'
        if finished == False:
            with open(pk_file,"wb") as pk:
                pickle.dump(self.partition, pk)
        else:
            os.remove(pk_file)
    
    @staticmethod
    def getResponse(url: str, session: Session, params: dict={}) -> Response:
        """Response 객체 정보를 가져옵니다.

        Args:
            url (str): 다운받을 파일의 URL.
            session (Session): Session 객체.

        Returns:
            Response: Response 객체.
        """
        return session.head(url, params=params)
    
    @staticmethod
    def contentSize(response: Response) -> int:
        """다운받을 파일의 크기를 확인합니다.

        Args:
            response (Response): Response 객체.

        Returns:
            int: 파일 크기.
        """
        return int(response.headers['Content-Length'])
    
    @staticmethod
    def getType(response: Response, session: Session, params: dict={}) -> str:
        """파일 확장자를 구합니다.

        Args:
            response (Response): Response 객체.
            session (Session): Session 객체.

        Raises:
            FileTypeError: 파일의 확장자를 알 수 없는 경우.

        Returns:
            str: 파일의 확장자.
        """
        type_ = response.headers['Content-Type'].split('/')[-1]
        if type_ == 'octet-stream':                                                 # 파일 시그니처(매직 넘버)를 확인한다.
            headers = dict(session.headers) | {'Range': 'bytes=%d-%d' % (0, 15)}    # 첫 16바이트를 확인한다.
            b = session.get(response.url, headers=headers, params=params).content
            type_ = magic_test(b)
        if type_ == None:
            raise FileTypeError('파일 확장자를 알 수 없습니다.')
        return type_
    
    @staticmethod
    def getName(url: str) -> str:
        """url에서 파일 이름을 정합니다.

        Args:
            url (str): url.

        Returns:
            str: 파일 이름.
        """
        return url.split('/')[-1][:30]
    
    def setPartition(self, number: int) -> None:
        """분할 크기를 정하고 각 부분의 크기(byte)를 지정합니다.

        Args:
            number (int): 분할 크기.
        """
        partial_size, remainder = divmod(self.size, number)
        self.partition = [      # 다운로드 시작지점, 현재지점, 끝지점을 각각 설정한다.
            [i * partial_size,  # 시작지점
             i * partial_size,  # 현재지점
             (i + 1) * partial_size + (remainder if i == number - 1 else 0)] # 마지막은 끝까지 설정한다.
            for i in range(number)
        ]
        # [0, 0, 10]이면 0~10까지 총 11바이트가 저장된다.
        
    @property
    def current(self) -> int:
        """다운로드 받은 총 byte양을 알려주는 method입니다."""
        return sum((current[1] - current[0] for current in self.partition))
        
    def Handler(self, partition_order: int) -> None:
        """실제로 다운로드를 하는 method입니다.

        Args:
            partition_order (int): 분할 다운로드 조각 순서.
        """
        chunk_size = self.chunk_size
        _, start, end = self.partition[partition_order]
        
        # 파일의 시작점과 끝점을 지정한다.
        headers = dict(self.session.headers) | {'Range': 'bytes=%d-%d' % (start, end - 1)}
        url = self.url
        filename = self.filename

        with self.session.get(url, headers=headers, params=self.params, stream=True) as r:  # stream=True -> 메모리 절약
            with open(filename, 'r+b') as fp:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    fp.seek(start)
                    fp.write(chunk)
                    start += chunk_size
                    self.partition[partition_order][1] += len(chunk)    # 진행상황 기록
                    
    # @stopwatch
    def save(self, silent=False) -> None:
        """파일을 다운로드 합니다.

        Raises:
            DownloadError: 파일이 정상적으로 다운로드 되지 않은 경우.
        """
        # temp 파일 만들기
        if (not os.path.exists(self.filename)) or (os.path.getsize(self.filename) != self.size):
            with open(self.filename, "wb") as fp:
                fp.write(b'\0' * self.size)
        
        # Progressbar 스레드
        pr = []
        progressbar = threading.Thread(target=DL.printProgress, kwargs={'self': self, 'silent': silent}, daemon=True)
        pr.append(progressbar)
        progressbar.start()
            
        # 다운로드 스레드
        th = []
        for i in range(len(self.partition)):
            # 파티션 번호를 지정하고 다운로드를 시작한다.
            t = threading.Thread(target=DL.Handler, kwargs={'self': self, 'partition_order': i}, daemon=True)
            th.append(t)
            t.start()

        # 모든 스레드가 끝날 때까지 기다린다.
        for thr in th:
            thr.join()
        self.state = 'finished' # progressbar thread를 끝낸다.

        if self.current != self.size:
            raise DownloadError('다운로드가 완료되지 않았습니다.')
        else:
            pass
            # logging.info(f'{self.filename} 다운 완료.')
    
    @staticmethod
    def ETA(current: int, total: int, speed: float) -> str: # speed(byte/sec)
        """남은 시간(분, 초)을 계산해주는 method입니다.

        Args:
            current (int): 현재 다운받은 양 (byte)
            total (int): 총 받아야하는 양 (byte)
            speed (float): 다운로드 속도 (byte/sec)

        Returns:
            str: 분:초의 형태.
        """
        if speed == 0:
            return 'Unknown'
        else:
            eta = int((total - current) / speed)    # 남은 시간(sec)
            min, sec = divmod(eta, 60)
            return f'{str(min).zfill(2)}:{str(sec).zfill(2)}'
    
    def printProgress(self, silent=False) -> None:
        """진행상황을 알려주고 저장하는 method입니다."""
        after_size = self.current
        total = self.size
        lenth_of_Progressbar = 25
        
        if not silent:
            print(f'\r[{str("").ljust(lenth_of_Progressbar, "□")}] 0.0% (0.0MB/{round(self.size / (1024 ** 2), 2)}MB)     ', end='')
        
        while self.state != 'finished':
            if not silent:
                # 1초 간격 변화량
                before_size = after_size
                time.sleep(1)
                after_size = self.current
                # 속도와 남은 시간
                speed = round(after_size - before_size, 2)    # (byte/sec)
                eta = self.ETA(after_size, total, speed)
                # progressbar 만들기
                persent = (after_size / total) * 100
                # ■□
                gage = ('█'*(int(persent * lenth_of_Progressbar / 100))).ljust(lenth_of_Progressbar, ' ')
                state = f'{round(after_size/(1024**2), 2)}MB/{round(total/(1024**2), 2)}MB'
                print(f'\r[{gage}] {str(round(persent, 1)).rjust(5," ")}% ({state}) {round((speed / 1024**2), 2)}MB/s ETA {eta}     ', end='')
            print()
            # 진행상황 저장
            with open(self.filename + '.pk',"wb") as pk:
                pickle.dump(self.partition, pk)

