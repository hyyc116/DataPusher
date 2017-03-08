# -*- encoding: utf-8 -*-
'''
Created on 2016/1/30
@author:chenbjin
'''

import re
import os
import time
import cookielib
import urllib2
import requests
import logging

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

class Spider(object):
	"""
		Spider for papers on Web of Science. 
	"""
	def __init__(self,url):
		super(Spider, self).__init__()
		self.SID = None
		self.cookie = None
		self.headers = None
		self.opener = None
		self.urls = []
		self._init_header()
		self._init_cookie(url)
		self._get_cookie()

	def _init_header(self):
		user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/47.0.2526.73 Chrome/47.0.2526.73 Safari/537.36'
		self.headers = { 'User-Agent': user_agent }
	
	def _init_cookie(self, url):
		logging.info("Init cookie with:"+url)
		filename = 'cookie.txt'
		cookie = cookielib.MozillaCookieJar(filename)
		handler = urllib2.HTTPCookieProcessor(cookie)
		self.opener = urllib2.build_opener(handler)
		response = self.opener.open(url)
		cookie.save(ignore_discard=True, ignore_expires=True)
	
	def _get_cookie(self):
		#cookie handler
		self.cookie = cookielib.MozillaCookieJar()
		self.cookie.load('cookie.txt',ignore_discard=True, ignore_expires=True)
		for x in self.cookie:
			if x.name == 'SID':
				self.SID = x.value
				break
		handler = urllib2.HTTPCookieProcessor(self.cookie)
		self.opener = urllib2.build_opener(handler)

	def get_sid(self):
		return self.SID.strip('"')

	def get_url_with_cookie(self, url):
		logging.info("getting url:"+url)
		request = urllib2.Request(url, headers=self.headers)
		html = None
		try:
			html = self.opener.open(request).read()
		except Exception, e:
			print e
			ep = open('exception14.txt', 'a')
			ep.write(url+'\n')
			ep.close() 
		return html

	#get url without cookie
	def get_url(self, url):
		logging.info("getting url:"+url)
		request = urllib2.Request(url, headers=self.headers)
		html = None
		try:
			html = urllib2.urlopen(request, timeout=20).read()
		except Exception, e:
			print e
			html = urllib2.urlopen(request).read()
		return html

	# find all papers link in a page
	def get_all_pages(self, html):
		self.urls = re.findall(r'<a class="smallV110" href="(.*?)"',html)

	def return_all_pages(self, html):
		return re.findall(r'<a class="smallV110" href="(.*?)"',html)



