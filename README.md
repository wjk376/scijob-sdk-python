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

Following examples are formulated using the sync client.

### Register Functions

You may register a new function which sources from GitLab and with VolcEngine specifications as below:

```python
from scijob.requests import *

resp = cli.register_function(
    request=RegisterFunctionRequestBuilder()
        .identity(...)
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