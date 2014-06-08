#!/usr/bin/python

''' 
    Author - Victor Pagan <paganv34@gmail.com>

    Created using:
    -YAPDI (https://raw.github.com/kasun/YapDi/)
    -serial (apt-get install python-serial)

    USAGE - python serial-log start|stop|restart

    python serial-log start would run log() in daemon mode 
    if there is no instance already running. 

    python serial-log stop would kill any running instance.

    python serial-log restart would kill any running instance; and
    start an instance. 
'''

import sys
import os
import syslog
import serial
import datetime
import yapdi
import string

COMMAND_START = 'start'
COMMAND_STOP = 'stop'
COMMAND_RESTART = 'restart'

class excepter:
    def __init__(self):
        import os
        import sys
        import traceback
        self.stacktrace = []
        self.filename = None
        
        tb = sys.exc_info()[2]
        stack = []
        __ExceptionStackStrace__ = []
        while tb:
            stack.append(tb.tb_frame)
            tb = tb.tb_next
        for frame in stack:
            self.stacktrace.append((frame.f_code.co_name, frame.f_code.co_filename, frame.f_lineno, frame.f_locals.copy()))
            if not self.filename:
                self.filename = frame.f_code.co_filename

        self.traceback = traceback.format_exc()

    def strinfo(self):
        for (name,filename,lineno,localz) in self.stacktrace:
            output = 'Function %s, from %s:%d\n' % (name, filename, lineno)
            keys = localz.keys()
            keys.sort()
            for key in keys:
                value = localz[key]
                try:
                    value = str(value)
                except:
                    value = '--Error converting value to string--'
                output += str(key) + ' => ' + value + '\n'
        output += '\n' + str(self.traceback)
        return output
    
    def printinfo(self):
        print self.strinfo()

    def mailinfo(self,email,relayserver):
        import smtplib
        import socket
        efrom = None
        try:
            efrom = self.filename+'@'+socket.gethostname()
        except:
            efrom = self.filename+'@'+'unkownhost'
        
        subject = self.traceback.split('\n')[-2]

        message = '''Subject: %s
From: %s
To: %s

''' % (subject, efrom, email)
        message += self.strinfo()
        
        server=smtplib.SMTP(relayserver)
        server.sendmail(efrom, email, message)

def usage():
    print("USAGE: python %s %s|%s|%s" % (sys.argv[0], COMMAND_START, COMMAND_STOP, COMMAND_RESTART))


def report(typ):
    ''' Outputs to syslog. (Started) (Restarted) (Stopped)'''

    syslog.openlog("Serial-log has", 0, syslog.LOG_USER)
    syslog.syslog(syslog.LOG_NOTICE, typ)#+": "+pid)

def log():
    
    try:
        ser = serial.Serial('/dev/ttyS0', 9600)
    except Exception:
        report("Unable to contact ttyS0")
        err = excepter()
        err.printinfo()
        retcode = daemon.restart()
        exit()

    prevhour = datetime.datetime.now()
    prevhour = prevhour.hour

    try:
        while(1):
            line = ser.readline()   # read up to a '\n' terminated line
        
            if len(line) != 0:
            
                newhour = datetime.datetime.now()
                newhour = newhour.hour
                if newhour != prevhour:
                    clearCurrentLog()
                    prevhour = newhour
                    report("Log rotated")
                writeToLog(line)

    except Exception:
        err = excepter()
        err.printinfo()
        #err.mailinfo('','') # removed for privacy
        report(err.printinfo())
        retcode = daemon.restart()

    ser.close()

def clearCurrentLog():
    log = open("/var/www/logs/current.log","w")
    log.close()

def writeToLog(line):

    now = datetime.datetime.now()
    day = now.day
    hour = now.hour
    if hour >= 20:
        hour = 20
    elif hour < 8: # this is the next day but we are continuing the nightly logs
        hour = 20
        day = day - 1
        
    path = "/var/www/logs/%d/%d/%d/"%(now.year,now.month,day)
    
    if not os.path.exists(path):
        os.makedirs(path)

    line = filter(lambda x: ord(x) == 10 or 32 <= ord(x) <= 126, line) # filter out non ascii characters
    
    log = open(path+"%d.log"%(hour),"a")
    log.write(line)
    log.close()

    # add line to current buffer and clear it if it is a new log
    log = open("/var/www/logs/current.log","a")
    log.write(line)
    log.close()

def main():
    # Invalid executions
    if len(sys.argv) < 2 or sys.argv[1] not in [COMMAND_START, COMMAND_STOP, COMMAND_RESTART]:
        usage()
        exit()

    daemon = ''
    pidfile = 0

    if sys.argv[1] == COMMAND_START:
        daemon = yapdi.Daemon(pidfile='/var/run/serial-log.pid')
        # Check whether an instance is already running
        if daemon.status():
            print("An instance is already running.")
            exit()
        retcode = daemon.daemonize()

        # Execute if daemonization was successful else exit
        if retcode == yapdi.OPERATION_SUCCESSFUL:
            report("Started")
            log()
        else:
            print('Daemonization failed')

    elif sys.argv[1] == COMMAND_STOP:
        daemon = yapdi.Daemon(pidfile='/var/run/serial-log.pid')

        # Check whether no instance is running
        if not daemon.status():
            print("No instance running.")
            exit()

        retcode = daemon.kill()
        report("Stopping")
        if retcode == yapdi.OPERATION_FAILED:
            print('Trying to stop running instance failed')
            report("Failed to kill previous instance")
    
    elif sys.argv[1] == COMMAND_RESTART:
        daemon = yapdi.Daemon()
        retcode = daemon.restart()

        # Execute if daemonization was successful else exit
        if retcode == yapdi.OPERATION_SUCCESSFUL:
            report("Restarted")
            log()
        else:
            print('Daemonization failed')
            report("Error on restart")


if __name__ == "__main__":
    main()