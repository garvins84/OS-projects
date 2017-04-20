#!/usr/bin/env python

import os, stat, errno
import random
import sys
import fuse
import time
from fuse import Fuse

fuse.fuse_python_api = (0, 2)

class RandFS(Fuse):
	#Current working directory 
    mntPath = os.getcwd()

    #file handle for our timestamps file
    timeStamps = open(mntPath+"/times",'r')

    #Get the attributes of the object at path
    def getattr(self, path):
        print "getattr", path

        #initialize the stat object
        st = fuse.Stat()

        #if we're looking at the root
        if path == '/':
            st.st_mode = stat.S_IFDIR | 0755    #directory
            st.st_nlink = 2                     #2 links

        #if we're looking at the counts per minute file
        elif path[1:] == "count":
            st.st_mode = stat.S_IFREG | 0644    #file            
            st.st_nlink = 1                     #1 link
            st.st_size = 4                      #size of count file

        #if we're looking at the random bits file
        elif path[1:] == "random":
            st.st_mode = stat.S_IFREG | 0644    #file            
            st.st_nlink = 1                     #1 link
            st.st_size = 1024                   #size of random file

        #else return an error
        else:
            return -errno.ENOENT #No such file or directory

        return st

    #read the directory pointed to by path
    def readdir(self, path, offset):
        print "***readdir", path, offset
        if path == "/":
            for name in [".", "..", "random", "count"]:
                yield fuse.Direntry(name)

    #open a file, make sure opening in a read-only manner
    def open(self, path, flags):
        print "***open", path, flags

        #if you're trying to open a different file, return an error
        if path != "/" and path[1:] != "count" and path[1:] != "random":
            return -errno.ENOENT #No such file or directory

        #file can only be read-only
        accmode = os.O_RDONLY | os.O_WRONLY | os.O_RDWR
        if (flags & accmode) != os.O_RDONLY:
            return -errno.EACCES #No access to this file or directory

    #read from a file pointed to by path
    def read(self, path, size, offset):
        print "***read", path, size, offset

        #"times" file line length in bytes
        #used for seeking to the correct position
        llen = 14

        #seed random number generator
        random.seed(time.time())

        #if we're looking at the random bits file
        if path[1:] == "random":

            #get the number of bytes in "times" file, read only
            with open(self.mntPath+"/times",'r') as f:
                for i, l in enumerate(f):
                    pass
            #make "i" in terms of number of lines
            i = i / llen

            #not enough timestamps
            if i < 4:
            	return -errno.ENODATA #No data
            flen = i-3 #"times" file length - 3
            
            #strang - a string containing our packed bytes
            strang = "" #our return value

            #now get the random bytes
            for x in range(0, size):

                #reset our byte each time
                byte = "" #assemble a byte

                #assemble 8 bits into a byte
                for y in range(0, 8):
                    #seed "times" file
                    startPoint = random.randrange(0, flen)
    
                    #seek to first spot (seek is in bytes)
                    self.timeStamps.seek(startPoint * llen)
                    
                    #get 4 timestamps
                    t1 = self.timeStamps.readline()[:-1]
                    t2 = self.timeStamps.readline()[:-1]
                    t3 = self.timeStamps.readline()[:-1]
                    t4 = self.timeStamps.readline()[:-1]
    
                    #get 2 intervals
                    i1 = float(t2) - float(t1)
                    i2 = float(t4) - float(t3)
    
                    #compare
                    if i1 < i2:
                        byte += "0"
                    else:
                        byte += "1"
                    
                #add our new byte to strang, cast "byte" string to a char
                strang += str(chr(int(byte, 2)))

            #return random data (as string)
            return  strang
            
        #if we're looking at the counts per minute file
        elif path[1:] == "count":

            #file handler to scan end of file            
            fo = open(self.mntPath+"/times",'r')

            #current time, and the time a minute ago
            currentTime = time.time()
            minuteAgo = currentTime - 60.0

            #total number of timestamps within a minute ago
            cpm = 0

            #control boolean
            done = False

            #line number from end of file
            i = 0

            while (not done):
                i += 1
                fo.seek(-llen*i, os.SEEK_END)
                timestamp = fo.readline()
                if (float(timestamp) > float(minuteAgo)):
                    cpm += 1
                else:
                    done = True #stop reading "times" file

            fo.close()
            return str(cpm)

        #if looking at something else return an error
        else:
            return -errno.ENOENT #No such file or directory


def main():
    print "Main Initiated"
    server = RandFS()
    server.parse()
    server.main()
    print "Main Finalized"

if __name__ == '__main__':
    main()
