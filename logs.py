"""Handlers and utilities for exposing app logs to users.
"""

import datetime
import logging
import re
import urllib

import appengine_config
import util

from google.appengine.api import logservice
import webapp2


LEVELS = {
  logservice.LOG_LEVEL_DEBUG:    'D',
  logservice.LOG_LEVEL_INFO:     'I',
  logservice.LOG_LEVEL_WARNING:  'W',
  logservice.LOG_LEVEL_ERROR:    'E',
  logservice.LOG_LEVEL_CRITICAL: 'F',
  }

def sanitize(msg):
  """Sanitizes access tokens and Authorization headers."""
  return re.sub('((?:oauth|access)?[ _]?(?:token|verifier|secret)[:= ])[^ &=]+', r'\1...',
                msg)


class LogHandler(webapp2.RequestHandler):
  """Searches for and renders the app logs for a single task queue request.
  """

  def get(self):
    """URL parameters:
      start_time: float, seconds since the epoch
      key: string that should appear in the first app log
    """
    start_time = float(util.get_required_param(self, 'start_time'))
    key = urllib.unquote(util.get_required_param(self, 'key'))

    self.response.headers['Content-Type'] = 'text/plain; charset=utf-8'

    offset = None
    for log in logservice.fetch(start_time=start_time, end_time=start_time + 120,
                                offset=offset, include_app_logs=True,
                                version_ids=['2', '3', '4', '5', '6', '7']):
      first_lines = '\n'.join([line.message.decode('utf-8') for line in
                               log.app_logs[:min(2, len(log.app_logs))]])
      if log.app_logs and key in first_lines:
        # found it! render and return
        self.response.out.write(sanitize(log.combined))
        self.response.out.write('\n\n')
        for a in log.app_logs:
          self.response.out.write('%s %s %s\n' %
              (datetime.datetime.utcfromtimestamp(a.time), LEVELS[a.level],
               sanitize(a.message)))
        return

      offset = log.offset

    self.response.out.write('No log found!')


application = webapp2.WSGIApplication([
    ('/log', LogHandler),
    ], debug=appengine_config.DEBUG)
