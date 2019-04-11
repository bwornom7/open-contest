from code.util.db import getKey, setKey, listSubKeys, deleteKey, User, Problem
from uuid import uuid4
import logging
import os
import shutil
import json

from readerwriterlock import rwlock

lock = rwlock.RWLockWrite()

submissions = {}

extensions = {
    "c": ".c",
    "cpp": ".cpp",
    "cs": ".cs",
    "java": ".java",
    "python2": ".py",
    "python3": ".py",
    "ruby": ".rb",
    "vb": ".vb"
}

class Submission:
    saveCallbacks = []
    def __init__(self, id=None):
        if id != None:
            details = getKey(f"/submissions/{id}/submission.json")
            self.id          = details["id"]
            self.user        = User.get(details["user"])
            self.problem     = Problem.get(details["problem"])
            self.timestamp   = int(details["timestamp"])
            self.language    = details["language"]
            self.code        = details["code"]
            self.type        = details["type"]
            self.results     = details["results"]
            self.inputs      = details["inputs"]
            self.outputs     = details["outputs"]
            self.errors      = details["errors"]
            self.answers     = details["answers"]
            self.result      = details["result"]
        else:
            self.id          = None
            self.user        = None
            self.problem     = None
            self.timestamp   = 0
            self.language    = None
            self.code        = None
            self.type        = None
            self.results     = []
            self.inputs      = []
            self.outputs     = []
            self.errors      = []
            self.answers     = []
            self.result      = []

    def get(id: str):
        with lock.gen_rlock():
            if id in submissions:
                return submissions[id]
        return None
    
    def toJSONSimple(self):
        return {
            "id":        self.id,
            "user":      self.user.id,
            "problem":   self.problem.id,
            "timestamp": self.timestamp,
            "language":  self.language,
            "code":      self.code,
            "type":      self.type,
            "results":   self.results,
            "inputs":    self.inputs,
            "outputs":   self.outputs,
            "errors":    self.errors,
            "answers":   self.answers,
            "result":    self.result
        }

    def save(self):
        with lock.gen_wlock():
            if self.id == None:
                self.id = str(uuid4())
                submissions[self.id] = self
            setKey(f"/submissions/{self.id}/submission.json", self.toJSONSimple())
        for callback in Submission.saveCallbacks:
            callback(self)
    
    def delete(self):
        with lock.gen_wlock():
            if self.id is not None and self.id in submissions:
                deleteKey(f"/submissions/{self.id}")
                del submissions[self.id]
        
    def toJSON(self):
        with lock.gen_rlock():
            #logging.info(self.__dict__.keys())
            if "compile" in self.__dict__:
                return {
                    "id":        self.id,
                    "user":      self.user.id,
                    "problem":   self.problem.id,
                    "timestamp": self.timestamp,
                    "language":  self.language,
                    "code":      self.code,
                    "type":      self.type,
                    "compile":   self.compile,
                    "results":   self.results
                }
            return {
                "id":        self.id,
                "user":      self.user.id,
                "problem":   self.problem.id,
                "timestamp": self.timestamp,
                "language":  self.language,
                "code":      self.code,
                "type":      self.type,
                "results":   self.results,
                "inputs":    self.inputs[:self.problem.samples],
                "outputs":   self.outputs[:self.problem.samples],
                "errors":    self.errors[:self.problem.samples],
                "answers":   self.answers[:self.problem.samples],
                "result":    self.result
            }

    def download(self):
        if not os.path.exists(f"/tmp/{self.id}"):
            os.mkdir(f"/tmp/{self.id}/")
        
        with open(f"/tmp/{self.id}/code{extensions[self.language]}","w+") as code:
            code.write(self.code)

        with open(f"/tmp/{self.id}/inputs.json","w+") as infile:
            input_dict = dict((i,self.inputs[i]) for i in range(len(self.inputs)))
            json.dump(input_dict,infile)
            
        with open(f"/tmp/{self.id}/outputs.json","w+") as outfile:
            output_dict = dict((i,self.outputs[i]) for i in range(len(self.outputs)))
            json.dump(output_dict,outfile)
        
        ret = shutil.make_archive(f"/tmp/{self.id}/zip_{self.id}","zip",f"/tmp/{self.id}")

        print("downloaded:",ret)
        return f"/tmp/{self.id}/zip_{self.id}"

    def rmDownload(self):
        if os.path.exists(f"/tmp/{self.id}"):
            shutil.rmtree(f"/tmp/{self.id}",ignore_errors=True)
        return "ok"

    def forEach(callback: callable):
        with lock.gen_rlock():
            for id in submissions:
                callback(submissions[id])
    
    def onSave(callback: callable):
        Submission.saveCallbacks.append(callback)
    
    def all():
        with lock.gen_rlock():
            return [submissions[id] for id in submissions]

with lock.gen_wlock():
    for id in listSubKeys("/submissions"):
        submissions[id] = Submission(id)
