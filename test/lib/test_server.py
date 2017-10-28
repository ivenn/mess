import os
import sys
import time
import signal
import traceback
import subprocess

from server.config import TestConfig


def is_process_running(pid):
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True


class TestServer:

    def __init__(self, port=9090):
        self.port = port
        self.pid = None
        self.retcode = None
        self.config = TestConfig()

    def up(self):
        proc_env = os.environ.copy()  # use the same env as parent process
        cmd = [sys.executable, os.path.join(self.config.project_path, 'server', 'run.py'), '--mode=test']
        print("Running server: {cmd}".format(cmd=' '.join(cmd)))
        self.proc = subprocess.Popen(cmd, shell=False, env=proc_env)
        time.sleep(1)  # to let server up
        self.pid = self.proc.pid

        return self.pid

    def down(self):
        print("Terminating server...")
        time.sleep(1)
        try:
            os.kill(self.pid, signal.SIGINT)  # emulate Ctrl+C
            self.retcode = self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print(traceback.format_exc())
        except Exception:
            print(traceback.format_exc())
        finally:
            if hasattr(self, 'devnull'):
                self.devnull.close()
            if self.retcode is not None:
                self.pid = None

    def kill(self):
        if self.pid:
            print("###### server is still running: %s" % self.pid)
            self.proc.terminate()

            if is_process_running(self.pid):
                print('still running')
                os.kill(self.pid, 9)
                if is_process_running(self.pid):
                    print('still still')


if __name__ == '__main__':
    s = TestServer(9090)
    s.up()
    print('between')
    time.sleep(1)
    s.down()
    s.kill()
