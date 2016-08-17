import logging

def get_logger(logger_name):
    FORMAT = '%(module)s-%(levelname)s--%(asctime)-15s %(message)s'
    logging.basicConfig(format=FORMAT,level=logging.INFO)
    logger=logging.getLogger(logger_name)
    return logger

