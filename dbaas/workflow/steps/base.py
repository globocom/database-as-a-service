
class BaseStep(object):
    
    def do(self, workflow_dict):
    	raise NotImplementedError

    def undo(self, workflow_dict):
    	raise NotImplementedError