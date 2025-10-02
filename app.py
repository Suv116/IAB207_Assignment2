from flask import Flask
from flask_bootstrap import Bootstrap

app = Flask(__name__)

app.secret_key = 'assignment_2_secret_key'
Bootstrap(app)

@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


if __name__ == '__main__':
    app.run()

