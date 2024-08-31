import json
import os
import boto3

s3 = boto3.client('s3')

def lambda_handler(event, context):
    """
    클라이언트에게 요청이 오면 버킷에서 객체를 꺼내 반환

    Params:
        event: Lambda 함수로 전달된 이벤트 데이터
        context: Lambda 실행 컨텍스트

    Returns: 
        dict: 응답 딕셔너리
    """
    try:
        user_info: dict = get_object_from_s3(os.environ['BUCKET'], os.environ['BUCKET_DIR_INFO'])
        timestamps: dict = get_object_from_s3(os.environ['BUCKET'], os.environ['BUCKET_DIR_TIMESTAMP'])
    except Exception as e:
        print(f"Error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps("failed get bucket data!")
        }
    
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps({
            'user_info': user_info,
            'timestamps_info': timestamps
        })
    }
    
def get_object_from_s3(my_bucket, object_key):
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
