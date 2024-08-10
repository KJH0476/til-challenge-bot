import os
import json
from typing import Dict, Any

def verify_slack_request(body: Dict[str, Any]) -> bool:
    """
    slack api 토큰을 검증합니다.

    Params:
        body: slack event 데이터

    Returns:
        bool: 검증 성공시 True, 실패시 False 반환
    """
    token = os.environ['SLACK_VERIFICATION_TOKEN']
    if 'token' in body and body['token'] == token:
        return True
    return False