import json
import os
import logging
from typing import Dict, Any
from s3_method import get_object_from_s3, put_object_to_s3
from alarm_channel import send_message_channel
from check_message import check_thread_from_til_msg, check_link_til_msg, check_rm_til_msg, check_til_post

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def handle_reaction_added(event_data: Dict[str, Any], user_info: Dict[str, Any]) -> None:
    """
    리액션 추가 이벤트를 처리
    '+1' 로 시작하는 리액션 데이터에 추가 후 저장

    Params:
        event_data: 반응 추가 이벤트 데이터
        user_info: 사용자 정보 딕셔너리
    """
    if event_data['reaction'].startswith('+1'):
        try:
            if event_data['item_user'] not in user_info:
                return
            
            user = user_info[event_data['item_user']]
            
            join_week: dict = user['join_week']
            for parent_ts, child_ts in join_week.items():
                if event_data['item']['ts'] in child_ts:
                    if event_data['user'] not in join_week[parent_ts][event_data['item']['ts']]['like']:
                        join_week[parent_ts][event_data['item']['ts']]['like'][event_data['user']] = 1
                        
                        if join_week[parent_ts][event_data['item']['ts']]['has_link']:
                            user['reaction_count'] += 1
                            join_week[parent_ts][event_data['item']['ts']]['total'] += 1
                            
                        put_object_to_s3("til-challenge-bucket", os.environ['BUCKET_DIR_INFO'], user_info)
                        
                        send_message_channel(os.environ['ADMIN_ID'], f"{user['name']} : {event_data['item']['ts']} 글에 좋아요 +1")
                        break

        except Exception as e:
            logger.error("Error occurred: %s", str(e))
            error_message = f"Error occurred: {str(e)}"
            send_message_channel(os.environ['ADMIN_ID'], error_message)

def handle_reaction_removed(event_data: Dict[str, Any], user_info: Dict[str, Any]) -> None:
    """
    리액션 제거 이벤트를 처리
    '+1' 로 시작하는 리액션 데이터에서 제거 후 저장

    Params:
        event_data: 반응 제거 이벤트 데이터
        user_info: 사용자 정보 딕셔너리
    """
    if event_data['reaction'].startswith('+1'):
        try:
            if event_data['item_user'] not in user_info:
                return
            
            user = user_info[event_data['item_user']]
            
            join_week: dict = user['join_week']
            for parent_ts, child_ts in join_week.items():
                if event_data['item']['ts'] in child_ts:
                    if event_data['user'] in join_week[parent_ts][event_data['item']['ts']]['like']:
                        del join_week[parent_ts][event_data['item']['ts']]['like'][event_data['user']]
                        
                        user['reaction_count'] -= 1
                        join_week[parent_ts][event_data['item']['ts']]['total'] -= 1
                        put_object_to_s3("til-challenge-bucket", os.environ['BUCKET_DIR_INFO'], user_info)
                        
                        send_message_channel(os.environ['ADMIN_ID'], f"{user['name']} : {event_data['item']['ts']} 글에 좋아요 -1")
                        break

        except Exception as e:
            logger.error("Error occurred: %s", str(e))
            error_message = f"Error occurred: {str(e)}"
            send_message_channel(os.environ['ADMIN_ID'], error_message)
            
            
def handle_message(event_data: Dict[str, Any], user_info: Dict[str, Any]) -> None:
    """
    메시지 이벤트를 처리
    slack api 에서 오는 요청 값이 경우에 따라 다르므로 요청 데이터의 필드 존재여부에 따라 분기 처리

    Params:
        event_data: 메시지 이벤트 데이터
        user_info: 사용자 정보 딕셔너리
    """
    if 'parent_user_id' in event_data:
        handle_thread_message(event_data, user_info)
    elif 'subtype' in event_data and event_data['subtype'] == 'message_deleted':
        handle_deleted_message(event_data, user_info)
    elif 'subtype' in event_data and event_data['subtype'] == 'message_changed':
        handle_edited_message(event_data, user_info)
    elif 'parant_user_id' not in event_data and 'bot_profile' in event_data:
        handle_channel_message(event_data, user_info)
    
def handle_channel_message(event_data: Dict[str, Any], user_info: Dict[str, Any]) -> None:
    """
    TIL 챌린지 게시글이 올라왔을 경우 처리(스레드 답글인 경우 X)
    
    Params:
        event_data: 스레드 메시지 이벤트 데이터
        user_info: 사용자 정보 딕셔너리
    """
    try:
        timestamps: dict = get_object_from_s3("til-challenge-bucket", os.environ['BUCKET_DIR_TIMESTAMP'])
        ts: str = event_data['ts']
        this_month = timestamps['timestamps']['this_month']
        
        if ts not in timestamps['timestamps'][this_month]:
            # text_elements는 event_data에서 텍스트를 포함하는 요소를 리스트 형태로 가져옴
            text_elements = event_data['blocks'][0]['elements'][0]['elements']
            # text_elements 리스트의 각 요소에서 'text' 필드를 추출하고 결합 해서 문자열로 만듬
            message_text = ''.join([el['text'] for el in text_elements if el['type'] == 'text'])
            
            # TIL 메세지인지 검증
            til_text = check_til_post(message_text)
            
            if til_text:
                # 요청 두번 방지
                for week in timestamps['timestamps'][this_month].values():
                    if til_text==week:
                        return
                
                timestamps['timestamps'][this_month][ts] = til_text
                
                # 각 사용자의 join_week에 ts 추가
                for user_id, info in user_info.items():
                    if user_id == "all_user":
                        continue  # all_user 키는 건너뜀
                    if 'join_week' not in info:
                        info['join_week'] = {}
                    info['join_week'][ts] = dict()
                
                put_object_to_s3("til-challenge-bucket", os.environ['BUCKET_DIR_TIMESTAMP'], timestamps)
                put_object_to_s3("til-challenge-bucket", os.environ['BUCKET_DIR_INFO'], user_info)
    except Exception as e:
        logger.error("Error occurred: %s", str(e))
        error_message = f"Error occurred: {str(e)}"
        send_message_channel(os.environ['ADMIN_ID'], error_message)

def handle_thread_message(event_data: Dict[str, Any], user_info: Dict[str, Any]) -> None:
    """
    스레드 메시지를 처리
    TIL 챌린지 게시글인지 확인하고 해당 답글의 링크를 검사한 후 데이터에 추가한 후 저장

    Params:
        event_data: 스레드 메시지 이벤트 데이터
        user_info: 사용자 정보 딕셔너리
    """
    try:
        check_message = check_thread_from_til_msg(event_data)
        if not check_message:
            print(f"TIL 챌린지 게시글이 아님: {event_data['blocks'][0]['elements'][0]['elements']}")
            return

        user = user_info[event_data['user']]
        join_week = user['join_week'][event_data['thread_ts']]
        
        # 답글 velog, githubio, naver 링크 검사
        if check_link_til_msg(event_data['blocks'][0]['elements'][0]['elements']):
            
            join_week[event_data['ts']] = dict(total=0, has_link=True, like={})
            
            put_object_to_s3("til-challenge-bucket", os.environ['BUCKET_DIR_INFO'], user_info)
            
            send_message_channel(event_data['channel'], f"{user['name']}이 {check_message} 챌린지에 참여하였습니다 :fire::fire:")
        else:
            join_week[event_data['ts']] = dict(total=0, has_link=False, like={})
            put_object_to_s3("til-challenge-bucket", os.environ['BUCKET_DIR_INFO'], user_info)
            
    except Exception as e:
        logger.error("Error occurred: %s", str(e))
        error_message = f"Error occurred: {str(e)}"
        send_message_channel(os.environ['ADMIN_ID'], error_message)

def handle_deleted_message(event_data: Dict[str, Any], user_info: Dict[str, Any]) -> None:
    """
    삭제된 메시지를 처리
    TIL 챌린지 게시글인지 확인하고 해당 답글의 링크를 검사한 후 데이터에서 제거한 후 저장

    Params:
        event_data: 삭제된 메시지 이벤트 데이터
        user_info: 사용자 정보 딕셔너리
    """
    try:
        if not check_rm_til_msg(event_data):
            print(f"삭제한 스레드 텍스트가 TIL 챌린지 게시글에 존재하지 않음")
            return
            
        user = user_info[event_data['previous_message']['user']]
        join_week = user['join_week'][event_data['previous_message']['thread_ts']]
        
        if event_data['previous_message']['ts'] in join_week:
            user['reaction_count'] -= join_week[event_data['previous_message']['ts']]['total']
            del join_week[event_data['previous_message']['ts']]
            
            put_object_to_s3("til-challenge-bucket", os.environ['BUCKET_DIR_INFO'], user_info)
            
            send_message_channel(os.environ['ADMIN_ID'], f"{user['name']}이 챌린지 글을 삭제하였습니다.")
        
    except Exception as e:
        logger.error("Error occurred: %s", str(e))
        error_message = f"Error occurred: {str(e)}"
        send_message_channel(os.environ['ADMIN_ID'], error_message)
    
def handle_edited_message(event_data: Dict[str, Any], user_info: Dict[str, Any]) -> None:
    """
    수정된 thread message 처리
    TIL 챌린지 게시글인지 확인하고 해당 답글의 링크를 검사한 후 새로 링크가 추가되었으면 has_link 필드 True로 변경 후 저장

    Params:
        event_data: 수정된 스레드 메시지 이벤트 데이터
        user_info: 사용자 정보 딕셔너리
    """
    try:
        if 'thread_ts' not in event_data['message']:
            print("수정된 메시지가 답글 메세지가 아닙니다.")
            return

        check_message = check_thread_from_til_msg(event_data['message'])
        if not check_message:
            print(f"수정된 메시지가 TIL 챌린지 답글이 아님: {event_data['message']['blocks'][0]['elements'][0]['elements']}")
            return
        
        if check_link_til_msg(event_data['message']['blocks'][0]['elements'][0]['elements']):
            user = user_info[event_data['message']['user']]
            join_week = user['join_week'][event_data['message']['thread_ts']]
            
            if event_data['message']['ts'] not in join_week:
                join_week[event_data['ts']] = dict(total=0, has_link=True, like={})
            
                put_object_to_s3("til-challenge-bucket", os.environ['BUCKET_DIR_INFO'], user_info)
            
                send_message_channel(event_data['channel'], f"{user['name']}이 챌린지에 참여하였습니다 :fire::fire:")
            else:
                if not join_week[event_data['message']['ts']]['has_link']:
                    join_week[event_data['message']['ts']]['has_link'] = True
                    
                    join_week[event_data['message']['ts']]['total'] = len(join_week[event_data['message']['ts']]['like'])
                    
                    user['reaction_count'] += join_week[event_data['message']['ts']]['total']
                    
                    put_object_to_s3("til-challenge-bucket", os.environ['BUCKET_DIR_INFO'], user_info)
                    
                    send_message_channel(os.environ['ADMIN_ID'], f"{user['name']}이 {event_data['message']['ts']} 에 링크를 추가했습니다.")
                    send_message_channel(event_data['channel'], f"{user['name']}이 {check_message} 챌린지에 참여하였습니다 :fire::fire:")
            
    except Exception as e:
        logger.error("Error occurred: %s", str(e))
        error_message = f"Error occurred: {str(e)}"
        send_message_channel(os.environ['ADMIN_ID'], error_message)