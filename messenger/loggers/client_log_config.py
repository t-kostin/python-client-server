import logging

CLIENT_LOG = logging.getLogger('client.app')
CLIENT_LOG.setLevel(logging.DEBUG)

FORMATTER = logging.Formatter('%(asctime)s %(levelname)-9s %(module)s %(message)s')
STREAM_FORMAT = logging.Formatter('%(module)s: %(message)s')

STREAM_HANDLER = logging.StreamHandler()
STREAM_HANDLER.setFormatter(STREAM_FORMAT)
STREAM_HANDLER.setLevel(logging.CRITICAL)

FILE_HANDLER = logging.FileHandler('client.app.log', encoding='utf-8')
FILE_HANDLER.setFormatter(FORMATTER)
FILE_HANDLER.setLevel(logging.DEBUG)

CLIENT_LOG.addHandler(FILE_HANDLER)
CLIENT_LOG.addHandler(STREAM_HANDLER)
CLIENT_LOG.setLevel(logging.DEBUG)
