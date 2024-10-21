import { Agent } from 'https';
import fetch from 'node-fetch';
import * as fs from 'fs';
import * as crypto from 'crypto';
import 'dotenv/config';

import fetchCallbackUrl from './login';
import { logChain, moduleLog } from './logger';
import { ICourse, ISimpleCourse } from './type';

const SHUSTUID = process.env.SHUSTUID;
const SHUSTUPWD = process.env.SHUSTUPWD;
const OUTPUTDIR = process.env.OUTPUTDIR || 'interval-crawler-task-result';

if (!SHUSTUID || !SHUSTUPWD) {
  throw new Error('SHUSTUID or SHUSTUPWD not found');
}

const httpsAgent = new Agent({
  rejectUnauthorized: false,
});
fs.mkdirSync(`./${OUTPUTDIR}/terms`, { recursive: true });

async function fetchBatch(): Promise<{ schoolTerm: string; name: string }> {
  const res = await fetch(
    'https://jwxk.shu.edu.cn/xsxk/profile/index.html',
    {
      agent: httpsAgent,
    }
  );
  const text = await res.text();
  const batchInfo = JSON.parse(text.split('var batch = ')[1].split(';')[0]);
  const { name } = batchInfo;
  moduleLog('JWXK', name);
  return batchInfo;
}

async function getToken(): Promise<string> {
  const url = await fetchCallbackUrl(SHUSTUID!, SHUSTUPWD!);
  const res = await fetch(url, {
    agent: httpsAgent,
  });
  const token = res.url.split('index.html?token=')[1];
  // moduleLog('JWXK', logChain('TOKEN', token));
  return token;
}

async function fetchAllCourses(token: string): Promise<ICourse[]> {
  const res = await fetch('https://jwxk.shu.edu.cn/xsxk/elective/shu/clazz/list', {
    method: 'POST',
    headers: {
      Authorization: token,
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: 'teachingClassType=ALLKC&pageNumber=1&pageSize=1',
    agent: httpsAgent,
  });
  const j = await res.json();
  const length = j.data.list.total;
  moduleLog('JWXK', logChain('课程总容量', length));
  moduleLog('JWXK', '获取所有课程信息中...');
  const res2 = await fetch('https://jwxk.shu.edu.cn/xsxk/elective/shu/clazz/list', {
    method: 'POST',
    headers: {
      Authorization: token,
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: 'teachingClassType=ALLKC&pageNumber=1&pageSize=' + length,
    agent: httpsAgent,
  });
  const j2 = await res2.json();
  const length2 = j2.data.list.rows.length;
  moduleLog('JWXK', logChain('返回课程总容量', length2));
  return j2.data.list.rows;
}

function getCourseLimitations(course: ICourse): string[] {
  let str = [];
  // 处理人数已满
  if (course.noCheckKrl === '0' && course.KRL == course.YXRS)
    str.push('人数已满');
  // 处理人满锁定
  else if (course.noCheckKrl === '0') str.push(`限制人数`);
  // 处理禁止选课
  if (course.canSelect === '0') str.push('禁止选课');
  // 处理禁止退课
  if (course.canDelete === '0') str.push('禁止退课');
  return str;
}

function makeCoursesSimple(courses: ICourse[]): ISimpleCourse[] {
  return courses.map((course) => {
    const simpleCourse: ISimpleCourse = {
      courseId: course.KCH,
      courseName: course.KCM,
      credit: course.XF,
      teacherId: course.KXH,
      teacherName: course.SKJS || '',
      teacherTitle: course.SKJSZC,
      classTime: course.YPSJDD,
      campus: course.XQ,
      position: course.teachingPlaceHide,
      capacity: course.KRL.toString(),
      number:
        course.noCheckKrl === '1'
          ? course.YXRS2.toString()
          : course.YXRS.toString(),
      limitations: getCourseLimitations(course),
    };
    return Object.keys(simpleCourse)
      .sort()
      .reduce((sortedObj, key) => {
        // @ts-ignore
        sortedObj[key] = simpleCourse[key];
        return sortedObj;
      }, {}) as ISimpleCourse;
  });
}

fetchBatch().then((batch) => {
  getToken().then((token) => {
    fetchAllCourses(token).then((courses) => {
      const simpleCourses = makeCoursesSimple(courses);
      const info = {
        backendOrigin: 'https://jwxk.shu.edu.cn',
        courses: simpleCourses,
        hash: crypto
          .createHash('md5')
          .update(JSON.stringify(simpleCourses))
          .digest('hex'),
        termName: batch.name,
        updateTimeMs: Date.now(),
      };
      fs.writeFileSync(
        `./${OUTPUTDIR}/terms/${batch.schoolTerm}.json`,
        JSON.stringify(info, null, 2)
      );
      fs.writeFileSync(
        `./${OUTPUTDIR}/current.json`,
        JSON.stringify([batch.schoolTerm], null, 2)
      );
      moduleLog('JWXK', logChain('课程信息已写入', batch.schoolTerm));
    });
  });
});
