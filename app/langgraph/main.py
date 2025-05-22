"""AI 어시스턴트 메인 실행 파일입니다."""
from dotenv import load_dotenv
load_dotenv()

from datetime import datetime
import uuid
from langchain.schema import HumanMessage, AIMessage

from src import graph
from src.state import ChatState
from src.tools import tools

def create_initial_state(user_input: str) -> dict:
    """사용자 입력으로 초기 상태를 생성합니다."""
    # 상태를 딕셔너리로 생성
    return {
        "user_input": user_input,
        "parsed_intent": {},
        "reply": "",
        "action_required": False,
        "executed_result": {},
        "timestamp": datetime.now().isoformat(),
        "user_id": str(uuid.uuid4()),
        "tool_info": None,
        "messages": [
            HumanMessage(content=user_input)
        ]
    }

def print_available_tools():
    """사용 가능한 도구들을 출력합니다."""
    print("\n=== 사용 가능한 도구들 ===")
    for tool in tools:
        print(f"\n🔧 {tool.name}")
        print(f"   설명: {tool.description}")
        print(f"   예시: {get_tool_example(tool.name)}")

def get_tool_example(tool_name: str) -> str:
    """도구별 사용 예시를 반환합니다."""
    examples = {
        "current_time": "지금 몇 시야?",
        "google_search": "파이썬 LangGraph에 대해 검색해줘",
        "schedule_meeting": "내일 오후 3시에 팀 미팅 잡아줘"
    }
    return examples.get(tool_name, "예시 없음")

# 설정 초기화
config = {
    "configurable": {
        "thread_id": "1",
        "model": "google_genai:gemini-pro",
        "temperature": 0.7,
        "max_tokens": 1024
    }
}

if __name__ == "__main__":
    print("🤖 AI 어시스턴트를 시작합니다. ('exit' 또는 'quit'으로 종료)")
    print_available_tools()
    print("\n명령어:")
    print("- help: 도움말 표시")
    print("- exit/quit: 프로그램 종료")
    print()
    
    # 대화 세션 시작
    while True:
        user_input = input("\n🤔 ")

        # 종료 명령 확인
        if user_input.lower() in ["exit", "quit"]:
            print("프로그램을 종료합니다. 👋")
            break
        
        # 도움말 표시
        if user_input.lower() == "help":
            print_available_tools()
            continue
        
        # 빈 입력 무시
        if not user_input.strip():
            continue

        try:
            # 초기 상태 생성
            initial_state = create_initial_state(user_input)
            
            # 그래프 실행
            result = graph.invoke(initial_state, config)
            
            # 오류 발생 시 확인
            if result.get("executed_result", {}).get("error"):
                error = result["executed_result"]["error"]
                print(f"⚠️ 도구 실행 중 오류 발생: {error.get('message', '알 수 없는 오류')}")
            
        except Exception as e:
            print(f"⚠️ 오류가 발생했습니다: {str(e)}")
            print("다시 시도해주세요.")
        
        print()
