# lambda/index.py
import json
import os
import re
import urllib.request
from botocore.exceptions import ClientError

FASTAPI_URL = "https://8ee8-34-73-87-36.ngrok-free.app"

# Lambda コンテキストからリージョンを抽出する関数（将来的に使う場合のため残す）
def extract_region_from_arn(arn):
    match = re.search('arn:aws:lambda:([^:]+):', arn)
    if match:
        return match.group(1)
    return "us-east-1"  # デフォルト値

def lambda_handler(event, context):
    try:
        print("=== Step 1: Event received ===")
        print(json.dumps(event))

        # Cognitoで認証されたユーザー情報を取得（オプション）
        user_info = None
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            user_info = event['requestContext']['authorizer']['claims']
            print(f"Authenticated user: {user_info.get('email') or user_info.get('cognito:username')}")

        # リクエストボディの解析
        body = json.loads(event['body'])
        message = body['message']
        conversation_history = body.get('conversationHistory', [])

        print("=== Step 2: Preparing FastAPI request ===")
        request_payload = json.dumps({
            "prompt": message,
            "max_new_tokens": 128
        }).encode("utf-8")


        # FastAPIへのリクエスト送信
        req = urllib.request.Request(
            f"{FASTAPI_URL}/generate",
            data=request_payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        print("=== Step 3: Sending request to FastAPI ===")
        with urllib.request.urlopen(req) as response:
            response_body = response.read()
            result = json.loads(response_body)
            print("FastAPI response:", result)

        # 成功レスポンスの返却
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": True,
                "response": result.get("generated_text"),
                "conversationHistory": result.get("conversationHistory", [])
            })
        }

    except Exception as error:
        print("Error:", str(error))
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": str(error)
            })
        }
