import json
import boto3
import os
from typing import Dict, Any

sqs = boto3.client('sqs')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    # slack event의 토큰을 검증
    if not verify_slack_request(event):
        return {
            'statusCode': 403,
            'body': json.dumps('검증되지 않은 요청')
        }

    print(event)
    body = json.loads(event['body'])

    # challenge 요청인 경우 처리
    # slack api event를 사용하기 위해선 challenge 검증을 해야함
    # 이를 위해 challenge 요청인 경우 요청 데이터의 challenge 값을 그대로 응답
    if 'challenge' in body:
        return {
            'statusCode': 200,
            'body': json.dumps(body['challenge'])
        }
        
    # 요청을 sqs로 전송
    response = sqs.send_message(
        QueueUrl=os.environ['SQS_URL'],
        MessageBody=json.dumps(body),
        MessageGroupId="default-group"  # 고유한 MessageGroupId 설정
    )
    
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Message sent to SQS",
            "messageId": response['MessageId']
        })
    }
    
def verify_slack_request(event: Dict[str, Any]) -> bool:
    """
    slack api 토큰을 검증
    ++ handle_slack_event/auth_slack_api 의 함수와 동일함

    Params:
        body: slack event 데이터

    Returns:
        bool: 검증 성공시 True, 실패시 False 반환
    """
    token = os.environ['SLACK_VERIFICATION_TOKEN']
    body = json.loads(event['body'])
    if 'token' in body and body['token'] == token:
        return True
    return False
