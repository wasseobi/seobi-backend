from config import Config
import redis
import pickle

_redis = redis.Redis(host=Config.REDIS_URL, port=Config.REDIS_PORT,
                     db=0, password=Config.REDIS_KEY, ssl=True)


class AgentStateStore:
    @staticmethod
    def set(user_id: str, state: dict):
        _redis.set(f"agent_state:{user_id}", pickle.dumps(state))

    @staticmethod
    def get(user_id: str) -> dict:
        data = _redis.get(f"agent_state:{user_id}")
        if data:
            return pickle.loads(data)
        else:
            return {
                "messages": [],
                "summary": "",
                "user_id": user_id,
                "current_input": "",
                "scratchpad": [],
                "step_count": 0,
                "next_step": "agent"
            }

    @staticmethod
    def delete(user_id: str):
        _redis.delete(f"agent_state:{user_id}")
