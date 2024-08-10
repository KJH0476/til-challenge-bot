import json
import boto3

s3 = boto3.client('s3')

def get_object_from_s3(my_bucket: str, object_key: str):
    """
    S3 버킷에서 json 파일으르 파싱하여 dict 객체로 변환하여 반환

    Params:
        my_bucket: 버킷 명
        object_key: S3 버킷 내에서 객체를 식별하는 키(파일경로)
    
    Returns:
        dict: json 객체를 파싱한 dict 객체
    """
    response = s3.get_object(Bucket=my_bucket, Key=object_key)
    data = response['Body'].read().decode('utf-8')
    return json.loads(data)

def put_object_to_s3(bucket_name: str, object_key: str, data: dict):
    """
    dict 객체를 json으로 변환하여 S3 버킷에 저장

    Params:
        my_bucket: 버킷 명
        object_key: S3 버킷 내에서 객체를 식별하는 키(파일경로)
        data: 버킷에 저장할 데이터
    """
    s3.put_object(
        Bucket=bucket_name,
        Key=object_key,
        Body=json.dumps(data),
        CacheControl='no-cache',
        ContentType='application/json'
        )
