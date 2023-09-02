from flask import Flask
from . extensions import api 


def create_app():
    app = Flask(__name__)
    
    from . import bread_crumbs
    api.init_app(app)
    api.add_namespace(bread_crumbs.ns)
    

    return app
