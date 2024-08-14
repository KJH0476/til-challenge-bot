import re
import os
import json
from slack_sdk import WebClient
from s3_method import get_object_from_s3, put_object_to_s3
from typing import Union, Dict, Any

client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])

def check_til_post(message: str) -> str:
    """
    메시지에서 'TIL' 키워드 뒤에 '숫자 월 숫자 주차' 형식이 있는지 확인하고, 
    해당 형식이 있는 경우 매칭된 텍스트를 반환

    Params:
        message: 확인할 메시지 문자열

    Returns:
        str: 매칭된 'TIL' 키워드와 날짜 정보 문자열
        False: 매칭이 없는 경우 False 반환
    """
    # 패턴 정의: 'TIL' 키워드 뒤에 정확한 '숫자 월 숫자 주차' 형식이 와야 함
    pattern = r'TIL\s*\d+\s*월\s*\d+\s*주차'
    
    # 정규표현식을 이용해 매칭된 부분을 찾음
    match = re.search(pattern, message)
    
    if match:
        matched_text = match.group()
        print(f"match = {matched_text}")
        return matched_text
    else:
        return False

def check_thread_from_til_msg(event_data: Dict[str, Any]) -> Union[bool, str]:
    """
    TIL 챌린지 게시글에 달린 메시지인지 확인
    S3 버킷에서 'til_timestamp.json' 파일을 가져와 해당 메시지의 thread_ts가 있는지 확인

    Params:
        event_data: slack 이벤트 데이터, 메시지 정보 포함

    Returns:
        Union[bool, str]: 
            - 해당 메시지가 TIL 챌린지 게시글에 달린 메시지가 아닌 경우 False 반환
            - 메시지가 TIL 챌린지 게시글에 달린 경우, 해당 메세지에 대한 정보("TIL 몇월 몇주차") 반환
    """
    timestamps = get_object_from_s3(os.environ['BUCKET'], os.environ['BUCKET_DIR_TIMESTAMP'])
    this_month = timestamps['timestamps']['this_month']
    
    if event_data['thread_ts'] not in timestamps['timestamps'][this_month]:
        return False
    
    return timestamps['timestamps'][this_month][event_data['thread_ts']]

def check_link_til_msg(message: list) -> bool:
    """
    메시지에 특정 URL이 포함되어 있는지 확인
    URL이 velog.io, github.io, blog.naver.com 중 하나일 경우 True를 반환

    Params:
        message: slack 메시지의 블록 형태, 각 블록이 dict로 표현됨

    Returns:
        bool: url이 포함되어 있으면 True, 아니면 False
    """
    compare_values = ['velog.io/', 'github.io/', 'blog.naver.com/']
    for msg in message:
        if msg['type']=='link':
            message = msg['url']
            if compare_values[0] in message or compare_values[1] in message or compare_values[2] in message:
                return True
    return False

def check_rm_til_msg(event_data: Dict[str, Any]) -> bool:
    """
    삭제된 스레드 메시지가 TIL 챌린지 게시글의 스레드인지 확인
    S3 버킷에서 파일을 가져와 해당 메시지의 thread_ts가 있는지 확인

    Params:
        event_data: slack 이벤트 데이터, 삭제된 메시지 정보 포함

    Returns:
        bool: 삭제된 스레드 메시지가 TIL 챌린지 게시글의 스레드인 경우 True, 아니면 False
    """
    timestamps = get_object_from_s3(os.environ['BUCKET'], os.environ['BUCKET_DIR_TIMESTAMP'])
    this_month = timestamps['timestamps']['this_month']

    deleted_ts = event_data['previous_message']['thread_ts']
    
    if deleted_ts in timestamps['timestamps'][this_month]:
        return True
    return False

