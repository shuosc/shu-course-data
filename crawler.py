import argparse
import asyncio
import getpass
import hashlib
import json
import os
import random
import re
import ssl
import time

import aiohttp
import certifi
from bs4 import BeautifulSoup

DEFAULT_BACKEND = 'http://xk.autoisp.shu.edu.cn'
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:33.0) Gecko/20120101 Firefox/33.0',
    'Opera/9.80 (Windows NT 6.0) Presto/2.12.388 Version/12.14',
    'Mozilla/5.0 (MSIE 10.0; Windows NT 6.1; Trident/5.0)',
]
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

    def __init__(self, backend, termid, username, password):
        self.__session = aiohttp.ClientSession(headers={
            'User-Agent': random.choice(USER_AGENTS),
        })
        self.__backend = backend
        self.__termid = termid
        self.__username = username
        self.__password = password
        self.__trimester = None

    async def login(self):
        assert not self.__session.closed
        r = await self.__session.get(f'{self.__backend}/', ssl=SSL_CONTEXT)
        r.raise_for_status()
        assert r.url.host == 'oauth.shu.edu.cn'
        assert r.url.path.startswith('/login/')
        await asyncio.sleep(0.5)

        r = await self.__session.post(r.url, data={
            'username': self.__username,
            'password': self.__password
        }, ssl=SSL_CONTEXT)
        r.raise_for_status()

        if self.__termid is None:
            soup = BeautifulSoup(await r.text(), 'html.parser')
            self.__termid = max([tr['value'] for tr in soup.find_all('tr', attrs={'name': 'rowterm'})])

        r = await self.__session.post(f'{self.__backend}/Home/TermSelect', data={
            'termId': self.__termid,
        }, ssl=SSL_CONTEXT)
        r.raise_for_status()

        match = re.search(r'(\d{4})-(\d{4})学年[秋冬春夏]季学期', await r.text())
        assert match is not None
        assert int(match.group(2)) - int(match.group(1)) == 1
        self.__trimester = match.group(0)
        print(f'Current trimester: {self.__trimester} ({self.__termid})')
        await asyncio.sleep(0.5)

    async def crawl(self):
        assert not self.__session.closed
        assert self.__trimester is not None

        data = []
        extra_data = {}
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
                    assert num_cols >= 13
                    tds = tr.find_all('td')
                    if len(tds) < num_cols - 3:
                        continue
                    if len(tds) == num_cols:
                        course_id = tds[0].get_text(strip=True)
                        course_name = tds[1].get_text(strip=True)
                        credit = tds[2].get_text(strip=True)
                        del tds[:3]
                    teacher_id = tds[0].get_text(strip=True)
                    teacher_name = tds[1].get_text(strip=True)
                    class_time = tds[2].get_text(strip=True)
                    venue = tds[3].get_text(strip=True)
                    capacity = tds[4].get_text(strip=True)
                    number = tds[5].get_text(strip=True)
                    campus = tds[6].get_text(strip=True)
                    limitations = tds[7].get_text(strip=True)

                    limitations = [] if limitations == '' else limitations.split(',')
                    print(course_id, course_name, credit, teacher_id, teacher_name, class_time, campus,
                          venue, capacity, number, limitations)

                    data.append({
                        'course_id': course_id,
                        'course_name': course_name,
                        'credit': credit,
                        'teacher_id': teacher_id,
                        'teacher_name': teacher_name,
                        'class_time': class_time,
                        'campus': campus
                    })
                    extra_data[f'{course_id}-{teacher_id}'] = {
                        'venue': venue,
                        'capacity': capacity,
                        'number': number,
                        'limitations': limitations
                    }
                    num += 1
            page += 1
            await asyncio.sleep(0.5)
        data_hash = hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()
        info = {
            'hash': data_hash[:8],
            'trimester': self.__trimester,
            'backend': self.__backend
        }
        extra = {
            'data': extra_data,
            'hash': data_hash[:8],
            'update_time': time.time_ns() // 1000
        }
        return {
            'info': info,
            'data': data,
            'extra': extra
        }

    async def logout(self):
        if self.__session.closed:
            return
        await self.__session.get(f'{self.__backend}/Login/Logout', ssl=SSL_CONTEXT)
        await self.__session.close()


async def do_crawl(output_dir, backend, termid, username, password):
    os.makedirs(output_dir, 0o755, True)
    session = CrawlerSession(backend, termid, username, password)
    try:
        print('Processing login...')
        await session.login()
        print('Processing crawl...')
        result = await session.crawl()
        json.dump(result['info'], open(os.path.join(output_dir, 'info.json'), 'w'), sort_keys=True)
        json.dump(result['data'], open(os.path.join(output_dir, f'{result["info"]["hash"]}.json'), 'w'), sort_keys=True)
        json.dump(result['extra'], open(os.path.join(output_dir, 'extra.json'), 'w'), sort_keys=True)
    finally:
        try:
            print('Processing logout...')
            await session.logout()
            print('Finished.')
        finally:
            pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Crawl courses data from SHU courses selection website.')
    parser.add_argument('backend', nargs='?', help='Backend URL.', default=DEFAULT_BACKEND)
    parser.add_argument('-o, --output-dir', nargs=1, help='Output dir, default is "data".', metavar='TERMID')
    parser.add_argument('-t, --termid', nargs=1, help='The term ID like "20203".', metavar='TERMID')
    parser.add_argument('-u, --username', nargs=1, help='Your username.', metavar='USERNAME', required=True)
    password_group = parser.add_mutually_exclusive_group()
    password_group.add_argument('-p, --password', nargs=1, metavar='PASSWORD', help='Your password.')
    password_group.add_argument('--password-stdin', action='store_true', help='Take the password from stdin.')

    args = vars(parser.parse_args())

    _output_dir = args['o, __output_dir'][0] if args['o, __output_dir'] is not None else 'interval-crawler-task-result'
    _backend = args['backend']
    _termid = args['t, __termid'][0] if args['t, __termid'] is not None else None
    _username = args['u, __username'][0]
    if args['p, __password'] is not None:
        _password = args['p, __password'][0]
    elif args['password_stdin']:
        _password = input()
    else:
        _password = getpass.getpass()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(do_crawl(_output_dir, _backend, _termid, _username, _password))
