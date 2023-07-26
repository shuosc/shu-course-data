import argparse
import asyncio
import base64
import getpass
import hashlib
import json
import os
import random
import re
import ssl
import time

import aiofiles
import aiohttp
import certifi
import rsa
from bs4 import BeautifulSoup

DEFAULT_BACKEND = 'http://xk.autoisp.shu.edu.cn'
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:33.0) Gecko/20120101 Firefox/33.0',
    'Opera/9.80 (Windows NT 6.0) Presto/2.12.388 Version/12.14',
    'Mozilla/5.0 (MSIE 10.0; Windows NT 6.1; Trident/5.0)',
]
# noinspection SpellCheckingInspection
RSA_PUBKEY = '''-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDl/aCgRl9f/4ON9MewoVnV58OL
OU2ALBi2FKc5yIsfSpivKxe7A6FitJjHva3WpM7gvVOinMehp6if2UNIkbaN+plW
f5IwqEVxsNZpeixc4GsbY9dXEk3WtRjwGSyDLySzEESH/kpJVoxO7ijRYqU+2oSR
wTBNePOk1H+LRQokgQIDAQAB
-----END PUBLIC KEY-----'''
PAGE_SIZE = 5000
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


class CrawlerSession:
    @staticmethod
    def __get_post_data(page_num):
        return {
            'PageIndex': str(page_num),
            'PageSize': str(PAGE_SIZE),
            'FunctionString': 'Query',
            'CID': '',
            'CourseName': '',
            'IsNotFull': 'false',
            'CourseType': 'B',
            'TeachNo': '',
            'TeachName': '',
            'Enrolls': '',
            'Capacity1': '',
            'Capacity2': '',
            'CampusId': '',
            'CollegeId': '',
            'Credit': '',
            'TimeText': ''
        }

    @staticmethod
    def __encrypt_password(password):
        key = rsa.PublicKey.load_pkcs1_openssl_pem(RSA_PUBKEY.encode())
        return base64.b64encode(rsa.encrypt(password.encode(), key)).decode()

    @staticmethod
    def __sanitize_text(text):
        text = re.sub(r'[\uff01-\uff5e]', lambda x: chr(ord(x.group(0)) - 0xfee0), text, flags=re.I | re.S)
        text = re.sub(r'\s+', ' ', text, flags=re.I | re.S)
        return text.strip()

    def __init__(self, backend, username, password):
        self.__session = aiohttp.ClientSession(headers={
            'User-Agent': random.choice(USER_AGENTS),
        })
        self.__backend = backend
        self.__term_id_list = []
        self.__term_name = None
        self.__term_id = None
        self.__username = username
        self.__password = password

    @property
    def term_id_list(self):
        return self.__term_id_list

    async def login(self):
        assert not self.__session.closed
        r = await self.__session.get(f'{self.__backend}/', ssl=SSL_CONTEXT)
        r.raise_for_status()
        assert r.url.host == 'oauth.shu.edu.cn'
        assert r.url.path.startswith('/login/')
        await asyncio.sleep(0.5)

        r = await self.__session.post(r.url, data={
            'username': self.__username,
            'password': self.__encrypt_password(self.__password)
        }, ssl=SSL_CONTEXT)
        r.raise_for_status()

        soup = BeautifulSoup(await r.text(), 'html.parser')
        self.__term_id_list = [tr['value'] for tr in soup.find_all('tr', attrs={'name': 'rowterm'})]

    async def select_term(self, term_id):
        assert term_id in self.__term_id_list

        r = await self.__session.post(f'{self.__backend}/Home/TermSelect', data={
            'termId': term_id,
        }, ssl=SSL_CONTEXT)
        r.raise_for_status()

        match = re.search(r'(\d{4})-(\d{4})学年[秋冬春夏]季学期', await r.text())
        assert match is not None
        assert int(match.group(2)) - int(match.group(1)) == 1
        self.__term_name = self.__sanitize_text(match.group(0))
        self.__term_id = term_id
        print(f'Select term: {self.__term_name} ({self.__term_id})')
        await asyncio.sleep(0.5)

    async def crawl(self):
        assert not self.__session.closed
        assert self.__term_id is not None
        assert self.__term_name is not None

        courses = []
        page, total, num = 1, PAGE_SIZE, 0
        while (page - 1) * PAGE_SIZE < total:
            r = await self.__session.post(f'{self.__backend}/StudentQuery/QueryCourseList',
                                          data=self.__get_post_data(page), ssl=SSL_CONTEXT)
            match = re.search(r'总行数：</span>(\d+?)', await r.text())
            assert match is not None
            total = int(match.group(1))

            soup = BeautifulSoup(await r.text(), 'html.parser')
            course_id = ''
            course_name = ''
            credit = ''
            num_cols = 0
            for tr in soup.find(attrs={'class': 'tbllist'}).find_all('tr'):
                ths = tr.find_all('th')
                if len(ths) > 0:
                    num_cols = len(ths)
                else:
                    assert num_cols >= 14
                    tds = tr.find_all('td')
                    if len(tds) < num_cols - 3:
                        continue
                    if len(tds) == num_cols:
                        course_id = self.__sanitize_text(tds[0].get_text(strip=True))
                        course_name = self.__sanitize_text(tds[1].get_text(strip=True))
                        credit = self.__sanitize_text(tds[2].get_text(strip=True))
                        del tds[:3]
                    teacher_id = self.__sanitize_text(tds[0].get_text(strip=True))
                    teacher_name = self.__sanitize_text(tds[1].get_text(strip=True))
                    teacher_title = self.__sanitize_text(tds[2].get_text(strip=True))
                    class_time = self.__sanitize_text(tds[3].get_text(strip=True))
                    position = self.__sanitize_text(tds[4].get_text(strip=True))
                    capacity = self.__sanitize_text(tds[5].get_text(strip=True))
                    number = self.__sanitize_text(tds[6].get_text(strip=True))
                    campus = self.__sanitize_text(tds[7].get_text(strip=True))
                    limitations = self.__sanitize_text(tds[8].get_text(strip=True))

                    limitations = [y for y in [self.__sanitize_text(x) for x in limitations.split(',')] if len(y) > 0]

                    courses.append({
                        'courseId': course_id,
                        'courseName': course_name,
                        'credit': credit,
                        'teacherId': teacher_id,
                        'teacherName': teacher_name,
                        'teacherTitle': teacher_title,
                        'classTime': class_time,
                        'campus': campus,
                        'position': position,
                        'capacity': capacity,
                        'number': number,
                        'limitations': limitations
                    })
                    num += 1
            page += 1
            await asyncio.sleep(0.5)
        courses.sort(key=lambda x: (x['courseId'], x['teacherId']))
        data_hash = hashlib.md5(json.dumps(courses, sort_keys=True).encode()).hexdigest()
        print(f'Fetch {len(courses)} courses ({data_hash})')
        return {
            'hash': data_hash,
            'termName': self.__term_name,
            'backendOrigin': self.__backend,
            'updateTimeMs': int(time.time() * 1000),
            'courses': courses,
        }

    async def logout(self):
        if self.__session.closed:
            return
        await self.__session.get(f'{self.__backend}/Login/Logout', ssl=SSL_CONTEXT)
        await asyncio.sleep(0.5)
        await self.__session.close()
        await asyncio.sleep(0.5)

async def save_data(output_dir, term_id, data):
    file_path = os.path.join(output_dir, 'terms', f'{term_id}.json')
    async with aiofiles.open(file_path, 'w') as fp:
        print(f'Save term data to {os.path.join("terms", f"{term_id}.json")}')
        await fp.write(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))

async def save_current(output_dir, current):
    file_path = os.path.join(output_dir, 'current.json')
    async with aiofiles.open(file_path, 'w') as fp:
        print('Save meta data to current.json')
        await fp.write(json.dumps(current, ensure_ascii=False, indent=2, sort_keys=True))

async def do_crawl(output_dir, backend, username, password):
    os.makedirs(output_dir, 0o755, True)
    os.makedirs(os.path.join(output_dir, 'terms'), 0o755, True)
    session = CrawlerSession(backend, username, password)
    try:
        result = {}
        print('Process login...')
        await session.login()
        print('Process crawl...')
        for term_id in session.term_id_list:
            await session.select_term(term_id)
            result[term_id] = await session.crawl()
            await save_data(output_dir, term_id, result[term_id])
        current = sorted([term_id for term_id in result.keys()], reverse=True)
        await save_current(output_dir, current)
    finally:
        try:
            print('Process logout...')
            await session.logout()
            print('Finished.')
        finally:
            pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Crawl courses data from SHU courses selection website.')
    parser.add_argument('backend', nargs='?', help='Backend URL.', default=DEFAULT_BACKEND)
    parser.add_argument('-o, --output-dir', nargs=1, help='Output dir, default is "data".', metavar='DIR')
    parser.add_argument('-u, --username', nargs=1, help='Your username.', metavar='USERNAME', required=True)
    password_group = parser.add_mutually_exclusive_group()
    password_group.add_argument('-p, --password', nargs=1, metavar='PASSWORD', help='Your password.')
    password_group.add_argument('--password-stdin', action='store_true', help='Take the password from stdin.')

    args = vars(parser.parse_args())

    _output_dir = args['o, __output_dir'][0] if args['o, __output_dir'] is not None else 'interval-crawler-task-result'
    _backend = args['backend']
    _username = args['u, __username'][0]
    if args['p, __password'] is not None:
        _password = args['p, __password'][0]
    elif args['password_stdin']:
        _password = input()
    else:
        _password = getpass.getpass()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(do_crawl(_output_dir, _backend, _username, _password))
