import os
import errno
import logging
from datetime import datetime


class Base:
    logger = None
    tmp_dir = ''
    def __init__(self, project_tag: str, basepath: str, file_log: bool = True)->None:
        if Base.logger is None:
            Base.logger = logging.getLogger(f'{project_tag}')
            Base.logger.setLevel(logging.INFO)
            c_handler = logging.StreamHandler()
            c_handler.setLevel(logging.INFO)
            c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
            c_handler.setFormatter(c_format)
            Base.logger.addHandler(c_handler)
            base_dir = os.path.abspath(basepath)
            Base.tmp_dir = Base.mkdir_p(os.path.join(base_dir, 'tmp'))
            if file_log:
                log_file_name = f"{project_tag}_{datetime.utcnow().strftime('%Y%m%d')}.log"
                log_dir = Base.mkdir_p(os.path.join(base_dir, 'log'))
                f_handler = logging.FileHandler(os.path.join(log_dir, log_file_name))
                f_handler.setLevel(logging.INFO)
                f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                f_handler.setFormatter(f_format)
                Base.logger.addHandler(f_handler)

    @staticmethod
    def mkdir_p(path):
        created_path = ''
        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise
        else:
            created_path = path
        finally:
            return created_path





