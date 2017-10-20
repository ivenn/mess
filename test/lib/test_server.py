import os
import sys
import time
import signal
import subprocess

from server.config import TestConfig


class TestServer:

    def __init__(self, stdout=False, port=9090):
        self.port = port
        self.pid = None
        self.stdout = stdout
        self.config = TestConfig()
        self.proc = None
        self.devnull = None

    def up(self):
        proc_env = os.environ.copy()  # use the same env as parent process
        if self.stdout:
            out = subprocess.STDOUT
            err = subprocess.STDERR
        else:
            self.devnull = open(os.devnull, 'w')
            out = self.devnull
            err = subprocess.STDOUT
        cmd = "{python} {py} --mode=test".format(
              python=sys.executable,  # use the same interpreter as parent process
              py=os.path.join(self.config.project_path, 'server', 'run.py'))
        print("Running server: {cmd}".format(cmd=cmd))
        self.proc = subprocess.Popen(cmd, shell=True, env=proc_env, stdout=out, stderr=err)
        time.sleep(1)  # to let server up
        self.pid = self.proc.pid

        return self.pid

    def down(self):
        print("Terminating server...")
        time.sleep(1)
        os.kill(self.pid, signal.SIGINT)  # emulate Ctrl+C
        self.proc.wait(timeout=5)
        if self.devnull:
            self.devnull.close()

    def kill(self):
        if self.pid:
            self.proc.terminate()


if __name__ == '__main__':
    s = TestServer()
    s.up()
    print('between')
    time.sleep(10)
    s.down()
