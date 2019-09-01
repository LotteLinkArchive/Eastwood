"""
B I N C A C H E

Naphtha's library for identifying and caching binary objects.

(Aaa! This one is so much more simpler than Plasma, it's scary!)
"""

import sqlite3, threading, time

class Cache(object):
	def __init__(self, elements: int = 8192, path: str = ':memory:', gctime: int = 4):
		self.connection = sqlite3.connect(path)
		self.cursor = self.connection.cursor()
		self.limit = elements
		self.gctime = gctime
		self.last_gc = time.time()
		
		self.cursor.execute('CREATE TABLE IF NOT EXISTS elements (identifier BLOB, accessed INTEGER, data BLOB);')
		try:
			self.cursor.execute('CREATE UNIQUE INDEX idx_elements_accessed ON elements (accessed);')
		except:
			pass
			
		self.connection.commit()
							
	def __regcall(self):
		if time.time() - self.last_gc > self.gctime:
			self.cursor.execute('DELETE FROM elements WHERE accessed IN (SELECT accessed FROM elements ORDER BY accessed DESC LIMIT -1 OFFSET {0});'.format(self.limit))
			self.connection.commit()
			self.last_gc = time.time()

	def __del__(self):
		self.connection.commit()
		self.connection.close()
							
	def insert(self, identifier: bytes, data: bytes):
		self.cursor.execute('INSERT OR REPLACE INTO elements (identifier, accessed, data) VALUES (?, ?, ?);', (identifier, time.time(), data))
		self.__regcall()
		
	def destroy(self, identifier: bytes):
		self.cursor.execute('DELETE FROM elements WHERE identifier = ?', (identifier,))
		self.__regcall()
		
	def update(self, identifier: bytes, data: bytes):
		self.insert(identifier, data)
		self.__regcall()
		
	def get(self, identifier: bytes):		
		self.cursor.execute('SELECT * FROM elements WHERE identifier = ?', (identifier,))
		
		try:
			t = self.cursor.fetchone()[0]
		except:
			return None
			
		self.cursor.execute('UPDATE elements SET accessed = ? where identifier = ?', (time.time(), identifier))
		self.__regcall()
		
		return t
