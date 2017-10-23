import os.path
import pathlib

# 2 parents up from this file
PROJECT_PATH = str(pathlib.Path(__file__).parents[2])


class Config:

    def __init__(self):
        self.project_path = PROJECT_PATH
        self.log = os.path.join(PROJECT_PATH, 'server', 'log')
        self.db_path = os.path.join(PROJECT_PATH, 'server', 'mess.db')
        self.db = 'sqlite:///{db_path}'.format(db_path=self.db_path)


class TestConfig:

    def __init__(self):
        self.project_path = PROJECT_PATH
        self.log = os.path.join(PROJECT_PATH, 'test', 'log')
        self.db_path = os.path.join(PROJECT_PATH, 'test', 'mess.db')
        self.db = 'sqlite:///{db_path}'.format(db_path=self.db_path)