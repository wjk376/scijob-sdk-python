import argparse
from pathlib import Path
import sys
import unittest

root_dir = Path(__file__).parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

import scijob

from commons import *


class TestAsyncClient(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.cli = scijob.AsyncClient(api_key=API_KEY, api_base_url=API_BASE_URL)

    async def asyncTearDown(self):
        await self.cli.aclose()
        
    async def test_register_function(self):
        resp = await self.cli.register_function(request=register_func_req)
        self.assertIsInstance(resp.function_id, str)
        func = await self.cli.get_function(resp.function_id)
        print(func)
        await self.cli.delete_function(resp.function_id)
        
    async def test_query_functions(self):
        funcs = await self.cli.query_functions(request=query_funcs_req)
        print(funcs)
        
    async def test_volc_job(self):
        job = await self.cli.submit_volc_job(request=submit_volc_job_req)
        res = await job.get_result()
        print(res)
        await self.cli.delete_job(job.id)
        
    async def test_volc_dry_run_job(self):
        job = await self.cli.submit_volc_dry_run_job(request=submit_volc_dry_run_job_req)
        res = await job.get_result()
        print(res)
        await self.cli.delete_job(job.id)

    async def test_call_function_by_name(self):
        job = await self.cli.call_function(request=call_func_reqs["by_name"])
        res = await job.get_result()
        print(res)
        await self.cli.delete_job(job.id)

    async def test_job_success(self):
        job = await self.cli.call_function(request=call_func_reqs["by_id_success"])
        res = await job.get_result()
        self.assertIsInstance(res, str)
        await self.cli.delete_job(job.id)
        
    async def test_job_failed(self):
        job = await self.cli.call_function(request=call_func_reqs["by_id_failed"])
        with self.assertRaises(scijob.JobStateFailedError, msg="did not raise JobStateFailedError") as cm:
            await job.get_result()
        print(f"Caught JobStateFailedError: {cm.exception}")
        await self.cli.delete_job(job.id)
        
    async def test_job_timeout(self):
        job = await self.cli.call_function(request=call_func_reqs["by_id_success"])
        with self.assertRaises(TimeoutError, msg="did not raise TimeoutError") as cm:
            await job.get_result(timeout=5)
        print(f"Caught TimeoutError: {cm.exception}")
        res = await job.get_result()
        self.assertIsInstance(res, str)
        
    async def test_job_timeout_and_cancel(self):
        job = await self.cli.call_function(request=call_func_reqs["by_id_success"])
        with self.assertRaises(TimeoutError, msg="did not raise TimeoutError") as cm:
            await job.get_result(timeout=5)
        print(f"Caught TimeoutError: {cm.exception}")
        await job.cancel()
        with self.assertRaises(scijob.JobCancelledError, msg="did not raise JobCancelledError") as cm:
            await job.get_result()
        print(f"Caught JobCancelledError: {cm.exception}")
        
        
class TestAsyncClientContextManager(unittest.IsolatedAsyncioTestCase):
    async def test_job_failed(self):
        async with scijob.AsyncClient(api_key=API_KEY, api_base_url=API_BASE_URL) as cli:
            job = await cli.call_function(request=call_func_reqs["by_id_failed"])
        with self.assertRaises(scijob.JobStateFailedError, msg="did not raise JobStateFailedError") as cm:
            await job.get_result()
        print(f"Caught JobStateFailedError: {cm.exception}")
        await cli.delete_job(job.id)
            
    async def test_job_timeout(self):
        async with scijob.AsyncClient(api_key=API_KEY, api_base_url=API_BASE_URL) as cli:
            job = await cli.call_function(request=call_func_reqs["by_id_success"])
            
        with self.assertRaises(TimeoutError, msg="did not raise TimeoutError") as cm:
            await job.get_result(timeout=5, cancel_on_timeout=True)
        print(f"Caught TimeoutError: {cm.exception}")
        
        with self.assertRaises(scijob.JobCancelledError, msg="did not raise JobCancelledError") as cm:
            await job.get_result()
        print(f"Caught JobCancelledError: {cm.exception}")
        

def suite_1():
    suite = unittest.TestSuite()
    suite.addTest(TestAsyncClient("test_job_success"))
    return suite


def suite_2():
    suite = unittest.TestSuite()
    suite.addTest(TestAsyncClient("test_job_failed"))
    return suite

def suite_3():
    suite = unittest.TestSuite()
    suite.addTest(TestAsyncClient("test_job_timeout"))
    return suite    


def suite_4():
    suite = unittest.TestSuite()
    suite.addTest(TestAsyncClient("test_register_function"))
    return suite


def suite_5():
    suite = unittest.TestSuite()
    suite.addTest(TestAsyncClient("test_volc_dry_run_job"))
    return suite


def suite_6():
    suite = unittest.TestSuite()
    suite.addTest(TestAsyncClient("test_query_functions"))
    return suite


def suite_7():
    suite = unittest.TestSuite()
    suite.addTest(TestAsyncClient("test_call_function_by_name"))
    return suite


def suite_8():
    suite = unittest.TestSuite()
    suite.addTest(TestAsyncClientContextManager("test_job_failed"))
    return suite


def suite_9():
    suite = unittest.TestSuite()
    suite.addTest(TestAsyncClientContextManager("test_job_timeout"))
    return suite


def suite_10():
    suite = unittest.TestSuite()
    suite.addTest(TestAsyncClient("test_volc_job"))
    return suite


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", type=int, required=True)
    args = parser.parse_args()
    
    _locals = locals()
    suite_name = f"suite_{args.suite}"
    if suite_name not in _locals:
        raise ValueError(f"Invalid test suite: {args.suite}")
    
    suite = _locals[suite_name]()
    runner = unittest.TextTestRunner()
    runner.run(suite)