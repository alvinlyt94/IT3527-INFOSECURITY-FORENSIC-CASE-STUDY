import subprocess
import os
import sys
import StringIO
import cPickle as pickle
import logging

#change current working directory to the folder the script is executing from 
AppBinPath = os.path.dirname(os.path.realpath(sys.argv[0]))

logFile = os.path.join(AppBinPath, 'sqlextract.log')
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)s %(levelname)s %(message)s',
                    filename=logFile)
logger = logging.getLogger(__name__)

class CheckPointManager(object):
    def __init__(self):
        self.last_id_file = os.path.join(AppBinPath,'lastidcheckpoint')
    
    def save(self, table, lastID):
        if not lastID > 0:
            return
        if os.path.exists(self.last_id_file) and os.path.getsize(self.last_id_file) > 0:
            with file(self.last_id_file, 'r') as f:
                cp = pickle.load(f)
            with file(self.last_id_file, 'w') as f:
                if not 'SMDF' in cp:
                    cp['SMDF'] = {}
                cp['SMDF'][table] = lastID
                pickle.dump(cp, f)
                logger.info('Saved last {0} id: {1}'.format(table, lastID))
        else:
            cp = {'SMDF': {table: lastID}}
            with file(self.last_id_file, 'w') as f:
                pickle.dump(cp, f)
                logger.info('Saved last {0} id: {1}'.format(table, lastID))
                        
    
    def load(self):
        cp = {}
        if os.path.exists(self.last_id_file) and os.path.getsize(self.last_id_file) > 0:
            with file(self.last_id_file, 'r') as f:
                cp = pickle.load(f)
                cp = cp.get('SMDF', {})
        return cp

class SQLExtract(object):
    sqlite_path = ""
    
    def __init__(self):
        self.sqlite_path = os.path.join(AppBinPath, "SMDF.sqlite")
        
    def start(self):
        cpmgr = CheckPointManager()
        cp = cpmgr.load()
        
        #Device table
        where = 'WHERE deviceID > {0}'.format(cp.get('Device')) if cp.get('Device') else ''
        sql = 'SELECT * FROM Device {0}'.format(where)
        events_arr = self.read_sqlite(self.sqlite_path, sql)
        for i in range(0, len(events_arr), 7):
            deviceID = str.strip(events_arr[i]).split(' = ')[1]
            OS = (str.strip(events_arr[i+1]).split(' = '))[1]
            manufacturer = str.strip(events_arr[i+2]).split(' = ')[1]
            model = str.strip(events_arr[i+3]).split(' = ')[1]
            serialNumber = str.strip(events_arr[i+4]).split(' = ')[1]
            IMEI = str.strip(events_arr[i+5]).split(' = ')[1]
            timeExtracted = str.strip(events_arr[i+6]).split(' = ')[1]
            print '{0} OS="{1}" Manufacturer="{2}" Model="{3}" \
SerialNumber="{4}" IMEI="{5}" Type="Device"'.format(timeExtracted,
                                                       OS,
                                                       manufacturer,
                                                       model,
                                                       serialNumber,
                                                       IMEI)
        if events_arr != []:
            lastID_sql = 'SELECT max(deviceID) FROM Device'
            lastID = self.read_last_id(self.sqlite_path, lastID_sql)
            cpmgr.save('Device', lastID)
        
        #ContactEmail table
        where = 'AND ContactEmail.contactEmailID > {0}'.format(cp.get('ContactEmail')) if cp.get('ContactEmail') else ''
        sql = 'SELECT Device.timeExtracted, Device.serialNumber, Contact.contactName, \
ContactEmail.emailType, ContactEmail.email \
FROM Device, Contact, ContactEmail WHERE Device.deviceID = Contact.deviceID \
AND Contact.contactID = ContactEmail.contactID {0}'.format(where)
        events_arr = self.read_sqlite(self.sqlite_path, sql)
        for i in range(0, len(events_arr), 5):
            timeExtracted = str.strip(events_arr[i]).split(' = ')[1]
            serialNumber = (str.strip(events_arr[i+1]).split(' = '))[1]
            contactName = str.strip(events_arr[i+2]).split(' = ')[1]
            emailType = str.strip(events_arr[i+3]).split(' = ')[1]
            email = str.strip(events_arr[i+4]).split(' = ')[1]
            print '{0} SerialNumber="{1}" ContactName="{2}" EmailType="{3}" Email="{4}" \
Type="ContactEmail"'.format(timeExtracted,
                            serialNumber,
                            contactName,
                            emailType,
                            email)
        if events_arr != []:
            lastID_sql = 'SELECT max(contactEmailID) FROM ContactEmail'
            lastID = self.read_last_id(self.sqlite_path, lastID_sql)
            cpmgr.save('ContactEmail', lastID)
            
        #ContactNumber table
        where = 'AND ContactNumber.contactNumberID > {0}'.format(cp.get('ContactNumber')) if cp.get('ContactNumber') else ''
        sql = 'SELECT Device.timeExtracted, Device.serialNumber, Contact.contactName, \
ContactNumber.numberType , ContactNumber.number \
FROM Device, Contact, ContactNumber WHERE Device.deviceID = Contact.deviceID \
AND Contact.contactID = ContactNumber.contactID {0}'.format(where)
        events_arr = self.read_sqlite(self.sqlite_path, sql)
        for i in range(0, len(events_arr), 5):
            timeExtracted = str.strip(events_arr[i]).split(' = ')[1]
            serialNumber = (str.strip(events_arr[i+1]).split(' = '))[1]
            contactName = str.strip(events_arr[i+2]).split(' = ')[1]
            numberType = str.strip(events_arr[i+3]).split(' = ')[1]
            number = str.strip(events_arr[i+4]).split(' = ')[1]
            print '{0} SerialNumber="{1}" ContactName="{2}" NumberType="{3}" Number="{4}" \
Type="ContactNumber"'.format(timeExtracted,
                            serialNumber,
                            contactName,
                            numberType,
                            number)
        if events_arr != []:
            lastID_sql = 'SELECT max(contactNumberID) FROM ContactNumber'
            lastID = self.read_last_id(self.sqlite_path, lastID_sql)
            cpmgr.save('ContactNumber', lastID)
        
        
        #ContactDetails table
        where = 'AND ContactDetails.contactDetailsID > {0}'.format(cp.get('ContactDetails')) if cp.get('ContactDetails') else ''
        sql = 'SELECT Device.timeExtracted, Device.serialNumber, Contact.contactName, \
ContactDetails.detailType , ContactDetails.detail \
FROM Device, Contact, ContactDetails WHERE Device.deviceID = Contact.deviceID \
AND Contact.contactID = ContactDetails.contactID {0}'.format(where)
        events_arr = self.read_sqlite(self.sqlite_path, sql)
        for i in range(0, len(events_arr), 5):
            timeExtracted = str.strip(events_arr[i]).split(' = ')[1]
            serialNumber = (str.strip(events_arr[i+1]).split(' = '))[1]
            contactName = str.strip(events_arr[i+2]).split(' = ')[1]
            detailType = str.strip(events_arr[i+3]).split(' = ')[1]
            detail = str.strip(events_arr[i+4]).split(' = ')[1]
            print '{0} SerialNumber="{1}" ContactName="{2}" DetailType="{3}" Detail="{4}" \
Type="ContactDetails"'.format(timeExtracted,
                            serialNumber,
                            contactName,
                            detailType,
                            detail)
        if events_arr != []:
            lastID_sql = 'SELECT max(contactDetailsID) FROM ContactDetails'
            lastID = self.read_last_id(self.sqlite_path, lastID_sql)
            cpmgr.save('ContactDetails', lastID)
        
        
        
        #CallLogs table
        where = 'AND CallLogs.callID > {0}'.format(cp.get('CallLogs')) if cp.get('CallLogs') else ''
        sql = 'SELECT CallLogs.timeCalled as timeCalled, Device.serialNumber as serialNumber, \
CallLogs.number as number, CallLogs.duration as duration, CallLogs.status as status \
FROM Device, CallLogs WHERE Device.deviceID = CallLogs.deviceID {0}'.format(where)
        events_arr = self.read_sqlite(self.sqlite_path, sql)
        for i in range(0, len(events_arr), 5):
            timeCalled = str.strip(events_arr[i]).split(' = ')[1]
            serialNumber = (str.strip(events_arr[i+1]).split(' = '))[1]
            number = str.strip(events_arr[i+2]).split(' = ')[1]
            duration = str.strip(events_arr[i+3]).split(' = ')[1]
            status = str.strip(events_arr[i+4]).split(' = ')[1]
            print '{0} SerialNumber="{1}" Number="{2}" Duration="{3}" Status="{4}" \
Type="CallLogs"'.format(timeCalled,
                        serialNumber,
                        number,
                        duration,
                        status)
        if events_arr != []:
            lastID_sql = 'SELECT max(callID) FROM CallLogs'
            lastID = self.read_last_id(self.sqlite_path, lastID_sql)
            cpmgr.save('CallLogs', lastID)
        
        #SMSHistory table
        where = 'AND SMSHistory.messageID > {0}'.format(cp.get('SMSHistory')) if cp.get('SMSHistory') else ''
        sql = 'SELECT SMSHistory.datetime as datetime, Device.serialNumber as serialNumber, \
SMSHistory.address as address, SMSHistory.messageType as messageType, SMSHistory.message as message \
FROM Device, SMSHistory WHERE Device.deviceID = SMSHistory.deviceID {0}'.format(where)
        events_arr = self.read_sqlite(self.sqlite_path, sql)
        for i in range(0, len(events_arr), 5):
            datetime = str.strip(events_arr[i]).split(' = ')[1]
            serialNumber = (str.strip(events_arr[i+1]).split(' = '))[1]
            address = str.strip(events_arr[i+2]).split(' = ')[1]
            messageType = str.strip(events_arr[i+3]).split(' = ')[1]
            message = str.strip(events_arr[i+4]).split(' = ')[1]
            print '{0} SerialNumber="{1}" Address="{2}" MessageType="{3}" Message="{4}" \
Type="SMS"'.format(datetime,
                    serialNumber,
                    address,
                    messageType,
                    message)
        if events_arr != []:
            lastID_sql = 'SELECT max(messageID) FROM SMSHistory'
            lastID = self.read_last_id(self.sqlite_path, lastID_sql)
            cpmgr.save('SMSHistory', lastID)
            
        #BrowserHistory table
        where = 'AND BrowserHistory.browserHistoryID > {0}'.format(cp.get('BrowserHistory')) if cp.get('BrowserHistory') else ''
        sql = 'SELECT BrowserHistory.lastVisited as lastVisited, Device.serialNumber as serialNumber, \
BrowserHistory.title as title, BrowserHistory.URL as url, BrowserHistory.visitCount as visitCount \
FROM Device, BrowserHistory WHERE Device.deviceID = BrowserHistory.deviceID {0}'.format(where)
        events_arr = self.read_sqlite(self.sqlite_path, sql)
        for i in range(0, len(events_arr), 5):
            lastVisited = str.strip(events_arr[i]).split(' = ')[1]
            serialNumber = (str.strip(events_arr[i+1]).split(' = '))[1]
            title = str.strip(events_arr[i+2]).split(' = ')[1]
            url = str.strip(events_arr[i+3]).split(' = ')[1]
            visitCount = str.strip(events_arr[i+4]).split(' = ')[1]
            print '{0} SerialNumber="{1}" Title="{2}" URL="{3}" VisitCount="{4}" \
Type="BrowserHistory"'.format(lastVisited,
                    serialNumber,
                    title,
                    url,
                    visitCount)
        if events_arr != []:
            lastID_sql = 'SELECT max(browserHistoryID) FROM BrowserHistory'
            lastID = self.read_last_id(self.sqlite_path, lastID_sql)
            cpmgr.save('BrowserHistory', lastID)
        
        
        #BrowserState
        where = 'AND BrowserState.browserStateID > {0}'.format(cp.get('BrowserState')) if cp.get('BrowserState') else ''
        sql = 'SELECT BrowserState.timeStamp as timeStamp, Device.serialNumber as serialNumber, \
BrowserState.title as title, BrowserState.URL as url \
FROM Device, BrowserState WHERE Device.deviceID = BrowserState.deviceID {0}'.format(where)
        events_arr = self.read_sqlite(self.sqlite_path, sql)
        for i in range(0, len(events_arr), 4):
            timeStamp = str.strip(events_arr[i]).split(' = ')[1]
            serialNumber = (str.strip(events_arr[i+1]).split(' = '))[1]
            title = str.strip(events_arr[i+2]).split(' = ')[1]
            url = str.strip(events_arr[i+3]).split(' = ')[1]
            print '{0} SerialNumber="{1}" Title="{2}" URL="{3}" \
Type="BrowserState"'.format(timeStamp,
                    serialNumber,
                    title,
                    url)
        if events_arr != []:
            lastID_sql = 'SELECT max(browserStateID) FROM BrowserState'
            lastID = self.read_last_id(self.sqlite_path, lastID_sql)
            cpmgr.save('BrowserState', lastID)
        
        
        #BrowserBookmark
        where = 'AND BrowserBookmark.browserBookmarkID > {0}'.format(cp.get('BrowserBookmark')) if cp.get('BrowserBookmark') else ''
        sql = 'SELECT Device.timeExtracted as timeExtracted, Device.serialNumber as serialNumber, \
BrowserBookmark.title as title, BrowserBookmark.URL as url \
FROM Device, BrowserBookmark WHERE Device.deviceID = BrowserBookmark.deviceID {0}'.format(where)
        events_arr = self.read_sqlite(self.sqlite_path, sql)
        for i in range(0, len(events_arr), 4):
            timeExtracted = str.strip(events_arr[i]).split(' = ')[1]
            serialNumber = (str.strip(events_arr[i+1]).split(' = '))[1]
            title = str.strip(events_arr[i+2]).split(' = ')[1]
            url = str.strip(events_arr[i+3]).split(' = ')[1]
            print '{0} SerialNumber="{1}" Title="{2}" URL="{3}" \
Type="BrowserBookmark"'.format(timeExtracted,
                    serialNumber,
                    title,
                    url)
        if events_arr != []:
            lastID_sql = 'SELECT max(browserBookmarkID) FROM BrowserBookmark'
            lastID = self.read_last_id(self.sqlite_path, lastID_sql)
            cpmgr.save('BrowserBookmark', lastID)
        
        
        #BrowserSearch
        where = 'AND BrowserSearch.browserSearchID > {0}'.format(cp.get('BrowserSearch')) if cp.get('BrowserSearch') else ''
        sql = 'SELECT BrowserSearch.date as date, Device.serialNumber as serialNumber, \
BrowserSearch.browserType as browserType, BrowserSearch.search as search \
FROM Device, BrowserSearch WHERE Device.deviceID = BrowserSearch.deviceID {0}'.format(where)
        events_arr = self.read_sqlite(self.sqlite_path, sql)
        for i in range(0, len(events_arr), 4):
            date = str.strip(events_arr[i]).split(' = ')[1]
            serialNumber = (str.strip(events_arr[i+1]).split(' = '))[1]
            browserType = str.strip(events_arr[i+2]).split(' = ')[1]
            search = str.strip(events_arr[i+3]).split(' = ')[1]
            print '{0} SerialNumber="{1}" BrowserType="{2}" Search="{3}" \
Type="BrowserSearch"'.format(date,
                    serialNumber,
                    browserType,
                    search.replace('"', '\''))
        if events_arr != []:
            lastID_sql = 'SELECT max(browserSearchID) FROM BrowserSearch'
            lastID = self.read_last_id(self.sqlite_path, lastID_sql)
            cpmgr.save('BrowserSearch', lastID)
    
        #SkypeAccount
        where = 'AND SkypeAccount.skypeAccountID > {0}'.format(cp.get('SkypeAccount')) if cp.get('SkypeAccount') else ''
        sql = 'SELECT SkypeAccount.lastUpdated_profile as lastUpdated, Device.serialNumber as serialNumber, \
SkypeAccount.skypename as skypeName, SkypeAccount.fullname as fullName, SkypeAccount.liveid_membername as liveID, \
SkypeAccount.emails as skypeEmail, SkypeAccount.birthday as birthday, SkypeAccount.gender as gender, \
SkypeAccount.phone_home as homePhone, SkypeAccount.phone_office as officePhone, SkypeAccount.phone_mobile as mobilePhone \
FROM Device, SkypeAccount WHERE Device.deviceID = SkypeAccount.deviceID {0}'.format(where)
        events_arr = self.read_sqlite(self.sqlite_path, sql)
        for i in range(0, len(events_arr), 11):
            lastUpdated = str.strip(events_arr[i]).split(' = ')[1]
            serialNumber = (str.strip(events_arr[i+1]).split(' = '))[1]
            skypeName = str.strip(events_arr[i+2]).split(' = ')[1]
            try: fullName = str.strip(events_arr[i+3]).split(' = ')[1] 
            except: fullName = '-'
            try: liveID = str.strip(events_arr[i+4]).split(' = ')[1]
            except: liveID = '-'
            skypeEmail = str.strip(events_arr[i+5]).split(' = ')[1]
            try: birthday = str.strip(events_arr[i+6]).split(' = ')[1]
            except: birthday = '-'
            try: gender = str.strip(events_arr[i+7]).split(' = ')[1]
            except: gender = '-'
            try: homePhone = str.strip(events_arr[i+8]).split(' = ')[1]
            except: homePhone = '-'
            try: officePhone = str.strip(events_arr[i+9]).split(' = ')[1]
            except: officePhone = '-'
            try: mobilePhone = str.strip(events_arr[i+10]).split(' = ')[1]
            except: mobilePhone = '-'
            print '{0} SerialNumber="{1}" SkypeName="{2}" FullName="{3}" LiveID="{4}" SkypeEmail="{5}" \
Birthday="{6}" Gender="{7}" HomePhone="{8}" OfficePhone="{9}" MobilePhone="{10}" \
Type="SkypeAccount"'.format(lastUpdated,
                    serialNumber,
                    skypeName,
                    fullName,
                    liveID,
                    skypeEmail,
                    birthday,
                    gender,
                    homePhone,
                    officePhone,
                    mobilePhone)
        if events_arr != []:
            lastID_sql = 'SELECT max(skypeAccountID) FROM SkypeAccount'
            lastID = self.read_last_id(self.sqlite_path, lastID_sql)
            cpmgr.save('SkypeAccount', lastID)
        
        
        #SkypeConversation
        where = 'AND SkypeConversation.skypeConvoID > {0}'.format(cp.get('SkypeConversation')) if cp.get('SkypeConversation') else ''
        sql = 'SELECT SkypeConversation.timestamp as timestamp, Device.serialNumber as serialNumber, \
SkypeConversation.author as author, SkypeConversation.author_fullname as authorFullName, \
SkypeConversation.dialogPartner as dialogPartner, SkypeConversation.type as convoType, \
SkypeConversation.messageContent as messageContent, SkypeConversation.callDuration as callDuration \
FROM Device, SkypeConversation, SkypeAccount WHERE Device.deviceID = SkypeAccount.deviceID \
AND SkypeAccount.skypeAccountID = SkypeConversation.skypeAccountID {0}'.format(where)
        events_arr = self.read_sqlite(self.sqlite_path, sql)
        for i in range(0, len(events_arr), 8):
            timestamp = str.strip(events_arr[i]).split(' = ')[1]
            serialNumber = (str.strip(events_arr[i+1]).split(' = '))[1]
            author = str.strip(events_arr[i+2]).split(' = ')[1]
            authorFullName = str.strip(events_arr[i+3]).split(' = ')[1]
            dialogPartner = str.strip(events_arr[i+4]).split(' = ')[1]
            convoType = str.strip(events_arr[i+5]).split(' = ')[1]
            try: messageContent = str.strip(events_arr[i+6]).split(' = ')[1]
            except: messageContent = ''
            callDuration = str.strip(events_arr[i+7]).split(' = ')[1]
            print '{0} SerialNumber="{1}" Author="{2}" AuthorFullName="{3}" DialogPartner="{4}" \
ConvoType="{5}" MessageContent="{6}" CallDuration="{7}s" \
Type="SkypeConversation"'.format(timestamp,
                                serialNumber,
                                author,
                                authorFullName,
                                dialogPartner,
                                convoType,
                                messageContent.replace('"', '\''),
                                callDuration)
        if events_arr != []:
            lastID_sql = 'SELECT max(skypeConvoID) FROM SkypeConversation'
            lastID = self.read_last_id(self.sqlite_path, lastID_sql)
            cpmgr.save('SkypeConversation', lastID)
        
        #SkypeContact
        where = 'AND SkypeContact.skypeContactID > {0}'.format(cp.get('SkypeContact')) if cp.get('SkypeContact') else ''
        sql = 'SELECT Device.timeExtracted as timeExtracted, Device.serialNumber as serialNumber, \
SkypeContact.skypename as skypeName, SkypeContact.fullname as fullName, \
SkypeContact.lastonline_timestamp as lastOnline, SkypeAccount.skypename \
FROM Device, SkypeContact, SkypeAccount WHERE Device.deviceID = SkypeAccount.deviceID \
AND SkypeAccount.skypeAccountID = SkypeContact.skypeAccountID {0}'.format(where)
        events_arr = self.read_sqlite(self.sqlite_path, sql)
        for i in range(0, len(events_arr), 6):
            timeExtracted = str.strip(events_arr[i]).split(' = ')[1]
            serialNumber = (str.strip(events_arr[i+1]).split(' = '))[1]
            skypeName = str.strip(events_arr[i+2]).split(' = ')[1]
            fullName = str.strip(events_arr[i+3]).split(' = ')[1]
            try: lastOnline = str.strip(events_arr[i+4]).split(' = ')[1]
            except: lastOnline = ''
            skypeaccount = str.strip(events_arr[i+5]).split(' = ')[1]
            print '{0} SerialNumber="{1}" SkypeName="{2}" FullName="{3}" LastOnline="{4}" SkypeAccount="{5}" \
Type="SkypeContact"'.format(timeExtracted,
                                serialNumber,
                                skypeName,
                                fullName,
                                lastOnline,
                                skypeaccount)
        if events_arr != []:
            lastID_sql = 'SELECT max(skypeContactID) FROM SkypeContact'
            lastID = self.read_last_id(self.sqlite_path, lastID_sql)
            cpmgr.save('SkypeContact', lastID)
            
        #Application List
        where = 'AND Application.applicationID > {0}'.format(cp.get('Application')) if cp.get('Application') else ''
        sql = 'SELECT Device.timeExtracted, Device.serialNumber, Application.application_name \
FROM Device, Application WHERE Device.deviceID = Application.deviceID {0}'.format(where)
        events_arr = self.read_sqlite(self.sqlite_path, sql)
        for i in range(0, len(events_arr), 3):
            timeExtracted = str.strip(events_arr[i]).split(' = ')[1]
            serialNumber = (str.strip(events_arr[i+1]).split(' = '))[1]
            application = str.strip(events_arr[i+2]).split(' = ')[1]
            print '{0} SerialNumber="{1}" Application="{2}" \
Type="ApplicationList"'.format(timeExtracted,
                            serialNumber,
                            application)
        if events_arr != []:
            lastID_sql = 'SELECT max(applicationID) FROM Application'
            lastID = self.read_last_id(self.sqlite_path, lastID_sql)
            cpmgr.save('Application', lastID)
        





    def read_sqlite(self, sqlite_path, sql):
        path_to_sqlite3 = os.path.join(AppBinPath, 'sqlite3.exe')
        command = [path_to_sqlite3, '-line', sqlite_path, sql]
        logger.debug(' '.join(command))
        p =subprocess.Popen(command, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if err:
            logger.error('SQL execution error: {0}'.format(' '.join(command)))
            return []
        events = ''
        for line in StringIO.StringIO(out).readlines():
            if line == '\r\n' or line == '\n':
                continue
            events += line
        events_arr = events.split('\r\n')
        events_arr.pop()
        return events_arr
    
    def read_last_id(self, sqlite_path, lastID_sql):
        lastID = 0
        path_to_sqlite3 = os.path.join(AppBinPath, 'sqlite3.exe')
        command = [path_to_sqlite3, '-column', sqlite_path, lastID_sql]
        p =subprocess.Popen(command, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result = p.communicate()
        if not result[1] and result[0]:
            lastID = result[0].strip()
        else:
            logger.error('Error getting last id: {0}'.format(result))
        return lastID

if __name__ == '__main__':
    sqlextract = SQLExtract()
    sqlextract.start()