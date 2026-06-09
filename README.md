# SciJob SDK

## Installation

## Usages

You may first initialize a SciJob client:

```python
from scijob import Client

cli = Client(api_key="your api key", api_base_url="your api base url")
```

Or go with the async version:

```python
from scijob import AsyncClient

cli = AsyncClient(api_key="your api key", api_base_url="your api base url")
```

### Register Functions

You may register a new function which sources from GitLab and with VolcEngine specifications as below:

```python
from scijob.requests import *

resp = cli.register_function(
    request=RegisterFunctionRequestBuilder()
        .identity(key="func_key", name="some_func", module="some_module", version="0.0.1")
        .description("This is a test function...")
        .repo_source("gitlab")
        .gitlab_repo_info(...)
        .envs([("SOME_ENVIRONMENT_VARIABLE", "hello world")])
        .volcengine_specs(specs=VolcEngineSpecsBuilder()
            .credentials(ak="your access key", sk="your secret key")
            .region("cn-beijing")
            .image(...)
            .num_cpus(4) # use 'num_gpus' instead if the function requires GPU resource 
            .vepfs(...)
            .build()
        )
        .build()
)
print(resp.function_id)
#> 6a1b48027b0e2e9c9d3ad8c7
```

### Call Functions

Below shows an example of calling a registered function by its ID, using with statements:

```python
async with AsyncClient(api_key="your api key", api_base_url="your api base url") as cli:
    job = await cli.call_function(
        request=CallFunctionRequestBuilder()
            .function_id("6a1b48027b0e2e9c9d3ad8c7")
            .function_args(...)
            .backend("volcengine_ml_platform")
            .build()
    )
    res = await job.get_result()
```