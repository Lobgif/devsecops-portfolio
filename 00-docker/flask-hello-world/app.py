from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def hello_world():
    return '''
    <h1>🚀 Bonjour depuis Flask !</h1>
    <p>Cette application a été construite avec les Cloud Native Buildpacks.</p>
    <p>Version Python : 3.11</p>
    <p>Port : {}</p>
    '''.format(os.environ.get('PORT', '5000'))

@app.route('/health')
def health_check():
    return {'status': 'OK', 'message': 'Application Flask fonctionne parfaitement'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)