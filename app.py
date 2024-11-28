# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request
import re
import shutil
import time
import random
import os
app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('movies.html')
@app.route('/t', methods=['GET', 'POST'])
def home1():
    return render_template('movies copy.html')

@app.route('/cinema_movies', methods=['POST'])
def get_cinema_movies():
    cinema_url = request.form.get('theater_id')
    print(cinema_url)
    cinema_movies_list = fetch_cinema_data(cinema_url)
    cinema_len = len(cinema_movies_list)
    # print(render_template('movies.html', cinemaLen=cinema_len, cinema_moviesList=cinema_movies_list))
    return render_template('movies.html', cinemaLen=cinema_len, cinema_moviesList=cinema_movies_list)

@app.route('/movie', methods=['GET'])
def get_movie():
    return create_moviehtml(request.args.get('url'))

element_filters = [
    [r'''<nav\s*id\s*=\s*('|")nav('|")\s*>.*?</nav\s*>''',re.DOTALL|re.IGNORECASE,"ONCE"],
    [r'''<header\s*id\s*=\s*('|")header('|")\s*>.*?</header\s*>''',re.DOTALL|re.IGNORECASE,"ONCE"],
    [r'''<div\s*id\s*=\s*('|")section_nav('|")\s*>.*?</div\s*>''',re.DOTALL|re.IGNORECASE,"ONCE"],
    [r'''<iframe\s*src\s*=\s*('|").*?>.*?</iframe\s*>''',re.DOTALL|re.IGNORECASE,"ONCE"],
    [r'''<span\s*class\s*=\s*('|")ratingbutton('|")\s*>.*?</span\s*>''',re.DOTALL|re.IGNORECASE,"ONCE"],
    [r'''<div\s*class\s*=\s*('|")video_view('|")\s*>.*?</div\s*>''',re.DOTALL|re.IGNORECASE,"ONCE"],
    [r'''<select\s*name\s*=\s*('|")FORMS('|").*?>.*?</select\s*>''',re.DOTALL|re.IGNORECASE,"ONCE"],
    [r'''(<div\s*style\s*=\s*('|")float:left;margin:5px;('|").*?>.*?</div\s*>)''',re.DOTALL|re.IGNORECASE,"ALL"],
    [r'''<ul\s*class\s*=\s*('|")actions('|").*?>.*?</ul\s*>''',re.DOTALL|re.IGNORECASE,"ONCE"],
    [r'''<ul\s*class\s*=\s*('|")bbs_list('|").*?>.*?</ul\s*>''',re.DOTALL|re.IGNORECASE,"ONCE"],
    [r'''(<div\s*class\s*=\s*('|")sub_content('|").*?>.*?\s*</ul>\s*</div\s*>)''',re.DOTALL|re.IGNORECASE,"ALL"],
    [r'''<!--////  右邊 Side BAR   ////-->.*?<!--////  右邊 Side BAR END  ////-->''',re.DOTALL|re.IGNORECASE,"ONCE"],
    [r'''<div\s*class\s*=\s*('|")updateTime('|")\s*>.*?</div\s*>''',re.DOTALL|re.IGNORECASE,"ONCE"],
    [r'''<footer\s*id\s*=\s*('|")footer('|").*?>.*?</footer\s*>''',re.DOTALL|re.IGNORECASE,"ONCE"],
    [r'''<script.*?>.*?</script\s*>''', re.DOTALL|re.IGNORECASE,"ALL"],
    [r'''<a\s*(href\s*=\s*('|").*?('|")).*?>.*?</a\s*>''', re.DOTALL|re.IGNORECASE,"ALL"],   
    [r'''<a\s*alt\s*=\s*('|")更多('|")\s*target\s*=\s*('|")_blank('|")\s*class\s*=\s*('|")button small('|")\s*>\s*more\s*</a\s*>''',re.DOTALL|re.IGNORECASE,"ONCE"],
]

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',}

def create_moviehtml(url):
    print('url:',url)
    url_domain = url.split('/')[:3]
    url_domain = '/'.join(url_domain)
    print('domain:',url_domain)

    response = requests.get(url)
    response.encoding = 'utf-8'
    html_text = response.text

    # with open(f'./templates/temp.html', 'w',encoding='utf-8') as f:
    #     f.write(html_text)

    for i,filter in enumerate(element_filters):
        if filter[2] == "ONCE":
            match = re.compile(filter[0], filter[1]).search(html_text)
            if i == 13:print(match.group(0) if match else match)
            if match:html_text = html_text.replace(match.group(filter[3] if len(filter) > 3 else 0),'') 
            else: print(f'未找到{filter[0]}')
        elif filter[2] == "ALL":
            matchs = re.compile(filter[0], filter[1]).findall(html_text)
            if matchs:
                for match in matchs:
                    if type(match) == str:
                        html_text = html_text.replace(match,'') 
                    else:
                        html_text = html_text.replace(match[filter[3] if len(filter) > 3 else 0],'') 
            else:
                print(f'未找到{filter[0]}')

    # css
    matchs = re.compile(r'''('|")(/assets/css/.*)('|")''').findall(html_text)
    for match in matchs:
        html_text = html_text.replace(match[1],match[1].split('?')[0].replace('/assets/css','../static'))
    
    # gif
    matchs = re.compile(r'''('|")(.*?\.gif)('|")''').findall(html_text)
    matchs = set(matchs)
    for match in matchs:
        if match[1].split('/')[0] == '':
            html_text = html_text.replace(match[1],f'{url_domain}/{match[1]}')

    # jpg(防跨域,使用本地)
    # matchs = re.compile(r'''('|")(http.*?\.jpg)('|")''').findall(html_text)
    # matchs = set(matchs)
    # for match in matchs:
    #     img_name = match[1].split('/')[-1]
    #     try:
    #         # 使用缓存 或 下载
    #         if not os.path.exists(f'./static/{img_name}'): 
    #             response = requests.get(match[1], stream=True,headers=headers)
    #             if response.status_code == 200:
    #                 with open(f'./static/{img_name}', 'wb') as f:
    #                     # 将响应内容写入文件
    #                     response.raw.decode_content = True
    #                     shutil.copyfileobj(response.raw, f)
    #             else:
    #                 raise Exception(f"失败请求{response.status_code}")
    #         html_text = html_text.replace(match[1],f'../static/{img_name}')
    #     except Exception as e:
    #         print(f'图片下载错误:{e}')
    #         print(f'url:{match[1]}')
    #     time.sleep(1 + random.random())
        
    return html_text

def fetch_cinema_data(url):
    # 一个字典来储存提取的数据
    extracted_data = []

    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, "lxml")
    movies = soup.find_all("ul", id="theaterShowtimeTable")
    # 一个字典来储存提取的数据
    extracted_data = []
    # 遍历电影信息并提取所需数据
    for movie in movies:
        film_title = movie.find('li', 'filmTitle').get_text(strip=True)
        film_url = f"./movie?url=http://www.atmovies.com.tw/{movie.find('li', 'filmTitle').a['href']}"
        film_image = movie.find_all(lambda tag: tag.name == 'img' and tag.has_attr('width'))[0]['src']
        age_rating = movie.find('img', align='absmiddle')['src'].split('/')[-1].split('.')[0]
        duration = movie.find(string=lambda x: '片長' in x)
        duration = duration.split('：')[-1] if duration else None
        showtimes = movie.find_all('li')[3:]  # Skip first three which has other details
        times = [time.get_text(strip=True) for time in showtimes if '其他戲院' not in time.get_text()]
        # 保存提取的信息到字典
        movie_data = {
            'title': film_title,
            'link': film_url,
            'image_link': film_image,
            'age_rating': age_rating,
            'duration': duration,
            'showtimes': times
        }
        extracted_data.append(movie_data)


    return extracted_data


if __name__ == "__main__":
    app.run(debug=True)



