# Variables
LOG_LEVEL_GLOBAL = 4
FILE_HANDLE = None


# Write the given message to a specific log file if appropriate
# loglevel is set.
# A seperate log file is created for each execution of ADEL.
# @message:             message to write to the log file
# @log_level:            desired log level of message
def log(message, log_level):
    global LOG_LEVEL_GLOBAL
    global LOG_DIR

    if (int(log_level) <= int(LOG_LEVEL_GLOBAL)) and (int(log_level) > 0):
        # Write message to log file
        if FILE_HANDLE is None:
            print "Log: ERROR! file handle not set\ (is \'None\')"
        else:
            FILE_HANDLE.write(message + "\n")
    if log_level == 1:
        print message
    if ((log_level == 2) and (not (message.startswith("#"))) and
       (not (message.startswith("\n#")))):
            print message
    if log_level == 0:
        print message