from chatterbot.logic import LogicAdapter
import json
import re
import sqlite3

class MyLogicAdapter(LogicAdapter):

    def __init__(self, chatbot, **kwargs):
        super(MyLogicAdapter, self).__init__(**kwargs)
        self.user = kwargs.get('user')
        try:
             conn2 = sqlite3.connect('PO.db')
             c2 = conn2.cursor()
             c2.execute("select approver from po where approver = (?)",(self.user,))
             if len(c2.fetchall()) < 1:
                 self.user = "user1"
        except Exception as e:
            print("could not connect due to {}".format(e))
    
    def can_process(self, statement):
        words = ['approve','approved','reject','approved approved','next','next next','skip','pos','po','prs','pr','leaves','leave','purchase']
        if any(x in statement.text.lower().split() for x in words):
            return True
        else:
            return False


    def process(self, input_statement, additional_response_selection_parameters=None):
        from chatterbot.conversation import Statement
        print('user')
        prs_matching = ['PR','PRS','pr','prs','Prs','Pr','purchase requisition','purchase requisitions','requisitions','requisition']
        pos_matching = ['PO','POS','po','pos','Po','Pos','purchase order','purchase orders','orders','order']
        leaves_matching = ['leave','leaves','LEAVE','LEAVES']
        approved_matching = ['approved','approve','Approve','Approved','APPROVED','Approved Approved','approved approved','APPROVED APPROVED']
        next_matching = ['next','skip','proceed']
        reject_matching = ['reject','no']
        try:
            conn = sqlite3.connect('savestates.db')
            conn1 = sqlite3.connect('PR.db')
            conn2 = sqlite3.connect('PO.db')
            conn3 = sqlite3.connect('leaves.db')
        except Exception as e:
            print('could not connect to db due to {}'.format(e))
        # Make a request to the  API
        c = conn.cursor()
        c1 = conn1.cursor()
        c2 = conn2.cursor()
        c3 = conn3.cursor()
        typeOfReq = ''
        result = ''        
        c.execute("CREATE TABLE IF NOT EXISTS savestates (user text,type text,previndex integer,nextindex integer)")
        if any(x in input_statement.text.split() for x in approved_matching):
            print('approved')
            c.execute("SELECT type FROM savestates where user = (?) ORDER BY rowid DESC LIMIT 1;",(self.user,))
            typeOfReq = c.fetchone()
            print(typeOfReq)
            if typeOfReq != None:
                if 'PR' in typeOfReq :
                   result = self.acceptPr(c,c1)  
                elif 'PO' in typeOfReq :
                    result = self.acceptPo(c,c2)
                elif 'LEAVE' in typeOfReq:
                    result = self.acceptLeave(c,c3)
            else:
                result = "Sorry!!The list is over.Please select some other request type."
        elif any(x in input_statement.text.lower().split() for x in reject_matching):
            print('reject')
            c.execute("SELECT type FROM savestates where user = (?) ORDER BY rowid DESC LIMIT 1;",(self.user,))
            typeOfReq = c.fetchone()
            print(typeOfReq)
            if typeOfReq != None:
                if 'PR' in typeOfReq :
                   result = self.rejectPr(c,c1)  
                elif 'PO' in typeOfReq :
                    result = self.rejectPo(c,c2)
                elif 'LEAVE' in typeOfReq:
                    result = self.rejecttLeave(c,c3)
            else:
                result = "Sorry!!The list is over.Please select some other request type."
        elif any(x in input_statement.text.split() for x in next_matching):
            c.execute("SELECT type FROM savestates where user = (?) ORDER BY rowid DESC LIMIT 1;",(self.user,))
            typeOfReq = c.fetchone()
            print(typeOfReq)
            if typeOfReq != None:
                if 'PR' in typeOfReq :
                    result = self.nextPr(c,c1)
                elif 'PO' in typeOfReq :
                    result = self.nextPO(c,c2)
                elif 'LEAVE' in typeOfReq:
                    result = self.nextLeave(c,c3)
            else:
                result = "Sorry!!The list is over.Please select some other request type."
        else:
            if any(x in input_statement.text.split() for x in prs_matching):
                typeOfReq = 'PR'
                c.execute("INSERT INTO savestates VAlUES ((?),(?),(?),(?))",(self.user,typeOfReq,1,1))
                c1.execute("SELECT * FROM pr where status = 'pending' and approver = (?) LIMIT 1 Offset 0;",(self.user,))
                fetched = c1.fetchone()
                print(fetched)
                if fetched[6] > 1:
                    item = fetched[5]+'s'
                else:
                    item = fetched[5]
                result = "The first Purchase requisition has been raised by "+fetched[1]+" for "+str(fetched[6])+" "+item+" to be delivered by "+fetched[4]+"."
            elif any(x in input_statement.text.split() for x in pos_matching):
                typeOfReq = 'PO'
                c.execute("INSERT INTO savestates VAlUES ((?),(?),(?),(?))",(self.user,typeOfReq,1,1))
                c2.execute("SELECT * FROM po where status = 'pending' and approver = (?)  LIMIT 1 Offset 0;",(self.user,))
                fetched = c2.fetchone()
                print(fetched)
                if fetched[3] > 1 :
                    item = fetched[2]+'s'
                else:
                    item = fetched[2]
                result = "The first Purchase order has been raised by, "+fetched[1]+" for "+str(fetched[3])+" "+item+" from "+fetched[4]+" amounting to a total of "+str(fetched[5])+" "+fetched[7]+"."
            elif any(x in input_statement.text.split() for x in leaves_matching):
                typeOfReq = 'LEAVE'
                c.execute("INSERT INTO savestates VAlUES ((?),(?),(?),(?))",(self.user,typeOfReq,1,1))
                c3.execute("SELECT * FROM leaves where status = 'pending' LIMIT 1 Offset 0;")
                fetched = c3.fetchone()
                print(fetched)
                result = "The first leave request has been raised by, "+fetched[1]+" from "+fetched[2]+" till "+fetched[3]+"."
        conn.commit()
        conn1.commit()
        conn2.commit()
        conn3.commit()
        response_statement = Statement(text='{}'.format(result))
        confidence = 1
        # Let's base the confidence value on if the request was successful
        # if response.status_code == 200:
        #     confidence = 1
        # else:
        #     confidence = 0
        response_statement.confidence = confidence
        conn.close()
        conn1.close()
        conn2.close()
        conn3.close()
        return response_statement
    def nextPr(self,c,c1):
        print('next PR')
        c.execute("SELECT previndex from savestates where type = 'PR' and user = (?) LIMIT 1",(self.user,))
        prevIndex = c.fetchall()[0][0]
        c1.execute("select rowid from pr where status = 'pending' and rowid > (?) and approver = (?) LIMIT 1;",(prevIndex,self.user))
        record = c1.fetchall()
        print(record)
        print(len(record))
        if len(record) == 0 :
            result = "That's it"
            c.execute("DELETE FROM savestates WHERE type = 'PR' and user = (?)",(self.user,))
            return result
        else:
            offset = record[0][0]
            if offset < prevIndex:
                result = "That's it"
                c.execute("DELETE FROM savestates WHERE type = 'PR' and user = (?)",(self.user,))
                return result
            print("offset : {}".format(offset))
            c.execute("UPDATE savestates SET nextindex = (?),previndex = (?) WHERE type = 'PR' and user = (?)",
                                                (offset+1,offset,self.user,))
            c1.execute("SELECT * FROM pr where rowid = (?);",(offset,))
            result = c1.fetchone()
            if result[6] > 1:
                item= result[5]+'s'
            else:
                item = result[5]
            text = "Next Purchase requisition has been raised by "+result[1]+" for "+str(result[6])+" "+item+" to be delivered by "+result[4]+"."
            return text
        return result
    def nextPO(self,c,c2):
        c.execute("SELECT previndex from savestates where type = 'PO' and user = (?) LIMIT 1",(self.user,))
        prevIndex = c.fetchall()[0][0]
        print(" PO "+str(prevIndex))
        print('for user {}'.format(self.user))
        c2.execute("select rowid from po where status = 'pending' and rowid > (?) and approver = (?) LIMIT 1;",(prevIndex,self.user,))
        record = c2.fetchall()
        print("record for po")
        print(record)
        print(len(record))
        if len(record) == 0 :
            result = "That's all!"
            c.execute("DELETE FROM savestates WHERE type = 'PO' and user = (?);",(self.user,))
            return result
        else:
            offset = record[0][0]
            if offset < prevIndex:
                result = "That's all!"
                c.execute("DELETE FROM savestates WHERE type = 'PO' and user = (?)",(self.user,))
                return result
            print("offset : {}".format(offset))
            c.execute("UPDATE savestates SET nextindex = (?),previndex = (?) WHERE type = 'PO' and user = (?)",
                                                (offset+1,offset,self.user,))
            c2.execute("SELECT * FROM po where rowid = (?);",(offset,))
            result = c2.fetchone()
            if result[3] > 1 :
                item = result[2]+'s'
            else:
                item = result[2]
            text = "Next Purchase order has been raised by "+result[1]+" for "+str(result[3])+" "+item+" from "+result[4]+" amounting to a total of "+str(result[5])+" "+result[7]+"."
            return text
        return result
    def nextLeave(self,c,c3):
        c.execute("SELECT previndex from savestates where type = 'LEAVE' LIMIT 1")
        prevIndex = c.fetchall()[0][0]
        c3.execute("select rowid from leaves where status = 'pending' and rowid > (?)  LIMIT 1;",(prevIndex,))        
        record = c3.fetchall()
        print(record)
        print(len(record))
        if len(record) == 0 :
            result = "That's all!"
            c.execute("DELETE FROM savestates WHERE type = 'LEAVE'")
            return result
        else:
            offset = record[0][0]
            if offset < prevIndex:
                result = "That's all"
                c.execute("DELETE FROM savestates WHERE type = 'LEAVE'")
                return result
            print("offset : {}".format(offset))
            c.execute("UPDATE savestates SET nextindex = (?),previndex = (?) WHERE type = 'LEAVE'",
                                                (offset+1,offset))
            c3.execute("SELECT * FROM leaves where rowid = (?);",(offset,))
            result = c3.fetchone()    
            text = "Next leave request has been raised by "+result[1]+" from "+result[2]+" till "+result[3]+"."
            return text
        return result
    def acceptPo(self,c,c2):
        print('Accept PO')
        row = c.execute("SELECT previndex from savestates where type = 'PO' and user = (?) LIMIT 1;",(self.user,))
        for offsets in row:
            offset = offsets[0]
        print(offset)
        result = self.nextPO(c,c2)
        c2.execute("UPDATE po SET status = 'accepted' where rowid = (?)",(offset,))
        approved = "Ok!This PO has been approved"
        return approved+"#"+result
    def acceptPr(self,c,c1):
        print('accept PR')
        row = c.execute("SELECT previndex from savestates WHERE type = 'PR' and user = (?) LIMIT 1;",(self.user,))
        for offsets in row:
            offset = offsets[0]
        print(offset)
        result = self.nextPr(c,c1)
        c1.execute("UPDATE pr SET status = 'accepted' where rowid = (?)",(offset,))
        approved = "Ok!This PR has been approved"
        return approved+"#"+result
    def acceptLeave(self,c,c3):
        print('accept Leave')
        row = c.execute("SELECT previndex from savestates where type = 'LEAVE' and user = (?) LIMIT 1;",(self.user,))
        for offsets in row:
            offset = offsets[0]
        print(offset)
        result = self.nextLeave(c,c3)
        c3.execute("UPDATE leaves SET status = 'accepted' where rowid = (?)",(offset,))
        print(result)
        approved = "Ok!This Leave request has been approved"
        return approved+"#"+result
    def rejectPo(self,c,c2):
        print('Reject PO')
        row = c.execute("SELECT previndex from savestates where type = 'PO' and user = (?) LIMIT 1;",(self.user,))
        for offsets in row:
            offset = offsets[0]
        print(offset)
        result = self.nextPO(c,c2)
        c2.execute("UPDATE po SET status = 'reject' where rowid = (?)",(offset,))
        rejected = "Ok!This PO has been rejected"
        return rejected+"#"+result
    def rejectPr(self,c,c1):
        print('reject PR')
        row = c.execute("SELECT previndex from savestates WHERE type = 'PR' and user = (?) LIMIT 1;",(self.user,))
        for offsets in row:
            offset = offsets[0]
        print(offset)
        result = self.nextPr(c,c1)
        c1.execute("UPDATE pr SET status = 'reject' where rowid = (?)",(offset,))
        rejected = "Ok!This PR has been rejected"
        return rejected+"#"+result
    def rejecttLeave(self,c,c3):
        print('reject Leave')
        row = c.execute("SELECT previndex from savestates where type = 'LEAVE' and user = (?) LIMIT 1;",(self.user,))
        for offsets in row:
            offset = offsets[0]
        print(offset)
        result = self.nextLeave(c,c3)
        c3.execute("UPDATE leaves SET status = 'reject' where rowid = (?)",(offset,))
        rejected = "Ok!This Leave request has been rejected"
        return rejected+"#"+result
    