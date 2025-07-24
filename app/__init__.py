from flask import Flask
from flask_mysqldb import MySQL

mysql = MySQL()

def create_app():
    app = Flask(__name__)
    app.secret_key = 'secret'

    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = 'deboleena'
    app.config['MYSQL_DB'] = 'retail_store'

    mysql.init_app(app)

    from .routes import main
    app.register_blueprint(main)

    return app


