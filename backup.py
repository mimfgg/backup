## -*- coding: utf8 -*-
from time import strftime
from time import localtime
from datetime import date, timedelta
import os
import subprocess
import logging
import sys

reload(sys)
sys.setdefaultencoding('utf8')

#app related properties
linkFile='last'
path='/mnt/backup/snapshots/'
logfile='/var/log/rsync.raid.log'
backupSources=['/mnt/IMPORTANT']

#defining logging
FORMAT = "%(asctime)-15s [%(levelname)-7s] %(message)s"
logging.basicConfig(format=FORMAT)
formatter = logging.Formatter(FORMAT)
hdlr = logging.FileHandler(logfile)
hdlr.setFormatter(formatter)
logger = logging.getLogger('backup')
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

#Let's start
logger.info("*************************************************************************")
logger.info("Starting daily backup")
logger.debug("About to backup the following folders:")
for backupSource in backupSources:
    logger.debug("\t"+backupSource)

now = strftime("%Y%m%d_%H%M%S", localtime())
newDirname=now
logger.info("creating folder: "+path+newDirname)
os.mkdir(path+newDirname)

#Checking if a snapshot already exists
if os.path.exists(path + linkFile):
    oldDirname = path + os.readlink(path + linkFile)
    linkDest = " --link-dest=" + oldDirname
    logger.info("previous snapshot is"+oldDirname)
else:
    linkDest = ""

for backupSource in backupSources:
    logger.info("Backing up "+ backupSource +" to "+path+newDirname+"/")
    # if FAT to EXT backup --modify-window=1 has to be used
    # to exclude files and directories use the following arguments: "--exclude '/Temp/' --exclude '/Temp2/'"
    p = subprocess.Popen("rsync -av"+linkDest+" --delete "+backupSource+" "+path+newDirname, shell=True, bufsize=0, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    (fin, fout) = (p.stdin, p.stdout)
    logger.debug("rsync output: \n"+fout.read().decode())

logger.info("Updating lastSnapshot")

#Deleting the old one
if os.path.exists(path+linkFile):
    os.system("rm "+path+linkFile)

#Creating the new one
os.system("ln -s "+newDirname+" "+path+linkFile)

#Let's do some cleaning
logger.info("Cleaning up ...")
currentDate = date.today()
aMonthAgo = currentDate - timedelta(days=30)
threeMonthsAgo = currentDate - timedelta(days=90)
logger.debug("aMonthAgo: "+str(aMonthAgo))
logger.debug("threeMonthAgo: "+str(threeMonthsAgo))

#keep every day for the past month, once a week for the next 2 months and then once a month
dirlist = os.listdir(path)
for dir in dirlist:
    if not os.path.islink(path+dir):
        thisDirDate = date(int(dir[0:4]),int(dir[4:6]),int(dir[6:8]))
        shouldDeleteIt = False
        if thisDirDate > aMonthAgo:
            logger.debug("    keeping "+path+dir+" it's not even a month old")
        elif thisDirDate <= aMonthAgo and thisDirDate >= threeMonthsAgo:
            if thisDirDate.isoweekday() == 1:
                #it's monday, let's keep it
                logger.debug("    keeping "+path+dir+" should be once a week and we keep this one")
            else:
                logger.debug("    "+path+dir+" should be once a week and we delete this one")
                shouldDeleteIt = True
        else:
            if thisDirDate.day >= 1 and thisDirDate.day <=7 and thisDirDate.isoweekday() == 1:
                #first monday of the month, that's the backup we keep
                logger.debug("    keeping "+path+dir+" should be once a month and we keep this one")
            else:
                logger.debug("    "+path+dir+" should be once a month and we delete this one")
                shouldDeleteIt = True

        if shouldDeleteIt:
            logger.info("    deleting "+path+dir)
            os.system("rm -fr "+path+dir)

logger.info("Done.")
