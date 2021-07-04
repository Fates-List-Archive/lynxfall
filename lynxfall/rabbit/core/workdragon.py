"""
Work in progress worker management for lynxfall

Note: This will only handle startup/shutdown and other tasks, not micromanaging individual workers. 
Stats and error handling is a maybe that will be implemented after core functionality
Worker-specific tasks are another maybe unless that task is done via redis PUBSUB or other as rabbit is round-robin so not all workers get every task

Workdragon will have a redis pubsub protocol for external management

Support for windows/mac is not planned as of right now.
"""
import os
import subprocess

class Worker():
    def __init__(self, worker_num, process):
        self.process = process
        self.worker_num = worker_num
    
class WorkDragon():
    def __init__(self, launcher):
        self.workers = []
        self.launcher = launcher
        
    def new_worker(self):
        proc = subprocess.Popen(['python3', '-u', launcher],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=dict(os.environ, LYNXFALL_WORKER_NUM=str(len(self.workers) + 1))
        )
