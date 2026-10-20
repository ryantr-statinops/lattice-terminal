import json
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from .process_tree import attach

class RunManager:
    def __init__(self,root:Path):self.root=root;self.jobs={};self.lock=threading.RLock();self.cpu=threading.Semaphore(1)
    def start(self,config):
        identity=config['id']
        if not isinstance(identity,str) or len(identity)!=64 or any(v not in '0123456789abcdef' for v in identity):raise ValueError('invalid run id')
        with self.lock:
            if identity in self.jobs:return
            job={'events':[],'cancel':threading.Event(),'process':None,'thread':None,'done':False};self.jobs[identity]=job
        self.append(identity,'state',{'status':'queued'})
        job['thread']=threading.Thread(target=self._run,args=(config,job),daemon=True)
        job['thread'].start()
    def append(self,identity,kind,payload):
        with self.lock:
            job=self.jobs[identity]
            if len(job['events'])>=5100:raise ValueError('event limit exceeded')
            job['events'].append({'seq':len(job['events'])+1,'type':kind,'payload':payload})
    def events(self,identity,after):
        with self.lock:
            if identity not in self.jobs:raise ValueError('run not found in active engine')
            return {'events':self.jobs[identity]['events'][after:after+100],'done':self.jobs[identity]['done']}
    def cancel(self,identity):
        with self.lock:
            job=self.jobs.get(identity)
            if job:job['cancel'].set()
    def close(self,timeout=10):
        with self.lock:
            jobs=list(self.jobs.values())
            for job in jobs:job['cancel'].set()
        deadline=time.monotonic()+timeout
        for job in jobs:
            thread=job.get('thread')
            if thread is not None:thread.join(max(0,deadline-time.monotonic()))
    def _run(self,config,job):
        acquired=False;process=None;close_tree=None
        try:
            if config['kind']!='strategy':
                while not job['cancel'].is_set():
                    if self.cpu.acquire(timeout=.1):acquired=True;break
                if not acquired:self.append(config['id'],'state',{'status':'cancelled'});return
            elif job['cancel'].is_set():self.append(config['id'],'state',{'status':'cancelled'});return
            config=dict(config,data_root=str(self.root))
            process=subprocess.Popen([sys.executable,'-m','kestrel_engine.worker'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,encoding='utf-8',cwd=Path(__file__).resolve().parents[1],creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0,start_new_session=os.name!='nt')
            close_tree=attach(process)
            job['process']=process
            process.stdin.write(json.dumps(config)+'\n');process.stdin.close()
            deadline=time.monotonic()+min(max(int(config.get('timeout_seconds',120)),1),3600)
            timed_out=threading.Event()
            def monitor():
                while process.poll() is None:
                    if job['cancel'].is_set() or time.monotonic()>deadline:
                        if not job['cancel'].is_set():timed_out.set()
                        close_tree()
                        return
                    time.sleep(.05)
            threading.Thread(target=monitor,daemon=True).start()
            terminal=False
            for line in process.stdout:
                if len(line)>1024*1024:raise ValueError('worker output limit exceeded')
                value=json.loads(line)
                self.append(config['id'],value['type'],value['payload'])
                if value['type']=='state' and value['payload'].get('status') in ['completed','failed']:terminal=True
            process.wait(timeout=5)
            if not terminal:
                status='cancelled' if job['cancel'].is_set() else 'failed'
                if timed_out.is_set():self.append(config['id'],'error',{'message':'worker time limit exceeded'})
                elif status=='failed':self.append(config['id'],'error',{'message':'worker exited before completing; check file contract and code snapshot'})
                self.append(config['id'],'state',{'status':status})
        except Exception as error:
            self.append(config['id'],'error',{'message':str(error)[:2000]});self.append(config['id'],'state',{'status':'failed'})
        finally:
            if close_tree is not None:close_tree()
            if process is not None and process.poll() is None:process.kill();process.wait()
            if acquired:self.cpu.release()
            with self.lock:job['done']=True
