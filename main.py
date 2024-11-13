import time
from flask import Flask, request
import os, psutil
import subprocess
import hashlib
import hmac
from keys import *


PROJECTS_DIR = '/root'
CURRENT_PROJECTS_DIR = os.path.realpath(os.path.curdir)
app = Flask(__name__)

open('logtext.log', 'wb')
def log(*text):
    open('logtext.log', 'a', -1, 'utf8').write(time.strftime("%Y-%m-%dT%H:%SZ ")+' '.join([str(x) for x in text])+'\n')


@app.route('/webhook/pull/<string:project_path>', methods=['POST'])
def webhook(project_path):
    if request.method == 'POST':
        signature_header = request.headers.get('X-Hub-Signature-256')
        if not signature_header:
            return "x-hub-signature-256 header is missing!", 403
        payload_body = request.get_data()
        hash_object = hmac.new(secret_token.encode('utf-8'), msg=payload_body, digestmod=hashlib.sha256)
        expected_signature = "sha256=" + hash_object.hexdigest()

        if hmac.compare_digest(expected_signature, signature_header):
            log('[I]: Получена команда для обновления и перезапуска проекта', project_path)
            project_path = f'{PROJECTS_DIR}/{project_path}'
            # Переход в директорию с проектом и выполнение команды
            log('[I]: Переходим в папку проекта...')
            os.chdir(project_path)
            subprocess.run(['git', 'pull', 'origin', 'main'])
            time.sleep(1)
            os.chdir(CURRENT_PROJECTS_DIR)
            
            log(f'[I]: Поиск запущенного проекта...')
            cmdline = []
            for process in psutil.process_iter(['pid', 'name', 'cmdline', 'cwd']):
                try:
                    cmdline = process.info['cmdline']
                    process_file_dir = process.info['cwd']

                    # Проверяем, что процесс является Python-процессом
                    if cmdline and ("python" in cmdline[0] or "python3" in cmdline[0]) and process_file_dir:
                        # Проверяем наличие файла скрипта
                        if len(cmdline) > 1:
                            if os.path.samefile(process_file_dir, project_path):
                                log('[I]: Проект найден. Заверщаю работы проекта для перезапуска...')
                                process.terminate()
                                time.sleep(.5)

                                for _ in range(10):
                                    try:
                                        process.kill()  # отправляет SIGKILL для немедленного завершения
                                        log(f'[W]: Процесс {process.pid} не был завершен, попробую завершить ещё раз...')
                                    except psutil.NoSuchProcess:
                                        log(f'[I]: Процесс с PID {process.pid} успешно завершен.')
                                        break
                                    except Exception as e:
                                        log(f'[E]: Не удалось завершить процесс: {e}')
                                    time.sleep(.5)
                                
                                else:
                                    log('[C]: Не удалось перезагрузить проект!')

                                break

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                
            launch_command = ['nohup', project_path+'/venv/bin/python', *cmdline[1:], '>', 'output.log', '2>&1', '&']  # Полная команда запуска
            log(f'[I]: Запускаю проект по команде: [{" ".join(launch_command)}]')
            os.chdir(project_path)
            subprocess.run(launch_command)
            os.chdir(CURRENT_PROJECTS_DIR)

            return 'Updated', 200
        else:
            return "Request signatures didn't match!", 403

    return 'Error', 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
