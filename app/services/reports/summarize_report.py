from app.utils.openai_client import get_openai_client, get_completion
from app.services.schedule_service import ScheduleService

class SummarizeReport:
    def __init__(self):
        self.schedule_service = ScheduleService()

    def _call_llm(self, messages: list, header: str = None, count: int = None) -> str:
        """LLM 호출 공통 로직"""
        try:
            client = get_openai_client()
            response = get_completion(client, messages)
            
            if not response:
                if header:
                    return f"## {header} (총 {count}건)"
                return "(데이터 없음)"
                
            # 응답이 헤더만 있는 경우
            if header and count and response.strip() == f"## {header} (총 {count}건)":
                print(f"[WARNING] LLM이 헤더만 반환함 (header={header}, count={count})")
                return f"## {header} (총 {count}건)"
                
            return response

        except Exception as e:
            print(f"[ERROR] LLM 호출 실패:", e)
            if header:
                return f"## {header} (총 {count}건)"
            return "(오류 발생)"

    def _create_messages(self, system_content: str, prompt: str, data_json: str = None) -> list:
        """메시지 생성 공통 로직"""
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": prompt}
        ]
        
        if data_json:
            messages[1]["content"] += f"\n[DATA] {data_json}"
            
        return messages