from chatterbot.logic import LogicAdapter
import json

class MyLogicAdapter(LogicAdapter):

    def __init__(self, chatbot, **kwargs):
        super(MyLogicAdapter, self).__init__(**kwargs)
        self.user = kwargs.get('user')
    
    def can_process(self, statement):
        words = ['requests', 'request','pending']
        if any(x in statement.text.split() for x in words):
            return True
        else:
            return False


    def process(self, input_statement, additional_response_selection_parameters=None):
        from chatterbot.conversation import Statement
        import sqlite3
        print('user in here is {} '.format(self.user))
        try:
            conn = sqlite3.connect('leaves.db')
            conn1 = sqlite3.connect('PO.db')
            conn2 = sqlite3.connect('PR.db')
        except Exception as e:
            print('could not connect to db due to {}'.format(e))

        # Make a request to the  API
        c = conn.cursor()
        c1 = conn1.cursor()
        c2 = conn2.cursor()
        status = 'pending'
        c.execute("SELECT * FROM leaves WHERE status = '%s'" % status)
        c1.execute("SELECT * FROM po WHERE status = (?) and approver = (?)",(status,self.user,))
        c2.execute("SELECT * FROM pr WHERE status = (?) and approver = (?)",(status,self.user,))
        no_of_pending_leavesReq = len(c.fetchall())
        no_of_pending_POReq = len(c1.fetchall())
        no_of_pending_PRReq = len(c2.fetchall())
        confidence = 1
        # Let's base the confidence value on if the request was successful
        # if response.status_code == 200:
        #     confidence = 1
        # else:
        #     confidence = 0
        if(no_of_pending_leavesReq > 0 or no_of_pending_POReq > 0 or no_of_pending_PRReq >0):
            response_statement = Statement(text='There are {} Purchase Orders , {} Purchase Requisitions and {} Leave Approvals waiting to be approved'.format(no_of_pending_POReq,no_of_pending_PRReq,no_of_pending_leavesReq))
            
        else:
            response_statement = Statement(text='No requests are pending to be approved!')
        response_statement.confidence = confidence    
        conn.close()
        conn1.close()
        conn2.close()
        return response_statement