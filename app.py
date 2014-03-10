##  The most Basic of modules you should always import  ##
import sys, os, time, re, random, string


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


## Webpy Debug mode ##
web.config.debug = True


## Configure database connector ##
import MYconfig
db = web.database(dbn=MYconfig.options.get('dbn'),
	user=MYconfig.options.get('user'),
	pw=MYconfig.options.get('pw'),
	db=MYconfig.options.get('db'))


## Some functions that all may need ##
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
	trans = paramiko.Transport((host,port))
	dsa_key = paramiko.DSSKey.from_private_key_file(prikey)
	trans.connect(username=system, pkey=dsa_key)
	session = trans.open_session()
	session.get_pty()
	session.exec_command('''export PATH="${PATH}:/usr/local/bin" ; cat - | sudo /bin/bash -x ''')
	cmd = '''USERID=''' + user +  '\n' + '''PASSWD=''' + "'" + crypt.crypt(mypass) + "'" + '\n' + script + '\n' + '\n' + '\n'
	session.send(cmd)
	time.sleep(4)
	session.send('\n')
	time.sleep(4)
	session.send('\n')
	time.sleep(4)
	session.close()
	time.sleep(4)
	stdout = session.makefile('rb', -1).readlines()
	stderr = session.makefile_stderr('rb', -1).readlines()
	status = session.recv_exit_status()
	return {'stdout' : stdout,
		'stderr' : stderr,
		'status' : status}


## path where the all the webpy html templates go ##
render = web.template.render('/var/www/webpy-app/templates/')


## Setup our web form ##
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
		form = my_form()
		form.validates()
		username = form.value['username']
		code = form.value['code']
		myvar1 = dict(username=username)
		myvar2 = dict(code=code)
		validuser = re.compile('^[.a-z0-9_-]+$').match(username)
		validcode = re.compile('^[\S]{32}').match(code)
		if validuser is None :
			return make_text("invalid, you are wrong, wrong, wrong.")
	

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
					reset = setpw(username, MYconfig.options.get('testhost'), MYconfig.options.get('prikey'), mypass, MYconfig.options.get('system'))
					if reset.get('status') is not 0:
						return 'Reset Failed: ' + str(reset.get('status'))


					return mypass, reset.get('status')
			

		results = db.select('users', myvar1, where="username = $username")
		for record in results:
			writecode = db.update('users', where="username = $username", code = msg._payload, vars=locals(), _test=True)
			db.update('users', where="username = $username", code = msg._payload, vars=locals())
			msg['To'] = record.email
			send = smtplib.SMTP(MYconfig.options.get('mailrelay'))
			send.sendmail(msg['From'], msg['To'], msg.as_string())
			send.quit
			time.sleep(4)
			return make_text("You got mail.")

		return make_text("not found")



## Uncomment to use internal webpy internal app engine(non production)
##app = web.application(urls, globals())
##if __name__ == '__main__':
##	app.run()

application = web.application(urls, globals()).wsgifunc()


