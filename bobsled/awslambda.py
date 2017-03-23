import os
import shutil
import zipfile
import tempfile
import boto3
import botocore
from .config import load_config


def bobsled_to_zip(zipfilename):
    tmpdir = tempfile.mkdtemp()
    dirname = os.path.dirname(os.path.dirname(__file__))
    os.system('pip install {} -t {}'.format(dirname, tmpdir))

    with zipfile.ZipFile(zipfilename, 'w') as zf:
        filenames = reduce(lambda x, y: x+y,
                           ([os.path.join(d, f) for f in files]
                           for d, _, files in os.walk(tmpdir)))
        for filename in filenames:
            if not filename.endswith('.pyc'):
                afilename = filename.replace(tmpdir + '/', '')
                print(afilename)
                zf.write(filename, afilename)

    shutil.rmtree(tmpdir)


def publish_function(name, handler, description, timeout=3,
                     delete_first=False):
    lamb = boto3.client('lambda', region_name='us-east-1')
    config = load_config()

    zipfilename = '/tmp/bobsled.zip'

    bobsled_to_zip(zipfilename)

    if delete_first:
        try:
            lamb.delete_function(FunctionName=name)
        except botocore.exceptions.ClientError:
            pass
    lamb.create_function(FunctionName=name,
                         Runtime='python2.7',
                         Role=config['aws']['lambda_role'],
                         Handler=handler,
                         Code={'ZipFile': open(zipfilename, 'rb').read()},
                         Description=description,
                         Timeout=timeout,
                         Publish=True)
