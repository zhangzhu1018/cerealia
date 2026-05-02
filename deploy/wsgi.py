import sys, os, traceback

# PythonAnywhere WSGI 入口
project_home = '/home/cerealiacaviar/cerealia'
if project_home not in sys.path:
    sys.path.insert(0, project_home)
os.chdir(project_home)

# 环境变量
os.environ['FLASK_ENV'] = 'production'
os.environ['SKIP_MIGRATIONS'] = 'true'
os.environ['DEEPSEEK_API_KEY'] = 'sk-b969d8e7c3d84ee8bd499170d6e52eaa'
os.environ['DEEPSEEK_BASE_URL'] = 'https://api.deepseek.com/v1'
os.environ['AI_SEARCH_MODEL'] = 'deepseek-v4-pro'

class ErrorLogApp:
    """错误捕获包装器"""
    def __init__(self, real_app):
        self.real_app = real_app
    def __call__(self, environ, start_response):
        try:
            return self.real_app(environ, start_response)
        except Exception as e:
            with open('/home/cerealiacaviar/error.log', 'a') as f:
                f.write(f'\n{"="*60}\n{str(e)}\n{traceback.format_exc()}\n')
            start_response('500 Internal Error', [('Content-Type','text/plain')])
            return [f'Error: {e}\n\n{traceback.format_exc()}'.encode()]

from backend.app import create_app
try:
    inner_app = create_app('production')
    application = ErrorLogApp(inner_app)
except Exception as e:
    with open('/home/cerealiacaviar/startup_error.log', 'w') as f:
        f.write(f'{traceback.format_exc()}')
    raise
