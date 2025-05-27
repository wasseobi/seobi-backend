"""Background task queue management."""
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID
from flask import current_app
from redis import Redis
from rq import Queue, Job
from rq.job import JobStatus

from .graph import build_background_graph, process_session
from .state import BackgroundState


class BackgroundQueue:
    """Manages background processing tasks for conversations."""
    
    def __init__(self):
        """Initialize the background queue with Redis connection."""
        self.redis_conn = Redis.from_url(current_app.config['REDIS_URL'])
        self.queue = Queue('background', connection=self.redis_conn)
        
    def enqueue_session_processing(self, session_id: UUID) -> str:
        """Enqueue a session for background processing.
        
        Args:
            session_id: UUID of the session to process
            
        Returns:
            str: Job ID for tracking the processing status
        """
        # Build graph first to validate configuration
        graph = build_background_graph()
        
        # Enqueue the job
        job = self.queue.enqueue(
            process_session,
            session_id,
            job_timeout='1h',  # Set reasonable timeout
            result_ttl=86400,  # Keep results for 24 hours
            failure_ttl=86400,  # Keep failed jobs for 24 hours
            meta={
                "graph_config": {
                    "nodes": list(graph.nodes),
                    "edges": [(str(e[0]), str(e[1])) for e in graph.edges]
                }
            }
        )
        
        return job.id
        
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get the status of a background processing job.
        
        Args:
            job_id: ID of the job to check
            
        Returns:
            Dict containing:
                - status: Current job status
                - state: Current processing state if available
                - error: Error message if failed
                - metadata: Job metadata including graph configuration
        """
        try:
            job = Job.fetch(job_id, connection=self.redis_conn)
            
            status_info = {
                "status": job.get_status(),
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "ended_at": job.ended_at.isoformat() if job.ended_at else None,
                "metadata": {
                    "job_id": job.id,
                    "queue": job.origin,
                    "timeout": str(job.timeout),
                    "result_ttl": str(job.result_ttl),
                    "failure_ttl": str(job.failure_ttl),
                    "graph_config": job.meta.get("graph_config", {})
                }
            }
            
            if job.is_finished:
                # Get the final state
                final_state: BackgroundState = job.result
                status_info["state"] = {
                    "conversation_id": final_state["conversation_id"],
                    "next_step": final_state["next_step"],
                    "error": final_state["error"],
                    "final_result": final_state["final_result"]
                }
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
            
    def process_job_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Process and store the final job result.
        
        This method should be called after a job is completed to store
        the results in the database or other persistent storage.
        
        Args:
            job_id: ID of the completed job
            
        Returns:
            Optional[Dict]: Stored result data if successful, None if failed
        """
        try:
            status = self.get_job_status(job_id)
            if status["status"] != "finished" or "state" not in status:
                return None
                
            state: BackgroundState = status["state"]
            if not state.get("final_result"):
                return None
                
            # TODO: Implement database storage
            # This is where you would store the results in your database
            # For now, just return the final result
            return state["final_result"]
            
        except Exception as e:
            current_app.logger.error(f"Error processing job result: {str(e)}")
            return None 