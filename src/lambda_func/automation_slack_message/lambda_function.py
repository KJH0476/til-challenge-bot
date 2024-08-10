import json
import os
import boto3
import datetime
import calendar
from typing import Dict, Any, Tuple

sqs = boto3.client('sqs')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    
    print(event)
    
    if 'event' in event:
        # 매주 월요일마다 트리거되는 트리거 요청인 경우
        if event['event']=='every_monday':
            today = datetime.date.today()
            month, week_number = get_month_week(today)

            message_to_send=f"""
            *[TIL {month}월 {week_number}주차]*\n
\u2705 일요일 자정까지 댓글로 게시물 링크를 올려주세요! (Velog, Github, Naver)\n
\u2705 필수 해시태그\n
#내맘대로TIL챌린지 #교보DTS #클라우드교육 #글로벌소프트웨어캠퍼스 #GSC신촌\n
\u2705 필수 포함 문구\n
글로벌소프트웨어캠퍼스와 교보DTS가 함께 진행하는 챌린지입니다.
\U0001F449 {os.environ['TIL_DOMAIN']}
            """
            
            body={
                "trigger": event['event'],
                "message": message_to_send
            }
        # 매월 첫번째 월요일마다 트리거되는 트리거 요청인 경우
        elif event['event']=='every_month':
            today = datetime.date.today()
            month = today.month
            
            body={
                "trigger": event['event'],
                "month": month
            }
        
        # 위의 요청을 sqs 메세지 큐로 전송
        response = sqs.send_message(
            QueueUrl=os.environ['SQS_URL'],
            MessageBody=json.dumps(body),
            MessageGroupId="default-group"
        )

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Message sent to SQS",
            "messageId": response['MessageId']
        })
    }

def get_month_week(date: datetime.date) -> Tuple[int, int]:
    """
    현재 몇월 몇주차인지 구하는 함수

    Params:
        date: 오늘 날짜

    Returns:
        Tuple(int, int): 몇월, 몇주차에 대한 정수 값 반환
    """
    year = date.year
    month = date.month
    
    # 월의 첫 날과 마지막 날 구하기
    first_day_of_month = datetime.date(year, month, 1)
    last_day_of_month = datetime.date(year, month, calendar.monthrange(year, month)[1])
    
    # 몇 번째 주인지 계산
    week_number = (date - first_day_of_month).days // 7 + 1
    
    return month, week_number
