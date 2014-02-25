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
		time.sleep(10)
		form = my_form()
		form.validates()
		username = form.value['username']
		code = re.compile('^[\S]{32}').match(form.value['code'])
		myvar1 = dict(username=username)
		myvar2 = dict(code=code)
		valid = re.compile('^[.a-z0-9_-]+$').match(username)
		if valid is None :
			return make_text("invalid, you are wrong, wrong, wrong.")
	

		msg = MIMEText(code_gen(32))
		msg['Subject'] = 'Reset code'
		msg['From'] = MYconfig.options.get('sender')


		if code is not None:
			results = db.select('users', myvar1, where="username = $username")
			for record in results:
				mycode = record.code
				if mycode == code:
					return make_text(pass_gen(32))
			

		results = db.select('users', myvar1, where="username = $username")
		for record in results:
			msg['To'] = record.email
			send = smtplib.SMTP(MYconfig.options.get('mailrelay'))
			send.sendmail(msg['From'], msg['To'], msg.as_string())
			send.quit
			return make_text("You got mail.")

		return make_text("not found")



## Uncomment to use internal webpy internal app engine(non production)
##app = web.application(urls, globals())
##if __name__ == '__main__':
##	app.run()

application = web.application(urls, globals()).wsgifunc()


