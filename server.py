#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  server.py
#  
#  Copyright 2016 kova <kova@kova-vm>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

from gevent import monkey; monkey.patch_all()
from gevent import sleep

from bottle import get, post, request, response
from bottle import GeventServer, run

import beanstalkc

beanstalk = beanstalkc.Connection(host='localhost', port=11300)
counter = 0

@get ('/enqueue')
def enqueue():
	global beanstalk, counter
	
	for i in range(5):
		data = "This is a message: %d" % counter
		beanstalk.put(data)
		counter += 1
		
	response.content_type = 'application/json'
	response.headers['Access-Control-Allow-Origin'] = '*'
	return { "status": "OK" }
	

@get('/datastream')
def datastream():
	print "Stream Connection!\n"
	global beanstalk
	
	response.content_type  = 'text/event-stream;charset=UTF-8'
	response.cache_control = 'no-cache'
	response.headers['Access-Control-Allow-Origin'] = '*'
	
	yield 'retry: 10000\r\n'
	
	while beanstalk.peek_ready() is not None:
		job = beanstalk.reserve()
		
		yield 'data: %s\r\n\n' % job.body
		print "Yielded: %s" % job.body

		job.delete()	
		sleep(6)

if __name__ == '__main__':
	run(server=GeventServer)
