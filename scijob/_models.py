from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from ._types import (
    RepoSourceTypes, 
    BackendTypes, 
    VolcJobState,
    VolcEngineImageTypes,
)


class GitLabRepoInfo(BaseModel):
    api_url: str
    project_id: int
    ref: str
    access_token: str
    
    
class GitHubRepoInfo(BaseModel):
    owner: str
    repo: str
    ref: str
    access_token: str
    
    
class FunctionEnv(BaseModel):
    name: str
    value: str
    

class VolcEngineImage(BaseModel):
    type: VolcEngineImageTypes
    url: str
    

class VolcEngineResource(BaseModel):
    num_gpus: int = 0
    num_cpus: int = 0
    
    
class VolcEngineStorage(BaseModel):
    type: Literal["Vepfs", "Tos"]
    mount_path: Optional[str] = None
    vepfs_id: Optional[str] = None
    tos_id: Optional[str] = None


class VolcEngineSpecs(BaseModel):
    ak: Optional[str] = None
    sk: Optional[str] = None
    region: Optional[str] = None
    image: Optional[VolcEngineImage] = None
    resource: VolcEngineResource = Field(default_factory=VolcEngineResource)
    storages: List[VolcEngineStorage] = Field(default_factory=list)
    
    
class VolcEngineRuntime(BaseModel):
    command: Optional[str] = None
    max_runtime: int = 0
    holding_time: int = 0
    
    
class FunctionIdentity(BaseModel):
    key: Optional[str] = None
    name: Optional[str] = None
    module: Optional[str] = None
    version: Optional[str] = None


class Function(FunctionIdentity):
    id: Optional[str] = None
    description: Optional[str] = None
    doc: Optional[str] = None
    source_code: Optional[str] = None
    repo_source: Optional[RepoSourceTypes] = None
    gitlab_repo_info: Optional[GitLabRepoInfo] = None
    github_repo_info: Optional[GitHubRepoInfo] = None
    envs: List[FunctionEnv] = Field(default_factory=list)
    volcengine_specs: Optional[VolcEngineSpecs] = None
    create_time: Optional[str] = None
    
    
class RegisterFunctionResponse(BaseModel):
    function_id: str
    

class CallFunctionResponse(BaseModel):
    job_id: str
    job_token: str
    function_id: str
    

class _BaseGetJobInfoResponse(BaseModel):
    job_id: str
    backend: BackendTypes
    
    
class VolcJobStatus(BaseModel):
    state: VolcJobState = Field(validation_alias="State")
    start_time: str = Field(validation_alias="StartTime")
    end_time: str = Field(validation_alias="EndTime")
    

class VolcJobInfo(BaseModel):
    id: str = Field(validation_alias="Id")
    name: str = Field(validation_alias="Name")
    description: str = Field(validation_alias="Description")
    created_by: str = Field(validation_alias="CreatedBy")
    status: VolcJobStatus = Field(validation_alias="Status")
    
    @property
    def state(self) -> VolcJobState:
        return self.status.state
    
    
class GetVolcJobInfoResponse(_BaseGetJobInfoResponse):
    info: VolcJobInfo
    
    def __str__(self):
        return f"Job '{self.job_id}' | backend={self.backend} | state={self.info.state}"
    
    
class GetJobResultResponsePayload(BaseModel):
    job_id: str
    result: str # JSON string
    
    
class GetJobRecordResponse(BaseModel):
    job_id: str
    backend: BackendTypes
    function_id: Optional[str] = None # 'None' for dry run jobs
    result: Optional[str] = None # JSON string
    create_time: Optional[str] = None
    save_result_time: Optional[str] = None
    
    
class SubmitVolcJobResponse(BaseModel):
    job_id: str
    job_token: str
    volc_job_id: str