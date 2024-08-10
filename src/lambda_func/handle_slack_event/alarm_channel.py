import os
import json
import datetime
import urllib.request
from typing import Dict, Any
from s3_method import get_object_from_s3, put_object_to_s3

def auto_send_message(event: Dict[str, Any], user_info:  Dict[str, Any]) -> None:
    """
    특정 이벤트에 따라 slack 채널에 메시지를 자동으로 전송
    매주 월요일마다 메시지를 전송하거나, 매월 첫번째 월요일 마다 챌린지 종합 결과 전송
    
    Args:
        event: 이벤트 정보, 트리거와 메시지를 포함
        user_info: 사용자 정보, 각 사용자의 주차별 참여 기록을 포함
    """
    if event['trigger']=='every_monday':
        send_message_channel(os.environ['TIL_CHANNEL'], event['message'])
    else:
        
        timestamps: dict = get_object_from_s3("til-challenge-bucket", os.environ['BUCKET_DIR_TIMESTAMP'])
        
        prev_month = timestamps['timestamps']['this_month']
        ts_in_month = timestamps['timestamps'][prev_month]
        
        challengers = list()
        for id, info in user_info.items():
            if isinstance(info, dict): 
                join_week = info['join_week']
            else: continue
        
            reaction_cnt = are_filtered_keys_included(join_week, ts_in_month)
            if reaction_cnt:
                challengers.append((info['name'], reaction_cnt))
        
        print(challengers)
        
        # 좋아요 가장 많은 사람의 좋아요 수 계산
        if challengers:
            max_value = max(item[1] for item in challengers)
        
            # 리스트 내포를 사용하여 가장 큰 값의 항목과 나머지 항목 분리
            super_challenger = [item for item in challengers if item[1] == max_value]
        
            # 리스트 항목을 포맷팅하여 문자열로 변환
            super_challenger_formatted_list = '\n'.join(f"- {item[0]} \U0001F44D `{item[1]}`" for item in super_challenger)
            challengers_formatted_list = '\n'.join(f"- {item[0]} \U0001F44D `{item[1]}`" for item in challengers)
        
            message = f"< {prev_month}월 스페셜 챌린저 >\n{super_challenger_formatted_list}\n\n< {prev_month}월 챌린저 >\n{challengers_formatted_list}\n다들 고생하셨습니다 \U0001F44F"
        
            print(message)
            send_message_channel(os.environ['TIL_CHANNEL'], message)
        
        today = datetime.date.today()
        month = today.month
        
        timestamps['timestamps'][str(month)] = dict()
        timestamps['timestamps']['this_month'] = str(month)
        
        put_object_to_s3("til-challenge-bucket", os.environ['BUCKET_DIR_TIMESTAMP'], timestamps)
        
    return

def send_message_channel(channel: str, text: str) -> None:
    """
    slack 채널에 메시지를 전송합니다.
    
    Params:
        channel: 메시지를 보낼 slack 채널 id
        text: 전송할 메시지 내용
    """
    url = 'https://slack.com/api/chat.postMessage'
    data = {
        'channel': channel,
        'text': text
    }
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {os.environ["SLACK_BOT_TOKEN"]}'
    }
    request = urllib.request.Request(url, json.dumps(data).encode(), headers)
    with urllib.request.urlopen(request) as response:
        print(f"response: {response}")
        return response.read()

def are_filtered_keys_included(join_week: Dict[str, Any], ts_in_month: Dict[str, Any]) -> Any:
    """
    주어진 사용자가 이번 달의 모든 TIL에 참여했는지 확인 alc
    참여한 TIL의 총 리액션 수를 계산
    
    Params:
        join_week (dict): 사용자의 주차별 참여 기록
        ts_in_month (dict): 이번 달에 해당하는 타임스탬프 집합
    
    Returns:
        int: 사용자가 받은 총 '좋아요' 수, 참여하지 않았으면 False 반환
    """
    # 비어있지 않은 딕셔너리 값을 가진 join_week의 상위 키를 필터링
    filtered_keys = {key for key, value in join_week.items() if isinstance(value, dict) and bool(value)}

    # ts_in_month의 키 집합
    ts_in_month_set = set(ts_in_month.keys())
    
    # 필터링된 join_week의 키가 ts_in_month에 모두 포함되어 있는지 검사
    if not ts_in_month_set.issubset(filtered_keys):
        return False
    
    # total 값을 합산
    # 반복문에서 ts_in_month 반복하는 이유는 포함 여부는 위에서 검사하기 때문에 이 로직이 실행될때는 모두 포함된 경우여서임
    total_sum = 0
    stack = list()
    for item in ts_in_month:
        stack.append(join_week[item])

    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            for total_value in current.values():
                total_sum += total_value['total']
    
    return total_sum