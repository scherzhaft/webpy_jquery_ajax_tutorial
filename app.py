##  The most Basic of modules you should always import  ##
import sys, os, time, re, random, string, StringIO, subprocess, syslog
from collections import OrderedDict


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


## Configure database connector ##
import MYconfig
db = web.database(dbn=MYconfig.options.get('dbn'),
	user=MYconfig.options.get('user'),
	pw=MYconfig.options.get('pw'),
	db=MYconfig.options.get('db'))

## escape() and unescape() takes care of &, < and >.
html_escape_table = {
	'"': "&quot;",
	"'": "&apos;"
}
html_unescape_table = dict(zip(html_escape_table.values(), html_escape_table.keys()))


## Some functions that all may need ##
def html_escape(text):
	return xml.sax.saxutils.escape(text, html_escape_table)

def html_unescape(text):
	return xml.sax.saxutils.unescape(text, html_unescape_table)

def make_text(string):
	return string

def code_gen(size=6, chars=string.digits + string.ascii_letters):
	return ''.join(random.choice(chars) for x in range(size))

def pass_gen(size=6, chars=string.digits + string.ascii_letters + string.punctuation):
	return ''.join(random.choice(chars) for x in range(size))

def setpw(user, host, prikey, mypass, system):
	f = open(my_libs + '/replace.hash.sh')
	script = f.read()
	f.close()
	port = 22
	try:
		trans = paramiko.Transport((host,port))
	except:
		return '''Error: unable to connect to %s ''' % (host)
	##trans.settimeout(5.0)
	trans.set_keepalive(1)
	dsa_key = paramiko.DSSKey.from_private_key_file(prikey)
	trans.connect(username=system, pkey=dsa_key)
	session = trans.open_session()
	session.settimeout(5.0)
	session.get_pty()
	session.exec_command('''(set -x ;export PATH="${PATH}:/usr/local/bin" ; sudo /bin/bash -x  ; MYPPID=`ps -f -p $$|tail -1|awk {'print $3'}` ; PPPMYPPID=`ps -f -p ${MYPPID} |tail -1|awk {'print $3'}`   ;echo "${MYPPID}" ; /bin/kill  "${MYPPID}"  ; exit 0 ) >> /tmp/out 2>&1''')

	cmd = '''USERID='%s'
SHA512HASH='%s'
CRYPTHASH='%s'
MD5HASH='%s'
%s
exit $?
''' % (user, crypt.crypt(mypass), crypt.crypt(mypass , salt=crypt.METHOD_CRYPT), crypt.crypt(mypass , salt=crypt.METHOD_MD5), script)

	cmdIO = StringIO.StringIO(cmd)
	for block in iter(lambda: cmdIO.read(1023), ""):
		test = session.send(block)
		time.sleep(1)

	session.send('\n')
	while not session.exit_status_ready():
		time.sleep(1)
		session.send('\n')

	session.close()
	stdout = session.makefile('rb', -1).readlines()
	stderr = session.makefile_stderr('rb', -1).readlines()
	status = session.recv_exit_status()

	return '''%s@%s  has  been  reset. ''' % (user, host)
	return {'stdout' : stdout,
		'stderr' : stderr,
		'status' : status,
		'sent'   : test}


def testpw(passwd):
	hasspace = re.compile('[\s].').search(passwd)
	hasuppers = re.compile('[A-Z].*[A-Z]').search(passwd)
	haslowers = re.compile('[a-z].*[a-z]').search(passwd)
	hasdigits = re.compile('[0-9].*[0-9]').search(passwd)
	hasspecil = re.compile('[^0-9,^a-z,^A-Z,^\s].*[^0-9,^a-z,^A-Z,^\s]').search(passwd)
	haslength = re.compile('.{15,}').search(passwd)
	if hasspace is not None:
		return 'hasspace'
	if hasuppers is None:
		return 'missing hasuppers'
	if haslowers is None:
		return 'missing haslowers'
	if hasdigits is None:
		return 'missing hasdigits'
	if hasspecil is None:
		return 'missing hasspecil'
	if haslength is None:
		return '..not long enough..'
	return 'allgood'


def logger(logmesg):
	syslog.openlog( 'unixPassWebapp', 0, syslog.LOG_LOCAL0 )
	syslog.syslog( '''%s''' % web.ctx.ip + ''' - - ''' + logmesg )
	syslog.closelog()
	return


def getserverlist():
	servers = []
	domains = []
	serversbydomain = []
	serverlist = subprocess.Popen('cd /unix_ops/master.git ; /usr/bin/git show master:system/', shell=True, stdout=subprocess.PIPE)
	for line in iter(serverlist.stdout.readline, ''):
		validserver = re.compile('(([a-z0-9]+|([a-z0-9]+[-]+[a-z0-9]+))[.])+').match(line)
		if validserver is not None:
			servers.append(line.rstrip('\/\n'))
			domains.append((line.rstrip('\/\n').split('.')[1]))
	serverlist.communicate()
	servers = list(OrderedDict.fromkeys(servers))
	servers.sort()
	domains = list(OrderedDict.fromkeys(domains))
	domains.sort()
	domains.reverse()
	for domain in domains:
		for fqdn in servers:
			mydomain = fqdn.split('.')[1]
			if mydomain == domain:
				serversbydomain.append(fqdn)
	serversbydomain.insert(0, 'Select a server.')
	serversbydomain = list(OrderedDict.fromkeys(serversbydomain))
	return serversbydomain


## path where the all the webpy html templates go ##
render = web.template.render('/unix_ops/webpy-app/templates/')


## servers list, needs to be init'd in global for my_form_just_server to use, should be populated immediately before use ##
####servers = []


## Setup our web form ##
my_form_just_server = web.form.Form(
	web.form.Dropdown('server', class_='server', id='server', description='server:', args=[], value='Select a server.', autocomplete="off"),
	web.form.Password('passwd', class_='passwd', id='passwd', description='passwd:', autocomplete="off")
	)

my_form = web.form.Form(
	web.form.Textbox('', class_='username', id='username', description='username:'),
	web.form.Password('', class_='code', id='code', description='code:', autocomplete="off")
	)


## Url/Class mapping ##
urls = ('/', 'tutorial',
	'/index', 'index')


## Actual classes that spawn when mapped url is hit ##
class tutorial:
	def GET(self):
		form = my_form()
		return render.tutorial(form, "Enter username.")

	def POST(self):
		foo = web.input()
		form = my_form()
		justserver = my_form_just_server()
		form.validates()
		if foo.has_key('passwd') is True :
			passwd = form.value['passwd']
		else :
			passwd = ''

		if foo.has_key('server') is True :
			server = form.value['server']
		else :
			server = 'waiting for Select a server.'

		if foo.has_key('username') is True :
			username = form.value['username']
		else :
			username = ''

		if foo.has_key('code') is True :
			code = form.value['code']
		else :
			code = ''

		myvar1 = dict(username=username)
		myvar2 = dict(code=code)
		validuser = re.compile('^[.a-z0-9_-]+$').match(username)
		validserver = re.compile('^[.a-z0-9_-]+$').match(server)
		validcode = re.compile('^[\S]{32}').match(code)
		validpasswd = testpw(passwd)

		if validuser is None :
			logger('''invalid user. ''')
			return make_text(''' ''')
	

		msg = MIMEText(code_gen(32))
		msg['Subject'] = 'Reset code'
		msg['From'] = MYconfig.options.get('sender')


		if validcode is not None:
			results = db.select('users', myvar1, where="username = $username")
			for record in results:
				mylastupdate = int('0')
				if record.timestamp is not None:
					mylastupdate = int(time.mktime(record.timestamp.timetuple()))
				currenttime = int(time.mktime(time.localtime()))
				codeage = currenttime - mylastupdate
				mycode = record.code
				if mycode == code and codeage < 80:
					mypass = pass_gen(32)
					db.update('users', where="username = $username", code = mycode, vars=locals())

					if validserver is None:
						selectmsg = ''' Please select a server.'''
						logger('''%s''' % username + selectmsg)
						justserver.server.args = getserverlist()

						return render.justserver(justserver, selectmsg)

					if validpasswd is not 'allgood' :
						logger('''%s''' % username + ''' Invalid passwd. ''' + validpasswd)
						justserver.server.args = getserverlist()
						justserver.server.value = server

						return render.justserver(justserver, 'Invalid passwd.')


					resetmsg = setpw(username, server, MYconfig.options.get('prikey'), passwd, MYconfig.options.get('system'))

					logger('''%s''' % username + ''' ''' + resetmsg)
					justserver.server.args = getserverlist()
					justserver.server.value = server
					justserver.passwd.value = passwd

					return render.justserver(justserver, resetmsg)
			

		results = db.select('users', myvar1, where="username = $username")
		for record in results:
			writecode = db.update('users', where="username = $username", code = msg._payload, vars=locals(), _test=True)
			db.update('users', where="username = $username", code = msg._payload, vars=locals())
			msg['To'] = record.email
			send = smtplib.SMTP(MYconfig.options.get('mailrelay'))
			send.sendmail(msg['From'], msg['To'], msg.as_string())
			send.quit
			time.sleep(4)
			logger('''%s''' % ( username + ''' ''' + msg['To'] + ''' You got mail.'''))
			return make_text("You got mail.")

		logger('''invalid user. ''')
		return make_text(''' ''')



## Uncomment to use internal webpy internal app engine(non production)
##app = web.application(urls, globals())
##if __name__ == '__main__':
##	app.run()

application = web.application(urls, globals()).wsgifunc()


