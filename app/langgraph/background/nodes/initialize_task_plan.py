from app.langgraph.background.bg_state import BGState, PlanStep
from collections import defaultdict, deque
from app.langgraph.background.planners.plan_generator import generate_plan_steps
from app.langgraph.background.planners.tool_registry import get_available_tools

def initialize_task_plan(state: BGState) -> BGState:
    """
    현재 Task에 대해 실행 계획(plan)을 초기화한다.
    - generate_plan_steps()를 통해 PlanStep 리스트 생성
    - ready_queue 및 plan, completed_ids 구성
    """
    task = state.get("task")
    if not task or task.get("plan"):
        return state  # 이미 초기화되었거나 task 없음

    title = task["title"]
    description = task["description"]
    tools = get_available_tools()

    plan_steps = generate_plan_steps(title, description, tools)

    plan = {}

    for step in plan_steps:
        step_id = step["step_id"]

        if step_id in plan:
            raise ValueError(f"❌ 중복된 step_id: {step_id}")

        tool = step["tool"]
        objective = step["objective"]
        depends_on = step.get("depends_on", [])

        plan[step_id] = PlanStep(
            step_id=step_id,
            tool=tool,
            tool_input=None,
            objective=objective,
            depends_on=depends_on,
            output=None,
            status="pending",
            attempt=0,
            max_attempt=2
        )

    # ready_queue는 별도 런타임에서 depends_on 만족 시 계산
    task["plan"] = plan

    # --- 위상 정렬 (Kahn's Algorithm)
    indegree = defaultdict(int)
    graph = defaultdict(list)

    # 그래프 구성
    for step in plan.values():
        for dep in step["depends_on"]:
            graph[dep].append(step["step_id"])
            indegree[step["step_id"]] += 1

    # 진입차수 0인 노드부터 시작
    queue = deque([step_id for step_id in plan if indegree[step_id] == 0])
    sorted_steps = []

    while queue:
        current = queue.popleft()
        sorted_steps.append(current)
        for neighbor in graph[current]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)

    if len(sorted_steps) != len(plan):
        raise ValueError("❌ 순환 의존성이 존재합니다. PlanStep들을 확인하세요.")

    # 결과 적용
    task["ready_queue"] = sorted_steps  # ✅ 의존 순서 기반 전체 실행 순서
    state["task"] = task
    
    return state