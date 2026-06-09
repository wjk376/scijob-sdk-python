from typing import (
    ClassVar, 
    Generic, 
    List, 
    Optional, 
    Sequence, 
    Tuple, 
    TypeVar, 
    Type, 
    Union,
)
from typing_extensions import Self

from pydantic import BaseModel, Field

from ._models import (
    Function, 
    FunctionEnv, 
    FunctionIdentity,
    GitHubRepoInfo, 
    GitLabRepoInfo, 
    VolcEngineImage,
    VolcEngineRuntime,
    VolcEngineSpecs,
    VolcEngineStorage,
)
from ._types import (
    BackendTypes,
    FunctionArgs,
    RepoSourceTypes, 
    SortFunctionsByTypes,
    SortOrderTypes, 
    VolcEngineImageTypes,
)
from ._utils import rsa_encrypt

__all__ = [
    "CallFunctionRequest",
    "CallFunctionRequestBuilder",
    "QueryFunctionsRequest",
    "QueryFunctionsRequestBuilder",
    "RegisterFunctionRequest",
    "RegisterFunctionRequestBuilder",
    "SubmitVolcDryRunJobRequest",
    "SubmitVolcDryRunJobRequestBuilder",
    "SubmitVolcJobRequest",
    "SubmitVolcJobRequestBuilder",
    "VolcEngineSpecsBuilder",
]


class _BaseRequest(BaseModel):
    def json(self):
        return self.model_dump(mode="json", exclude_none=True)
    

RequestType = TypeVar("RequestType", bound=_BaseRequest)


class _BaseRequestBuilder(Generic[RequestType]):    
    request_type: ClassVar[Type[RequestType]]
    
    def __init__(self):
        self.request = self.__class__.request_type()
    
    def build(self) -> RequestType:
        return self.request


RequestBuilderType = TypeVar("RequestBuilderType", bound=_BaseRequestBuilder)

def _check_instance(instance: Optional[RequestBuilderType]):
    if instance is None:
        raise AttributeError("cannot get attribute if instance is None")
    if not isinstance(instance, _BaseRequestBuilder):
        raise TypeError(f"instance has invalid type '{instance.__class__.__qualname__}'")
    
    
class _RepoSourceBinder(Generic[RequestBuilderType]):
    def __get__(self, instance: Optional[RequestBuilderType], owner: type[RequestBuilderType]):
        _check_instance(instance)
        
        def bind(repo_source: RepoSourceTypes) -> RequestBuilderType:
            instance.request.repo_source = repo_source
            return instance
        
        return bind
    

class _FunctionIdentityBinder(Generic[RequestBuilderType]):
    def __get__(self, instance: Optional[RequestBuilderType], owner: type[RequestBuilderType]):
        _check_instance(instance)
                       
        def bind(
            *,
            key: Optional[str] = None, 
            name: Optional[str] = None, 
            module: Optional[str] = None, 
            version: Optional[str] = None,
        ) -> RequestBuilderType:
            for attr, value in [
                ("key", key), ("name", name), ("module", module), ("version", version),
            ]:
                setattr(instance.request, attr, value)
            return instance
                
        return bind
    

class _EnvsBinder(Generic[RequestBuilderType]):
    def __get__(self, instance: Optional[RequestBuilderType], owner: type[RequestBuilderType]):
        _check_instance(instance)
        
        def bind(envs: Sequence[Tuple[str, str]]) -> RequestBuilderType:
            instance.request.envs.extend(
                FunctionEnv(name=name, value=value) for name, value in envs
            )
            return instance
        
        return bind
    

class _GitLabRepoInfoBinder(Generic[RequestBuilderType]):
    def __get__(self, instance: Optional[RequestBuilderType], owner: type[RequestBuilderType]):
        _check_instance(instance)
        
        def bind(
            *,
            api_url: str, 
            project_id: int, 
            ref: str, 
            access_token: str, 
            encrypt: bool = True,
        ) -> RequestBuilderType:
            instance.request.gitlab_repo_info = GitLabRepoInfo(
                api_url=api_url,
                project_id=project_id,
                ref=ref,
                access_token=(rsa_encrypt(access_token, label=b"repo-access-token") if encrypt else access_token),
            )
            return instance
            
        return bind
    
    
class _GitHubRepoInfoBinder(Generic[RequestBuilderType]):
    def __get__(self, instance: Optional[RequestBuilderType], owner: type[RequestBuilderType]):
        _check_instance(instance)
        
        def bind(
            *,
            owner: str, 
            repo: str, 
            ref: str, 
            access_token: str,
            encrypt: bool = True,
        ) -> RequestBuilderType:
            instance.request.github_repo_info = GitHubRepoInfo(
                owner=owner, 
                repo=repo, 
                ref=ref, 
                access_token=(rsa_encrypt(access_token, label=b"repo-access-token") if encrypt else access_token),
            )
            return instance
            
        return bind
    
    
class _VolcEngineSpecsBinder(Generic[RequestBuilderType]):
    def __get__(self, instance: Optional[RequestBuilderType], owner: type[RequestBuilderType]):
        _check_instance(instance)
        
        def bind(specs: VolcEngineSpecs) -> RequestBuilderType:
            instance.request.volcengine_specs = specs
            return instance
        
        return bind
    
    
class _VolcEngineRuntimeBinder(Generic[RequestBuilderType]):
    def __get__(self, instance: Optional[RequestBuilderType], owner: type[RequestBuilderType]):
        _check_instance(instance)
        
        def bind(*, max_runtime: int = 0, holding_time: int = 0) -> RequestBuilderType:
            # NOTE: be careful with field 'command', we restrict setting it here
            if (
                not hasattr(instance.request, "volcengine_runtime")
                or not instance.request.volcengine_runtime
            ):
                instance.request.volcengine_runtime = VolcEngineRuntime()
            
            instance.request.volcengine_runtime.max_runtime = max_runtime
            instance.request.volcengine_runtime.holding_time = holding_time
            return instance
        
        return bind


class VolcEngineSpecsBuilder:
    __slots__ = ("model",)
    
    def __init__(self):
        self.model = VolcEngineSpecs()
        
    def credentials(self, ak: str, sk: str, encrypt: bool = True):
        self.model.ak = rsa_encrypt(ak, label=b"volc-access-key") if encrypt else ak
        self.model.sk = rsa_encrypt(sk, label=b"volc-secret-key") if encrypt else sk
        return self
    
    def region(self, region: str):
        self.model.region = region
        return self
    
    def image(self, type: VolcEngineImageTypes, url: str):
        self.model.image = VolcEngineImage(type=type, url=url)
        return self
    
    def num_gpus(self, value: int):
        self.model.resource.num_gpus = value
        return self
    
    def num_cpus(self, value: int):
        self.model.resource.num_cpus = value
        return self
    
    def vepfs(self, mount_path: str, vepfs_id: str):
        self.model.storages.append(
            VolcEngineStorage(type="Vepfs", mount_path=mount_path, vepfs_id=vepfs_id),
        )
        return self
    
    def tos(self, mount_path: str, tos_id: str):
        self.model.storages.append(
            VolcEngineStorage(type="Tos", mount_path=mount_path, tos_id=tos_id),
        )
        return self
    
    def build(self):
        return self.model
    
    
class RegisterFunctionRequest(_BaseRequest, Function):
    pass


class RegisterFunctionRequestBuilder(_BaseRequestBuilder[RegisterFunctionRequest]):
    request_type = RegisterFunctionRequest
    identity = _FunctionIdentityBinder[Self]()
    repo_source = _RepoSourceBinder[Self]()
    envs = _EnvsBinder[Self]()
    gitlab_repo_info = _GitLabRepoInfoBinder[Self]()
    github_repo_info = _GitHubRepoInfoBinder[Self]()
    volcengine_specs = _VolcEngineSpecsBinder[Self]()
    
    def id(self, id: str):
        self.request.id = id
        return self
    
    def description(self, description: str):
        self.request.description = description
        return self
    
    def doc(self, doc: str):
        self.request.doc = doc
        return self
    
    def source_code(self, source_code: str):
        self.request.source_code = source_code
        return self

    
class QueryFunctionsRequest(_BaseRequest, FunctionIdentity):
    page_size: int = 20
    sort_by: SortFunctionsByTypes = "create_time"
    sort_order: SortOrderTypes = "asc"
    
    
class QueryFunctionsRequestBuilder(_BaseRequestBuilder[QueryFunctionsRequest]):
    request_type = QueryFunctionsRequest
    function_identity = _FunctionIdentityBinder[Self]()
    
    def page_size(self, page_size: int):
        self.request.page_size = page_size
        return self
    
    def sort_by(self, sort_by: SortFunctionsByTypes):
        self.request.sort_by = sort_by
        return self
    
    def sort_order(self, sort_order: SortOrderTypes):
        self.request.sort_order = sort_order
        return self
    
    
class CallFunctionRequest(_BaseRequest, FunctionIdentity):
    id: Optional[str] = None
    args: Optional[FunctionArgs] = None
    backend: Optional[BackendTypes] = None
    volcengine_runtime: Optional[VolcEngineRuntime] = None
    
    @property
    def api_url(self):
        return "/function/call/by-id" if self.id else "/function/call/by-name"
    
    def json(self):
        return self.model_dump(
            mode="json", 
            exclude=["key", "name", "module", "version"] if self.id else ["id"],
            exclude_none=True,
        )

    
class CallFunctionRequestBuilder(_BaseRequestBuilder[CallFunctionRequest]):
    request_type = CallFunctionRequest
    function_identity = _FunctionIdentityBinder[Self]()
    volcengine_runtime = _VolcEngineRuntimeBinder[Self]()
            
    def function_id(self, id: str):
        self.request.id = id
        return self
    
    def function_args(self, **kwargs):
        self.request.args = kwargs
        return self
    
    def backend(self, backend: BackendTypes):
        self.request.backend = backend
        return self
    
    
class SubmitVolcJobRequest(_BaseRequest):
    envs: List[FunctionEnv] = Field(default_factory=list)
    volcengine_specs: Optional[VolcEngineSpecs] = None
    volcengine_runtime: VolcEngineRuntime = Field(default_factory=VolcEngineRuntime)
    

class SubmitVolcJobRequestBuilder(_BaseRequestBuilder[SubmitVolcJobRequest]):
    request_type = SubmitVolcJobRequest
    envs = _EnvsBinder[Self]()
    volcengine_specs = _VolcEngineSpecsBinder[Self]()
    volcengine_runtime = _VolcEngineRuntimeBinder[Self]()
    
    def command(self, cmd: Union[str, Sequence[str]]):
        if isinstance(cmd, str):
            self.request.volcengine_runtime.command = cmd
        else:
            try:
                self.request.volcengine_runtime.command = "\n".join(cmd)
            except:
                raise ValueError("Command must be a string or a sequence of strings")
        
        return self


class SubmitVolcDryRunJobRequest(_BaseRequest, Function):
    volcengine_runtime: VolcEngineRuntime = Field(default_factory=VolcEngineRuntime)
    
    def json(self):
        payload = super().json()
        payload["function_name"] = self.name
        payload["function_module"] = self.module
        payload.pop("name", None)
        payload.pop("module", None)
        return payload


class SubmitVolcDryRunJobRequestBuilder(_BaseRequestBuilder[SubmitVolcDryRunJobRequest]):
    request_type = SubmitVolcDryRunJobRequest
    repo_source = _RepoSourceBinder[Self]()
    envs = _EnvsBinder[Self]()
    gitlab_repo_info = _GitLabRepoInfoBinder[Self]()
    github_repo_info = _GitHubRepoInfoBinder[Self]()
    volcengine_specs = _VolcEngineSpecsBinder[Self]()
    volcengine_runtime = _VolcEngineRuntimeBinder[Self]()
    
    def function_name(self, name: str):
        self.request.name = name
        return self
    
    def function_module(self, module: str):
        self.request.module = module
        return self
