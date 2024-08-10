import json
import os
from typing import Dict, Any
from s3_method import get_object_from_s3
from auth_slack_api import verify_slack_request
from handle_method import handle_message, handle_reaction_added, handle_reaction_removed
from alarm_channel import auto_send_message

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda 핸들러 함수. Slack 이벤트를 처리합니다.

    Params:
        event: Lambda 함수로 전달된 이벤트 데이터
        context: Lambda 실행 컨텍스트

    Returns: 
        dict: 응답 딕셔너리
    """
    print(f"event: {event}")
    
    body = json.loads(event['Records'][0]['body']) # SQS 메세지 바디
    user_info = get_object_from_s3("til-challenge-bucket", os.environ['BUCKET_DIR_INFO'])   # 사용자 정보
    
    # Event Bridge 에 의해 트리거될 때 실행
    if 'trigger' in body:
        auto_send_message(body, user_info)
        
        return {
            'statusCode': 200,
            'body': json.dumps('슬랙 트리거 요청 완료')
        }
    
    # slack api 토큰 검증 
    if not verify_slack_request(body):
        return {
            'statusCode': 403,
            'body': json.dumps('검증되지 않은 요청')
        }

    if 'event' in body: # 이벤트 데이터가 있는 경우
        event_data = body['event']
        print(f"event_data: {event_data}")
        
        # 리액션이 추가된 경우
        if event_data['type'] == 'reaction_added':
            handle_reaction_added(event_data, user_info)
        # 리액션이 제거된 경우
        elif event_data['type'] == 'reaction_removed':
            handle_reaction_removed(event_data, user_info)
        # 메시지 관련 요청인 경우
        elif event_data['type'] == 'message':
            handle_message(event_data, user_info)
                    
    return {
        'statusCode': 200,
        'body': json.dumps('OK')
    }
