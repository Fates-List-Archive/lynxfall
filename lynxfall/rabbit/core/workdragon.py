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
import threading

class Worker():
    def __init__(self, worker_num, process, thread):
        self.process = process
        self.worker_num = worker_num
        self.thread = thread
    
class WorkDragon():
    def __init__(self, launcher):
        self.workers = []
        self.launcher = launcher
        self.log_workers = True
        self.workers_to_log = []
    
    def worker_log(self, proc):
        for line in iter(proc.stdout.readline, b''):
            line = line.decode('utf-8')
            wnum = proc.env["LYNXFALL_WORKER_NUM"]
            if int(wnum) in self.workers_to_log and self.log_workers:
                print(f"{wnum}: {line}", end='')
        
    def new_worker(self): 
        wnum = len(self.workers) + 1
        proc = subprocess.Popen(['python3', '-u', self.launcher],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=dict(os.environ, LYNXFALL_WORKER_NUM=str(wnum))
        )
        t = threading.Thread(target=self.worker_log, args=(proc,))
        t.start()
        self.workers.append(Worker(wnum, proc, thread))
