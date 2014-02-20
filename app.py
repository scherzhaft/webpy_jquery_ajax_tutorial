##  The most Basic of modules you should always import  ##
import sys, os, time, re



##  Setup environment.... look in ./py_libs first  ##
fqself = os.path.abspath(__file__)
my_libs = os.path.dirname(fqself) + '/py_libs/'
sys.path.insert(1, my_libs)



##  Import dependencies  ##
import web



## Webpy Debug mode ##
web.config.debug = True



def make_text(string):
	return string

urls = ('/', 'tutorial')
render = web.template.render('/var/www/webpy-app/templates/')

app = web.application(urls, globals())

my_form = web.form.Form(
	web.form.Textbox('', class_='textfield', id='textfield'),
	)

class tutorial:
	def GET(self):
		form = my_form()
		return render.tutorial(form, "Enter username.")

	def POST(self):
		time.sleep(10)
		form = my_form()
		form.validates()
		s = form.value['textfield']
		valid = re.compile('^[.a-z0-9_-]+$').match(s)
		if valid is None :
			return make_text("invalid, you are wrong, wrong, wrong.")
	


		return make_text(s)




## Uncomment to use internal webpy internal app engine(non production)
##if __name__ == '__main__':
##	app.run()

application = web.application(urls, globals()).wsgifunc()


