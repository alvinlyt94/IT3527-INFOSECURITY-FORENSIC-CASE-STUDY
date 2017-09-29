# Imports
import os
import subprocess
import threading
import StringIO
from progressbar import Bar, Percentage, ProgressBar

import aft_log

class RunCmd(threading.Thread):
    def __init__(self, cmd, timeout):
        threading.Thread.__init__(self)
        self.cmd = cmd
        self.timeout = timeout

    def run(self):
        fh = open("NUL","w")
        self.p = subprocess.Popen(self.cmd, stdout=fh, stderr=fh)
        self.p.wait()
        fh.close()

    def Run(self):
        self.start()
        self.join(self.timeout)

        if self.is_alive():
            self.p.terminate()      #use self.p.kill() if process needs a kill -9
            self.join()

# Extract databases files
def extract_SQLite_Files(curr_dir, file_dir, picture_dir, os_version, device_name):
    adbPath = os.path.join(curr_dir, "tools", "adb.exe")
    print "Extracting SQLite Files..."
    
    # Initialize a progress bar
    databaseList = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22]
    pbar = ProgressBar(widgets=[Percentage(), Bar()], maxval=len(databaseList)).start()
    
    for database in databaseList:
        extractDatabase(database, adbPath, file_dir, os_version);
        pbar.update(database)
    
    pbar.finish()
    extract_pictures(adbPath, picture_dir, device_name)
    
def extractDatabase(counter, adbPath, file_dir, os_version):
    # Standard Applications Databases
    if counter == 0:
        # Accounts Database
        try:
            RunCmd([adbPath, 'pull', '/data/system/accounts.db', file_dir], 5).Run()
            isExtracted = checkExtracted('accounts.db', file_dir)
            if isExtracted:
                aft_log.log("accounts.db successfully extracted!", 3)
            else:
                aft_log.log("Extractor: -> accounts.db doesn't exist!", 3)
        except:
            aft_log.log("Extractor: -> Can't extract accounts.db!", 3)
            
    elif counter == 1:
        # Contacts database
        if os_version < 2.0:
            contactsdb_name = "contacts.db"
        else:
            contactsdb_name = "contacts2.db"
        try:
            RunCmd([adbPath, 'pull', '/data/data/com.android.providers.contacts/databases/' + contactsdb_name, file_dir], 5).Run()
            isExtracted = checkExtracted(contactsdb_name, file_dir)
            if isExtracted:
                aft_log.log(contactsdb_name + " successfully extracted!", 3)
            else:
                aft_log.log("Extractor: -> contacts.db doesn't exist!!", 3)
        except:
            aft_log.log("Extractor: -> Can't extract contacts.db!", 3)      

    elif counter == 2:
        # MMS and SMS database ()
        try:
            RunCmd([adbPath, 'pull', '/data/data/com.android.providers.telephony/databases/mmssms.db', file_dir], 5).Run()
            isExtracted = checkExtracted('mmssms.db', file_dir)
            if isExtracted:
                aft_log.log("mmssms.db successfully extracted!", 3)
            else:
                aft_log.log("Extractor: -> mmssms.db doesn't exist!!", 3)
        except:
            aft_log.log("Extractor: -> Can't extract contacts.db!", 3)
            
    elif counter == 3:
        # Calendar database ()
        try:
            RunCmd([adbPath, 'pull', '/data/data/com.android.providers.calendar/databases/calendar.db', file_dir], 5).Run()
            isExtracted = checkExtracted('calendar.db', file_dir)
            if isExtracted:
                aft_log.log("calendar.db successfully extracted!", 3)
            else:
                aft_log.log("Extractor: -> calendar.db doesn't exist!!", 3)
        except:
            aft_log.log("Extractor: -> Can't extract calendar.db!", 3)
            
    elif counter == 4:
        # Settings database ()
        try:
            RunCmd([adbPath, 'pull', '/data/data/com.android.providers.settings/databases/settings.db', file_dir], 5).Run()
            isExtracted = checkExtracted('settings.db', file_dir)
            if isExtracted:
                aft_log.log("settings.db successfully extracted!", 3)
            else:
                aft_log.log("Extractor: -> settings.db doesn't exist!!", 3)
        except:
            aft_log.log("Extractor: -> Can't extract settings.db!", 3)
            
    elif counter == 5:
        # Location caches (cell & wifi)
        try:
            RunCmd([adbPath, 'pull', '/data/data/com.google.android.location/files/cache.cell', file_dir], 5).Run()
            isExtracted = checkExtracted('chache.cell', file_dir)
            if isExtracted:
                aft_log.log("chache.cell successfully extracted!", 3)
            else:
                aft_log.log("Extractor: -> chache.cell doesn't exist!!", 3)
        except:
            aft_log.log("Extractor: -> Can't extract cell cache!", 3)
        try:
            RunCmd([adbPath, 'pull', '/data/data/com.google.android.location/files/cache.wifi', file_dir], 5).Run()
            isExtracted = checkExtracted('chache.wifi', file_dir)
            if isExtracted:
                aft_log.log("chache.wifi successfully extracted!", 3)
            else:
                aft_log.log("Extractor: -> chache.wifi doesn't exist!!", 3)
        except:
            aft_log.log("Extractor: -> Can't extract wifi cache!", 3)
            
    elif counter == 6:
        # Browser History
        try:
            RunCmd([adbPath, 'pull', '/data/data/com.android.browser/databases/browser2.db', file_dir], 5).Run()
            isExtracted = checkExtracted('browser2.db', file_dir)
            if isExtracted:
                aft_log.log("browser2.db successfully extracted!", 3)
            else:
                aft_log.log("Extractor: -> browser2.db doesn't exist!!", 3)
        except:
            aft_log.log("Extractor: -> Can't extract browser2.db!", 3)
    
    elif counter == 7:
        # Downloaded data and apps database ()
        try:
            RunCmd([adbPath, 'pull', '/data/data/com.android.providers.downloads/databases/downloads.db', file_dir], 5).Run()
            isExtracted = checkExtracted('downloads.db', file_dir)
            if isExtracted:
                aft_log.log("downloads.db successfully extracted!", 3)
            else:
                aft_log.log("Extractor: -> downloads.db doesn't exist!!", 3)
        except:
            aft_log.log("Extractor: -> Can't extract downloads.db!", 3)
    
    elif counter == 8:
        # User dictionary database ()
        try:
            RunCmd([adbPath, 'pull', '/data/data/com.android.providers.userdictionary/databases/user_dict.db', file_dir], 5).Run()
            isExtracted = checkExtracted('userdb.db', file_dir)
            if isExtracted:
                aft_log.log("userdb.db successfully extracted!", 3)
            else:
                aft_log.log("Extractor: -> userdb.db doesn't exist!!", 3)
        except:
            aft_log.log("Extractor: -> Can't extract userdb.db!", 3)  
    
    elif counter == 9:
        # Phone database ()
        try:
            RunCmd([adbPath, 'pull', '/data/data/com.android.providers.telephony/databases/telephony.db', file_dir], 5).Run()
            isExtracted = checkExtracted('telephony.db', file_dir)
            if isExtracted:
                aft_log.log("telephony.db successfully extracted!", 3)
            else:
                aft_log.log("Extractor: -> telephony.db doesn't exist!!", 3)
        except:
            aft_log.log("Extractor: -> Can't extract telephony.db!", 3) 
    
    elif counter == 10:
        # Automated dictionary database ()
        try:
            RunCmd([adbPath, 'pull', '/data/data/com.android.inputmethod.latin/databases/auto_dict.db', file_dir], 5).Run()
            isExtracted = checkExtracted('auto_dict.db', file_dir)
            if isExtracted:
                aft_log.log("auto_dict.db successfully extracted!", 3)
            else:
                aft_log.log("Extractor: -> auto_dict.db doesn't exist!!", 3)
        except:
            aft_log.log("Extractor: -> Can't extract auto_dict.db!", 3) 
    
    elif counter == 11:
        # Weather data database ()
        try:
            RunCmd([adbPath, 'pull', '/data/data/com.google.android.apps.genie.geniewidget/databases/weather.db', file_dir], 5).Run()
            isExtracted = checkExtracted('weather.db', file_dir)
            if isExtracted:
                aft_log.log("weather.db successfully extracted!", 3)
            else:
                aft_log.log("Extractor: -> weather.db doesn't exist!!", 3)
        except:
            aft_log.log("Extractor: -> Can't extract weather.db!", 3) 
        try:
            RunCmd([adbPath, 'pull', '/data/data/com.sec.android.widgetapp.weatherclock/databases/WeatherClock', file_dir], 5).Run()
            isExtracted = checkExtracted('WeatherClock', file_dir)
            if isExtracted:
                aft_log.log("weather widget successfully extracted!", 3)
            else:
                aft_log.log("Extractor: -> weather widget doesn't exist!!", 3)
        except:
            aft_log.log("Extractor: -> Can't extract weather widget!", 3) 

    elif counter == 12:
        # Google-Mail program database ()
        try:
            RunCmd([adbPath, 'pull', '/data/data/com.google.android.gm/databases/gmail.db', file_dir], 5).Run()
            isExtracted = checkExtracted('gmail.db', file_dir)
            if isExtracted:
                aft_log.log("gmail.db successfully extracted!", 3)
            else:
                aft_log.log("Extractor: -> gmail.db doesn't exist!!", 3)
        except:
            aft_log.log("Extractor: -> Can't extract gmail.db!", 3) 
    
    elif counter == 13:
        # Other Email Accounts than Gmail ()
        try:
            RunCmd([adbPath, 'pull', '/data/data/com.android.email/databases/EmailProvider.db', file_dir], 5).Run()
            isExtracted = checkExtracted('EmailProvider.db', file_dir)
            if isExtracted:
                aft_log.log("EmailProvider.db successfully extracted!", 3)
            else:
                aft_log.log("Extractor: -> EmailProvider.db doesn't exist!!", 3)
        except:
            aft_log.log("Extractor: -> Can't extract EmailProvider.db!", 3) 

    elif counter == 14:
        # Clock and alarms database ()
        try:
            RunCmd([adbPath, 'pull', '/data/data/com.android.deskclock/databases/alarms.db', file_dir], 5).Run()
            isExtracted = checkExtracted('alarms.db', file_dir)
            if isExtracted:
                aft_log.log("alarms.db successfully extracted!", 3)
            else:
                aft_log.log("Extractor: -> alarms.db doesn't exist!!", 3)
        except:
            aft_log.log("Extractor: -> Can't extract alarms.db!", 3) 
            
    elif counter == 15:
        # Twitter database ()
        try:
            for i in range(6):
                try:
                    file_name = subprocess.Popen([adbPath, 'shell', 'ls', '/data/data/com.twitter.android/databases/'], stdout=subprocess.PIPE).communicate(0)[0].split()[i]
                    if ".db" in file_name:
                        twitter_db = '/data/data/com.twitter.android/databases/' + file_name
                        RunCmd([adbPath, 'pull', twitter_db, file_dir], 5).Run()
                        isExtracted = checkExtracted('twitter.db', file_dir)
                        if isExtracted:
                            aft_log.log(file_name + " successfully extracted!", 3)
                        else:
                            aft_log.log("Extractor: -> " + file_name + " doesn't exist!!", 3)
                    else:
                        continue
                except:
                    continue
        except:
            aft_log.log("Extractor: -> twitter.db doesn't exist!!", 3)
    
    elif counter == 16:   
        # Google-Talk database ()
        try:
            RunCmd([adbPath, 'pull', '/data/data/com.google.android.gsf/databases/talk.db', file_dir], 5).Run()
            isExtracted = checkExtracted('talk.db', file_dir)
            if isExtracted:
                aft_log.log("talk.db successfully extracted!", 3)
            else:
                aft_log.log("Extractor: -> talk.db (Google-Talk) doesn't exist!!", 3)
        except:
            aft_log.log("Extractor: -> Can't extract talk.db!", 3) 
   
    elif counter == 17:
        # Search and download the Google-Mail mail database ()
        try:
            for i in range(6):
                file_name = subprocess.Popen([adbPath, 'shell', 'ls', '/data/data/com.google.android.gm/databases/'], stdout=subprocess.PIPE).communicate(0)[0].split()[i]
                if file_name.startswith('mailstore'):
                    mail_db = '/data/data/com.google.android.gm/databases/' + file_name
                    RunCmd([adbPath, 'pull', mail_db, file_dir], 5).Run()
                    isExtracted = checkExtracted(file_name, file_dir)
                    if isExtracted:                
                        aft_log.log(file_name + " successfully extracted!", 3)
                    break
                else:
                    continue
        except:
            aft_log.log("Extractor:  -> Google-Mail database doesn't exist!!", 3)
        
    elif counter == 18:   
        # Google+ database
        try:
            for i in range(6):
                try:
                    file_name = subprocess.Popen([adbPath, 'shell', 'ls', '/data/data/com.google.android.apps.plus/databases/'], stdout=subprocess.PIPE).communicate(0)[0].split()[i]
                    if ".db" in file_name:
                        plus_db = '/data/data/com.google.android.apps.plus/databases/' + file_name
                        RunCmd([adbPath, 'pull', plus_db, file_dir], 5).Run()
                        isExtracted = checkExtracted(file_name, file_dir)
                        if isExtracted:                
                            aft_log.log(file_name + " successfully extracted!", 3)
                    else:
                        continue
                except:
                    continue
        except:
            aft_log.log("Extractor: -> Google+ database doesn't exist!!", 3)
    
    elif counter == 19:   
        # Google-Maps database
        try:
            try:
                RunCmd([adbPath, 'pull', '/data/data/com.google.android.apps.maps/databases/da_destination_history', file_dir], 5).Run()
                isExtracted = checkExtracted('da_destination_history', file_dir)
                if isExtracted: 
                    aft_log.log("da_destination_history successfully extracted!", 3)
            except:
                aft_log.log("Extractor: -> Google-Maps navigation history doesn't exist!!", 3)
            for i in range(6):
                try:
                    file_name = subprocess.Popen([adbPath, 'shell', 'ls', '/data/data/com.google.android.apps.maps/databases/'], stdout=subprocess.PIPE).communicate(0)[0].split()[i]
                    if ".db" in file_name:
                        maps_db = '/data/data/com.google.android.apps.maps/databases/' + file_name
                        RunCmd([adbPath, 'pull', maps_db, file_dir], 5).Run()
                        isExtracted = checkExtracted(file_name, file_dir)
                        if isExtracted: 
                            aft_log.log("da_destination_history successfully extracted!", 3)
                    else:
                        continue
                except:
                    continue
        except:
            aft_log.log("Extractor: -> Google-Maps database doesn't exist!!", 3)

    elif counter == 20:   
        # Facebook database
        try:
            RunCmd([adbPath, 'pull', '/data/data/com.facebook.katana/databases/fb.db', file_dir], 5).Run()
            isExtracted = checkExtracted('fb.db', file_dir)
            if isExtracted:
                aft_log.log("fb.db successfully extracted!", 3)
            else:
                aft_log.log("Extractor: -> facebook database doesn't exist!!", 3)
        except:
            aft_log.log("Extractor: -> Can't extract fb.db!", 3) 
    
    elif counter == 21:
        # Browser GPS database
        try:
            RunCmd([adbPath, 'pull', '/data/data/com.android.browser/app_geolocation/CachedGeoposition.db', file_dir], 5).Run()
            isExtracted = checkExtracted('CachedGeoposition.db', file_dir)
            if isExtracted:
                aft_log.log("CachedGeoposition.db successfully extracted!", 3)
            else:
                aft_log.log("Extractor: -> CachedGeoposition.db (Browser) doesn't exist!!", 3)
        except:
            aft_log.log("Extractor: -> Can't extract fb.db!", 3) 
            
    elif counter == 22:
        # Extract Skype database
        try:
            p =subprocess.Popen([adbPath, 'shell', 'ls', '/data/data/com.skype.raider/files/'], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
            events = ''
            for line in StringIO.StringIO(out).readlines():
                if line == '\r\n' or line == '\n':
                    continue
                events += line
            files_list = events.split('\r\n')
            files_list.pop()
            
            skype_user_list = []
            for files in files_list:
                if "." not in files:
                    skype_user_list.append(files.replace("\r", ""))
                else:
                    pass
            try:
                skype_user_list.remove('shared_httpfe')
            except:
                pass
            
            for user in skype_user_list:
                skype_path = os.path.join(file_dir, 'Skype', user)
                if (os.path.exists(skype_path)):
                    pass
                else:
                    os.makedirs(skype_path, 0777)
                skype_database = '/data/data/com.skype.raider/files/' + user + '/main.db'
                RunCmd([adbPath, 'pull', skype_database, skype_path], 5).Run()
            aft_log.log("Skype database successfully extracted!", 3)
        except:
            aft_log.log("Extractor: -> Can't extract Skype database!", 3) 

def extract_pictures(adbPath, picture_dir, device_name):
    # Stored files (pictures, documents, etc.)
    if device_name != "local":
        try:
            aft_log.log("Extracting pictures (internal_sdcard)....", 0)
            RunCmd([adbPath, 'pull', '/sdcard/DCIM/Camera/', picture_dir], 10).Run()
            aft_log.log("Pictures on the internal SD-card successfully extracted!", 3)
        except:
            aft_log.log("Extractor: -> No pictures on the internal SD-card found !!", 3)
        
        try:
            aft_log.log("Extracting pictures (external_sdcard)....", 0)
            RunCmd([adbPath, 'pull', '/external_sd/DCIM/Camera/', picture_dir], 10).Run()
            aft_log.log("Pictures on the external SD-card successfully extracted!", 3)
        except:
            aft_log.log("Extractor: -> No pictures on the external SD-card found !!", 3)
        try:
            aft_log.log("Extracting screen captures (internal_sdcard)....", 0)
            RunCmd([adbPath, 'pull', '/sdcard/pictures/screenshots/', picture_dir], 10).Run()
            aft_log.log("Screen captures on the internal SD-card successfully extracted!", 3)
        except:
            aft_log.log("Extractor: -> No screen captures on the internal SD-card found !!", 3)

def checkExtracted(database, database_dir):
    dataabseFile = os.path.join(database_dir, database)
    isExisted = os.path.isfile(dataabseFile)
    return isExisted


"""
# Gesture Lock File
try:
    gesture = subprocess.Popen([adbPath, 'pull', '/data/system/gesture.key', file_dir], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    gesture.wait()
    aft_log.log("gesture.key successfully extracted!", 3)
except:
    aft_log.log("Extractor: -> No gesture lock found!", 3)

# Password Lock File
try:
    password = subprocess.Popen([adbPath, 'pull', '/data/system/password.key', file_dir], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    password.wait()
    aft_log.log("password.key successfully extracted!", 3)
except:
    aft_log.log("Extractor: -> No password lock found!", 3)

def get_twitter_sqlite_files(adbPath, backup_dir, os_version):
aft_log.log("====== Extract Twitter SQLite Databases ======", 3)
twitterdbnamelist = []
try:
    for i in range(6):
        try:
            file_name = subprocess.Popen([adbPath, 'shell', 'ls', '/data/data/com.twitter.android/databases/'], stdout=subprocess.PIPE).communicate(0)[0].split()[i]
            if ".db" in file_name:
                twitterdbnamelist.append(file_name)
                twitter_db = '/data/data/com.twitter.android/databases/' + file_name
                twitter_db_name = subprocess.Popen([adbPath, 'pull', twitter_db, backup_dir], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                twitter_db_name.wait()
                aft_log.log(file_name + " -> " + twitter_db_name.communicate(0)[1].split("(")[1].split(")")[0], 3)
            else:
                continue
        except:
            continue
except:
    aft_log.log("Extractor: -> twitter.db doesn't exist!!", 3)
return twitterdbnamelist
"""    