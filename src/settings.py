# -*- coding: utf-8 -*-
import logging
import utilit


config_file = 'src/config.json'
logging_level = logging.INFO
logging_format = '%(asctime)s : %(levelname)s : %(module)s : %(funcName)s : %(threadName)s : %(message)s'


utilit.setup_settings()
