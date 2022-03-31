import requests, json, re

def gall_name():
    """(메이저) 갤러리"""
    requests('http://json.dcinside.com/App/gall_name.php').json()

def mgall_up():
    """승격 마이너 갤러리"""
    url = 'https://json2.dcinside.com/json1/mgallmain/mgallery_up.php'
    res = requests.get(url)
    return json.loads(re.sub(r"[\n\t]", '', res.text[1:-2]))

def mgallery_ranking():
    """실시간 북적 m.갤러리 (TOP 100)"""
    url = 'https://json2.dcinside.com/json1/mgallmain/mgallery_ranking.php'
    res = requests.get(url)
    return json.loads(re.sub(r"[\n\t]", '', res.text[1:-2]))

def mgallery_hot():
    """흥한 마이너 갤러리"""
    url = 'https://json2.dcinside.com/json0/mgallmain/mgallery_hot.php'
    return requests.get(url).json()

def mgallery_new():
    """신설 마이너 갤러리"""
    url ='https://json2.dcinside.com/json1/mgallmain/mgallery_new.php'
    res = requests.get(url)
    return json.loads(re.sub(r"[\n\t]", '', res.text[1:-2]))
    
def new_gallary(category: int):
    """신설 갤러리

    Args:
        category (int): 카테고리 고유 넘버.

    Returns:
        json: json.
    """
    url = f'https://json2.dcinside.com/mgallmain/new_gallery/{category}.php'
    return requests.get(url).json()

def app_check_A_rina():
    """???"""
    
    """[
    {
        "result": true,
        "ver": "4.5.8",
        "notice": false,
        "notice_update": false,
        "date": "Sat8426661232603"
    }
    ]"""
    url = 'http://json2.dcinside.com/json0/app_check_A_rina.php'
    return requests.get(url).json()