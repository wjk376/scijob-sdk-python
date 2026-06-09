import argparse
from pathlib import Path
import sys
import unittest

root_dir = Path(__file__).parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

import scijob

from commons import *


class TestClient(unittest.TestCase):
    def setUp(self):
        self.cli = scijob.Client(api_key=API_KEY, api_base_url=API_BASE_URL)
        
    def tearDown(self):
        self.cli.close()
    
    def test_register_function(self):
        resp = self.cli.register_function(request=register_func_req)
        self.assertIsInstance(resp.function_id, str)
        func = self.cli.get_function(resp.function_id)
        print(func)
        self.cli.delete_function(resp.function_id)
        
        resp = self.cli.register_function(
            request=RegisterFunctionRequestBuilder()
                .identity(key="unit-test", name="sample_function", module="sample_module", version="beta")
                .build()
        )
        
    def test_query_functions(self):
        funcs = self.cli.query_functions(request=query_funcs_req)
        print(funcs)
        
    def test_volc_dry_run_job(self):
        job = self.cli.submit_volc_dry_run_job(request=submit_volc_dry_run_job_req)
        res = job.get_result()
        print(res)
        
    def test_call_function_by_name(self):
        job = self.cli.call_function(request=call_func_by_name_req)
        res = job.get_result()
        print(res)
        
    def test_job_success(self):
        job = self.cli.call_function(request=success_call_func_req)
        res = job.get_result()
        print(res)
        
    def test_job_failed(self):
        job = self.cli.call_function(request=failed_call_func_req)
        with self.assertRaises(scijob.JobStateFailedError, msg="did not raise JobStateFailedError") as cm:
            job.get_result()
        print(f"Caught JobStateFailedError: {cm.exception}")
        self.cli.delete_job(job.id)


def suite_1():
    suite = unittest.TestSuite()
    suite.addTest(TestClient("test_job_success"))
    return suite


def suite_2():
    suite = unittest.TestSuite()
    suite.addTest(TestClient("test_job_failed"))
    return suite

def suite_3():
    suite = unittest.TestSuite()
    suite.addTest(TestClient("test_job_timeout"))
    return suite    


def suite_4():
    suite = unittest.TestSuite()
    suite.addTest(TestClient("test_register_function"))
    return suite


def suite_5():
    suite = unittest.TestSuite()
    suite.addTest(TestClient("test_volc_dry_run_job"))
    return suite


def suite_6():
    suite = unittest.TestSuite()
    suite.addTest(TestClient("test_query_functions"))
    return suite


def suite_7():
    suite = unittest.TestSuite()
    suite.addTest(TestClient("test_call_function_by_name"))
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