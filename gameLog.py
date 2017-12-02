class Logger:
	def __init__(self, level, searchForKeywords=[]):
		''' TODO: Colors '''
		self.logLevel = level
		self.keywords = searchForKeywords
	def println(self, msg, level, keywords=[]):
		if self.keywords:
			for keyword in self.keywords:
				if keyword in keywords:
					break
			else:
				return
		if level < self.logLevel:
			return
		print keywords,msg
