from flask import Flask, render_template
from flask_cors import CORS
from config import Config
from models import db
from routes import register_routes

test=True #测试整个前端
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)
db.init_app(app)

register_routes(app)

# 只有当test为True时才启用前端测试页面
if test:
    @app.route('/')
    def index():
        return render_template('index.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)