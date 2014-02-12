#!/usr/bin/python

import os,sys

##print os.getcwd()
##print os.path.basename(__file__)
##print os.path.abspath(__file__)
##print os.path.dirname(__file__)
print
print
fqself = os.path.abspath(__file__)

print "fqself %s" % fqself
my_libs = os.path.dirname(fqself) + "/py_libs/"

print "my_libs %s" % my_libs

print sys.path
print
sys.path.insert(1, my_libs)
print
print sys.path


