import os
import logging
from code.util import register
from code.util.db import Submission, Problem
import time
import shutil
import difflib
import re
from uuid import uuid4

def addSubmission(probId, lang, code, user, type):
    sub = Submission()
    sub.problem = Problem.get(probId)
    sub.language = lang
    sub.code = code
    sub.result = "pending"
    sub.user = user
    sub.timestamp = time.time() * 1000
    sub.type = type
    if type == "submit":
        sub.save()
    else:
        sub.id = str(uuid4())
    return sub

exts = {
    "c": "c",
    "cpp": "cpp",
    "cs": "cs",
    "java": "java",
    "python2": "py",
    "python3": "py",
    "ruby": "rb",
    "vb": "vb"
}

def readFile(path):
    try:
        with open(path, "rb") as f:
            return f.read(1000000).decode("utf-8")
    except:
        return None

def strip(text):
    return re.sub("[ \t\r]*\n", "\n", text)

def runCode(sub):
    # Copy the code over to the runner /tmp folder
    extension = exts[sub.language]
    os.mkdir(f"/tmp/{sub.id}")
    with open(f"/tmp/{sub.id}/code.{extension}", "wb") as f:
        f.write(sub.code.encode("utf-8"))
    
    prob = sub.problem
    tests = prob.samples if sub.type == "test" else prob.tests
    
    # Copy the input over to the tmp folder for the runner
    for i in range(tests):
        shutil.copyfile(f"/db/problems/{prob.id}/input/in{i}.txt", f"/tmp/{sub.id}/in{i}.txt")

    # Output files will go here
    os.mkdir(f"/tmp/{sub.id}/out")

    # Run the runner
    if os.system(f"docker run --rm --network=none -m 256MB -v /tmp/{sub.id}/:/source nathantheinventor/open-contest-dev-{sub.language}-runner {tests} {prob.timelimit} > /tmp/{sub.id}/result.txt") != 0:
        raise Exception("Something went wrong")

    inputs = []
    outputs = []
    answers = []
    errors = []
    results = []
    result = "ok"

    for i in range(tests):
        test_input = sub.problem.testData[i].input
        test_error = readFile(f"/tmp/{sub.id}/out/err{i}.txt")
        test_output = readFile(f"/tmp/{sub.id}/out/out{i}.txt")
        test_answer = sub.problem.testData[i].output

        inputs.append(test_input)
        errors.append(test_error)
        outputs.append(test_output)
        answers.append(test_answer)
 
        res = readFile(f"/tmp/{sub.id}/out/result{i}.txt")

        last_output = strip((outputs[-1] or "").rstrip())
        last_answer = strip((answers[-1] or "").rstrip())

        # improved auto-judge implementaion
        if res == "ok":
            output_lines = last_output.split()
            answer_lines = last_answer.split()

            # set intersecction
            matches = list(set(output_lines) & set(answer_lines))

            print("MATCHES",matches)
            print("OUTPUT","({})".format(last_output))
            print("ANSWER","({})".format(last_answer))

            if len(matches) and len(output_lines) < len(answer_lines):
                res = "incomplete"
            elif len(matches) and len(output_lines) > len(answer_lines):
                res = "extra"
            elif not len(matches):
                res = "wrong_answer"
            elif last_answer == last_output:
                res = "ok"
            
        if res == None:
            res = "tle"

        # Make result the first incorrect result
        if res != "ok" and result == "ok":
            result = res

        results.append(res)

    sub.result = result
    if readFile(f"/tmp/{sub.id}/result.txt") == "compile_error\n":
        sub.results = "compile_error"
        sub.delete()
        sub.compile = readFile(f"/tmp/{sub.id}/out/compile_error.txt")
        shutil.rmtree(f"/tmp/{sub.id}", ignore_errors=True)
        return

    sub.results = results
    sub.inputs = inputs
    sub.outputs = outputs
    sub.answers = answers
    sub.errors = errors

    if sub.type == "submit":
        sub.save()

    shutil.rmtree(f"/tmp/{sub.id}", ignore_errors=True)

def submit(params, setHeader, user):
    probId = params["problem"]
    lang   = params["language"]
    code   = params["code"]
    type   = params["type"]
    submission = addSubmission(probId, lang, code, user, type)
    runCode(submission)
    return submission.toJSON()

def changeResult(params, setHeader, user):
    id = params["id"]
    sub = Submission.get(id)
    if not sub:
        return "Error: incorrect id"
    sub.result = params["result"]
    sub.save()
    return "ok"

def rejudge(params, setHeader, user):
    id = params["id"]
    submission = Submission.get(id)
    if os.path.exists(f"/tmp/{id}"):
        shutil.rmtree(f"/tmp/{id}")
    runCode(submission)
    return submission.result

register.post("/submit", "loggedin", submit)
register.post("/changeResult", "admin", changeResult)
register.post("/rejudge", "admin", rejudge)
