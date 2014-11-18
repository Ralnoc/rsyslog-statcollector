#!/bin/env python2.6

import datetime
import time
import optparse
import os
import re
import signal
import socket
import string
import sys
from collections import defaultdict
from macpath import basename


####
# DO NOT CHANGE
__reload = False
####

def timeit(method):
  def timed(*args, **kw):
    ts = time.time()
    result = method(*args, **kw)
    te = time.time()
    print '%r %10f sec' % \
          (method.__name__, te-ts)
    return result
  return timed

def timeit_detailed(method):
  def timed(*args, **kw):
    ts = time.time()
    result = method(*args, **kw)
    te = time.time()
    print '%r (%r, %r) %2.2f sec' % \
          (method.__name__, args, kw, te-ts)
    return result
  return timed

def get_options():
  parser = optparse.OptionParser(version='%prog 0.5',
      description='This tool converts rsyslog impstats ' +
      'processed through the rsyslog per interval based on the output ' +
      'and submits them into graphite.')

  parser.add_option('-f', action='store', dest='file', type='string',
      metavar='</PATH/TO/STATS/FILE>', default=False,
      help='Path and filename for stats file')

  parser.add_option('-s', action='store', dest='server', type='string',
      metavar='<servername>:<port>', default=False,
      help='Destination Graphite server.')

  parser.add_option('-m', action='store', dest='metric_root', type='string',
      metavar='base.metric.path', default=False,
      help='Metric base path for Graphite.')

  (opts, args) = parser.parse_args()
  miss_error = '\nSee "' + basename(__file__) + ' -h" for help.'

  if opts.file:
    pass
  else:
    parser.error('Please specify a stats file to process.' + miss_error)

  return (opts, args)

def errhandler(err):
  raise err

def SIGQUITHandler(signum, frame):
  print 'Shutting down process....'
  sys.exit(0)

def SIGReloadHandler(signum, frame):
  global __reload
  print 'Reopening stat file....'
  __reload = True
  
def gen_metrics(line):
  #print 'Generating Metrics'
  global __prev_stats_dict
  _stats_dict = {}

  raw_list = line.split(': ')
  _stats_timestamp = raw_list[0]
  _stats_server = socket.getfqdn().replace('.','_')
  stat_msg = [raw_list[1].strip().translate(string.maketrans('-(', '_.'), '*/-)').strip(), ' '.join(raw_list[2:]).translate(string.maketrans('-', '_'), '()*/.-').strip()]
  stat_msg[0] = stat_msg[0].translate(string.maketrans(' ', '_'), ':')
  stat_msg[1] = dict((k, int(v)) for k, v in [x.split('=') for x in stat_msg[1].strip().split(' ')])
  for k, v in stat_msg[1].iteritems():
    metric_name = stat_msg[0] + '.' + k
    _stats_dict[metric_name] = v
  return (_stats_timestamp, _stats_server, _stats_dict)

def submit(metric_root, filename, metrics, server):
  graphite_server = server.split(':')
  graphite_socket = {'socket': socket.socket( socket.AF_INET, socket.SOCK_STREAM ), 'host': graphite_server[0], 'port': int(graphite_server[1])}
  time_struct = time.strptime(metrics[0])
  time_epoch = time.mktime(time_struct)
  try:
    graphite_socket['socket'].connect( ( graphite_socket['host'], int( graphite_socket['port'] ) ) )
  except socket.error, serr:
    print 'Connection to Graphite server failed: ' + str(serr)

  for metric_name, metric_value in metrics[2].iteritems():
    if metric_value < 0:
      metric_value = 0
    metric_string = "%s %s %d" % ( metric_root + '.' + metrics[1] + '.'  + filename.split('.')[0] + '.' + metric_name, metric_value, time_epoch )
    try:
      #print 'Metric String: %s' % (metric_string,)
      graphite_socket['socket'].send( "%s\n" % metric_string )
    except socket.error:
      pass


def main(options, arguments):
  global __reload

  signal.signal(signal.SIGINT, SIGQUITHandler)
  signal.signal(signal.SIGHUP, SIGReloadHandler)

  fd = open(options.file, 'r')
  fd.seek(0, os.SEEK_END)

  while True:

    for line in fd.readlines():
      metrics = gen_metrics(line)
      submit(metric_root=options.metric_root, filename=options.file.split('/')[-1], metrics=metrics, server=options.server)
    else:
      time.sleep(10)

    if __reload == True:
        fd.close()
        fd = open(options.file, 'r')
        fd.seek(0, os.SEEK_END)
        __reload = False

if __name__ == '__main__':
  opts, args = get_options()
  main(opts, args)
