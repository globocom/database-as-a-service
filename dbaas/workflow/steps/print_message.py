from base import BaseStep

class ClassPrintMessage(BaseStep):

	def do(self, workflow_dict):
		print workflow_dict['message']
		workflow_dict['test'] = 1
		return True

	def undo(self, workflow_dict):
		print "Executando undo"
		return True



class ClassPrintNumber(BaseStep):

	def do(self, workflow_dict):
		try:
			raise Exception, "Exception raised"
		except Exception,e:
			print e
			return False
			
		

	def undo(self, workflow_dict):
		print "Undoing the proccess"


