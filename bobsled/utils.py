import os


def all_files(dirname):
    return reduce(lambda a, b: a+b,
                  [[os.path.join(d, f) for f in filenames]
                    for d, _, filenames in  os.walk(dirname)])
