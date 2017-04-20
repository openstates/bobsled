import os
import shutil
import zipfile
import tempfile
import boto3
import botocore

from .utils import all_files


def bobsled_to_zip(zipfilename):
    tmpdir = tempfile.mkdtemp()
    dirname = os.path.dirname(os.path.dirname(__file__))
    os.system('pip install {} -t {}'.format(dirname, tmpdir))

    with zipfile.ZipFile(zipfilename, 'w') as zf:
        filenames = all_files(tmpdir)
        for filename in filenames:
            afilename = filename.replace(tmpdir + '/', '')
            if not afilename.endswith('.pyc') and not afilename.startswith('boto'):
                afilename = filename.replace(tmpdir + '/', '')
                print(afilename)
                zf.write(filename, afilename)

    shutil.rmtree(tmpdir)


def publish_function(name, handler, description, environment,
                     timeout=3, delete_first=False):
    lamb = boto3.client('lambda', region_name='us-east-1')

    zipfilename = '/tmp/bobsled.zip'

    bobsled_to_zip(zipfilename)

    try:
        lamb.get_function(FunctionName=name)
    except botocore.exceptions.ClientError:
        print('creating function', name)
        lamb.create_function(FunctionName=name,
                             Runtime='python3.6',
                             Role=os.environ['BOBSLED_LAMBDA_ROLE'],
                             Handler=handler,
                             Code={'ZipFile': open(zipfilename, 'rb').read()},
                             Description=description,
                             Timeout=timeout,
                             Environment={
                                 'Variables': environment
                             },
                             Publish=True)
    else:
        # runs if there is no error getting the function (i.e. it exists)
        print('updating function code', name)
        lamb.update_function_code(FunctionName=name,
                                  ZipFile=open(zipfilename, 'rb').read(),
                                  Publish=True,
                                  )
        print('updating function config', name)
        lamb.update_function_configuration(FunctionName=name,
                                           Role=os.environ['BOBSLED_LAMBDA_ROLE'],
                                           Runtime='python3.6',
                                           Handler=handler,
                                           Description=description,
                                           Timeout=timeout,
                                           Environment={
                                               'Variables': environment
                                           },
                                           )
