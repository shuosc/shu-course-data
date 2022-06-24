import hashlib
import json
import os

import oss2

data_dir = os.environ['DATA_DIR']
access_key_id = os.environ['OSS_ACCESS_KEY_ID']
access_key_secret = os.environ['OSS_ACCESS_KEY_SECRET']
endpoint = os.environ['OSS_ENDPOINT']
bucket = os.environ['OSS_BUCKET']

auth = oss2.Auth(access_key_id, access_key_secret)
bucket = oss2.Bucket(auth, endpoint, bucket)

JSON_DUMPS_KWARGS = {
    'ensure_ascii': False,
    'separators': (',', ':'),
    'sort_keys': True
}


def get_current_term_ids():
    with open(os.path.join(data_dir, 'current.json')) as fp:
        return json.load(fp)


def load_term_json(term_id):
    with open(os.path.join(data_dir, 'terms', f'{term_id}.json')) as fp:
        try:
            return json.load(fp)
        except ValueError:
            return None


def get_term_data(term_id):
    data = load_term_json(term_id)
    if data is None:
        return None
    return {
        'termId': term_id,
        'backendOrigin': data['backendOrigin'],
        'termName': data['termName'],
        'updateTimeMs': data['updateTimeMs'],
        'courses': data['courses']
    }


if __name__ == '__main__':
    current_term_ids = get_current_term_ids()
    use_term_id = max(current_term_ids)
    print(f'Current term ids: {", ".join(current_term_ids)}, use {use_term_id}.')
    term_data = get_term_data(use_term_id)

    courses = [{
        'campus': course['campus'],
        'class_time': course['classTime'],
        'course_id': course['courseId'],
        'course_name': course['courseName'],
        'credit': course['credit'],
        'teacher_id': course['teacherId'],
        'teacher_name': course['teacherName']
    } for course in term_data['courses']]
    course_hash = hashlib.md5(json.dumps(courses, sort_keys=True).encode('utf-8')).hexdigest()[:8]

    info = {
        'backend': term_data['backendOrigin'],
        'hash': course_hash,
        'trimester': term_data['termName'],
        'url': f'https://xk.shuosc.com/api/courses/{course_hash}.json'
    }

    extra = {
        'data': {
            f'{course["courseId"]}-{course["teacherId"]}': {
                'capacity': course['capacity'],
                'limitations': course['limitations'],
                'number': course['number'],
                'venue': course['position'],
                'teacher_title': course['teacherTitle']
            } for course in term_data['courses']
        },
        'hash': course_hash,
        'update_time': term_data['updateTimeMs']
    }

    print(f'Upload term data file "api/courses/{course_hash}.json"')
    bucket.put_object(
        f'api/courses/{course_hash}.json',
        json.dumps(courses, **JSON_DUMPS_KWARGS).encode('utf-8'),
        {'Content-Type': 'application/json'}
    )
    print(f'Upload term info file "api/courses/info"')
    bucket.put_object(
        'api/courses/info',
        json.dumps(info, **JSON_DUMPS_KWARGS).encode('utf-8'),
        {'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}
    )
    print(f'Upload term extra data file "api/courses/extra"')
    bucket.put_object(
        'api/courses/extra',
        json.dumps(extra, **JSON_DUMPS_KWARGS).encode('utf-8'),
        {'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}
    )

    print('Finished.')
