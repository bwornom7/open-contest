// document.addEventListener("visibilitychange", _ => {
//     window.setTimeout(_ => {
//         window.location.reload();
//     }, 500);
// }, false);

/*--------------------------------------------------------------------------------------------------
General page code
--------------------------------------------------------------------------------------------------*/
    // from https://www.quirksmode.org/js/cookies.html
    function readCookie(name) {
        var nameEQ = name + "=";
        var ca = document.cookie.split(';');
        for(var i=0;i < ca.length;i++) {
            var c = ca[i];
            while (c.charAt(0)==' ') c = c.substring(1,c.length);
            if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
        }
        return null;
    }    

    function setupHeaderDiv() {
        $("div.header").click(_ => {
            window.location = "/";
        });
    }

    var userType = "";
    var user = "";
    function setupMenu() {
        if (document.cookie) {
            userType = readCookie("userType");
            user = readCookie("user");
        }
        $("div.menu-item").each(function() {
            var perms = $(this).attr("role");
            if (perms == "any" || perms == userType) {
                $(this).css("display", "inline-block");
            }
        });
    }

    $(document).ready(function() {
        var pageName = $("#pageId").val();
        setupMenu();
        setupLoginButton();
        setupHeaderDiv();
        fixFormatting();
        showCountdown();
        displayIncomingMessages();
        if ($("#ace-editor").length > 0) {
            setupAceEditor();
            setupSortability();
        }
        if (pageName == "Users") {
            displayExistingUsers();
            setupUserButtons();
        } else if (pageName == "Contests") {
            displayExistingContests();
            setupContestButton();
        } else if (pageName == "Contest") {
            setupContestPage();
        } else if (pageName == "Problem") {
            setupProblemPage();
        }
        $(".result-tabs").tabs();
        // $(".tablesorter").tablesorter();
        var props = {  
            sort: true,  
            filters_row_index:1,  
            remember_grid_values: true,  
            alternate_rows: true,
            custom_slc_options: {  
                cols:[],
                texts: [],
                values: [],
                sorts: []
            }
        }  
    if ($("#submissions").length) {
        var tf = setFilterGrid("submissions",props); 
    }
    });
/*--------------------------------------------------------------------------------------------------
Problem page
--------------------------------------------------------------------------------------------------*/
    function showCountdown() {
        if ($(".countdown").length == 0) {
            return;
        }
        var contestStart = parseInt($(".countdown").text() || "0");
        var updateTime = _ => {
            var diff = Math.floor((contestStart - new Date().getTime()) / 1000);
            if (diff <= 0) {
                window.location.reload();
            }
            var seconds = diff % 60;
            var minutes = Math.floor(diff / 60) % 60;
            var hours = Math.floor(diff / 3600);
            if (seconds < 10) seconds = "0" + seconds;
            if (minutes < 10) minutes = "0" + minutes;
            $(".countdown").text(`${hours}:${minutes}:${seconds}`)
        };
        window.setInterval(updateTime, 1000);
        updateTime();
    }

    var languages;
    var language;

    async function getLanguages() {
        return new Promise((res, rej) => {
            if (localStorage.languages != undefined) {
                languages = JSON.parse(localStorage.languages);
                res();
            } else {
                $.post("/static/languages.json", {}, data => {
                    localStorage.languages = JSON.stringify(data);
                    languages = JSON.parse(localStorage.languages);
                    res();
                });
            }
        });
    }

    function setupLanguageDropdown() {
        for (var language in languages) {
            $("select.language-picker").append(`<option value="${language}">${languages[language].name}</option>`);
        }
        if (localStorage.language != undefined) {
            $("select.language-picker").val(localStorage.language);
        }
    }

    async function getLanguageDefault(language) {
        return new Promise((res, rej) => {
            if (localStorage[language] != undefined) {
                res(localStorage[language]);
            } else {
                $.post("/static/examples/" + languages[language].example, {}, data => {
                    localStorage[language] = data;
                    res(data);
                });
            }
        });
    }

    function createResultsCard() {
        if ($(".card.results").length == 0) {
            $(".main-content").append(`<div class="results card">
                <div class="card-header">
                    <h2 class="card-title">Results</h2>
                </div>
                <div class="card-contents">
                </div>
            </div>`);
        }
        $(".results.card .card-contents").html(`<div class="results-pending"><i class="fa fa-spinner fa-pulse fa-3x fa-fw"></i></div>`);
    }

    var icons = {
        "ok": "check",
        "wrong_answer": "times",
        "tle": "clock",
        "runtime_error": "exclamation-triangle"
    };
    var verdict_name = {
        "ok": "Accepted",
        "wrong_answer": "Wrong Answer",
        "tle": "Time Limit Exceeded",
        "runtime_error": "Runtime Error"
    };

    function showResults(sub) {
        if (sub.results == "compile_error") {
            $(".results.card .card-contents").html(`
                <h3>Compile Error</h3>
                <code>${sub.compile.replace(/\n/g, "<br/>").replace(/ /g, "&nbsp;")}</code>
            `);
        } else if (sub.type == "test") {
            var tabs = "";
            var results = "";
            var samples = sub.results.length;
            for (var i = 0; i < samples; i ++) {
                var res = sub.results[i];
                var icon = icons[res];
                tabs += `<li><a href="#tabs-${i}"><i class="fa fa-${icon}" title="${verdict_name[res]}"></i> Sample #${i}</a></li>`;

                var input = sub.inputs[i];
                var output = sub.outputs[i];
                var error = sub.errors[i];
                var answer = sub.answers[i];
                var errorStr = `<div class="col-12">
                    <h4>Stderr Output</h4>
                    <code>${error.replace(/\n/g, "<br/>").replace(/ /g, "&nbsp;")}</code>
                </div>`;
                if (!error) {
                    errorStr = "";
                }
                results += `<div id="tabs-${i}">
                    <div class="row">
                        <div class="col-12">
                            <h4>Input</h4>
                            <code>${input.replace(/\n/g, "<br/>").replace(/ /g, "&nbsp;")}</code>
                        </div>
                        <div class="col-6">
                            <h4>Your Output</h4>
                            <code>${output.replace(/\n/g, "<br/>").replace(/ /g, "&nbsp;")}</code>
                        </div>
                        <div class="col-6">
                            <h4>Correct Answer</h4>
                            <code>${answer.replace(/\n/g, "<br/>").replace(/ /g, "&nbsp;")}</code>
                        </div>
                        ${errorStr}
                    </div>
                </div>`;
            }
            $(".results.card .card-contents").html(`<div id="result-tabs">
                <ul>
                    ${tabs}
                </ul>
                ${results}
            </div>`);
            $("#result-tabs").tabs();
        } else {
            var results = "";
            for (var i = 0; i < sub.results.length; i ++) {
                var res = sub.results[i];
                var icon = icons[res];
                results += `<div class="col-2"><i class="fa fa-${icon}" title="${verdict_name[res]}"></i> Case #${i}</div>`;
            }
            $(".results.card .card-contents").html(`<div class="pad">
                <h2>Result: ${verdict_name[sub.result]}</h2>
                <div class="row">
                    ${results}
                </div>
            </div>`);
        }
        scrollTo(0,document.body.scrollHeight);
    }

    async function setupAceEditor() {
        await getLanguages();
        // Get problem ID
        var thisProblem = $("#problem-id").val();

        // Setup ACE editor
        var editor = ace.edit("ace-editor");
        editor.setShowPrintMargin(false);
        editor.setTheme("ace/theme/chrome");

        setupLanguageDropdown();

        // Change the editor when the language changes
        async function setLanguage() {
            language = $("select.language-picker").val();
            localStorage.language = language;
            editor.session.setMode("ace/mode/" + languages[language].aceName);
            if (localStorage[language + "-" + thisProblem] == undefined) {
                localStorage[language + "-" + thisProblem] = await getLanguageDefault(language);
                editor.setValue(localStorage[language + "-" + thisProblem]);
            } else {
                editor.setValue(localStorage[language + "-" + thisProblem]);
            }
        }
        setLanguage();
        $("select.language-picker").change(setLanguage);

        // Save the editor contents to local storage when the editor changes
        editor.session.on('change', delta => {
            localStorage[language + "-" + thisProblem] = editor.getValue();
        });

        function disableButtons() {
            $(".submit-problem").attr("disabled", true);
            $(".submit-problem").addClass("button-gray");
            $(".test-samples").attr("disabled", true);
            $(".test-samples").addClass("button-gray");
        }

        function enableButtons() {
            $(".submit-problem").attr("disabled", false);
            $(".submit-problem").removeClass("button-gray");
            $(".test-samples").attr("disabled", false);
            $(".test-samples").removeClass("button-gray");
        }

        // When you click the submit button, submit the code to the server
        $("button.submit-problem").click(_ => {
            createResultsCard();
            var code = editor.getValue();
            disableButtons();
            $.post("/submit", {problem: thisProblem, language: language, code: code, type: "submit"}, results => {
                enableButtons();
                showResults(results);
            });
        });

        // When you click the test code button, test the code
        $("button.test-samples").click(_ => {
            createResultsCard();
            var code = editor.getValue();
            disableButtons();
            $.post("/submit", {problem: thisProblem, language: language, code: code, type: "test"}, results => {
                enableButtons();
                showResults(results);
            });
        });
    }

    function setupSortability() {
        var thisProblem = $("#problem-id").val();
        if (localStorage["sort-" + thisProblem] != undefined) {
            var order = JSON.parse(localStorage["sort-" + thisProblem]);
            for (var i of [0,1,2,3,4]) {
                var cls = order[i];
                $("div.problem-description").append($("div.problem-description div." + cls))
            }
        }
        $("div.problem-description").sortable({
            placeholder: "ui-state-highlight",
            forcePlaceholderSize: true,
            stop: (event, ui) => {
                var indices = {};
                for (var cls of ["stmt", "inp", "outp", "constraints", "samples"]) {
                    var index = $("div.problem-description > div." + cls).index();
                    indices[index] = cls;
                }
                localStorage["sort-" + thisProblem] = JSON.stringify(indices);
            }
        });
        $("div.problem-description").disableSelection();
    }

/*--------------------------------------------------------------------------------------------------
Login page
--------------------------------------------------------------------------------------------------*/
    function login() {
        // Clear localStorage
        for (var key of Object.keys(localStorage)) {
            delete localStorage[key];
        }

        var username = $("input[name=username]").val();
        var password = $("input[name=password]").val();
        $.post("/login", {username: username, password: password}, data => {
            if (data == "ok") {
                window.location = "/problems";
            } else {
                alert(data);
            }
        });
    }

    function loginIfEnter(event) {
        if (event.keyCode == 13) {
            // the user pressed the enter key
            login();
        }
    }

    function setupLoginButton() {
        if ($("input[name=username]").length > 0) {
            $(".login-button").click(login);
            $("input[name=username]").focus();
            $("input[name=username]").keypress(loginIfEnter);
            $("input[name=password]").keypress(loginIfEnter);
        }
    }

/*--------------------------------------------------------------------------------------------------
Users page
--------------------------------------------------------------------------------------------------*/
    function deleteUser(username) {
        if (confirm(`Are you sure you want to delete ${username}?`)) {
            $.post("/deleteUser", {username: username}, data => {
                if (data == "ok") {
                    window.location.reload();
                }
            });
        }
    }

    function createUser(type) {
        var username = prompt("New User's Name")
        if (username) {
            $.post("/createUser", {type: type, username: username}, password => {
                window.location.reload();
            });
        }
    }

/*--------------------------------------------------------------------------------------------------
Contests page
--------------------------------------------------------------------------------------------------*/
    function deleteContest(id) {
        var name = $(`.card.${id} .card-title`).text();
        if (confirm(`Are you sure you want to delete ${name}?`)) {
            $.post("/deleteContest", {id: id}, data => {
                if (data == "ok") {
                    window.location.reload();
                }
            });
        }
    }

/*--------------------------------------------------------------------------------------------------
Contest page
--------------------------------------------------------------------------------------------------*/
    function editContest(newProblem=undefined) {
        var id = $("#contest-id").val();
        var name = $("#contest-name").val();
        var startDate = $("#contest-start-date").val();
        var startTime = $("#contest-start-time").val();
        var endDate = $("#contest-end-date").val();
        var endTime = $("#contest-end-time").val();
        var scoreboardOffTime = $("#scoreboard-off-time").val();


        // Invalid DATE format; "T" after the date and "Z" after the time have been inserted 
        // for the correct format for creating the Dates, then the milliseconds are adjusted 
        // for the correct time zone for each of the following variables, since "Z" assumes you
        // are entering a UTC time.

        var start = new Date(`${startDate}T${startTime}Z`);
        start = start.getTime() + (start.getTimezoneOffset() * 60000);
        var end = new Date(`${endDate}T${endTime}Z`);
        end = end.getTime() + (end.getTimezoneOffset() * 60000);
        var endScoreboard = new Date(`${endDate}T${scoreboardOffTime}Z`);
        endScoreboard = endScoreboard.getTime() + (endScoreboard.getTimezoneOffset() * 60000);

        if (end <= start) {
            alert("The end of the contest must be after the start.");
            return;
        }

        if (!(start < endScoreboard && endScoreboard <= end)) {
            alert("The scoreboard off time must be between the start and end time.");
            return;
        }

        var problems = [];
        var uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
        $(".problem-cards .card").each((_, card) => {
            var prob = "";
            for (var cls of $(card).attr("class").split(" ")) {
                if (uuid.test(cls)) {
                    prob = cls;
                    break;
                }
            }
            problems.push(prob);
        });
        if (newProblem != undefined) {
            problems.push(newProblem);
        }

        $.post("/editContest", {id: id, name: name, start: start, end: end, scoreboardOff: endScoreboard, problems: JSON.stringify(problems)}, id => {
            if (window.location.pathname == "/contests/new") {
                window.location = `/contests/${id}`;
            } else {
                window.location.reload()
            }
        });
    }

    function fix(num) {
        // Fix to 2 decimals
        if (num < 10) {
            return "0" + num;
        }
        return num;
    }

    var problemsHere = {};
    function setupContestPage() {
        var start = new Date(parseInt($("#start").val()));
        $("#contest-start-date").val(`${start.getFullYear()}-${fix(start.getMonth() + 1)}-${fix(start.getDate())}`);
        $("#contest-start-time").val(`${fix(start.getHours())}:${fix(start.getMinutes())}`);
        
        var end = new Date(parseInt($("#end").val()));
        $("#contest-end-date").val(`${end.getFullYear()}-${fix(end.getMonth() + 1)}-${fix(end.getDate())}`);
        $("#contest-end-time").val(`${fix(end.getHours())}:${fix(end.getMinutes())}`);

        var endScoreboard = new Date(parseInt($("#scoreboardOff").val()));
        $("#scoreboard-off-time").val(`${fix(endScoreboard.getHours())}:${fix(endScoreboard.getMinutes())}`);

        $("div.problem-cards").sortable({
            placeholder: "ui-state-highlight",
            forcePlaceholderSize: true,
            stop: _ => editContest()
        });
    }

    function deleteContestProblem(id) {
        $(`.card.${id}`).remove();
        editContest();
    }

    function chooseProblemDialog() {
        $("div.modal").modal();
    }

    function chooseProblem() {
        if ($("select.problem-choice").val() != "-") {
            var problem = $("select.problem-choice").val();
            editContest(problem);
        }
    }

/*--------------------------------------------------------------------------------------------------
Problems page
--------------------------------------------------------------------------------------------------*/
    function deleteProblem(id) {
        var title = $(`div.card.${id}`).find(".card-title").text();
        if (!confirm(`Are you sure you want to delete ${title}?`)) {
            return;
        }
        $.post("/deleteProblem", {id: id}, data => {
            if (data == "ok") {
                window.location.reload();
            }
        });
    }

/*--------------------------------------------------------------------------------------------------
Problem page
--------------------------------------------------------------------------------------------------*/
    function createTestDataDialog() {
        $("div.modal").modal();
    }

    function createTestData() {
        var input = $(".test-data-input").val();
        var output = $(".test-data-output").val();
        editProblem({input: input, output: output});
    }

    var handlingClick = false;
    function editProblem(newTest=undefined) {
        // Eliminate double-click problem
        if (handlingClick) {
            // User has already clicked the button recently and the request isn't done
            return;
        }
        handlingClick = true;

        var id = $("#prob-id").val();
        var problem = {id: id};
        problem.title       = $("#problem-title").val();
        problem.description = $("#problem-description").val();
        problem.statement   = mdEditors[0].value();
        problem.input       = mdEditors[1].value();
        problem.output      = mdEditors[2].value();
        problem.constraints = mdEditors[3].value();
        problem.samples     = $("#problem-samples").val();
        testData = [];
        $(".test-data-cards .card").each((_, card) => {
            var input = $(card).find("code:eq(0)").html().replace(/<br>/g, "\n").replace(/<br\/>/g, "\n").replace(/&nbsp;/g, " ");
            var output = $(card).find("code:eq(1)").html().replace(/<br>/g, "\n").replace(/<br\/>/g, "\n").replace(/&nbsp;/g, " ");
            testData.push({input: input, output: output});
        });
        if (newTest != undefined) {
            testData.push(newTest);
        }
        problem.testData = JSON.stringify(testData);
        
        if (problem.samples > testData.length) {
            alert("You have set the number of samples beyond the number of tests available.");
            return;
        }

        $.post("/editProblem", problem, id => {
            if (window.location.pathname == "/problems/new") {
                window.location = `/problems/${id}/edit`;
            } else {
                window.location.reload();
            }
        });
        return false;
    }

    function deleteTestData(dataNum) {
        if ($(".test-data-cards .card").length <= $("#problem-samples").val()) {
            alert("Deleting this item would make the number of sample cases invalid.");
            return;
        }
        $(`.test-data-cards .card:eq(${dataNum})`).remove();
        editProblem();
    }
    
    var mdEditors = [];
    function setupProblemPage() {
        $(".rich-text textarea").each((_, elem) => {
            mdEditors.push(new SimpleMDE({ element: elem }));
        });
        $("div.test-data-cards").sortable({
            placeholder: "ui-state-highlight",
            forcePlaceholderSize: true,
            stop: _ => editProblem()
        });
    }

/*--------------------------------------------------------------------------------------------------
General
--------------------------------------------------------------------------------------------------*/
    async function fixFormatting() {
        $(".time-format").each((_, span) => {
            var timestamp = $(span).text();
            var d = new Date(parseInt(timestamp));
            $(span).text(d.toLocaleString());
        });
        await getLanguages();
        $("span.language-format").each((_, span) => {
            var lang = $(span).text();
            $(span).text(languages[lang].name);
        });
        $("span.result-format").each((_, span) => {
            var result = $(span).text();
            $(span).text(verdict_name[result]);
        });
    }
/*--------------------------------------------------------------------------------------------------
Messages Page
--------------------------------------------------------------------------------------------------*/
    function createMessage() {
        $("div.modal").modal();
    }

    function sendMessage() {
        var text = $("textarea.message").val();
        var recipient = $("select.recipient").val();
        var replyTo = $("#replyTo").val();
        $.post("/sendMessage", {to: recipient, message: text, replyTo: replyTo}, result => {
            if (result == "ok") {
                $("div.modal").modal("hide");
            } else {
                alert(result);
            }
        });
    }

    function reply(user, replyToMsgId) {
        $("select.recipient").val(user);
        $("#replyTo").val(replyToMsgId);
        createMessage();
        $("textarea.message").focus();
    }

    function showIncomingMessage(msg) {
        $("div.message-alerts").append(`<div class="alert alert-warning alert-dismissible fade show" role="alert">
            ${msg.message}
            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                <span aria-hidden="true">&times;</span>
            </button>
        </div>`);
    }

    var lastChecked = 0;
    var seenMessages = JSON.parse(localStorage.seenMessages || "{}");
    function displayIncomingMessages() {
        $.post("/getMessages", {timestamp: lastChecked}, messages => {
            lastChecked = messages.timestamp
            for (message of messages.messages) {
                if (message.id in seenMessages || message.from.id == user) {
                    continue;
                }
                showIncomingMessage(message);
                seenMessages[message.id] = message;
            }
            localStorage.seenMessages = JSON.stringify(seenMessages);
        });
        window.setTimeout(displayIncomingMessages, 5000);
    }

/*--------------------------------------------------------------------------------------------------
Judging Page
--------------------------------------------------------------------------------------------------*/
    function changeSubmissionResult(id) {
        var result = $(`.result-choice.${id}`).val();
        $.post("/changeResult", {id: id, result: result}, result => {
            if (result == "ok") {
                window.location.reload();
            } else {
                alert(result);
            }
        })
    }

    function submissionPopup(id) {
        $.post(`/judgeSubmission/${id}`, {}, data => {
            $(".modal-dialog").html(data);
            $(".result-tabs").tabs();
            fixFormatting();
            $(".modal").modal();
        });
    }

    function rejudge(id) {
        $(".rejudge").attr("disabled", true);
        $(".rejudge").addClass("button-gray");

        $.post("/rejudge", {id: id}, data => {
            $(".rejudge").attr("disabled", false);
            $(".rejudge").removeClass("button-gray");
            alert(`New Result: ${verdict_name[data]}`);
        });
    }
