"""Bridgy App Engine config.
"""

from activitystreams.appengine_config import *

DISQUS_ACCESS_TOKEN = read('disqus_access_token')
DISQUS_API_KEY = read('disqus_api_key')
DISQUS_API_SECRET = read('disqus_api_secret')
SUPERFEEDR_TOKEN = read('superfeedr_token')
SUPERFEEDR_USERNAME = read('superfeedr_username')

# Add library modules directories to sys.path so they can be imported.
#
# I used to use symlinks and munge sys.modules, but both of those ended up in
# duplicate instances of modules, which caused problems. Background in
# https://github.com/snarfed/bridgy/issues/31
for path in (
  'webmention-tools',
  ):
  path = os.path.join(os.path.dirname(__file__), path)
  if path not in sys.path:
    sys.path.append(path)

# bridgy.util overrides tag_uri() from webutil.tag_uri(). import it here so we
# know that happens everywhere tag_uri() might be used.
import util

# Twitter returns HTTP 429 for rate limiting, which webob doesn't know. Tell it.
import webob
webob.util.status_reasons[429] = 'Twitter rate limited'

# ereporter records exceptions and emails them to me.
# https://developers.google.com/appengine/articles/python/recording_exceptions_with_ereporter
# to test, open this path:
# http://localhost:8080/_ereporter?sender=ryan@brid.gy&to=ryan@brid.gy&debug=true&delete=false&date=2014-07-09
# where the date is today or tomorrow (because of UTC)
from google.appengine.ext import ereporter
import traceback

# monkey patch ereporter to combine exceptions from different versions and dates
ereporter.ExceptionRecord.get_key_name = \
    classmethod(lambda cls, signature, version, date=None: signature)

# monkey patch ereporter to blacklist some exceptions
class BlacklistingHandler(ereporter.ExceptionRecordingHandler):
  """An ereporter handler that ignores exceptions in a blacklist."""
  # Exception message prefixes to ignore
  BLACKLIST = (
    'ConnectionError: HTTPConnectionPool',
    'ConnectionError: HTTPSConnectionPool',
    'DeadlineExceededError: The API call taskqueue.BulkAdd() took too long',
    'error: An error occured while connecting to the server: Unable to fetch URL:',
    'HTTPError: HTTP Error 400: Bad Request:',
    'HTTPError: HTTP Error 500: Internal Server Error',
    'HTTPError: 404 Client Error:',
    'HTTPError: 500 Server Error: Internal Server Error',
    'HttpError: <HttpError 500 when requesting',
    'HTTPException: Deadline exceeded while waiting for HTTP response from URL:',
    'InstagramClientError: Unable to parse response, not valid JSON:',
    'InternalError: server is not responding',  # usually datastore
    'TransientError',
    )

  def emit(self, record):
    if record and record.exc_info:
      type_and_msg = traceback.format_exception_only(*record.exc_info[:2])[-1]
      for prefix in self.BLACKLIST:
        if type_and_msg.startswith(prefix):
          return
    return super(BlacklistingHandler, self).emit(record)


ereporter_logging_handler = BlacklistingHandler()
import logging
logging.getLogger().addHandler(ereporter_logging_handler)


# temporarily disabled:
# turn off ndb's in-process cache. i'd love to use it, but the frontends
# constantly hit the memory cap and get killed with it on.
# https://developers.google.com/appengine/docs/python/ndb/cache
# from google.appengine.ext import ndb
# ndb.Context.default_cache_policy = ndb.Context._cache_policy = \
#     lambda ctx, key: False

# I used a namespace for a while when I had both versions deployed, but not any
# more; I cleared out the old v1 datastore entities.
# Called only if the current namespace is not set.
# from google.appengine.api import namespace_manager
# def namespace_manager_default_namespace_for_request():
#   return 'webmention-dev'

# uncomment for app stats
# appstats_CALC_RPC_COSTS = True
# def webapp_add_wsgi_middleware(app):
#   from google.appengine.ext.appstats import recording
#   app = recording.appstats_wsgi_middleware(app)
#   return app
