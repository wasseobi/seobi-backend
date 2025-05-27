"""Background task queue management."""
from typing import Dict, Any, List
from flask import current_app
from redis import Redis
from rq import Queue, Job
from rq.job import JobStatus

from .graph import build_background_graph


class BackgroundQueue:
    """Manages background processing tasks for conversations."""
    
    def __init__(self):
        """Initialize the background queue with Redis connection."""
        self.redis_conn = Redis.from_url(current_app.config['REDIS_URL'])
        self.queue = Queue('background', connection=self.redis_conn)
        self.graph = build_background_graph()
        
    def enqueue_conversation(self, conversation_id: str, messages: List[Dict[str, Any]]) -> str:
        """Enqueue a conversation for background processing.
        
        Args:
            conversation_id: ID of the conversation to process
            messages: List of messages in the conversation
            
        Returns:
            str: Job ID for tracking the processing status
        """
        # Create initial state
        initial_state = {
            "conversation_id": conversation_id,
            "messages": messages
        }
        
        # Enqueue the job
        job = self.queue.enqueue(
            self.graph.ainvoke,
            initial_state,
            job_timeout='1h',  # Set reasonable timeout
            result_ttl=86400,  # Keep results for 24 hours
            failure_ttl=86400  # Keep failed jobs for 24 hours
        )
        
        return job.id
        
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get the status of a background processing job.
        
        Args:
            job_id: ID of the job to check
            
        Returns:
            Dict containing:
                - status: Current job status
                - result: Job result if completed
                - error: Error message if failed
                - progress: Processing progress if available
        """
        try:
            job = Job.fetch(job_id, connection=self.redis_conn)
            
            status_info = {
                "status": job.get_status(),
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "ended_at": job.ended_at.isoformat() if job.ended_at else None
            }
            
            if job.is_finished:
                status_info["result"] = job.result
            elif job.is_failed:
                status_info["error"] = str(job.exc_info)
                
            return status_info
            
        except Exception as e:
            current_app.logger.error(f"Error getting job status: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
            
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running background processing job.
        
        Args:
            job_id: ID of the job to cancel
            
        Returns:
            bool: True if job was cancelled, False otherwise
        """
        try:
            job = Job.fetch(job_id, connection=self.redis_conn)
            if job.get_status() in [JobStatus.STARTED, JobStatus.QUEUED]:
                job.cancel()
                return True
            return False
        except Exception as e:
            current_app.logger.error(f"Error cancelling job: {str(e)}")
            return False 