# -*- coding: utf-8 -*-
import logging
import utilit


__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = "Copyright © 2019"
__license__ = "MIT License"
__version__ = [0, 0]


config_file = 'src/config.json'
logging_level = logging.INFO
logging_format = '%(asctime)s : %(levelname)s : %(module)s : %(threadName)s : %(funcName)s : %(message)s'


utilit.setup_settings()
