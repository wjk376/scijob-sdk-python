from types import TracebackType
from typing import Any, Optional, Type

import httpx

from ._config import *
from ._exceptions import *
from ._proxy import AsyncJobProxy, JobProxy
from ._logger import logger
from ._models import *
from ._types import Numeric, QueryFunctionsResponse
from .requests import *

__all__ = ["AsyncClient", "Client"]


class _BaseClient:
    def __init__(
        self, 
        *,
        api_key: str, 
        api_base_url: str,
        poll_interval: Numeric = DEFAULT_POLL_INTERVAL,
    ):
        self._api_base_url = f"{api_base_url}/{API_VERSION}"
        self._headers = {API_KEY_HEADER: api_key}
        self._poll_interval = poll_interval


class Client(_BaseClient):
    def __init__(
        self, 
        *, 
        api_key: str, 
        api_base_url: str,
        poll_interval: Numeric = DEFAULT_POLL_INTERVAL,
    ):
        super().__init__(
            api_key=api_key, 
            api_base_url=api_base_url, 
            poll_interval=poll_interval,
        )
        self._cli = httpx.Client(base_url=self._api_base_url, headers=self._headers)
        
    def __del__(self):
        self.close()
        
    def close(self):
        self._cli.close()
        
    def __enter__(self):
        return self
    
    def __exit__(
        self, 
        exc_type: Optional[Type[BaseException]], 
        exc_value: Optional[BaseException], 
        traceback: Optional[TracebackType],
    ):
        self.close()
        
    def _get(self, url: str):
        resp = self._cli.get(url)
        if not resp.is_success:
            raise HttpRequestError(resp)
        return resp
    
    def _post(self, url: str, json: Any):
        resp = self._cli.post(url, json=json)
        if not resp.is_success:
            raise HttpRequestError(resp)
        return resp
        
    def get_function(self, function_id: str):
        """
        Get function details by function ID.
        """
        resp = self._get(url=f"/function/{function_id}")
        return Function.model_validate_json(resp.content, strict=True)
    
    def query_functions(self, request: QueryFunctionsRequest):
        """
        Query matched functions by identity information.
        """
        
        # Fetch all matched functions by pagination
        json = {**request.json(), "page": 1}
        funcs = []
        
        while True:
            resp = self._post(url=f"/function/query", json=json)
            payload: QueryFunctionsResponse = resp.json()
            funcs.extend(payload["functions"])
            if payload["has_more"]:
                json["page"] += 1
            else:
                break
        
        return [Function.model_validate(fn, strict=True) for fn in funcs]
    
    def register_function(self, request: RegisterFunctionRequest):
        """
        Register a new function to job platform.
        """
        resp = self._post(url=f"/function/register", json=request.json())
        payload = RegisterFunctionResponse.model_validate_json(resp.content, strict=True)
        logger.info(f"Registered function '{payload.function_id}'")
        return payload
    
    def delete_job(self, job_id: str):
        """
        Delete job by job ID (for admin users only).
        """
        self._post(url=f"/job/delete", json={"job_id": job_id})
    
    def delete_function(self, function_id: str):
        """
        Delete function by function ID (for admin users only).
        """
        self._post(url=f"/function/delete", json={"id": function_id})
        logger.info(f"Deleted function '{function_id}'")
        
    def call_function(
        self, 
        request: CallFunctionRequest, 
        verbose: bool = True,
    ):
        """
        Call function either by function ID or identity (key, name, module, version).
        
        Usage:
        
        ```python
        >>> from scijob import SciJobClient
        >>> from scijob.requests import CallFunctionRequestBuilder
        >>> 
        >>> client = SciJobClient(...)
        >>> job = client.call_function(
        >>>     request=CallFunctionRequestBuilder()
        >>>         .function_id("your-function-id")
        >>>         .function_args(...)
        >>>         .backend(...)
        >>>         .build()
        >>> )
        >>> result = job.get_result()
        ```
        """        
        resp = self._post(url=request.api_url, json=request.json())
        payload = CallFunctionResponse.model_validate_json(resp.content, strict=True)
        
        if verbose:
            logger.info(
                f"Created job '{payload.job_id}' | backend={request.backend} | "
                f"function_id={payload.function_id}"
            )
        
        return JobProxy(
            id=payload.job_id,
            backend=request.backend,
            api_base_url=self._api_base_url,
            headers=self._headers,
            poll_interval=self._poll_interval,
            verbose=verbose,
        )
    
    def submit_volc_job(
        self,
        request: SubmitVolcJobRequest,
        verbose: bool = True,
    ):
        """
        Submit a job to VolcEngine.
        """
        resp = self._post(url=f"/job/volc/submit", json=request.json())
        payload = SubmitVolcJobResponse.model_validate_json(resp.content, strict=True)
        
        if verbose:
            logger.info(f"Submitted job '{payload.job_id}' | volc_job_id={payload.volc_job_id}")
        
        return JobProxy(
            id=payload.job_id,
            backend="volcengine_ml_platform",
            api_base_url=self._api_base_url,
            headers=self._headers,
            poll_interval=self._poll_interval,
            verbose=verbose,
            ignore_result=True,
        )
        
    def submit_volc_dry_run_job(
        self, 
        request: SubmitVolcDryRunJobRequest, 
        verbose: bool = True,
    ):
        """
        Submit a dry run job to VolcEngine.
        """
        resp = self._post(url=f"/job/volc/submit-dry-run", json=request.json())
        payload = SubmitVolcJobResponse.model_validate_json(resp.content, strict=True)
        
        if verbose:
            logger.info(
                f"Submitted dry run job '{payload.job_id}' | volc_job_id={payload.volc_job_id}"
            )
        
        return JobProxy(
            id=payload.job_id,
            backend="volcengine_ml_platform",
            api_base_url=self._api_base_url,
            headers=self._headers,
            poll_interval=self._poll_interval,
            verbose=verbose,
        )


class AsyncClient(_BaseClient):
    def __init__(
        self, 
        *,
        api_key: str, 
        api_base_url: str,
        poll_interval: Numeric = DEFAULT_POLL_INTERVAL,
    ):
        super().__init__(
            api_key=api_key, 
            api_base_url=api_base_url, 
            poll_interval=poll_interval,
        )
        self._cli = httpx.AsyncClient(base_url=self._api_base_url, headers=self._headers)
        
    async def aclose(self):
        await self._cli.aclose()
        
    async def __aenter__(self):
        return self
    
    async def __aexit__(
        self, 
        exc_type: Optional[Type[BaseException]], 
        exc_value: Optional[BaseException], 
        traceback: Optional[TracebackType],
    ):
        await self.aclose()
        
    async def _get(self, url: str):
        resp = await self._cli.get(url)
        if not resp.is_success:
            raise HttpRequestError(resp)
        return resp
    
    async def _post(self, url: str, json: Any):
        resp = await self._cli.post(url, json=json)
        if not resp.is_success:
            raise HttpRequestError(resp)
        return resp
        
    async def get_function(self, function_id: str):
        """
        Get function details by function ID.
        """
        resp = await self._get(url=f"/function/{function_id}")
        return Function.model_validate_json(resp.content, strict=True)
    
    async def query_functions(self, request: QueryFunctionsRequest):
        """
        Query matched functions by identity information.
        """
        
        # Fetch all matched functions by pagination
        json = {**request.json(), "page": 1}
        funcs = []
        
        while True:
            resp = await self._post(url=f"/function/query", json=json)
            payload: QueryFunctionsResponse = resp.json()
            funcs.extend(payload["functions"])
            if payload["has_more"]:
                json["page"] += 1
            else:
                break
        
        return [Function.model_validate(fn, strict=True) for fn in funcs]
    
    async def register_function(self, request: RegisterFunctionRequest):
        """
        Register a new function to job platform.
        """
        resp = await self._post(url=f"/function/register", json=request.json())
        payload = RegisterFunctionResponse.model_validate_json(resp.content, strict=True)
        logger.info(f"Registered function '{payload.function_id}'")
        return payload
    
    async def delete_function(self, function_id: str):
        """
        Delete function by function ID (for admin users only).
        """
        await self._post(url=f"/function/delete", json={"id": function_id})
        logger.info(f"Deleted function '{function_id}'")
        
    async def delete_job(self, job_id: str):
        """
        Delete job by job ID (for admin users only).
        """
        await self._post(url=f"/job/delete", json={"job_id": job_id})
    
    async def call_function(
        self, 
        request: CallFunctionRequest, 
        verbose: bool = True,
    ):
        """
        Call function either by function ID or identity (key, name, module, version).
        
        Usage:
        
        ```python
        >>> from scijob import AsyncSciJobClient
        >>> from scijob.requests import CallFunctionRequestBuilder
        >>> 
        >>> client = AsyncSciJobClient(...)
        >>> job = await client.call_function(
        >>>     request=CallFunctionRequestBuilder()
        >>>         .function_id("your-function-id")
        >>>         .function_args(...)
        >>>         .backend(...)
        >>>         .build()
        >>> )
        >>> result = await job.get_result()
        ```
        """        
        resp = await self._post(url=request.api_url, json=request.json())
        payload = CallFunctionResponse.model_validate_json(resp.content, strict=True)
        
        if verbose:
            logger.info(
                f"Created job '{payload.job_id}' | backend={request.backend} | "
                f"function_id={payload.function_id}"
            )
        
        return AsyncJobProxy(
            id=payload.job_id,
            backend=request.backend,
            api_base_url=self._api_base_url,
            headers=self._headers,
            poll_interval=self._poll_interval,
            verbose=verbose,
        )
        
    async def submit_volc_job(
        self,
        request: SubmitVolcJobRequest,
        verbose: bool = True,
    ):
        """
        Submit a job to VolcEngine.
        """
        resp = await self._post(url=f"/job/volc/submit", json=request.json())
        payload = SubmitVolcJobResponse.model_validate_json(resp.content, strict=True)
        
        if verbose:
            logger.info(f"Submitted job '{payload.job_id}' | volc_job_id={payload.volc_job_id}")
        
        return AsyncJobProxy(
            id=payload.job_id,
            backend="volcengine_ml_platform",
            api_base_url=self._api_base_url,
            headers=self._headers,
            poll_interval=self._poll_interval,
            verbose=verbose,
            ignore_result=True,
        )
    
    async def submit_volc_dry_run_job(
        self, 
        request: SubmitVolcDryRunJobRequest, 
        verbose: bool = True,
    ):
        """
        Submit a dry run job to VolcEngine.
        """
        resp = await self._post(url=f"/job/volc/submit-dry-run", json=request.json())
        payload = SubmitVolcJobResponse.model_validate_json(resp.content, strict=True)
        
        if verbose:
            logger.info(
                f"Submitted dry run job '{payload.job_id}' | volc_job_id={payload.volc_job_id}"
            )
        
        return AsyncJobProxy(
            id=payload.job_id,
            backend="volcengine_ml_platform",
            api_base_url=self._api_base_url,
            headers=self._headers,
            poll_interval=self._poll_interval,
            verbose=verbose,
        )
