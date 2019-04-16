from code.util.db import Submission, User, Contest, Problem
from code.generator.lib.htmllib import *
from code.generator.lib.page import *
import logging
from code.util import register
import time

def custom_sort(submission):
    return submission[2]

def constructTableRows(listOfSubmissions):
    tableRows = []
    for sub in listOfSubmissions:
        tableRows.append(
            h.tr(
                h.td(sub[0]), # name
                h.td(sub[1]), # title
                h.td(sub[2], cls="time-format"), # time, converted to a human readable format
            )
        )
    return tableRows

def generateLogReport(params, user):
    contest = Contest.getCurrent() or Contest.getPast()
    if not contest:
        return Page(
            h1("&nbsp;"),
            h1("No Contest Available", cls="center")
        )
    elif contest.scoreboardOff <= time.time() * 1000 and not user.isAdmin():
        return Page(
            h1("&nbsp;"),
            h1("Scoreboard is off.", cls="center")
        )

    start = contest.start
    end = contest.end

    users = {}

    for sub in Submission.all():
        if start <= sub.timestamp <= end and not sub.user.isAdmin() and sub.result == "ok":
            username = User.get(sub.user.id).username
            problemName = Problem.get(sub.problem.id).title

            if (username not in users.keys()):
                users[username] = {}
            if (problemName not in users[username].keys()):
                users[username][problemName] = sub
            if (sub.timestamp < users[username][problemName].timestamp):
                users[username][problemName] = sub

    correctSubmissions = []
    for user in users.keys():
        for problem in users[user].keys():
            correctSubmissions.append((user, problem, users[user][problem].timestamp))

    # https://www.afternerd.com/blog/python-sort-list/
    correctSubmissions.sort(key=custom_sort)

    tableRows = constructTableRows(correctSubmissions)

    return Page(
        h2("Correct Submissions Log", cls="page-title"),
        h.table(
            h.thead(
                h.tr(
                    h.th("Contestant Name"),
                    h.th("Problem title"),
                    h.th("Time"),
                )
            ),
            h.tbody (
                *tableRows
            )
        )
    )












register.web("/logreport", "loggedin", generateLogReport)
