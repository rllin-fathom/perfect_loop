import json
import pickle
from functools import partial
from concurrent.futures import _base, Future, ThreadPoolExecutor
from zappa.cli import ZappaCLI

def execute_on_lambda(lambda_client, function_name, task):
    """Executes work on a lambda instance"""
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',
        LogType='Tail',
        Payload=json.dumps({
            'command': 'lambdapoolexecutor._base.perform_work',
            'task': pickle.dumps(task)
        })
    )

    result = pickle.loads(json.loads(response['Payload'].read()))

    return result


def perform_work(content):
    """For use with LambdaPoolExecutor

    Unpickles and executes fully applied (functools.partial) functions
    """
    # Pickled Fully applied function
    fn_applied_pickled = content['task']

    # Fully applied function
    fn_applied = pickle.loads(fn_applied_pickled)

    # Result for the work
    result = fn_applied()

    # Pickled result for transport
    pickled_result = pickle.dumps(result)

    return pickled_result


class LambdaPoolExecutor(_base.Executor):
    """Async execution of function calls on AWS Lambda"""

    def __init__(self, stage, max_workers=None, update=True, undeploy_on_del=False):
        """Initializes a new LambdaPoolExecutor instance.
        Args:
            stage: A stage name defined in zappa_settings.py

            max_workers: The maximum number of Lambda functions that can be used to
                execute the given calls. If None or not given then calls to Lambda
                functions will not be throttled.

            update: If True, update the Lambda functions on initalization
        """
        self._undeploy_on_del = undeploy_on_del

        if max_workers is None:
            self._max_workers = 1000
        else:
            if max_workers <= 0:
                raise ValueError("max_workers must be greater than 0")
            self._max_workers = max_workers

        # Initalize zappa cli
        self._zappacli = ZappaCLI()

        # TODO(or): Error handling
        # TODO(or): Don't use CLI
        if update:
            try:
                self._zappacli.handle(argv = ['deploy', stage])#, '-q'])
            except:
                self._zappacli.handle(argv = ['update', stage])#, '-q'])

        # ThreadPoolExecutor to return futures immedaitely
        self._tpe = ThreadPoolExecutor(max_workers=2)

    def submit(self, fn, *args, **kwargs):
        # Function to invoke
        fn_applied = partial(fn, *args, **kwargs)

        return self._tpe.submit(execute_on_lambda,
                               self._zappacli.zappa.lambda_client,
                               self._zappacli.lambda_name,
                               fn_applied)

    submit.__doc__ = _base.Executor.submit.__doc__

    def shutdown(self):
        if self._undeploy_on_del:
            self._zappacli.handle(argv = ['undeploy', stage, '-q'])

    shutdown.__doc__ = _base.Executor.shutdown.__doc__


PRIMES = [
    112272535095293,
    112582705942171,
    112272535095293,
    115280095190773,
    115797848077099,
    1099726899285419]

def is_prime(n):
    if n % 2 == 0:
        return False

    sqrt_n = int(math.floor(math.sqrt(n)))
    for i in range(3, sqrt_n + 1, 2):
        if n % i == 0:
            return False
    return True

def main(stage):
    with LambdaPoolExecutor(stage) as executor:
        for number, prime in zip(PRIMES, executor.map(is_prime, PRIMES)):
            print('%d is prime: %s' % (number, prime))

if __name__ == '__main__':
    main('dev')
