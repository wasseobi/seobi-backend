from typing import TypedDict, List, Optional, Any, Literal, Dict
from datetime import datetime
import uuid

class PlanStep(TypedDict, total=False):
    step_id: str                       # "search_google"
    tool: str                          # "google_search"
    tool_input: Optional[Dict[str, Any]]   # 도구 실행에 사용된 입력값
    objective: Optional[str]
    depends_on: List[str]              # 선행 Step id (없으면 즉시 실행 가능)
    output: Optional[Dict[str, Any]]   # 메모리 결과
    status: Literal["pending", "running", "done", "failed"]
    attempt: int                             # 현재까지 시도 횟수 (기본값 0)
    max_attempt: int                         # 최대 허용 재시도 횟수 (기본값 2)

class TaskRuntime(TypedDict, total=False):
    task_id: uuid.UUID                     # AutoTask PK
    title: str
    description: str
    task_list: Optional[str]          # None ⇒ 메인 Task, # NOTE: task_list는 하나만 존재하는 걸로 이야기 함(기덕-주형)
    plan: Dict[str, PlanStep]         # id ➜ PlanStep
    ready_queue: List[str]            # 실행 가능한 Step id 들
    completed_ids: List[str]          # 이미 끝난 Step id (Set 불가 in TypedDict)
    task_result: Optional[Dict[str, Any]]
    start_at: Optional[datetime]
    finish_at: Optional[datetime]

class BGState(TypedDict):
    user_id: uuid.UUID                     # user_id
    task: Optional[TaskRuntime]
    last_completed_title: Optional[str]
    error: Optional[str]
    finished: bool
    step: Optional[PlanStep]