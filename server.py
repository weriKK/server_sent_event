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


counter = 0

@get ('/enqueue')
def enqueue():
	global counter
	
	beanstalk = beanstalkc.Connection(host='localhost', port=11300)
	
	for i in range(5):
		data = 'This is a message: %d' % counter
		
		beanstalk.use('client1')
		beanstalk.put(data)
		
		beanstalk.use('client2')
		beanstalk.put(data)
				
		counter += 1
		
	print '-!- Enqueued 5 messages'
		
	response.content_type = 'application/json'
	response.headers['Access-Control-Allow-Origin'] = '*'
	return { "status": "OK" }
	

@get('/datastream/<client_id>')
def datastream(client_id):
	print "--> Client connected: %s" % client_id
	
	beanstalk = beanstalkc.Connection(host='localhost', port=11300)
	
	response.content_type  = 'text/event-stream;charset=UTF-8'
	response.cache_control = 'no-cache'
	response.headers['Access-Control-Allow-Origin'] = '*'
	
	yield 'retry: 10000\r\n'
	
	beanstalk.watch(client_id)
	beanstalk.ignore('default')
	
	while True:
		# reserve blocks until a job is ready, or after 5 seconds it
		# times out and returns None
		job = beanstalk.reserve(5)
		if job is not None:
		
			yield 'data: %s\r\n\n' % job.body
			print '<-- %s: %s' % (client_id, job.body)

			job.delete()
			sleep(1)	
		else:
			print '<-- %s: heartbeat' % client_id
			yield ': heartbeat\n\n'
		
		
if __name__ == '__main__':
	run(server=GeventServer)
