from config import Config
import redis
import pickle

_redis = redis.Redis.from_url(Config.AGENT_STATE_REDIS_URL)

class AgentStateStore:
    @staticmethod
    def set(user_id: str, state: dict):
        _redis.set(f"agent_state:{user_id}", pickle.dumps(state))

    @staticmethod
    def get(user_id: str) -> dict:
        data = _redis.get(f"agent_state:{user_id}")
        if data:
            return pickle.loads(data)
        return None

    @staticmethod
    def delete(user_id: str):
        _redis.delete(f"agent_state:{user_id}")
