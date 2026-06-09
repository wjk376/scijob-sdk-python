from typing import (
    Any, 
    Dict,
    List,
    Literal, 
    Mapping, 
    TypedDict,
    Union,
)

BackendTypes = Literal["volcengine_ml_platform"]
RepoSourceTypes = Literal["gitlab", "github", "zipfile"]
VolcEngineImageTypes = Literal["Prebuild", "VolcEngine", "Public"]
SortFunctionsByTypes = Literal["create_time", "version"]
SortOrderTypes = Literal["asc", "desc"]

Numeric = Union[int, float]
FunctionArgs = Mapping[str, Any]

VolcJobState = Literal[
    "Creating",
    "Waiting",
    "Queueing",
    "Deploying",
    "Running",
    "Completed",
    "Failed",
    "Stopping",
    "Stopped",
]


class _Null:
    def __str__(self):
        return "NULL"
    
NULL = _Null()


class QueryFunctionsResponse(TypedDict):
    total: int
    functions: List[Dict[str, Any]]
    has_more: bool