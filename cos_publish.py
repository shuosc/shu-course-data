import json
import os

from qcloud_cos import CosConfig, CosS3Client

data_dir = os.environ['DATA_DIR']
secret_id = os.environ['COS_SECRET_ID']
secret_key = os.environ['COS_SECRET_KEY']
region = os.environ['COS_REGION']
bucket = os.environ['COS_BUCKET']

config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
client = CosS3Client(config)

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


def extract_term_meta(term_id):
    data = load_term_json(term_id)
    if data is None:
        return None
    try:
        return {
            'termId': term_id,
            'backendOrigin': data['backendOrigin'],
            'hash': data['hash'],
            'termName': data['termName'],
            'updateTimeMs': data['updateTimeMs']
        }
    except KeyError:
        return None


def extract_term_courses(term_id):
    data = load_term_json(term_id)
    if data is None:
        return None
    return {
        'termId': term_id,
        'hash': data['hash'],
        'courses': data['courses']
    }


def get_all_term_meta():
    terms = []
    for filename in os.listdir(os.path.join(data_dir, 'terms')):
        if not filename.endswith('.json'):
            continue
        term_id = filename[:-5]
        meta = extract_term_meta(term_id)
        if meta is not None:
            terms.append(meta)
    terms.sort(key=lambda x: x['termId'], reverse=True)
    return terms


if __name__ == '__main__':
    current_term_ids = get_current_term_ids()
    print(f'Current term ids: {", ".join(current_term_ids)}.')
    all_term_meta = get_all_term_meta()
    print(f'Totally {len(all_term_meta)} terms found.')

    manifest = {
        'current': current_term_ids,
        'terms': all_term_meta,
    }

    courses_data_list = []
    manifest_data = json.dumps(manifest, **JSON_DUMPS_KWARGS).encode('utf-8')

    for current_term_id in current_term_ids:
        courses = extract_term_courses(current_term_id)
        courses_data = json.dumps(courses['courses'], **JSON_DUMPS_KWARGS).encode('utf-8')
        courses_data_list.append({
            'filename': f'{courses["termId"]}.{courses["hash"]}.json',
            'data': courses_data
        })

    for courses_data in courses_data_list:
        response = client.put_object(
            Bucket=bucket,
            Key=f'v2/terms/{courses_data["filename"]}',
            Body=courses_data['data'],
            CacheControl='public, max-age=2592000',
            ContentType='application/json; charset=utf-8'
        )
        print(f'Upload term data file "v2/terms/{courses_data["filename"]}" (ETag={response["ETag"]})')

    response = client.put_object(
        Bucket=bucket,
        Key=f'v2/manifest',
        Body=manifest_data,
        CacheControl='no-cache',
        ContentType='application/json; charset=utf-8'
    )
    print(f'Upload manifest file "v2/manifest" (ETag={response["ETag"]})')

    print('Finished.')
