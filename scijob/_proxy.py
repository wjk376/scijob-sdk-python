import asyncio
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from http import HTTPStatus
import json
import threading
import time
from typing import Any, Mapping, Optional

import httpx

from ._config import *
from ._exceptions import *
from ._logger import logger
from ._models import *
from ._types import NULL, BackendTypes, Numeric

__all__ = ["AsyncJobProxy", "JobProxy"]


class _State(Enum):
    PENDING = "Pending"
    FINISHED = "Finished"
    CANCELLED = "Cancelled"
    
    
class _BaseJobProxy:
    def __init__(
        self, 
        *,
        asynchronous: bool,
        id: str, 
        backend: BackendTypes,
        api_base_url: str,
        headers: Mapping[str, str],
        poll_interval: Numeric = DEFAULT_POLL_INTERVAL,
        null_state_tolerance: Numeric,
        verbose: bool = True,
        ignore_result: bool = False,
    ):
        self._async = asynchronous
        self._id = id
        self._backend = backend
        self._poll_interval = poll_interval
        self._null_state_tolerance = null_state_tolerance
        self._verbose = verbose
        self._result = NULL
        self._ignore_result = ignore_result
        
        if self._async:
            self._cli = httpx.AsyncClient(base_url=api_base_url, headers=headers)
        else:
            self._cli = httpx.Client(base_url=api_base_url, headers=headers)
            
            # NOTE: Cannot use context manager here as it calls `shutdown(wait=True)`
            # when exiting the scope
            self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix=f"poll-job-{self.id}")
        
    def __str__(self):
        return f"job '{self.id}'"
    
    @property
    def id(self):
        return self._id
    
    @property
    def backend(self) -> BackendTypes:
        return self._backend
        
    def _post(self, url: str, json: Any):
        assert isinstance(self._cli, httpx.Client), "Cannot use async client in sync method"
        resp = self._cli.post(url, json=json)
        if not resp.is_success:
            raise HttpRequestError(resp)
        return resp
        
    async def _apost(self, url: str, json: Any):
        assert isinstance(self._cli, httpx.AsyncClient), "Cannot use sync client in async method"
        resp = await self._cli.post(url, json=json)
        if not resp.is_success:
            raise HttpRequestError(resp)
        return resp
    
    def _parse_job_info_response(self, response: httpx.Response):
        payload = response.json()
        if not isinstance(payload, dict):
            raise TypeError("Response payload is not a dictionary")
        
        backend = payload.get("backend")
        if backend != self.backend:
            raise RuntimeError(f"Job backend mismatch: '{backend}' and '{self.backend}'")
        
        if backend == "volcengine_ml_platform":
            payload = GetVolcJobInfoResponse.model_validate(payload, strict=True)
            return payload.info
        else:
            raise RuntimeError(f"Invalid job backend '{backend}'")
        

class JobProxy(_BaseJobProxy):
    def __init__(
        self, 
        *,
        id: str, 
        backend: BackendTypes,
        api_base_url: str,
        headers: Mapping[str, str],
        poll_interval: Numeric = DEFAULT_POLL_INTERVAL,
        null_state_tolerance: Numeric = 30,
        verbose: bool = True,
        ignore_result: bool = False,
    ):
        super().__init__(
            asynchronous=False,
            id=id,
            backend=backend,
            api_base_url=api_base_url,
            headers=headers,
            poll_interval=poll_interval,
            null_state_tolerance=null_state_tolerance,
            verbose=verbose,
            ignore_result=ignore_result,
        )
        self._state = _State.PENDING
        self._lock = threading.RLock()
        
        # This background task will start immediately, and a running future CANNOT 
        # be cancelled by calling `Future.cancel()`
        self._bg_task = self._executor.submit(self._background_monitor_job)
        
    def __del__(self):
        self._cli.close()
        self._executor.shutdown(wait=False, cancel_futures=True)
    
    @property
    def pending(self):
        with self._lock:
            return self._state == _State.PENDING
    
    @property
    def finished(self):
        with self._lock:
            return self._state == _State.FINISHED
    
    @property
    def cancelled(self):
        with self._lock:
            return self._state == _State.CANCELLED
    
    def cancel(self):
        if not self.pending:
            return
        
        with self._lock:
            self._state = _State.CANCELLED
            
        if self._verbose:
            logger.info(f"Cancelled {self}")
        
        # Try to stop the remote job
        try:
            self._send_stop_job_request()
        except HttpRequestError as exc:
            # It's okay if the stop request fails, as a running remote job doesn't hurt
            logger.warning(exc)
        
    def _get_job_info(self):      
        return self._parse_job_info_response(
            response=self._post(url=f"/job/get-info", json={"job_id": self.id}),
        )
        
    def _send_stop_job_request(self):
        self._post(url=f"/job/stop", json={"job_id": self.id})
        
    def _get_job_result(self):        
        resp = self._post(url=f"/job/get-record", json={"job_id": self.id})
        payload = GetJobRecordResponse.model_validate_json(resp.content, strict=True)
        
        if payload.result is None:
            raise RuntimeError("The 'result' field of job record is None")
        
        return json.loads(payload.result)
    
    def _poll_job_once(self):
        try:
            info = self._get_job_info()
        except HttpRequestError as exc:
            if exc.code == HTTPStatus.INTERNAL_SERVER_ERROR:
                # We give internal server errors some tolerance
                logger.warning(exc)
                return None, None
            else:
                return None, exc
        except Exception as exc:
            return None, exc
        else:
            return info, None
    
    def _end_job_polling(self, error: Optional[Exception]):
        if self.cancelled:
            if error:
                raise error
            return
        
        # Set inner state to finished, no matter success or not
        with self._lock:
            self._state = _State.FINISHED
            
        if error:
            raise error
        
        if not self._ignore_result:
            try:
                result = self._get_job_result()
            except Exception as exc:
                raise GetJobResultError(self.id) from exc
            
            # Set job result cache
            with self._lock:
                self._result = result
        
    def _background_monitor_job(self):
        """
        Poll the job until it reaches a terminal state and then fetch result.
        """
        prev_state = NULL
        t0_null = time.time()
        
        while True:
            # Stop background polling if the job has been cancelled
            if self.cancelled:
                raise JobCancelledError(self.id)
            
            info, error = self._poll_job_once()
            if error:
                break
            
            curr_state = info.state if info else NULL
            
            if self._verbose and curr_state != prev_state:
                logger.info(f"{self} state: {curr_state}")
                
            if curr_state == NULL:
                # Update start time for null state if not set
                t0_null = t0_null or time.time()
                # If null state persists for too long, raise an error
                if time.time() - t0_null > self._null_state_tolerance:
                    error = JobStateMissingError(job_id=self.id)
            else:
                t0_null = None
            
                # Handle various types of job states
                if isinstance(info, VolcJobInfo):
                    if curr_state == "Completed":
                        break
                    elif curr_state == "Failed":
                        error = JobStateFailedError(job_id=self.id)
                    elif curr_state == "Stopped":
                        error = JobStateStoppedError(job_id=self.id)
                else:
                    pass
                
            if error:
                break
            
            prev_state = curr_state
            time.sleep(self._poll_interval)
        
        # While loop exited
        self._end_job_polling(error)

    def get_result(
        self, 
        timeout: Optional[Numeric] = None,
        cancel_on_timeout: bool = False,
    ) -> Any:
        if self.cancelled:
            raise JobCancelledError(self.id)
        
        try:
            self._bg_task.result(timeout=timeout)
        except TimeoutError:
            if cancel_on_timeout:
                self.cancel()
            raise TimeoutError(f"Get {self} result timed out") from None
        except Exception as exc:
            raise exc
        
        with self._lock:
            if not self._ignore_result and self._result == NULL:
                raise RuntimeError(f"{self} finished with null result")
            return self._result
            
            
class AsyncJobProxy(_BaseJobProxy):
    def __init__(
        self, 
        *,
        id: str, 
        backend: BackendTypes,
        api_base_url: str,
        headers: Mapping[str, str],
        poll_interval: Numeric = DEFAULT_POLL_INTERVAL,
        null_state_tolerance: Numeric = 30,
        verbose: bool = True,
        ignore_result: bool = False,
    ):
        super().__init__(
            asynchronous=True,
            id=id,
            backend=backend,
            api_base_url=api_base_url,
            headers=headers,
            poll_interval=poll_interval,
            null_state_tolerance=null_state_tolerance,
            verbose=verbose,
            ignore_result=ignore_result,
        )
        self._lock = asyncio.Lock()
        self._bg_task = asyncio.create_task(
            self._background_monitor_job(), name=f"poll-job-{self.id}",
        )
            
    async def cancel(self):
        if self._bg_task.cancel():
            if self._verbose:
                logger.info(f"Cancelled {self}")
            
            # Task has just been cancelled, try to stop the remote job
            try:
                await self._send_stop_job_request()
            except HttpRequestError as exc:
                logger.warning(exc)
            
            # Close the HTTP client
            await self._cli.aclose()
        
    async def _get_job_info(self):
        return self._parse_job_info_response(
            response=await self._apost(url=f"/job/get-info", json={"job_id": self.id}),
        )
        
    async def _send_stop_job_request(self):
        await self._apost(url=f"/job/stop", json={"job_id": self.id})
        
    async def _get_job_result(self):        
        resp = await self._apost(url=f"/job/get-record", json={"job_id": self.id})
        payload = GetJobRecordResponse.model_validate_json(resp.content, strict=True)
        
        if payload.result is None:
            raise RuntimeError("The 'result' field of job record is None")
        
        return json.loads(payload.result)
    
    async def _poll_job_once(self):
        try:
            info = await self._get_job_info()
        except HttpRequestError as exc:
            if exc.code == HTTPStatus.INTERNAL_SERVER_ERROR:
                # We give internal server errors some tolerance
                logger.warning(exc)
                return
            else:
                raise exc
        except Exception as exc:
            raise exc
        else:
            return info
    
    async def _end_job_polling(self):
        if not self._ignore_result:
            try:
                result = await self._get_job_result()
            except Exception as exc:
                raise GetJobResultError(self.id) from exc
            
            # Set job result cache
            async with self._lock:
                self._result = result
            
        # Close the HTTP client right away
        await self._cli.aclose()
    
    async def _background_monitor_job(self):
        """
        Poll the job until it reaches a terminal state and then fetch result.
        """
        
        # NOTE: This entire coroutine may be cancelled anytime, and it will raise 
        # an `asyncio.CancelledError` automatically
        prev_state = NULL
        t0_null = time.time()
        
        while True:                
            info = await self._poll_job_once()          
            curr_state = info.state if info else NULL
            
            if self._verbose and curr_state != prev_state:
                logger.info(f"{self} state: {curr_state}")
                
            if curr_state == NULL:
                # Update start time for null state if not set
                t0_null = t0_null or time.time()
                # If null state persists for too long, raise an error
                if time.time() - t0_null > self._null_state_tolerance:
                    raise JobStateMissingError(job_id=self.id)
            else:
                t0_null = None
            
                # Handle various types of job states
                if isinstance(info, VolcJobInfo):
                    if curr_state == "Completed":
                        break
                    elif curr_state == "Failed":
                        raise JobStateFailedError(job_id=self.id)
                    elif curr_state == "Stopped":
                        raise JobStateStoppedError(job_id=self.id)
                else:
                    pass

            prev_state = curr_state
            await asyncio.sleep(self._poll_interval)
        
        # While loop exited
        await self._end_job_polling()
        
    async def get_result(
        self, 
        timeout: Optional[Numeric] = None,
        cancel_on_timeout: bool = False,
    ) -> Any:
        # See: https://docs.python.org/3/library/asyncio-task.html#timeouts
        done, _ = await asyncio.wait(
            [self._bg_task], timeout=timeout, return_when=asyncio.FIRST_EXCEPTION,
        )

        if not done:
            # Background task is still pending, therefore it must have timed out
            if cancel_on_timeout:
                await self.cancel()
            raise TimeoutError(f"Get {self} result timed out")

        bg_task = next(iter(done))
        
        try:
            err = bg_task.exception()
        except asyncio.CancelledError:
            raise JobCancelledError(self.id) from None
        except Exception as exc:
            raise exc
        
        if err:
            raise err
        
        async with self._lock:
            if not self._ignore_result and self._result == NULL:
                raise RuntimeError(f"{self} finished with null result")
            return self._result
        