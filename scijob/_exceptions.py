from httpx import Response

__all__ = [
    "HttpRequestError",
    "GetJobResultError",
    "JobCancelledError",
    "JobStateFailedError",
    "JobStateMissingError",
    "JobStateStoppedError",
]


class HttpRequestError(Exception):
    def __init__(self, response: Response):
        self.code = response.status_code
        self.url = response.url
        self.request_id = response.headers.get("X-Request-ID", "")
        
        payload = response.json()
        self.msg = ""
        if isinstance(payload, dict):
            self.msg = payload.get("error", "").rstrip(".")
        
    def __str__(self):
        return f"'{self.code} {self.msg}' for URL '{self.url}' on request '{self.request_id}'"
    
    
class _BaseJobException(Exception):
    def __init__(self, job_id: str):
        self.job_id = job_id
        
    
class JobCancelledError(_BaseJobException):
    def __str__(self):
        return f"Job '{self.job_id}' cancelled by client"
    
    
class GetJobResultError(_BaseJobException):        
    def __str__(self):
        return f"Failed to get result of job '{self.job_id}' from backend"
    
        
class JobStateMissingError(_BaseJobException):        
    def __str__(self):
        return f"Lost track of job '{self.job_id}' state at backend"
    
    
class JobStateFailedError(_BaseJobException):
    def __str__(self):
        return f"Job '{self.job_id}' failed at backend"
    

class JobStateStoppedError(_BaseJobException):
    def __str__(self):
        return f"Job '{self.job_id}' stopped at backend"
