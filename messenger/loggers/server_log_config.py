import logging.handlers

SERVER_LOG = logging.getLogger('client.app')
SERVER_LOG.setLevel(logging.DEBUG)

FORMATTER = logging.Formatter('%(asctime)s %(levelname)-9s'
                              ' %(module)s %(message)s')

FILE_HANDLER = logging.handlers.TimedRotatingFileHandler('server.app.log', 'D',
                                                         1, 3, encoding='utf-8')
FILE_HANDLER.setFormatter(FORMATTER)
FILE_HANDLER.setLevel(logging.DEBUG)

SERVER_LOG.addHandler(FILE_HANDLER)
SERVER_LOG.setLevel(logging.DEBUG)
