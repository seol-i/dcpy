# dcpy

## Python ver.
    3.9.12
    python -m venv {blah} 3.9.12

## nstall
    pip install -r requirements.txt
![image_820](https://user-images.githubusercontent.com/102517971/160980926-e1a60e63-9b58-4e39-a344-416803259406.png)
    
## 갤러리 id로 크롤링
### 게시물 페이지
    from dcpy import gallary
    
    gall = gallary.gallary(id='{id}')

    for p in gall.page(page=1, list_count=500, device='desktop'):

        print(f"{p.number}) {p.title} | "
              f"{p.writer.fullname} | {p.date.strftime('%Y.%m.%d')} | "
              f"조회: {p.count} 추천: {p.recommend}\n")

### 내용까지 크롤링
    from dcpy import gallary
    
    gall = gallary.gallary(id='{id}')
    for p in gall.page(page=1, list_count=10, device='desktop', only_number=True):
        p.read()
        _ = p.simple_content

        print(f"{p.number}) {p.title}\n{'-'*80}\n"
                f"{p.writer.fullname} | {p.date.strftime('%Y.%m.%d %H:%M:%S')} | "
                f"조회: {p.count} "
                f"추천: {p.recommend}({p.recommend_gonick}) 비추: {p.nonrecommend}\n{'-' * 80}\n"
                f"{p.content_text}\n{'-' * 80}")

        c_page = 1
        while c_page:
            comments = p.comments(page=c_page)
            for comm in comments:
                print(f"{comm.writer.fullname} | {comm.date.strftime('%Y.%m.%d %H:%M:%S')}\n"
                      f"{comm.text}\n{'-'*80}")
            if comments['comments'] is None:
                c_page = 0
            else:
                c_page += 1

## URL로 불러오기
    from dcpy.gallary import post
    
    p = post.fromURL('{url}', device='desktop')
    p.read()
    print(f"{p.number}) {p.title}\n{'-'*80}\n"
          f"{p.writer.fullname} | {p.date.strftime('%Y.%m.%d %H:%M:%S')} | "
          f"조회: {p.count} "
          f"추천: {p.recommend}({p.recommend_gonick}) 비추: {p.nonrecommend}\n{'-' * 80}\n"
          f"{p.content_text}\n{'-' * 80}")
    
## 게시물 첨부 파일 저장하기 (영상 포함)
    from dcpy.gallary import post
    
    p = post.fromURL('{url}', device='desktop')
    simple_content = p.simple_content
    appending_files = p.appending_files
    
    p.download_all(simple_content=simple_content, appending_files=appending_files)   

### 간단한 방법
    from dcpy.gallary import post
    
    p = post.fromURL('{url}')
    p.download_all()
