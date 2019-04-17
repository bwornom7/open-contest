from code.util.db import Submission, User, Contest, Problem
from code.generator.lib.htmllib import *
from code.generator.lib.page import *
from .leaderboard import *
import logging
from code.util import register
import time

def constructTableRows(data, placement):

    tableRows = []

    for user in data.keys():

        problems = []
        for problem in sorted(data[user]["problems"]):
            problems.append(h.td(data[user]["problems"][problem][0]))
            problems.append(h.td(data[user]["problems"][problem][1], cls="time-format"))
        tableRows.append(
            h.tr(
                h.td(str(placement.index(data[user]["contestant"]) + 1), cls="center"),
                h.td(data[user]["contestant"], cls="center"),
                h.td(data[user]["correct"], cls="center"),
                *problems
            )
        )
    return tableRows

def generateDetailedReport(params, user):
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


    subs = {}

    for sub in Submission.all():
        if start <= sub.timestamp <= end and not sub.user.isAdmin():
            subs[sub.user.id] = subs.get(sub.user.id) or []
            subs[sub.user.id].append(sub)

    problemSummary = {}
    for prob in contest.problems:
        problemSummary[prob.id] = [0, 0]

    scores = []
    for user in subs:
        usersubs = subs[user]
        scor = score(usersubs, start, problemSummary)
        scores.append((
            User.get(user).username,
            scor[0],
            scor[1],
            scor[2],
            len(usersubs)
        ))


    #TODO: make this compatible with sample data tie breaker
    scores = sorted(scores, key=lambda score: score[1] * 1000000000 + score[2] * 10000000 - score[3], reverse=True)

    placement = []
    for user in scores:
        placement.append(user[0])

    rankings = {}
    for sub in Submission.all():
        if start <= sub.timestamp <= end and not sub.user.isAdmin():
            if sub.user.id not in rankings.keys():
                rankings[sub.user.id] = {}
                rankings[sub.user.id]["contestant"] = User.get(sub.user.id).username
                rankings[sub.user.id]["id"] = User.get(sub.user.id).id
                rankings[sub.user.id]["correct"] = 0
                rankings[sub.user.id]["problems"] = {}

                for problem in contest.problems:
                    rankings[sub.user.id]["problems"][problem.title] = [0, 0]

            probTitle = Problem.get(sub.problem.id).title

            if sub.result == "ok" and rankings[sub.user.id]["problems"][probTitle][1] == 0:
                rankings[sub.user.id]["problems"][probTitle][0] += 1
                rankings[sub.user.id]["problems"][probTitle][1] = sub.timestamp
                rankings[sub.user.id]["correct"] = 1
            elif sub.result == "ok" and rankings[sub.user.id]["problems"][probTitle][1] != 0:
                rankings[sub.user.id]["problems"][probTitle][0] += 1
            elif sub.result != "ok":
                rankings[sub.user.id]["problems"][probTitle][0] += 1

    problemHeader = []

    for problem in sorted(contest.problems):
        problemHeader.append( h.th(problem.title + " submissions"))
        problemHeader.append( h.th("Time"))


    problemRows = constructTableRows(rankings, placement)

    return Page(
            h2("Final Standings", cls="page-title"),
            h.table(
                h.thead(
                    h.tr(
                        h.th("Rank", cls="center"),
                        h.th("Contestant", cls="center"),
                        h.th("Correct", cls="center"),
                        *problemHeader
                    )
                ),
                h.tbody(
                    *problemRows
                )
            ),
        )





register.web("/detailedreport", "loggedin", generateDetailedReport)
