from code.util.db import Submission, User, Contest, Problem
from code.generator.lib.htmllib import *
from code.generator.lib.page import *
from .leaderboard import *
import logging
from code.util import register
import time

def constructTableRows(data):
    tableRows = []
    for user in data:
        tableRows.append(
            h.tr(
                h.td(0),
                h.td(user["contestant"]),
                h.td(user["id"])

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
    scores = sorted(scores, key=lambda score: score[1] * 1000000000 + score[2] * 10000000 - score[3], reverse=True)

    rankings = {}
    for entry in Submission.all():
        if start <= sub.timestamp <= end and not sub.user.isAdmin():
            if sub.user.id not in rankings.keys():
                rankings[sub.user.id] = {}
                rankings[sub.user.id]["contestant"] = User.get(sub.user.id).username
                rankings[sub.user.id]["id"] = User.get(sub.user.id).id




    problemHeader = []

    for problem in contest.problems:
        problemHeader.append( h.th(problem.title) )

    problemRows = constructTableRows(rankings)

    return Page(
            h2("Final Standings", cls="page-title"),
            h.table(
                h.thead(
                    h.tr(
                        h.th("Rank", cls="center"),
                        h.th("Contestant", cls="center"),
                        h.th("ID", cls="center"),
                        h.th("Correct", cls="center"),
                        h.th("Penalty", cls="center"),
                        *problemHeader
                    )
                ),
                h.tbody(
                    *problemRows
                )
            ),
        )





register.web("/detailedreport", "loggedin", generateDetailedReport)
