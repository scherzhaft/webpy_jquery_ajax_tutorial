##  The most Basic of modules you should always import  ##
import sys, os, time, re, random, string, StringIO, subprocess


## We need to send mail ##
import smtplib
from email.mime.text import MIMEText


##  Setup environment.... look in ./py_libs first  ##
fqself = os.path.abspath(__file__)
my_libs = os.path.dirname(fqself) + '/py_libs/'
sys.path.insert(1, my_libs)


##  Import dependencies  ##
import web
import paramiko
import crypt, getpass, pwd
import xml.sax.saxutils


## Webpy Debug mode ##
web.config.debug = True

from web import form

render = web.template.render('/var/www/webpy-app/templates/')

urls = ('/', 'index')
app = web.application(urls, globals())

myform = form.Form( 
    form.Textbox("boe"), 
    form.Textbox("bax", 
        form.notnull,
        form.regexp('\d+', 'Must be a digit'),
        form.Validator('Must be more than 5', lambda x:int(x)>5)),
    form.Textarea('moe'),
    form.Checkbox('curly'), 
    form.Dropdown('french', ['mustard', 'fries', 'wine'])) 

class index: 
    def GET(self): 
        form = myform()
        # make sure you create a copy of the form by calling it (line above)
        # Otherwise changes will appear globally
        return render.formtest(form)

    def POST(self): 
        form = myform() 
        if not form.validates(): 
            return render.formtest(form)
        else:
            # form.d.boe and form['boe'].value are equivalent ways of
            # extracting the validated arguments from the form.
            return "Grrreat success! boe: %s, bax: %s, Drop: %s" % (form.d.boe, form['bax'].value, form['french'].value)

####if __name__=="__main__":
####    web.internalerror = web.debugerror
####    app.run()

application = web.application(urls, globals()).wsgifunc()

