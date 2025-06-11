from app.langgraph.background.executor import create_background_executor
from app.services.auto_task_service import AutoTaskService
from app.utils.openai_client import get_completion
import json
from typing import Dict, Any
from datetime import datetime, date
import uuid

GENERATE_AUTO_TASKS_OUTPUT = """
당신은 여러 자동화 업무의 결과를 하나의 완성도 높은 문서로 정리하는 작가입니다.
아래 단계별 업무 정보를 참고하여 다음 조건을 모두 충족하는 마크다운(Markdown) 문서를 작성해 주세요:

1. 전체 내용을 종합하여 하나의 통합 문서로 구성하세요.
2. 각 업무 단계의 `title`, `description`, `output`을 논리적으로 연결하고, 자연스럽게 이어지는 구성으로 작성하세요.
3. 문서의 구조는 아래 기준에 따라 자유롭게 설계하되, 정보가 깔끔하게 정돈되도록 하세요:
   - 제목, 목차, 소제목은 단계별 정보를 통합하여 알맞는 내용으로 작성하세요.
   - 문서 맨 위에는 **문서 제목(#)**을 설정하세요.
   - 그 다음에 **목차(##)**를 작성하세요.
   - 중심 내용은 **소제목(##)** 으로 구분하고, 필요한 경우 하위 항목(-)이나 표 등을 적절히 사용하세요.
4. 단순 요약이 아닌, **업무 단계 간 연관성과 흐름이 느껴지는** 문단을 작성하세요.
5. 마크다운 문법(`#`, `##`, `-`, `|`, `:--`)을 적극적으로 활용하여 **읽기 쉽고 시각적으로 구조화된 문서**를 만들어 주세요.
6. **절대 코드블록(```)을 사용하지 말고**, 순수 마크다운 텍스트 형식으로만 작성하세요.
7. 표현은 문서 스타일에 맞게 자연스럽고 정돈된 문체를 사용하세요.

[입력 예시: 단계별 정보(JSON)]
{task_outputs}
"""


class BackgroundService:
    def __init__(self):
        self._background_executor = None
        self.auto_task_service = AutoTaskService()

    def _serialize_background(self, obj):
        # 기존 로직 그대로, self는 안 쓰더라도 필수!
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, dict):
            return {k: self._serialize_background(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._serialize_background(v) for v in obj]
        return obj

    @property
    def background_executor(self):
        if self._background_executor is None:
            self._background_executor = create_background_executor()
        return self._background_executor

    def background_auto_task(self, user_id: str) -> Dict[str, Any]:
        try:
            result = self.background_executor(user_id = user_id)
            return self._serialize_background(result)
        
        except Exception as e:
            print(f"Error during background: {str(e)}")
            return {"error": str(e)}

    def generate_auto_tasks_output(self, user_id: str) -> Dict[str, Any]:
        """
        해당 user의 한 그룹의 auto_task output을 모아 하나의 문서(문자열)로 반환
        (최신순 정렬, done 상태, 메인→서브 순서대로)
        """
        auto_tasks = self.auto_task_service.get_user_auto_tasks(user_id)
        outputs_list = []

        # 1. 첫 번째 메인 task (done, task_list==[])
        main_task = next((t for t in auto_tasks if t["status"] == "done" and not (t.get("task_list"))), None)
        if not main_task:
            return "(완료된 메인 AutoTask가 없습니다)"
        current_task = main_task
        while current_task:
            # 2. output, title, description 저장
            outputs_list.append({
                "title": current_task["title"],
                "description": current_task.get("description", ""),
                "output": current_task.get("output", "")
            })
            # 3. 다음 task: 현재 task의 title이 task_list에 있으면서 done인 항목
            next_task = next(
                (t for t in auto_tasks if t["status"] == "done" and t.get("task_list") and t["task_list"][0] == current_task["title"]),
                None
            )
            if next_task:
                current_task = next_task
            else:
                break

        outputs_list_json = json.dumps(outputs_list, ensure_ascii=False, indent=2)

        prompt = GENERATE_AUTO_TASKS_OUTPUT.format(task_outputs=outputs_list_json)
        messages = [
            {"role": "system", "content": "아래 프롬프트에 따라 마크다운 업무 리포트를 생성해줘."},
            {"role": "user", "content": prompt}
        ]
        error_response = "# 자동화 업무 요약 리포트\n(데이터 없음)"

        try:
            generate_output = get_completion(messages)
            if not generate_output:
                generate_output = error_response
        except Exception as e:
            generate_output = error_response

        # 첫 번째 메인 task의 output 컬럼에 업데이트
        if main_task:
            try:
                return self.auto_task_service.update(main_task["id"], output=generate_output)
            except Exception as e:
                print(f"[ERROR] 메인 task output 업데이트 실패: {e}")