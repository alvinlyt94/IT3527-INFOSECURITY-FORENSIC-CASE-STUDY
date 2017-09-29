import os, sys, sqlite3, hashlib, time, zipfile, shutil, xlwt
import mbdbdecoding, plistutils, plugins_utils, magic
from datetime import datetime, timedelta
from progressbar import Bar, Percentage, ProgressBar

AppBinPath = os.path.dirname(os.path.realpath(sys.argv[0]))
os.chdir(AppBinPath)
os.chdir('..')

class ReadBackup:
    deviceID=0
    
    FILTER=''.join([(len(repr(chr(x)))==3) and chr(x) or '.' for x in range(256)])
    def hex2nums(self, src, length=8):
        N=0; result=''
        while src:
            s,src = src[:length],src[length:]
            hexa = ' '.join(["%02X"%ord(x) for x in s])
            s = s.translate(self.FILTER)
            N+=length
            result += (hexa + " ")
        return result
    
    # Repairs sqlite files (windows only) by Fabio Sangiacomo <fabio.sangiacomo@digital-forensics.it> 
    def repairDBFiles(self):        
        if os.name == 'nt':        
            zipfilename = os.path.join(self.backup_path, 'original_files.zip')

            # skips this phase if original_files.zip is already present into backup_path
            if (os.path.exists(zipfilename) == 0):   

                #------------------ reading file dir and checking magic for sqlite databases -------------------------------

                # list sqlite files to be repaired
                sqliteFiles = []
                backupFiles = os.listdir(self.backup_path)               
                
                readCount = 0
                for backupFile in backupFiles:
                    item_realpath = os.path.join(self.backup_path,backupFile)
                    if (os.path.exists(item_realpath) == 0):
                        continue    
                    filemagic = magic.file(item_realpath)
                    if (filemagic.partition("/")[2] == "sqlite"):
                        sqliteFiles.append([backupFile, item_realpath])
                    readCount += 1

                #------------------- converting sqlite files found in the previous step ----------------------------------
        
                print '\nRepairing the databases... '
                zf = zipfile.ZipFile(zipfilename, mode='w')
                
                pbar = ProgressBar(widgets=[Percentage(), Bar()], maxval=len(sqliteFiles)).start()
                
                convertedCount = 0
                for sqliteFile in sqliteFiles:
                    fname = sqliteFile[0]
                    item_realpath = sqliteFile[1]

                    #print("Repairing database: %s"%fname)

                    # dump the database in an SQL text format (Temp.sql temporary file)
                    os.system('echo .dump | sqlite3 "%s" > Temp.sql' % item_realpath)

                    # saves the original file into the archive and releases the archive handle
                    current = os.getcwd()
                    os.chdir(self.backup_path)
                    zf.write(fname)
                    os.chdir(current)

                    #Removes original file
                    os.remove(item_realpath)

                    #Overwrites the original file with the Temp.sql content
                    os.system('echo .quit | sqlite3 -init Temp.sql "%s"' % item_realpath)

                    #Removes temporary file
                    if os.path.exists("Temp.sql"):
                        os.remove("Temp.sql")
                    
                    # update progress bar
                    convertedCount += 1
                    pbar.update(convertedCount)
                    
                pbar.finish()
                zf.close()
                print "Successfully Repaired!"
                
                return True
            
            else:
                return True

    
    def readBackupArchive(self):
        print "\nDecoding Backup Path..."
        
        # if exists Manifest.mbdx, then iOS <= 4
        iOSVersion = 5
        mbdxPath = os.path.join(self.backup_path, "Manifest.mbdx")
        if (os.path.exists(mbdxPath)):
            iOSVersion = 4
        
        # decode Manifest files
        mbdbPath = os.path.join(self.backup_path, "Manifest.mbdb")
        if (os.path.exists(mbdbPath)):
            mbdb = mbdbdecoding.process_mbdb_file(mbdbPath)
        else:
            #usage()
            print("\nManifest.mbdb not found in path \"%s\". Are you sure this is a " +
                  "correct iOS backup dir?\n"%(self.backup_path))
            sys.exit(1)
        
        # decode mbdx file (only iOS 4)
        if (iOSVersion == 4):
            mbdxPath = os.path.join(self.backup_path, "Manifest.mbdx")
            if (os.path.exists(mbdxPath)):
                mbdx = mbdbdecoding.process_mbdx_file(mbdxPath)
            else:
                #usage()
                print("\nManifest.mbdx not found in path \"%s\". Are you sure this is a correct " +
                      "iOS backup dir, and are you sure this is an iOS 4 backup?\n"%(self.backup_path))
                sys.exit(1)    
        
        # prepares DB
        database = sqlite3.connect(':memory:') # Create a database file in memory
        database.row_factory = sqlite3.Row
        self.cursor = database.cursor() # Create a cursor
        
        self.cursor.execute(
            "CREATE TABLE indice (" + 
            "id INTEGER PRIMARY KEY AUTOINCREMENT," +
            "type VARCHAR(1)," +
            "permissions VARCHAR(9)," +
            "userid VARCHAR(8)," +
            "groupid VARCHAR(8)," +
            "filelen INT," +
            "mtime INT," +
            "atime INT," +
            "ctime INT," +
            "fileid VARCHAR(50)," +
            "domain_type VARCHAR(100)," +
            "domain VARCHAR(100)," +
            "file_path VARCHAR(100)," +
            "file_name VARCHAR(100)," + 
            "link_target VARCHAR(100)," + 
            "datahash VARCHAR(100)," + 
            "flag VARCHAR(100)"
            ");"
        )
        
        self.cursor.execute(
            "CREATE TABLE properties (" + 
            "id INTEGER PRIMARY KEY AUTOINCREMENT," +
            "file_id INTEGER," +
            "property_name VARCHAR(100)," +
            "property_val VARCHAR(100)" +
            ");"
        )
        
        # count items parsed from Manifest file
        items = 0;
        
        # populates database by parsing manifest file
        for offset, fileinfo in mbdb.items():
            
            # iOS 4 (get file ID from mbdx file)
            if (iOSVersion == 4):
            
                if offset in mbdx:
                    fileinfo['fileID'] = mbdx[offset]
                else:
                    fileinfo['fileID'] = "<nofileID>"
                    #print >> sys.stderr, "No fileID found for %s" % fileinfo_str(fileinfo)
                    print >> sys.stderr, "No fileID found"
            
            # iOS 5 (no MBDX file, use SHA1 of complete file name)
            elif (iOSVersion == 5):
                fileID = hashlib.sha1()
                fileID.update("%s-%s"%(fileinfo['domain'], fileinfo['filename']) )
                fileinfo['fileID'] = fileID.hexdigest()    
        
            # decoding element type (symlink, file, directory)
            if (fileinfo['mode'] & 0xE000) == 0xA000: obj_type = 'l' # symlink
            elif (fileinfo['mode'] & 0xE000) == 0x8000: obj_type = '-' # file
            elif (fileinfo['mode'] & 0xE000) == 0x4000: obj_type = 'd' # dir
            
            # separates domain type (AppDomain, HomeDomain, ...) from domain name
            [domaintype, sep, domain] = fileinfo['domain'].partition('-');
            
            # separates file name from file path
            [filepath, sep, filename] = fileinfo['filename'].rpartition('/')
            if (type == 'd'):
                filepath = fileinfo['filename']
                filename = "";

            # Insert record in database
            query = "INSERT INTO indice(type, permissions, userid, groupid, filelen, mtime, atime, ctime, fileid, domain_type, domain, file_path, file_name, link_target, datahash, flag) VALUES(";
            query += "'%s',"     % obj_type
            query += "'%s',"     % mbdbdecoding.modestr(fileinfo['mode']&0x0FFF)
            query += "'%08x',"     % fileinfo['userid']
            query += "'%08x',"     % fileinfo['groupid']
            query += "%i,"         % fileinfo['filelen']
            query += "%i,"         % fileinfo['mtime']
            query += "%i,"         % fileinfo['atime']
            query += "%i,"         % fileinfo['ctime']
            query += "'%s',"     % fileinfo['fileID']
            query += "'%s',"     % domaintype.replace("'", "''")
            query += "'%s',"     % domain.replace("'", "''")
            query += "'%s',"     % filepath.replace("'", "''")
            query += "'%s',"     % filename.replace("'", "''")
            query += "'%s',"     % fileinfo['linktarget']
            query += "'%s',"     % self.hex2nums(fileinfo['datahash']).replace("'", "''")
            query += "'%s'"     % fileinfo['flag']
            query += ");"
            self.cursor.execute(query)
            
            # check if file has properties to store in the properties table
            if (fileinfo['numprops'] > 0):
        
                query = "SELECT id FROM indice WHERE "
                query += "domain = '%s' " % domain.replace("'", "''")
                query += "AND fileid = '%s' " % fileinfo['fileID']
                query += "LIMIT 1"
                 
                self.cursor.execute(query);
                id = self.cursor.fetchall()
                
                if (len(id) > 0):
                    index = id[0][0]
                    properties = fileinfo['properties']
                    for property in properties.keys():
                        query = "INSERT INTO properties(file_id, property_name, property_val) VALUES (";
                        query += "'%i'," % index
                        query += "'%s'," % property
                        query += "'%s'" % self.hex2nums(properties[property]).replace("'", "''")
                        query += ");"
                        
                        self.cursor.execute(query);
            
                #print("File: %s, properties: %i"%(domain + ":" + filepath + "/" + filename, fileinfo['numprops']))
                #print(fileinfo['properties'])
                
            # manage progress bar
            items += 1;
            #if (items%10 == 0):
                #progress.setValue(items/10)

        database.commit() 
        
        print "Successfully Decoded!"
        
        # print banner
        #print("\nWorking directory: %s"%self.backup_path)
        #print("Read elements: %i" %items)

    def exportToSqlite(self):
        conn = sqlite3.connect('SMDF.sqlite')
        c = conn.cursor()
        
        print "\nDatabase Location: " + os.path.join(os.getcwd(), "SMDF.sqlite")
        
        
        
        # *********************
        # **** DEVICE INFO ****
        # *********************
        print "\nExporting Device Info..."
        deviceinfo = plistutils.deviceInfo(os.path.join(self.backup_path, "Info.plist"))
        for element in deviceinfo.keys():
            #print "%s: %s"%(element, deviceinfo[element])
            if element == 'Product Version':
                OS = deviceinfo[element]
            elif element == 'Product Type':
                model = deviceinfo[element]
            elif element == 'Serial Number':
                serialNumber = deviceinfo[element]
            elif element == 'Last Backup Date':
                timeExtracted = deviceinfo[element]
                timeExtracted += timedelta(hours=8)  # Convert UTC Time to GMT+8 Time    
        
        # Insert data into Device table
        c.execute("INSERT INTO Device VALUES (NULL,'{0}','{1}','{2}','{3}','{4}','{5}')"
                    .format('iOS ' + OS, 'Apple', model, serialNumber, '-', timeExtracted))
        conn.commit()
        print "Successfully Exported!"
        


        # ***********************
        # **** SET DEVICE ID ****
        # ***********************
        c.execute("SELECT deviceID FROM Device WHERE serialNumber = '{0}'".format(serialNumber))
        self.deviceID = c.fetchone()[0]
        
        
        
#         # ****************
#         # ***** MAIL *****
#         # ****************
#         print "\nExporting Mail Information..."    
#         self.exportMailDatabase()
#         
#         mailFolder = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), "Temp Mail Export")
#         mailDBFiles = os.listdir(mailFolder)
#         
#         for mailDBFile in mailDBFiles:
#             # Get the file path of the Mail DB
#             mailDBPath = os.path.join(mailFolder, mailDBFile)  
#             
#             # opening database
#             mail_conn = sqlite3.connect(mailDBPath)
#             mail_cursor = mail_conn.cursor()
#             
#             smail_Query = "SELECT sending_address, display_name, address, dates, bundle_identifier FROM recents"
#             mail_cursor.execute(smail_Query)
#             mails = mail_cursor.fetchall()
#             
#             # ************************
#             # ***** DEVICE EMAIL *****
#             # ************************
#             for mail in mails:  
#                 # Check that only collect information from mail
#                 if mail[4] != "com.apple.mobilemail":
#                     continue
#                 
#                 sending_address = mail[0]
# 
#                 # Insert data into DeviceEmail table
#                 c.execute("INSERT INTO DeviceEmail VALUES (NULL,{0},'{1}')"
#                           .format(self.deviceID, sending_address))
#                 break
# 
#             for mail in mails:  
#                 # Check that only collect information from mail
#                 if mail[4] != "com.apple.mobilemail":
#                     continue
#                 
#                 sending_address = mail[0]
# 
#                 # *****************************
#                 # **** SET DEVICE EMAIL ID ****
#                 # *****************************
#                 c.execute("SELECT deviceEmailID FROM DeviceEmail WHERE deviceEmail = '{0}' ORDER BY deviceEmailID desc".format(sending_address))
#                 deviceEmailID = c.fetchone()[0]
#                 
#                 display_name = str(mail[1])
#                 if display_name == "None":
#                     display_name = ''
#                 address = mail[2]
#                 dates = mail[3]
#                 
#                 dateList = dates.split(':')
#                 
#                 for date in dateList:
#                     date = int(date) / 1000
#                     
#                     dateUnix = float(date)
#                     date = datetime.fromtimestamp(dateUnix).strftime('%Y-%m-%d %H:%M:%S')
#                     # Insert data into Mail table
#                     c.execute("INSERT INTO Mail VALUES (NULL,{0},'{1}','{2}','{3}')"
#                               .format(deviceEmailID, address, display_name, date))
#                 
#             # Close mailDB connection
#             mail_conn.close()
#     
#         conn.commit()
#     
#         # Delete the Temporary Mail Directory
#         shutil.rmtree(mailFolder)
#         print "Successfully Exported!"  
        
        
        
        # *****************
        # ***** SKYPE *****
        # *****************
        print "\nExporting Skype Information..."      
        self.exportSkypeDatabase()
        
        skypeFolder = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), "Temp Skype Export")
        try:
            skypeDBFiles = os.listdir(skypeFolder)
            
            for skypeDBFile in skypeDBFiles:
                # Get the file path of the Skype DB
                skypeDBPath = os.path.join(skypeFolder, skypeDBFile)  
                
                # opening database
                skype_conn = sqlite3.connect(skypeDBPath)
                skype_cursor = skype_conn.cursor()
                
                # *************************
                # ***** SKYPE ACCOUNT *****
                # *************************
                skype_Query = "SELECT skypename, fullname, liveid_membername, birthday, "
                skype_Query += "gender, languages, country, province, city, phone_home, "
                skype_Query += "phone_office, phone_mobile, about, emails, profile_timestamp, "
                skype_Query += "mood_text, mood_timestamp FROM Accounts"
                skype_cursor.execute(skype_Query)
                skype_Accounts = skype_cursor.fetchall()
                
                for account in skype_Accounts:          
                    skypename = account[0]
                    fullname = account[1]
                    liveid_membername = str(account[2])
                    if liveid_membername == "None":
                        liveid_membername = ""
                    birthday = str(account[3])
                    gender = account[4]
                    if gender == 1:
                        gender = "Male"
                    elif gender == 2:
                        gender = "Female"
                    elif gender == 0:
                        gender = ""
                    languages = account[5]
                    country = account[6]
                    province = account[7]
                    city = account[8]
                    phone_home = account[9]
                    if phone_home is None:
                        phone_home = ""
                    phone_office = account[10]
                    if phone_office is None:
                        phone_office = ""
                    phone_mobile = account[11]
                    if phone_mobile is None:
                        phone_mobile = ""
                    about_me = account[12]
                    emails = account[13]
                    lastUpdated_profile = account[14]
                    mood_text = account[15]
                    lastUpdated_mood = account[16]
                    
                    if birthday != '0':
                        birthday = birthday[:4] + '-' + birthday[4:]
                        birthday = birthday[:7] + '-' + birthday[7:]
                    elif birthday == '0':
                        birthday = ''
                    try:
                        dateUnix = float(lastUpdated_profile)
                        lastUpdated_profile = datetime.fromtimestamp(dateUnix).strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        lastUpdated_profile = str(lastUpdated_profile)
                        if lastUpdated_profile == "None":
                            lastUpdated_profile = ''
                    try:
                        dateUnix = float(lastUpdated_mood)
                        lastUpdated_mood = datetime.fromtimestamp(dateUnix).strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        lastUpdated_mood = str(lastUpdated_mood)
                        if lastUpdated_mood == "None":
                            lastUpdated_mood = ''
    
                    # Insert data into SkypeAccount table
                    c.execute("INSERT INTO SkypeAccount VALUES (NULL,{0},'{1}','{2}','{3}','{4}','{5}','{6}','{7}','{8}','{9}','{10}','{11}','{12}','{13}','{14}','{15}','{16}','{17}')"
                              .format(self.deviceID, skypename, fullname, liveid_membername, birthday, gender, languages, country, province, city, phone_home, phone_office, phone_mobile, about_me, emails, lastUpdated_profile, mood_text, lastUpdated_mood))
                              
                    # ******************************
                    # **** SET SKYPE ACCOUNT ID ****
                    # ******************************
                    c.execute("SELECT skypeAccountID FROM SkypeAccount WHERE deviceID = '{0}' AND skypename = '{1}'".format(self.deviceID,skypename))
                    skypeAccountID = c.fetchone()[0]
                    
                    # *************************
                    # ***** SKYPE CONTACT *****
                    # *************************
                    skype_Query = "SELECT skypename, displayname, lastonline_timestamp, "
                    skype_Query += "birthday, gender, languages, country, province, city, "
                    skype_Query += "phone_home, phone_office, phone_mobile, about, emails, "
                    skype_Query += "profile_timestamp, mood_text FROM Contacts "
                    skype_Query += "WHERE given_authlevel != 0"
                    skype_cursor.execute(skype_Query)
                    skype_Contacts = skype_cursor.fetchall()
                    
                    for contact in skype_Contacts:                
                        skypename = contact[0]
                        displayname = contact[1]
                        displayname = displayname.encode('utf-8')
                        lastonline_timestamp = contact[2]
                        birthday = contact[3]
                        if birthday is None:
                            birthday = ""
                        gender = contact[4]
                        if gender == 1:
                            gender = "Male"
                        elif gender == 2:
                            gender = "Female"
                        elif gender is None:
                            gender = ""
                        languages = contact[5]
                        if languages is None:
                            languages = ""
                        country = contact[6]
                        if country is None:
                            country = ""
                        province = contact[7]
                        if province is None:
                            province = ""
                        city = contact[8]
                        if city is None:
                            city = ""
                        phone_home = contact[9]
                        if phone_home is None:
                            phone_home = ""
                        phone_office = contact[10]
                        if phone_office is None:
                            phone_office = ""
                        phone_mobile = contact[11]
                        if phone_mobile is None:
                            phone_mobile = ""
                        about_me = contact[12]
                        if about_me is None:
                            about_me = ""
                        emails = contact[13]
                        if emails is None:
                            emails = ""
                        lastUpdated_profile = contact[14]
                        mood_text = str(contact[15])
                        mood_text = mood_text.replace('\'', '\'\'')
                        if mood_text == "None":
                            mood_text = ""
                        
                        if birthday != "":
                            birthday = str(birthday)
                            birthday = birthday[:4] + '-' + birthday[4:]
                            birthday = birthday[:7] + '-' + birthday[7:]
    
                        try:
                            dateUnix = float(lastonline_timestamp)
                            lastonline_timestamp = datetime.fromtimestamp(dateUnix).strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            lastonline_timestamp = str(lastonline_timestamp)
                            if lastonline_timestamp == "None":
                                lastonline_timestamp = ''
                        try:
                            dateUnix = float(lastUpdated_profile)
                            lastUpdated_profile = datetime.fromtimestamp(dateUnix).strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            lastUpdated_profile = str(lastUpdated_profile)
                            if lastUpdated_profile == "None":
                                lastUpdated_profile = ''
                        
                        # Insert data into SkypeContact table
                        c.execute("INSERT INTO SkypeContact VALUES (NULL,{0},'{1}','{2}','{3}','{4}','{5}','{6}','{7}','{8}','{9}','{10}','{11}','{12}','{13}','{14}','{15}','{16}')"
                                  .format(skypeAccountID, skypename, displayname, lastonline_timestamp, birthday, gender, languages, country, province, city, phone_home, phone_office, phone_mobile, about_me, emails, lastUpdated_profile, mood_text))
                              
                    # ******************************
                    # ***** SKYPE CONVERSATION *****
                    # ******************************
                    skype_Query = "SELECT author, from_dispname, dialog_partner, identities, "
                    skype_Query += "type, body_xml, param_value, timestamp FROM Messages"
                    skype_cursor.execute(skype_Query)
                    skype_Convos = skype_cursor.fetchall()
                    
                    for message in skype_Convos: 
                        author = message[0]
                        author_fullname = message[1]
                        dialog_partner = str(message[2])

                        messageContent = ''
                        callDuration = 0
                        
                        type = message[4]            
                        if type == 30:
                            type = "Call (Start)"
                            callDuration = message[6]
                        elif type == 39:
                            type = "Call (End)"
                            callDuration = message[6]
                        elif type == 61:
                            type = "Text Message"
                            messageContent = message[5]
                            messageContent = messageContent.encode('utf-8')
                        elif type == 50:
                            type = "Contact Invitation"
                        elif type == 51:
                            type = "Contact Acceptance"
                        else:
                            continue
                            
                        timestamp = message[7]
                        dateUnix = float(timestamp)
                        timestamp = datetime.fromtimestamp(dateUnix).strftime('%Y-%m-%d %H:%M:%S')
                        
                        # Insert data into SkypeConversation table
                        c.execute("INSERT INTO SkypeConversation VALUES (NULL,{0},'{1}','{2}','{3}','{4}','{5}',{6},'{7}')"
                                  .format(skypeAccountID, author, author_fullname, dialog_partner, type, messageContent, callDuration, timestamp))
                          
                # Close skypeDB connection
                skype_conn.close()
        
            conn.commit()
        
            # Delete the Temporary Skype Directory
            shutil.rmtree(skypeFolder)
            print "Successfully Exported!"  
        
        except:
            print "No available Skype Information found."
            
            
            
        # ************************
        # ***** SMS/iMESSAGE *****
        # ************************
        print "\nExporting SMS/iMessage..."
        messsageFilename = os.path.join(self.backup_path, plugins_utils.realFileName(
                                    self.cursor, filename="sms.db", 
                                    domaintype="HomeDomain")) 
        
        # opening database
        tempdb = sqlite3.connect(messsageFilename)
        tempdb.row_factory = sqlite3.Row
        tempcur = tempdb.cursor() 

        # populating tree with SMS groups
        query = "SELECT ROWID, chat_identifier FROM chat;"
        tempcur.execute(query)
        groups = tempcur.fetchall()
        
        for group in groups:
            groupid = group['ROWID']
            address = group['chat_identifier'].replace(' ', '')
            
            query = 'SELECT ROWID, text, date, is_from_me, cache_has_attachments, service FROM message INNER JOIN chat_message_join ON message.ROWID = chat_message_join.message_id WHERE chat_id = ?;'
            tempcur.execute(query, (groupid,))
            messages = tempcur.fetchall()

            for message in messages:
                messageText = message['text'].replace("\'", "\'\'").encode('utf-8')
                timestamp = message['date']
                messageType = ''
            
                dateUnix = float(timestamp) + 978307200 #JAN 1 1970
                timestamp = datetime.fromtimestamp(dateUnix).strftime('%Y-%m-%d %H:%M:%S')
                
                if (message['is_from_me'] == 1):
                    messageType = "Outgoing"
                else:
                    messageType = "Incoming"
                    
                # Insert data into SMSHistory table
                c.execute("INSERT INTO SMSHistory VALUES (NULL,{0},'{1}','{2}','{3}','{4}')"
                          .format(self.deviceID, address, messageType, messageText, timestamp))
        
        conn.commit()  
        print "Successfully Exported!"
            


        # closing database
        tempdb.close()        

        
        # *******************
        # ***** CONTACT *****
        # *******************
        print "\nExporting Contact..."
        contactFilename = os.path.join(self.backup_path, plugins_utils.realFileName(
                                        self.cursor, filename="AddressBook.sqlitedb", 
                                        domaintype="HomeDomain"))
        
        # opening database
        tempdb = sqlite3.connect(contactFilename)
        tempdb.row_factory = sqlite3.Row
        tempcur = tempdb.cursor() 
        
        peopleData = []
        additionalResources = []

        # acquire multivalue labels (just once)
        query = "SELECT value FROM ABMultiValueLabel"
        tempcur.execute(query)
        multivaluelabels = tempcur.fetchall()

        # acquire multivalue labels keys (just once)
        query = "SELECT value FROM ABMultiValueEntryKey"
        tempcur.execute(query)
        multivalueentrykeys = tempcur.fetchall()            
        
        # retrieve people list
        query = 'SELECT * FROM ABPerson;'
        tempcur.execute(query)
        people = tempcur.fetchall()

        for person in people:
            #print "\n***************************\n"  
            personID = person['ROWID']

            # complete name
            if (person['First'] != None):
                contactName = person['First']
            if (person['Last'] != None):
                contactName = contactName + " " + person['Last']
            if (person['First'] == None and person['Last'] == None):
                contactName = person['Organization']    
            if (contactName == None):
                contactName = "<None>"
                
            # Insert data into Contact table
            c.execute("INSERT INTO Contact VALUES (NULL,{0},'{1}')"
                      .format(self.deviceID, contactName))
            
            # ************************
            # **** SET CONTACT ID ****
            # ************************
            c.execute("SELECT contactID FROM Contact WHERE contactName = '{0}' ORDER BY contactID desc".format(contactName))
            contactID = c.fetchone()[0]
            
            records = [
                ["First name", person['First']],
                ["Last name", person['Last']],
                ["Organization", person['Organization']],
                ["Middle name", person['Middle']],
                ["Department", person['Department']],
                ["Note", person['Note']],
                ["Birthday", person['Birthday']],
                ["Job Title", person['JobTitle']],
                ["Nickname", person['Nickname']],
            ]
            
            for record in records:                 
                key = record[0]
                value = record[1]
                if (value != None):
                    if key == "Birthday":
                        dateUnix = float(value) + 978307200 #JAN 1 1970
                        value = datetime.fromtimestamp(dateUnix).strftime('%Y-%m-%d')
                    #print "{0}: {1}".format(key,value)
                    if key != "First name":
                        if key != "Last name":
                            # ***************************
                            # ***** CONTACT DETAILS *****
                            # ***************************
                            # Insert data into ContactDetails table
                            c.execute("INSERT INTO ContactDetails VALUES (NULL,{0},'{1}','{2}')"
                                      .format(contactID, key, value.replace("\'", "\'\'").encode('utf-8')))
                    
                    
            # multivalues
            query = "SELECT property, label, value, UID FROM ABMultiValue WHERE record_id = \"%s\""%personID
            tempcur.execute(query)
            multivalues = tempcur.fetchall()
         
            # print multivalues
            for multivalue in multivalues:
                 
                # decode multivalue type
                if (multivalue[0] == 3):    
                    property = "Phone number"
                elif (multivalue[0] == 4):
                    property = "EMail address"
                elif (multivalue[0] == 5):
                    property = "Multivalue"
                elif (multivalue[0] == 22):
                    property = "URL"
                else: 
                    property = "Unknown (%s)"%multivalue[0]
                 
                # decode multivalue label
                label = ""
                if (multivalue[1] != None):
                    label = multivaluelabels[int(multivalue[1]) - 1][0]
                    label = label.lstrip("_!<$")
                    label = label.rstrip("_!>$")
                  
                value = multivalue[2]
                 
                # if multivalue is multipart (an address)...
                if (multivalue[0] == 5):
                    multivalueid = multivalue[3]
                    query = "SELECT KEY, value FROM ABMultiValueEntry WHERE parent_id = \"%i\" ORDER BY key"%multivalueid
                    tempcur.execute(query)
                    parts = tempcur.fetchall()
                     
                    multipartKey = "Address (%s)"%label
             
                    multipartValue = ""
                    for part in parts:
                     
                        partkey = part[0]
                        partValue = part[1]
                        label = multivalueentrykeys[int(partkey) - 1][0]
                         
                        multipartValue += "%s: %s "%(label, partValue)
                        multipartValue = multipartValue.replace("\\n"," ")
 
                    #print "{0}: {1}".format(multipartKey, multipartValue)
                    
                    # ***************************
                    # ***** CONTACT DETAILS *****
                    # ***************************
                    # Insert data into ContactDetails table
                    c.execute("INSERT INTO ContactDetails VALUES (NULL,{0},'{1}','{2}')"
                              .format(contactID, multipartKey, multipartValue))
                else:                
                    #print "{0}: {1}".format("%s (%s)"%(property, label), value)
                    
                    # *************************
                    # ***** CONTACT EMAIL *****
                    # *************************
                    if property == "EMail address":
                        # Insert data into ContactEmail table
                        c.execute("INSERT INTO ContactEmail VALUES (NULL,{0},'{1}','{2}')"
                                  .format(contactID, label, value))
                        
                    # **************************
                    # ***** CONTACT NUMBER *****
                    # **************************
                    elif property == "Phone number":
                        value = value.replace(" ", "") # Remove spaces in between numbers
                        value = int(value) # Convert str to int
                        # Insert data into ContactNumber table
                        c.execute("INSERT INTO ContactNumber VALUES (NULL,{0},'{1}',{2})"
                                  .format(contactID, label, value))
            
        tempdb.close()

        conn.commit()
        print "Successfully Exported!"
        
        
        
        # *************************
        # **** SAFARI BOOKMARK ****
        # *************************
        print "\nExporting Safari Bookmark..."
        safariBookFilename = os.path.join(self.backup_path, plugins_utils.realFileName(
                                        self.cursor, filename="Bookmarks.db", 
                                        domaintype="HomeDomain"))
        
        # opening database
        tempdb = sqlite3.connect(safariBookFilename)
        tempdb.row_factory = sqlite3.Row
        tempcur = tempdb.cursor()

        parent_id = 1
        bookmarkQuery = "SELECT id, title, num_children, type, url, editable, deletable, order_index, external_uuid FROM bookmarks WHERE parent = \"%s\" ORDER BY order_index"%parent_id
        tempcur.execute(bookmarkQuery)
        bookmarks = tempcur.fetchall()
        
        for bookmark in bookmarks:
            title = ""
            URL = ""
            
            title = bookmark['title']
            #title = title.encode('utf-8')
            
            URL = bookmark['url']
            #URL = URL.encode('utf-8')

            # Insert data into SafariBookmark table
            c.execute("INSERT INTO BrowserBookmark VALUES (NULL,{0},'{1}','{2}','{3}','{4}')"
                      .format(self.deviceID, "Safari", title, URL, ""))
          
        conn.commit()  
        print "Successfully Exported!"
        
        
        
        # **********************
        # **** SAFARI STATE ****
        # **********************
        print "\nExporting Safari State..."
        safariStateFilename = os.path.join(self.backup_path, plugins_utils.realFileName(
                                        self.cursor, filename="SuspendState.plist", 
                                        domaintype="HomeDomain"))
        
        documents = plistutils.readPlist(safariStateFilename)['SafariStateDocuments']
        
        counter = 0
        for document in documents:
            #documentTitle = document['SafariStateDocumentTitle']
            documentTimestamp = document['SafariStateDocumentLastViewedTime'] + 978307200 #JAN 1 1970
            documentTimestamp = datetime.fromtimestamp(documentTimestamp).strftime('%Y-%m-%d %H:%M:%S')

            currentTab = documents[counter]
            currentList = currentTab['SafariStateDocumentBackForwardList']
            
            currentOpenElement = currentTab['SafariStateDocumentBackForwardList']['current']
            
            index = 0
            for element in currentList['entries']:
                title = ''
                URL = ''
                
                title = element['title']
                URL = element['']
                    
                if (index == currentOpenElement):
                    # Insert data into SafariState table
                    c.execute("INSERT INTO BrowserState VALUES (NULL,{0},'{1}','{2}','{3}', '{4}')"
                      .format(self.deviceID, "Safari", title, URL, documentTimestamp))
                
                index = index + 1
            counter = counter + 1
          
        conn.commit()  
        print "Successfully Exported!"
        
        
        
        # ************************
        # **** SAFARI HISTORY ****
        # ************************
        print "\nExporting Safari History..."
        safariHistFilename = os.path.join(self.backup_path, plugins_utils.realFileName(
                                        self.cursor, filename="History.plist", 
                                        domaintype="HomeDomain", path="Library/Safari"))
        historyRecords = plistutils.readPlist(safariHistFilename)['WebHistoryDates']
        
        #print "Filename: " + filename
        
        # Counter for record
        counter = 0
        
        for record in historyRecords:
            counter += 1 # Increment counter by 1
            title = ""
            URL = ""
            dateStr = ""
            visitCount = ""
            redirectURLs = ""
            
            # Title
            if ('title' in record.keys()):
                title = record['title']
            else:
                title = record['']
            title = title.encode('utf-8')
            # URL
            URL = record['']
            URL = URL.encode('utf-8')
            # Last Visited Date
            if ('lastVisitedDate' in record.keys()):
                dateUnix = float(record['lastVisitedDate']) + 978307200 #JAN 1 1970
                dateStr = datetime.fromtimestamp(dateUnix).strftime('%Y-%m-%d %H:%M:%S')
            # Visit Count
            if ("visitCount" in record.keys()):
                visitCount = record['visitCount']
            # Redirect URLs
            if ("redirectURLs" in record.keys()):
                redirectURLs = ""
                for element in record['redirectURLs']:
                    redirectURLs += element
                    redirectURLs = redirectURLs.encode('utf-8')
                    
            # Insert data into SafariHistory table
            c.execute("INSERT INTO BrowserHistory VALUES (NULL,{0},'{1}','{2}','{3}','{4}',{5},'{6}')"
                      .format(self.deviceID, "Safari", title, URL, dateStr, visitCount, redirectURLs))
          
        conn.commit()  
        print "Successfully Exported!"
        
        
        
        # *********************
        # **** APPLICATION ****
        # *********************
        print "\nExporting Applications..."
        # retrieve domain families
        self.cursor.execute("SELECT DISTINCT(domain_type) FROM indice");
        domain_types = self.cursor.fetchall()
        
        for domain_type_u in domain_types:
            
            domain_type = str(domain_type_u[0])
            
            # Proceed on with the codes only when the domain_type is "AppDomain"
            if domain_type != "AppDomain":
                continue
            
            # retrieve domains for the selected family
            query = "SELECT DISTINCT(domain) FROM indice WHERE domain_type = \"%s\" ORDER BY domain" % domain_type
            self.cursor.execute(query);
            domain_names = self.cursor.fetchall()
            
            for domain_name_u in domain_names:
                domain_name = str(domain_name_u[0]) 
            
                # Insert data into Application table
                c.execute("INSERT INTO Application VALUES (NULL,{0},'{1}')"
                          .format(self.deviceID, domain_name))
          
        conn.commit()  
        print "Successfully Exported!"
        
        
    
        conn.close()
    
    def getElementFromID(self, id):
        query = "SELECT * FROM indice WHERE id = ?"
        self.cursor.execute(query, (id,))
        data = self.cursor.fetchone()
        
        if (data == None): return None
        
        if (len(data) == 0): 
            return None
        else:
            return data
        
    def exportMailDatabase(self):        
        # retrieve domain families
        self.cursor.execute("SELECT DISTINCT(domain_type) FROM indice");
        domain_types = self.cursor.fetchall()
        
        for domain_type_u in domain_types:
            
            domain_type = str(domain_type_u[0])
            
            # Proceed on with the codes only when the domain_type is "AppDomain"
            if domain_type != "HomeDomain":
                continue
            
            # retrieve paths for the selected family
            query = "SELECT DISTINCT(file_path) FROM indice WHERE domain_type = \"%s\" ORDER BY domain" % domain_type
            self.cursor.execute(query);
            paths = self.cursor.fetchall()
            
            for path_u in paths:
                path = str(path_u[0])         
                
                # Proceed on with the codes only when the domain_name is "com.skype.SkypeForiPad"
                if path != "Library/Mail":
                    continue
            
                # retrieve files for selected path
                query = "SELECT file_name, filelen, id, type, datahash FROM indice WHERE domain_type = \"%s\" AND file_path = \"%s\" ORDER BY file_name" %(domain_type, path)
                self.cursor.execute(query)
                files = self.cursor.fetchall()
                
                for file in files:
                    file_name = str(file[0].encode("utf-8"))
                    if (file[1]) < 1024:
                        file_dim = str(file[1]) + " b"
                    else:
                        file_dim = str(file[1] / 1024) + " kb"
                    file_id = int(file[2])
                    file_type = str(file[3])
                
                    if file_name == "Recents":
                        # export main.db file
                        element = self.getElementFromID(file_id)
                        if (element == None): return
                        realFileName = os.path.join(self.backup_path, element['fileid'])
                        newName = element['file_name']
                    
                        # Export a Temporary Mail Directory
                        exportPath = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), "Temp Mail Export")
                        
                        if not os.path.exists(exportPath):
                            os.makedirs(exportPath) # Create directory folder for exporting
                        
                        if (len(exportPath) == 0): return
                         
                        try:
                            count = 1
                            while True:
                                exportName = "%s_"%count + newName
                                if os.path.exists(os.path.join(exportPath, exportName)):
                                    count = count + 1
                                else:
                                    break
                            shutil.copy(realFileName, os.path.join(exportPath, exportName))
                        except:
                            self.error("Error while exporting file.")
    
    def exportSkypeDatabase(self):        
        # retrieve domain families
        self.cursor.execute("SELECT DISTINCT(domain_type) FROM indice");
        domain_types = self.cursor.fetchall()
        
        for domain_type_u in domain_types:
            
            domain_type = str(domain_type_u[0])
            
            # Proceed on with the codes only when the domain_type is "AppDomain"
            if domain_type != "AppDomain":
                continue
            
            # retrieve domains for the selected family
            query = "SELECT DISTINCT(domain) FROM indice WHERE domain_type = \"%s\" ORDER BY domain" % domain_type
            self.cursor.execute(query);
            domain_names = self.cursor.fetchall()
            
            for domain_name_u in domain_names:
                domain_name = str(domain_name_u[0])            
                
                # Proceed on with the codes only when the domain_name is "com.skype.SkypeForiPad"
                if domain_name != "com.skype.SkypeForiPad":
                    continue
            
                # retrieve paths for selected domain
                query = "SELECT DISTINCT(file_path) FROM indice WHERE domain_type = \"%s\" AND domain = \"%s\" ORDER BY file_path" %(domain_type, domain_name)
                self.cursor.execute(query)
                paths = self.cursor.fetchall()
                
                for path_u in paths:
                    path = str(path_u[0])
                    
                    if path.startswith("Library/Application Support/Skype/"):
                        if path.count('/') == 3:
                            # retrieve files for selected path
                            query = "SELECT file_name, filelen, id, type, datahash FROM indice WHERE domain_type = \"%s\" AND domain = \"%s\" AND file_path = \"%s\" ORDER BY file_name" %(domain_type, domain_name, path)
                            self.cursor.execute(query)
                            files = self.cursor.fetchall()
                             
                            for file in files:
                                file_name = str(file[0].encode("utf-8"))
                                if (file[1]) < 1024:
                                    file_dim = str(file[1]) + " b"
                                else:
                                    file_dim = str(file[1] / 1024) + " kb"
                                file_id = int(file[2])
                                file_type = str(file[3])
         
                                if file_name == "main.db":
                                    # export main.db file
                                    element = self.getElementFromID(file_id)
                                    if (element == None): return
                                    realFileName = os.path.join(self.backup_path, element['fileid'])
                                    newName = element['file_name']
                                
                                    # Export a Temporary Skype Directory
                                    exportPath = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), "Temp Skype Export")
                                    
                                    if not os.path.exists(exportPath):
                                        os.makedirs(exportPath) # Create directory folder for exporting
                                    
                                    if (len(exportPath) == 0): return
                                     
                                    try:
                                        count = 1
                                        while True:
                                            exportName = "%s_"%count + newName
                                            if os.path.exists(os.path.join(exportPath, exportName)):
                                                count = count + 1
                                            else:
                                                break
                                        shutil.copy(realFileName, os.path.join(exportPath, exportName))
                                    except:
                                        self.error("Error while exporting file.")
        
    def isSQLite3(self, fileName):
        from os.path import isfile, getsize
        
        # Get the current working directory
        currentWorkingDir = os.getcwd()
        
        # Join the current working directory with the filename
        filePath = os.path.join(currentWorkingDir,fileName)
    
        # If file does not exist, return false
        if not os.path.isfile(filePath):
            return False
        
        if getsize(filePath) < 100: # SQLite database file header is 100 bytes
            return False
        else:
            fd = open(filePath, 'rb')
            Header = fd.read(100)
            fd.close()
    
            if Header[0:16] == 'SQLite format 3\000':
                return True
            else:
                return False
    
    def generateExportDir(self):
        localTime = time.localtime() # Get current local time
        timeString = time.strftime("%Y%m%d%H%M%S", localTime) # Format localTime to timeString
        
        # Join the current working directory with the new export directory (timeString)
        exportDir = os.path.join(os.getcwd(), timeString)
        
        if not os.path.exists(exportDir):
            os.makedirs(exportDir) # Create directory folder for exporting
                        
    def setBackupPath(self):
        backupFolder = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), "Backup")
        backupFiles = os.listdir(backupFolder)
        
        # Validation Check: If no available backup path found
        if len(backupFiles) == 0:
            print "No available backup path in the following directory: "
            print backupFolder
            self.backup_path = raw_input("\nEnter backup path: ")
            return
            
        print "Please choose an available backup path: "
        print "0) Enter backup path"
        
        fileCount = 1        
        
        for backupFile in backupFiles:  
            print "%s) "%fileCount + backupFile
            
            fileCount = fileCount + 1 # increment for every file count
        
        # Validation Check: Check for invalid input from user. If valid, break loop
        while True:
            try:
                backupChoice = int(raw_input("\nInput: "))
            except:
                print "Invalid Input! Please re-enter!"
                continue
            
            # Validation Check: Check for invalid index input from user
            if backupChoice <= 0:
                self.backup_path = raw_input("\nEnter backup path: ")
                return
            elif backupChoice > len(backupFiles):
                print "Index out of range! Please re-enter!"
                continue
                
            break
        
        self.backup_path = os.path.join(backupFolder, backupFiles.pop(backupChoice-1))
        
    def exportToXLSDeep(self, sheet, dataColumns, dataRows):
        colStyle = xlwt.easyxf('pattern: pattern solid, fore_color yellow;font: name Times New Roman, color-index red, bold on',
        num_format_str='#,##0.00')
        
        count = 0
   
        for col in dataColumns:
            sheet.write(0, count, col, colStyle)
            sheet.col(count).width = 256 * (len(col) + 1) 
            count = count + 1
        
        countRow = 1
        
        for row in dataRows:
            countCol = 0 
            for rowData in row:
                if isinstance(rowData,basestring):
                    rowData = rowData.encode('utf-8')
                sheet.write(countRow, countCol, rowData)
                if sheet.col(countCol).width < 256 * (len(str(rowData)) + 1):
                    if 256 * (len(str(rowData)) + 1) > 15000:
                        sheet.col(countCol).width = 15000
                    else:
                        sheet.col(countCol).width = 256 * (len(str(rowData)) + 1) 
                countCol = countCol + 1
            countRow = countRow + 1
    
    def exportToXLS(self):        
        book = xlwt.Workbook(encoding="utf-8")
        
        # opening database
        conn = sqlite3.connect('SMDF.sqlite')
        c = conn.cursor()
        
        # Create an instance of the ReadBackup class       
        ins = ReadBackup()
        
        # ************************
        # ***** Device TABLE *****
        # ************************        
        c.execute("SELECT * FROM Device WHERE deviceID = '{0}'".format(self.deviceID))
        dataRows = c.fetchall() # Retrieve a list of rows
        dataColumns = list(map(lambda x: x[0], c.description)) # Retrieve a list of columns

        if len(dataRows) != 0:
            sheet = book.add_sheet("Device")
            ins.exportToXLSDeep(sheet, dataColumns, dataRows)
            
            
        # *****************************
        # ***** Application TABLE *****
        # *****************************
        c.execute("SELECT * FROM Application WHERE deviceID = '{0}'".format(self.deviceID))
        dataRows = c.fetchall() # Retrieve a list of rows
        dataColumns = list(map(lambda x: x[0], c.description)) # Retrieve a list of columns
        
        if len(dataRows) != 0:
            sheet = book.add_sheet("Application")
            ins.exportToXLSDeep(sheet, dataColumns, dataRows)
        
        
#         # *****************************
#         # ***** DeviceEmail TABLE *****
#         # *****************************
#         c.execute("SELECT * FROM DeviceEmail WHERE deviceID = '{0}'".format(self.deviceID))
#         dataRows = c.fetchall() # Retrieve a list of rows
#         dataColumns = list(map(lambda x: x[0], c.description)) # Retrieve a list of columns
#         
#         if len(dataRows) != 0:
#             sheet = book.add_sheet("DeviceEmail")
#             ins.exportToXLSDeep(sheet, dataColumns, dataRows)
#         
#         
#         # *****************************
#         # **** SET DEVICE EMAIL ID ****
#         # *****************************
#         c.execute("SELECT deviceEmailID FROM DeviceEmail WHERE deviceID = '{0}'".format(self.deviceID))
#         deviceEmailIDs = c.fetchall() # Retrieve a list of skypeAccountID
#         
#         deviceEmailIDLists = []
#         for deviceEmailID in deviceEmailIDs:
#             for data in deviceEmailID:
#                 deviceEmailIDLists.append(str(data))
#                 
#         if len(deviceEmailIDLists) == 1:
#             deviceEmailIDQuery = deviceEmailIDLists[0]
#         elif len(deviceEmailIDLists) > 1:
#             deviceEmailIDQuery = ','.join(deviceEmailIDLists)
#             
#             
#         # **********************
#         # ***** Mail TABLE *****
#         # **********************
#         c.execute("SELECT * FROM Mail WHERE deviceEmailID IN ({0})".format(deviceEmailIDQuery))
#         dataRows = c.fetchall() # Retrieve a list of rows
#         dataColumns = list(map(lambda x: x[0], c.description)) # Retrieve a list of columns
#         
#         if len(dataRows) != 0:
#             sheet = book.add_sheet("Mail")
#             ins.exportToXLSDeep(sheet, dataColumns, dataRows)
        
        
        # ****************************
        # ***** SMSHistory TABLE *****
        # ****************************
        c.execute("SELECT * FROM SMSHistory WHERE deviceID = '{0}'".format(self.deviceID))
        dataRows = c.fetchall() # Retrieve a list of rows
        dataColumns = list(map(lambda x: x[0], c.description)) # Retrieve a list of columns
        
        if len(dataRows) != 0:
            sheet = book.add_sheet("SMSHistory")
            ins.exportToXLSDeep(sheet, dataColumns, dataRows)
        
        
        # ******************************
        # ***** BrowserState TABLE *****
        # ******************************
        c.execute("SELECT * FROM BrowserState WHERE deviceID = '{0}'".format(self.deviceID))
        dataRows = c.fetchall() # Retrieve a list of rows
        dataColumns = list(map(lambda x: x[0], c.description)) # Retrieve a list of columns
        
        if len(dataRows) != 0:
            sheet = book.add_sheet("BrowserState")
            ins.exportToXLSDeep(sheet, dataColumns, dataRows)
        
        
        # *********************************
        # ***** BrowserBookmark TABLE *****
        # *********************************
        c.execute("SELECT * FROM BrowserBookmark WHERE deviceID = '{0}'".format(self.deviceID))
        dataRows = c.fetchall() # Retrieve a list of rows
        dataColumns = list(map(lambda x: x[0], c.description)) # Retrieve a list of columns
        
        if len(dataRows) != 0:
            sheet = book.add_sheet("BrowserBookmark")
            ins.exportToXLSDeep(sheet, dataColumns, dataRows)
        
        
        # ********************************
        # ***** BrowserHistory TABLE *****
        # ********************************
        c.execute("SELECT * FROM BrowserHistory WHERE deviceID = '{0}'".format(self.deviceID))
        dataRows = c.fetchall() # Retrieve a list of rows
        dataColumns = list(map(lambda x: x[0], c.description)) # Retrieve a list of columns
        
        if len(dataRows) != 0:
            sheet = book.add_sheet("BrowserHistory")
            ins.exportToXLSDeep(sheet, dataColumns, dataRows)
        
        
        # *************************
        # ***** Contact TABLE *****
        # *************************
        c.execute("SELECT * FROM Contact WHERE deviceID = '{0}'".format(self.deviceID))
        dataRows = c.fetchall() # Retrieve a list of rows
        dataColumns = list(map(lambda x: x[0], c.description)) # Retrieve a list of columns
        
        if len(dataRows) != 0:
            sheet = book.add_sheet("Contact")
            ins.exportToXLSDeep(sheet, dataColumns, dataRows)
        
        
        # ************************
        # **** SET CONTACT ID ****
        # ************************
        c.execute("SELECT contactID FROM Contact WHERE deviceID = '{0}'".format(self.deviceID))
        contactIDs = c.fetchall() # Retrieve a list of skypeAccountID
        
        contactIDLists = []
        for contactID in contactIDs:
            for data in contactID:
                contactIDLists.append(str(data))
                
        if len(contactIDLists) == 1:
            contactIDQuery = contactIDLists[0]
        elif len(contactIDLists) > 1:
            contactIDQuery = ','.join(contactIDLists)
            
            
        # *******************************
        # ***** ContactNumber TABLE *****
        # *******************************
        c.execute("SELECT * FROM ContactNumber WHERE contactID IN ({0})".format(contactIDQuery))
        dataRows = c.fetchall() # Retrieve a list of rows
        dataColumns = list(map(lambda x: x[0], c.description)) # Retrieve a list of columns
        
        if len(dataRows) != 0:
            sheet = book.add_sheet("ContactNumber")
            ins.exportToXLSDeep(sheet, dataColumns, dataRows)
        
        
        # ******************************
        # ***** ContactEmail TABLE *****
        # ******************************
        c.execute("SELECT * FROM ContactEmail WHERE contactID IN ({0})".format(contactIDQuery))
        dataRows = c.fetchall() # Retrieve a list of rows
        dataColumns = list(map(lambda x: x[0], c.description)) # Retrieve a list of columns
        
        if len(dataRows) != 0:
            sheet = book.add_sheet("ContactEmail")
            ins.exportToXLSDeep(sheet, dataColumns, dataRows)
        
        
        # ********************************
        # ***** ContactDetails TABLE *****
        # ********************************
        c.execute("SELECT * FROM ContactDetails WHERE contactID IN ({0})".format(contactIDQuery))
        dataRows = c.fetchall() # Retrieve a list of rows
        dataColumns = list(map(lambda x: x[0], c.description)) # Retrieve a list of columns
        
        if len(dataRows) != 0:
            sheet = book.add_sheet("ContactDetails")
            ins.exportToXLSDeep(sheet, dataColumns, dataRows)
                
                
        # ******************************
        # ***** SkypeAccount TABLE *****
        # ******************************
        c.execute("SELECT * FROM SkypeAccount WHERE deviceID = '{0}'".format(self.deviceID))
        dataRows = c.fetchall() # Retrieve a list of rows
        dataColumns = list(map(lambda x: x[0], c.description)) # Retrieve a list of columns
        
        if len(dataRows) != 0:
            sheet = book.add_sheet("SkypeAccount")
            ins.exportToXLSDeep(sheet, dataColumns, dataRows)
        
        
        # ******************************
        # **** SET SKYPE ACCOUNT ID ****
        # ******************************
        c.execute("SELECT skypeAccountID FROM SkypeAccount WHERE deviceID = '{0}'".format(self.deviceID))
        skypeAccountIDs = c.fetchall() # Retrieve a list of skypeAccountID
        
        skypeAccountIDLists = []
        for skypeAccountID in skypeAccountIDs:
            for data in skypeAccountID:
                skypeAccountIDLists.append(str(data))
                
        if len(skypeAccountIDLists) == 1:
            skypeAccountIDQuery = skypeAccountIDLists[0]
        elif len(skypeAccountIDLists) > 1:
            skypeAccountIDQuery = ','.join(skypeAccountIDLists)
        elif len(skypeAccountIDLists) == 0:
            skypeAccountIDQuery = 0
                

        # ******************************
        # ***** SkypeContact TABLE *****
        # ******************************)
        c.execute("SELECT * FROM SkypeContact WHERE skypeAccountID IN ({0})".format(skypeAccountIDQuery))
        dataRows = c.fetchall() # Retrieve a list of rows
        dataColumns = list(map(lambda x: x[0], c.description)) # Retrieve a list of columns
        
        if len(dataRows) != 0:
            sheet = book.add_sheet("SkypeContact")
            ins.exportToXLSDeep(sheet, dataColumns, dataRows)
            
        
        # ***********************************
        # ***** SkypeConversation TABLE *****
        # ***********************************
        c.execute("SELECT * FROM SkypeConversation WHERE skypeAccountID IN ({0})".format(skypeAccountIDQuery))
        dataRows = c.fetchall() # Retrieve a list of rows
        dataColumns = list(map(lambda x: x[0], c.description)) # Retrieve a list of columns
        
        if len(dataRows) != 0:
            sheet = book.add_sheet("SkypeConversation")
            ins.exportToXLSDeep(sheet, dataColumns, dataRows)
        
        
        

    
        localTime = time.localtime() # Get current local time
        timeString = time.strftime("%Y-%m-%d %H.%M.%S", localTime) # Format localTime to timeString
        
        # Join the current working directory with the new export filename (timeString)
        filename = os.path.join(os.getcwd(), timeString)
        
        book.save(filename + ".xls")
            
if __name__ == '__main__':                    
    # Create an instance of the ReadBackup class       
    ins = ReadBackup()
    
    # Set the backup path location
    ins.setBackupPath()
                
    try:
        # Repair the DB files in the backup path
        ins.repairDBFiles()
    except:
        print "\nInvalid iTunes backup folder or backup path not found!"
        sys.exit(1)
    
    ins.readBackupArchive() 
        
    ins.exportToSqlite()
    
    ins.exportToXLS()
    
    # To preserve the console information until user enter a key
    raw_input()