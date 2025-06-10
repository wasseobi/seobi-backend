"""General Agent 관련 라우트를 정의하는 모듈입니다."""
from flask import request, Response, stream_with_context
from flask_restx import Resource, Namespace, fields
from app.utils.auth_middleware import require_auth
from app.utils.app_config import is_dev_mode
from app.langgraph.general_agent import general_agent
import uuid
import json
import asyncio
from datetime import datetime, timezone
from langchain_core.messages import ToolMessage

# Create namespace
ns = Namespace('ga', description='General Agent API')

def extract_tools_used(messages):
    """메시지에서 사용된 도구 정보를 추출합니다."""
    tools_used = []
    for message in messages:
        if isinstance(message, ToolMessage):
            tool_info = {
                'name': getattr(message, 'name', 'unknown'),
                'tool_call_id': getattr(message, 'tool_call_id', 'unknown'),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            tools_used.append(tool_info)
        elif hasattr(message, 'tool_calls') and message.tool_calls:
            # AI 메시지에서 도구 호출 정보 추출
            for tool_call in message.tool_calls:
                # LangChain의 tool_calls 구조에 맞게 수정
                tool_info = {
                    'name': getattr(tool_call, 'name', 'unknown'),
                    'tool_call_id': getattr(tool_call, 'id', 'unknown'),
                    'arguments': getattr(tool_call, 'args', {}),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                tools_used.append(tool_info)
    return tools_used

# Define models for documentation
general_agent_input = ns.model('GeneralAgentInput', {
    'content': fields.String(required=True,
                            description='사용자 메시지 내용',
                            example='서울 날씨 어때?'),
    'conversation_history': fields.List(fields.Raw, required=False,
                                       description='대화 기록',
                                       example=[{'role': 'user', 'content': '안녕하세요'}, {'role': 'assistant', 'content': '안녕하세요! 무엇을 도와드릴까요?'}])
})

general_agent_response = ns.model('GeneralAgentResponse', {
    'type': fields.String(description='응답 타입',
                         enum=['chunk', 'toolmessage', 'error'],
                         example='chunk'),
    'content': fields.String(description='응답 내용',
                            example='서울의 현재 날씨는 맑습니다.'),
    'metadata': fields.Raw(description='메타데이터',
                          example={
                              'timestamp': '2025-01-23T09:10:39.366Z',
                              'role': 'assistant',
                              'tools_used': [
                                  {
                                      'name': 'maps_search_places',
                                      'tool_call_id': 'call_zXScHgJTxjRgMS7qw3FLodVL',
                                      'arguments': {
                                          'query': '일하기 좋은 커피숍',
                                          'location': {'latitude': 37.339045, 'longitude': 127.108593},
                                          'radius': 2000
                                      },
                                      'timestamp': '2025-01-23T09:10:39.366Z'
                                  }
                              ]
                          })
})

@ns.route('/chat')
class GeneralAgentChat(Resource):
    @ns.doc('General Agent 채팅',
            description='General Agent와 대화를 나눕니다. MCP 도구를 사용할 수 있습니다.',
            security='Bearer' if not is_dev_mode() else None,
            params={
                'Authorization': {
                    'description': 'Bearer <jwt>',
                    'in': 'header',
                    'required': not is_dev_mode()
                },
                'Accept': {
                    'description': 'text/event-stream',
                    'in': 'header',
                    'required': True
                },
                'user-id': {'description': '<사용자 UUID>', 'in': 'header', 'required': True}
            })
    @ns.expect(general_agent_input)
    @ns.response(200, '응답 성공', [general_agent_response])
    @ns.response(400, '잘못된 요청')
    @ns.response(401, '인증 실패')
    @ns.response(500, '서버 오류')
    @require_auth
    def post(self):
        """General Agent와 대화를 나눕니다."""
        try:
            user_id = request.headers.get('user-id')
            if not user_id:
                ns.abort(400, "User ID is required")

            data = request.get_json()
            if not data or 'content' not in data:
                ns.abort(400, "Message content is required")

            user_message = data['content']
            conversation_history = data.get('conversation_history', [])

            def generate():
                try:
                    # 사용자 메시지 먼저 전송
                    yield f"data: {json.dumps({'type': 'user', 'content': user_message, 'metadata': {'timestamp': datetime.now(timezone.utc).isoformat()}}, ensure_ascii=False)}\n\n"
                    
                    # General Agent 실행
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    try:
                        # general_agent 함수 호출 (대화 기록과 함께)
                        response = loop.run_until_complete(general_agent(
                            user_message, 
                            conversation_history,
                            user_id=request.headers.get('user-id', 'anonymous')
                        ))
                        
                        # 응답 처리
                        if response and 'messages' in response:
                            # 도구 사용 정보 추출
                            tools_used = extract_tools_used(response['messages'])
                            
                            # 도구 사용 정보를 별도 이벤트로 전송
                            if tools_used:
                                for tool_info in tools_used:
                                    tool_data = {
                                        'type': 'toolmessage',
                                        'content': f"도구 '{tool_info['name']}' 사용 중...",
                                        'metadata': {
                                            'timestamp': tool_info['timestamp'],
                                            'tool_name': tool_info['name'],
                                            'tool_call_id': tool_info['tool_call_id'],
                                            'arguments': tool_info.get('arguments', {})
                                        }
                                    }
                                    yield f"data: {json.dumps(tool_data, ensure_ascii=False)}\n\n"
                            
                            for message in response['messages']:
                                if hasattr(message, 'content') and message.content:
                                    chunk_data = {
                                        'type': 'chunk',
                                        'content': message.content,
                                        'metadata': {
                                            'timestamp': datetime.now(timezone.utc).isoformat(),
                                            'role': getattr(message, 'type', 'assistant'),
                                            'tools_used': tools_used
                                        }
                                    }
                                    yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                        else:
                            # 응답이 없는 경우 기본 메시지
                            chunk_data = {
                                'type': 'chunk',
                                'content': '죄송합니다. 응답을 생성할 수 없습니다.',
                                'metadata': {
                                    'timestamp': datetime.now(timezone.utc).isoformat(),
                                    'role': 'assistant',
                                    'tools_used': []
                                }
                            }
                            yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                            
                    finally:
                        loop.close()
                        
                except Exception as e:
                    error_data = {
                        'type': 'error',
                        'error': str(e),
                        'metadata': {
                            'timestamp': datetime.now(timezone.utc).isoformat()
                        }
                    }
                    yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

            return Response(
                stream_with_context(generate()),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'X-Accel-Buffering': 'no'
                }
            )

        except ValueError as e:
            ns.abort(400, str(e))
        except Exception as e:
            ns.abort(500, str(e))


@ns.route('/chat/sync')
class GeneralAgentChatSync(Resource):
    @ns.doc('General Agent 채팅 (동기)',
            description='General Agent와 대화를 나눕니다. 동기 방식으로 응답을 받습니다.',
            security='Bearer' if not is_dev_mode() else None,
            params={
                'Authorization': {
                    'description': 'Bearer <jwt>',
                    'in': 'header',
                    'required': not is_dev_mode()
                },
                'user-id': {'description': '<사용자 UUID>', 'in': 'header', 'required': True}
            })
    @ns.expect(general_agent_input)
    @ns.response(200, '응답 성공', general_agent_response)
    @ns.response(400, '잘못된 요청')
    @ns.response(401, '인증 실패')
    @ns.response(500, '서버 오류')
    @require_auth
    def post(self):
        """General Agent와 대화를 나눕니다. (동기 방식)"""
        try:
            user_id = request.headers.get('user-id')
            if not user_id:
                ns.abort(400, "User ID is required")

            data = request.get_json()
            if not data or 'content' not in data:
                ns.abort(400, "Message content is required")

            user_message = data['content']
            conversation_history = data.get('conversation_history', [])

            # General Agent 실행
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                response = loop.run_until_complete(general_agent(
                    user_message, 
                    conversation_history,
                    user_id=request.headers.get('user-id', 'anonymous')
                ))
                
                # 응답 처리
                if response and 'messages' in response:
                    # 도구 사용 정보 추출
                    tools_used = extract_tools_used(response['messages'])
                    
                    # 마지막 메시지의 내용을 반환
                    last_message = response['messages'][-1] if response['messages'] else None
                    if last_message and hasattr(last_message, 'content'):
                        return {
                            'type': 'chunk',
                            'content': last_message.content,
                            'metadata': {
                                'timestamp': datetime.now(timezone.utc).isoformat(),
                                'role': getattr(last_message, 'type', 'assistant'),
                                'tools_used': tools_used
                            }
                        }, 200
                
                # 응답이 없는 경우
                return {
                    'type': 'chunk',
                    'content': '죄송합니다. 응답을 생성할 수 없습니다.',
                    'metadata': {
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'role': 'assistant',
                        'tools_used': []
                    }
                }, 200
                
            finally:
                loop.close()

        except ValueError as e:
            ns.abort(400, str(e))
        except Exception as e:
            ns.abort(500, str(e)) 