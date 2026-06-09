import os
from pathlib import Path
import sys

root_dir = Path(__file__).parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

from dotenv import load_dotenv
load_dotenv(
    dotenv_path=Path(__file__).parent.parent / ".env",
    override=True,
)

from scijob.requests import *

API_KEY = os.getenv("API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL")
GITLAB_REPO_ACCESS_TOKEN = os.getenv("GITLAB_REPO_ACCESS_TOKEN")
VOLC_ACCESS_KEY = os.getenv("VOLC_ACCESS_KEY")
VOLC_SECRET_KEY = os.getenv("VOLC_SECRET_KEY")

query_funcs_req = QueryFunctionsRequestBuilder() \
    .function_identity(key="test", name="embed_mol") \
    .page_size(10) \
    .sort_by("create_time") \
    .sort_order("asc") \
    .build()
    
call_func_reqs = {
    "by_id_success": (
        CallFunctionRequestBuilder()
            .function_id("69e8cb73383e4e527525d136")
            .function_args(smi="CC(=O)OC1=CC=CC=C1C(=O)O", max_iters=200)
            .backend("volcengine_ml_platform")
            .build()
    ),
    "by_id_failed": (
        CallFunctionRequestBuilder()
            .function_id("69e8cb73383e4e527525d136")
            .function_args(smi="qwerty", max_iters=200)
            .backend("volcengine_ml_platform")
            .build()
    ),
    "by_name": (
        CallFunctionRequestBuilder()
            .function_identity(key="test", name="embed_mol")
            .function_args(smi="CC(=O)OC1=CC=CC=C1C(=O)O", max_iters=200)
            .backend("volcengine_ml_platform")
            .build()
    ),
}
    
call_func_by_name_req = CallFunctionRequestBuilder() \
    .function_identity(key="test", name="embed_mol") \
    .function_args(smi="CC(=O)OC1=CC=CC=C1C(=O)O", max_iters=200) \
    .backend("volcengine_ml_platform") \
    .build()

success_call_func_req = CallFunctionRequestBuilder() \
    .function_id("6a1d48027b0e2e9c9d9ad8c8") \
    .function_args(smi="CC(=O)OC1=CC=CC=C1C(=O)O", max_iters=200) \
    .backend("volcengine_ml_platform") \
    .build()

failed_call_func_req = CallFunctionRequestBuilder() \
    .function_id("6a1d48027b0e2e9c9d9ad8c8") \
    .function_args(smi="qwerty", max_iters=200) \
    .backend("volcengine_ml_platform") \
    .build()

register_func_req = RegisterFunctionRequestBuilder() \
    .identity(key="unit-test", name="sample_function", module="sample_module", version="beta") \
    .description("This is a sample function for unit test") \
    .doc("Sample function document") \
    .source_code("print('Hello, World!')") \
    .repo_source("gitlab") \
    .gitlab_repo_info(
        api_url="https://gitlab.com/test/test.git", 
        project_id=1034, 
        ref="main", 
        access_token="1234567", 
        encrypt=False,
    ) \
    .envs([("TEST_ENV", "xxxxxxxxxxx")]) \
    .volcengine_specs(specs=VolcEngineSpecsBuilder()
        .credentials(ak=VOLC_ACCESS_KEY, sk=VOLC_SECRET_KEY, encrypt=True)
        .region("cn-beijing")
        .image(type="Prebuild", url="vemlp-cn-beijing.cr.volces.com/preset-images/python:3.12-ubuntu22.04")
        .num_cpus(4)
        .vepfs(mount_path="/fs_mol", vepfs_id="vepfs-cnbj395bdd2cbb24")
        .build()
    ) \
    .build()
    
submit_volc_job_req = SubmitVolcJobRequestBuilder() \
    .command(["echo 'Hello, World!'", "sleep 20"]) \
    .volcengine_specs(specs=VolcEngineSpecsBuilder()
        .credentials(ak=VOLC_ACCESS_KEY, sk=VOLC_SECRET_KEY, encrypt=True)
        .region("cn-beijing")
        .image(type="VolcEngine", url="dp-ve-registry-cn-beijing.cr.volces.com/public/python:3.13-slim-trixie")
        .num_cpus(4)
        .build()
    ) \
    .volcengine_runtime(max_runtime=300) \
    .build()
    
submit_volc_dry_run_job_req = SubmitVolcDryRunJobRequestBuilder() \
    .function_name("embed_mol") \
    .function_module("sample_module_1") \
    .repo_source("gitlab") \
    .gitlab_repo_info(
        api_url="https://git.dp.tech/api/v4", 
        project_id=1066, 
        ref="aec5cc66f66ca581188b4ceb91b37a0647b121f8", 
        access_token=GITLAB_REPO_ACCESS_TOKEN,
        encrypt=True,
    ) \
    .envs([("TEST_ENV", "xxxxxxxxxxx")]) \
    .volcengine_specs(specs=VolcEngineSpecsBuilder()
        .credentials(ak=VOLC_ACCESS_KEY, sk=VOLC_SECRET_KEY, encrypt=True)
        .region("cn-beijing")
        .image(type="VolcEngine", url="dp-ve-registry-cn-beijing.cr.volces.com/gitlab/test:rdkit")
        .num_cpus(4)
        .vepfs(mount_path="/fs_mol", vepfs_id="vepfs-cnbj395bdd2cbb24")
        .build()
    ) \
    .volcengine_runtime(max_runtime=3600) \
    .build()
    