"""
jsonrpc11base tests
"""
import json
import jsonrpc11base
from jsonrpc11base.service_description import ServiceDescription
from jsonrpc11base.errors import APIError
import pytest
import os


class MyError(APIError):
    code = 123
    message = "My error"

    def __init__(self, id):
        self.error = {
            'id': id
        }


SCHEMA_DIR = os.path.join(os.path.dirname(__file__), '../data/schema/api')


@pytest.fixture(scope='module')
def service():
    service_description = ServiceDescription(
        'Test Service',
        'https://github.com/kbase/kbase-jsonrpc11base/test',
        summary='An test JSON-RPC 1.1 service',
        version='1.0'
    )

    # Our service instance
    service = jsonrpc11base.JSONRPCService(
        description=service_description,
        schema_dir=SCHEMA_DIR,
        validate_params=True,
        validate_result=True
    )

    # Add testing methods to the service.
    # Note that each method needs param schema in data/schema

    def method1(params, options):
        return params

    def method2(params, options):
        raise MyError(456)

    service.add(method1)
    service.add(method2)
    return service


# -------------------------------
# Ensure acceptable forms all work
# Happy path testing
# Note id omitted from all requests, to
# keep them simpler
# -------------------------------


# Test direct usage of call which deals with the
# actual payload, a JSON string.
#
# In most cases we test using call_py, which consumes the
# parsed request.

# Test all forms of params.
# Params may be any valid JSON, so we have a method to
# handle each one!
def test_array_param(service):
    """
    Test valid jsonrpc multiple argument calls.
    """
    params = {
        'version': '1.1',
        'method': 'method1',
        'params': {
            'param1': 'hello'
        }
    }
    res_str = service.call(json.dumps(params))
    result = json.loads(res_str)
    assert result['version'] == "1.1"
    print('RESULT', result)
    assert result['result']['param1'] == 'hello'


def test_api_error(service):
    """
    When a method accepts no args, but they are provided,
    should return error.
    """
    res = service.call_py({
        "version": "1.1",
        "method": "method2",
        "params": {
            "param1": "hi"
        }
    })
    assert res['error']['name'] == 'APIError'
    assert res['error']['message'] == 'My error'
    assert res['error']['code'] == 123
    assert res['error']['error']['id'] == 456


# API Errors

def test_own_api_error():
    with pytest.raises(MyError) as me:
        raise MyError(456)
    err = me.value.to_json()
    assert err['name'] == 'APIError'
    assert err['code'] == 123
    assert err['message'] == 'My error'
    assert err['error']['id'] == 456


def test_base_api_error():
    """ Although not recommended, one may use the APIError directly"""
    with pytest.raises(APIError) as apie:
        raise APIError()
    err = apie.value.to_json()
    assert err['name'] == 'APIError'
    assert err['code'] == 1
    assert err['message'] == 'API error'
