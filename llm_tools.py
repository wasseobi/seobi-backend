import os
import logging
from dotenv import load_dotenv
from openai import AzureOpenAI
from langchain_core.tools import tool
from typing import List, Dict
from langgraph.prebuilt import ToolNode

load_dotenv(override=True)



# --- 로깅 설정 ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Azure OpenAI 설정 (환경변수 사용) ---
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-01")

# 모델 이름을 직접 지정 (예: o4-mini)
AZURE_MODEL_NAME = "o4-mini"

if not AZURE_OPENAI_ENDPOINT or not AZURE_OPENAI_API_KEY:
    logger.warning("환경변수(AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY)가 올바르게 설정되지 않았습니다.")

# AzureOpenAI 클라이언트 초기화
client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)

@tool
def ask_azure_openai(prompt: str) -> str:
    """
    주어진 프롬프트에 대해 Azure OpenAI 모델의 응답을 반환합니다.
    이 함수는 LangGraph에서 도구(tool)로 사용될 수 있습니다.
    """
    try:
        response = client.chat.completions.create(
            model=AZURE_MODEL_NAME,  # Azure에 배포한 모델의 이름을 직접 지정
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Azure OpenAI API 호출 중 오류 발생: {e}")
        return f"오류: LLM 응답을 가져오는 중 문제가 발생했습니다. 상세 정보: {str(e)}"

@tool
def add_numbers(a: int, b: int) -> int:
    """두 숫자를 더합니다."""
    return a + b

# --- LangGraph에서 사용할 도구 목록 (예시) ---
# ToolExecutor 및 관련 코드는 최신 langgraph 버전에서는 지원하지 않으므로 모두 주석 처리합니다.
# try:
#     from langgraph.prebuilt import ToolExecutor
# except ImportError:
#     # 대체 경로 시도
#     from langgraph.prebuilt.tool_executor import ToolExecutor

# LangGraph 에이전트나 그래프에 제공할 도구 목록
# available_tools = [ask_azure_openai]

# ToolExecutor를 사용하면 여러 도구를 편리하게 관리하고 실행할 수 있습니다.
# tool_executor = ToolExecutor(available_tools)

# --- LangGraph 노드에서 직접 LLM을 호출해야 할 경우를 위한 함수 ---
def direct_llm_call_for_graph(messages: List[Dict]) -> str:
    """
    LangGraph 노드 내에서 직접 Azure OpenAI를 호출하기 위한 함수입니다.
    messages 형식: [{"role": "user", "content": "안녕하세요"}, {"role": "assistant", "content": "반갑습니다!"}]
    """
    try:
        response = client.chat.completions.create(
            model=AZURE_MODEL_NAME,
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Azure OpenAI API 직접 호출 중 오류 발생: {e}")
        return f"오류: LLM 응답을 가져오는 중 문제가 발생했습니다. 상세 정보: {str(e)}"

if __name__ == '__main__':
    # 테스트를 위한 간단한 호출 예시
    # 환경변수에 값이 올바르게 들어가 있어야 테스트가 동작합니다.
    test_prompt = "Azure prompt test. dongtestdongtestdongtestdongtest."
    print(f"테스트 프롬프트: {test_prompt}")
    response = ask_azure_openai(test_prompt)
    print(f"LLM 응답: {response}")

    # add_numbers 툴 테스트
    add_result = add_numbers.invoke({"a": 3, "b": 5})
    print(f"[TOOL 사용] add_numbers(3, 5) 결과: {add_result}")

    # 사용자 입력으로 쿼리 테스트
    print("\n직접 프롬프트를 입력해 Azure OpenAI에 쿼리해보세요. (엔터만 입력하면 종료)")
    while True:
        user_prompt = input("프롬프트 입력: ")
        if not user_prompt.strip():
            print("종료합니다.")
            break
        # 계산기 툴 사용 예시: '계산: 1+2' 입력 시 툴 사용
        if user_prompt.strip().startswith("계산:"):
            try:
                expr = user_prompt.strip().replace("계산:", "").replace(" ", "")
                if "+" in expr:
                    a, b = map(int, expr.split("+"))
                    tool_result = add_numbers.invoke({"a": a, "b": b})
                    print(f"[TOOL 사용] {a} + {b} = {tool_result}\n")
                    continue
                else:
                    print("지원하는 연산은 + 뿐입니다. 예: 계산: 1+2\n")
                    continue
            except Exception as e:
                print(f"입력 파싱 오류: {e}\n")
                continue
        response = ask_azure_openai(user_prompt)
        print(f"LLM 응답: {response}\n")

print("AZURE_OPENAI_ENDPOINT:", AZURE_OPENAI_ENDPOINT)
print("AZURE_OPENAI_API_KEY:", AZURE_OPENAI_API_KEY)
print("AZURE_OPENAI_API_VERSION:", AZURE_OPENAI_API_VERSION)

# 툴 리스트
tools = [ask_azure_openai, add_numbers]

# 툴 노드 생성
add_node = ToolNode(add_numbers)
llm_node = ToolNode(ask_azure_openai)

# 그래프에 노드 추가 및 연결 (예시, 실제 그래프 객체 필요)
# graph.add_node("add", add_node)
# graph.add_node("llm", llm_node)
# graph.add_edge("llm", "add")  # LLM이 add 툴을 호출할 수 있도록 연결