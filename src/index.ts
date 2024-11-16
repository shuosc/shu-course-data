import { Agent } from 'https';
import fetch from 'node-fetch';
import * as fs from 'fs';
import * as crypto from 'crypto';
import 'dotenv/config';

import fetchCallbackUrl from './login';
import { logChain, moduleLog } from './logger';
import { ICourse, IElectiveBatch, ISimpleCourse } from './type';

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

function fetchBatch(
  token: string
): Promise<{ schoolTerm: string; name: string; code: string }[]> {
  return new Promise((resolve, reject) => {
    fetch(`https://jwxk.shu.edu.cn/xsxk/web/studentInfo`, {
      method: 'POST',
      headers: {
        Authorization: token,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: `token=${token}`,
      agent: httpsAgent,
    })
      .then((r) => {
        r.json()
          .then((r) => {
            if (r.code !== 200) reject(r.msg);
            const raw_batches: {
              schoolTerm: string;
              name: string;
              code: string;
            }[] = (r.data.student.electiveBatchList as IElectiveBatch[])
              // .filter((e) => e.canSelect === '1')
              .map((e) => ({
                schoolTerm: e.schoolTerm,
                name: e.name,
                code: e.code,
              }))
              .sort((a, b) => {
                const convertTermToNumber = (term: string) => {
                  const [startYear, endYear, semester] = term.split('-');
                  return parseInt(startYear) * 10 + parseInt(semester);
                };
                return (
                  convertTermToNumber(b.schoolTerm) -
                  convertTermToNumber(a.schoolTerm)
                );
              });
            const batches_set = new Set<string>();
            const batches = raw_batches.filter((e) => {
              if (!batches_set.has(e.schoolTerm)) {
                batches_set.add(e.schoolTerm);
                return true;
              }
              return false;
            });
            moduleLog(
              'JWXK',
              logChain(
                '批次信息',
                '\n - ' +
                  batches
                    .map((e) => `${e.name}(${e.schoolTerm}) ${e.code}`)
                    .join('\n - ')
              )
            );
            resolve(batches);
          })
          .catch(reject);
      })
      .catch(reject);
  });
}

function getToken(): Promise<string> {
  return new Promise((resolve, reject) => {
    fetchCallbackUrl(SHUSTUID!, SHUSTUPWD!)
      .then((url) => {
        fetch(url, {
          agent: httpsAgent,
        })
          .then((r) => {
            const token = r.url.split('index.html?token=')[1];
            // moduleLog('JWXK', logChain('TOKEN', token));
            resolve(token);
          })
          .catch(reject);
      })
      .catch(reject);
  });
}

function fetchAllCourses(token: string, code: string): Promise<ICourse[]> {
  return new Promise((resolve, reject) => {
    fetch(
      `https://jwxk.shu.edu.cn/xsxk/elective/shu/grablessons?batchId=${code}`,
      {
        agent: httpsAgent,
        headers: {
          Cookie: `Authorization=${token}`,
        },
      }
    )
      .then(() =>
        fetch('https://jwxk.shu.edu.cn/xsxk/elective/shu/clazz/list', {
          method: 'POST',
          headers: {
            Authorization: token,
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: 'teachingClassType=ALLKC&pageNumber=1&pageSize=1',
          agent: httpsAgent,
        })
          .then((r) => {
            r.json()
              .then((r) => {
                if (r.code === 200) {
                  const length = r.data.list.total;
                  moduleLog('JWXK', logChain('课程总容量', length));
                  moduleLog('JWXK', '获取所有课程信息中...');
                  fetch(
                    'https://jwxk.shu.edu.cn/xsxk/elective/shu/clazz/list',
                    {
                      method: 'POST',
                      headers: {
                        Authorization: token,
                        'Content-Type': 'application/x-www-form-urlencoded',
                      },
                      body:
                        'teachingClassType=ALLKC&pageNumber=1&pageSize=' +
                        length,
                      agent: httpsAgent,
                    }
                  )
                    .then((r) => {
                      r.json()
                        .then((r) => {
                          if (r.code === 200) {
                            moduleLog(
                              'JWXK',
                              logChain(
                                '返回课程总容量',
                                r.data.list.rows.length
                              )
                            );
                            resolve(r.data.list.rows);
                          } else {
                            reject(r.msg);
                          }
                        })
                        .catch(reject);
                    })
                    .catch(reject);
                } else {
                  reject(r.msg);
                }
              })
              .catch(reject);
          })
          .catch(reject)
      )
      .catch(reject);
  });
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
      position: course.teachingPlaceHide || '',
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

getToken().then((token) => {
  fetchBatch(token).then(async (batches) => {
    for (const batch of batches) {
      moduleLog('JWXK', logChain('开始处理学期', batch.schoolTerm));
      await fetchAllCourses(token, batch.code).then((courses) => {
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
      });
    }
    moduleLog('JWXK', '所有学期均已获取完毕');
    fs.writeFileSync(
      `./${OUTPUTDIR}/current.json`,
      JSON.stringify(
        batches.map((b) => b.schoolTerm),
        null,
        2
      )
    );
  });
});
