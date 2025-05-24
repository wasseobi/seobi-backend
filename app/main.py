import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage

from app.langgraph.executor import create_agent_executor

def main():
    # .env 파일에서 환경 변수 로드
    load_dotenv()
    
    # Agent 생성
    agent = create_agent_executor()
    
    # 대화 시작
    chat_history = []
    
    print("AI 어시스턴트와 대화를 시작합니다. 종료하려면 'exit'를 입력하세요.")
    
    while True:
        # 사용자 입력 받기
        user_input = input("\n사용자: ")
        if user_input.lower() == 'exit':
            break
            
        try:
            # Agent 실행
            result = agent(user_input, chat_history)
            
            # 대화 기록 업데이트
            if isinstance(result, dict) and "messages" in result:
                chat_history = result["messages"]
                
                # 마지막 AI 메시지 찾기
                ai_messages = [msg for msg in chat_history[::-1] 
                            if getattr(msg, "__class__", None).__name__ == "AIMessage"]
                
                if ai_messages:
                    print(f"\nAI: {ai_messages[0].content}")
                else:
                    print("\nAI: 죄송합니다. 응답을 생성하는 데 문제가 발생했습니다.")
            else:
                print("\nAI: 죄송합니다. 처리 중 오류가 발생했습니다.")
            
        except Exception as e:
            print(f"\n오류가 발생했습니다: {str(e)}")
            print("시스템을 재시작합니다...")
            chat_history = []

if __name__ == "__main__":
    main()
