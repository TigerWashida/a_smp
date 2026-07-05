const API_BASE = "http://localhost:8000";

/* ===================================
   NAVIGATION
=================================== */

function showPage(pageId, element) {

    document.querySelectorAll(".page")
        .forEach(page => {
            page.classList.add("hidden");
        });

    document.getElementById(pageId)
        .classList.remove("hidden");

    document.querySelectorAll(".nav-item")
        .forEach(item => {
            item.classList.remove("active");
        });

    if (element) {
        element.classList.add("active");
    }

    if (pageId === "calendar-page") {

        if (calendar) {

            calendar.render();

            setTimeout(() => {

                calendar.updateSize();

            }, 100);
        }
    }
}

/* ===================================
   MODAL
=================================== */

// function openModal() {

//     document.getElementById(
//         "studyModal"
//     ).style.display = "flex";
// }

function openModal() {


    document.getElementById(
        "studyModal"
    ).style.display = "flex";

    if (!deadlineCalendar) {

        initializeDeadlineCalendar();

    } else {

        deadlineCalendar.render();

        deadlineCalendar.updateSize();
    }

}

function closeModal() {

    document.getElementById(
        "studyModal"
    ).style.display = "none";
}

/* ===================================
   THEME
=================================== */

function setTheme(theme) {

    if (theme === "dark") {

        document.body.classList.add(
            "dark-theme"
        );

    } else {

        document.body.classList.remove(
            "dark-theme"
        );
    }

    localStorage.setItem(
        "theme",
        theme
    );
}

/* ===================================
   HELPERS
=================================== */

function formatHour(hour) {

    if (hour === 24) {
        return "12:00 AM";
    }

    const period =
        hour >= 12 ? "PM" : "AM";

    let displayHour =
        hour % 12;

    if (displayHour === 0) {
        displayHour = 12;
    }

    return `${displayHour}:00 ${period}`;
}

/* ===================================
   CREATE STUDY PLAN
=================================== */

async function generatePlan() {

    const payload = {

        subject:
            document.getElementById(
                "subject"
            ).value,

        total_hours:
            parseInt(
                document.getElementById(
                    "hours"
                ).value
            ),

        difficulty:
            document.getElementById(
                "difficulty"
            ).value,

        preferred_slot:
            document.getElementById(
                "slot"
            ).value,

        exam_date:
            document.getElementById(
                "examDate"
            ).value
    };

    console.log(
        "Payload:",
        payload
    );

    try {

        const response =
            await fetch(
                `${API_BASE}/generate-plan`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type":
                            "application/json"
                    },
                    body:
                        JSON.stringify(
                            payload
                        )
                }
            );

        console.log(
            "Status:",
            response.status
        );

        const data =
            await response.json();

        console.log(data);

        closeModal();

        await loadDashboard();
        await loadTasks();
        await loadCompletionRecommendation();

        showToast(
            "✅ Study Plan Created Successfully"
        );

    } catch (error) {

        console.error(error);

        showToast(
            "Failed to create plan. Please try again."
        );
    }
}

/* ===================================
   DASHBOARD
=================================== */

async function loadDashboard() {

    try {

        const response =
            await fetch(
                `${API_BASE}/dashboard`
            );

        const data =
            await response.json();

        const subjects =
            document.getElementById(
                "subjectsCount"
            );

        const planned =
            document.getElementById(
                "plannedHours"
            );

        const completed =
            document.getElementById(
                "completedHours"
            );

        const progress =
            document.getElementById(
                "progress"
            );

        if (subjects) {
            subjects.innerText =
                data.subjects;
        }

        if (planned) {
            planned.innerText =
                data.planned_hours;
        }

        if (completed) {
            completed.innerText =
                data.completed_hours;
        }

        if (progress) {
            progress.innerText =
                data.progress + "%";
        }

        const circle =
            document.getElementById(
                "completionCircle"
            );

        if (circle) {

            const progress =
                data.progress;

            circle.innerText =
                progress + "%";

            const degrees =
                (progress / 100) * 360;

            circle.style.background = `

                conic-gradient(

                    #22c55e 0deg,

                    #22c55e ${degrees}deg,

                    #960b2e ${degrees}deg,

                    #960b2e 360deg

                )

            `;
        }

    } catch (error) {

        console.error(
            "Dashboard Error",
            error
        );
    }
}

/* ===================================
   TASKS
=================================== */

async function loadTasks() {

    try {

        const response =
            await fetch(
                `${API_BASE}/tasks`
            );

        const tasks =
            await response.json();

        const tracker =
            document.getElementById(
                "taskTracker"
            );

        const allTasks =
            document.getElementById(
                "allTasksContainer"
            );

        let html = "";

        let currentStartHour =
            9;

        tasks.forEach((task) => {

            const duration =
                Number(task.hours);

            html += `

                <div class="task-card">

                    <div class="task-left">

                        <input
                            type="checkbox"
                            ${task.status === "completed"
                                ? "checked"
                                : ""}
                            onchange="updateTask(${task.id})">

                        <span>

                            ${task.subject}

                        </span>

                    </div>

                    <div class="task-time">

                        ${formatHour(currentStartHour)}

                    </div>

                </div>

            `;

            currentStartHour += duration;
        });

        if (tracker) {
            tracker.innerHTML =
                html;
        }

        if (allTasks) {
            allTasks.innerHTML =
                html;
        }

        renderSchedule(tasks);

    } catch (error) {

        console.error(
            "Task Error",
            error
        );
    }
}

async function updateTask(taskId) {

    try {

        const response =
            await fetch(
                `${API_BASE}/tasks/${taskId}`,
                {
                    method: "PATCH"
                }
            );

        const data =
            await response.json();

        console.log(data);

        await loadTasks();
        await loadDashboard();
        await loadCompletionRecommendation();

    } catch (error) {

        console.error(error);
    }
}

/* ===================================
   TOAST
=================================== */

function showToast(message) {

    const toast =
        document.getElementById(
            "toast"
        );

    if (!toast) {
        return;
    }

    toast.innerText =
        message;

    toast.classList.add(
        "show-toast"
    );

    setTimeout(() => {

        toast.classList.remove(
            "show-toast"
        );

    }, 3000);
}

/* ===================================
   RECOMMENDATIONS
=================================== */

async function loadCompletionRecommendation() {

    try {

        const response =
            await fetch(
                `${API_BASE}/recommendations`
            );

        const data =
            await response.json();

        const recommendationDiv =
            document.getElementById(
                "completionRecommendation"
            );

        if (recommendationDiv) {

            recommendationDiv.innerHTML = `

                <strong>

                    ${data.completed_tasks}
                    /
                    ${data.total_tasks}
                    sessions completed

                </strong>

                <br><br>

                ${data.recommendation}

            `;
        }

    } catch(error) {

        console.error(error);
    }
}

/* ===================================
   CHAT
=================================== */

function toggleChat() {

    const chat =
        document.getElementById(
            "chatWindow"
        );

    if (!chat) {
        return;
    }

    if (chat.style.display === "flex") {

        chat.style.display =
            "none";

    } else {

        chat.style.display =
            "flex";
    }
}

async function sendMessage() {

    const input =
        document.getElementById(
            "chatInput"
        );

    if (!input) {
        return;
    }

    const message =
        input.value.trim();

    if (!message) {
        return;
    }

    const messages =
        document.getElementById(
            "chatMessages"
        );

    if (!messages) {
        return;
    }

    messages.innerHTML += `

        <div class="message-row user-row">

            <div class="message-label">

                User

            </div>

            <div class="user-message">

                ${message}

            </div>

        </div>

    `;

    const aiMessageId =
        "ai-" + Date.now();

    messages.innerHTML += `

        <div class="message-row ai-row">

            <div class="message-label">

                AI Study Coach

            </div>

            <div
                id="${aiMessageId}"
                class="ai-message">

                <span class="typing">

                    Thinking...

                </span>

            </div>

        </div>

    `;

    messages.scrollTop =
        messages.scrollHeight;

    input.value = "";

    input.focus();

    try {

        const response =
            await fetch(
                `${API_BASE}/chat`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type":
                            "application/json"
                    },
                    body:
                        JSON.stringify({
                            query: message
                        })
                }
            );

        const data =
            await response.json();

        document.getElementById(
            aiMessageId
        ).innerHTML =
            data.response;

        messages.scrollTop =
            messages.scrollHeight;

    } catch (error) {

        document.getElementById(
            aiMessageId
        ).innerHTML =
            "❌ Unable to get response.";

        console.error(error);
    }
}

/* ===================================
   CALENDAR
=================================== */

let calendar;

function initializeCalendar() {

    const calendarEl =
        document.getElementById(
            "calendar"
        );

    if (!calendarEl) {
        return;
    }

    calendar =
        new FullCalendar.Calendar(
            calendarEl,
            {
                initialView:
                    "dayGridMonth",

                height: 700,

                dateClick(info) {

                    openModal();

                    document.getElementById(
                        "examDate"
                    ).value =
                        info.dateStr;
                }
            }
        );
}

/* ===================================
   CHART
=================================== */

let energyChart;

function initializeChart(tasks = []) {

    const chart =
        document.getElementById(
            "energyChart"
        );

    if (!chart) {
        return;
    }

    const subjectHours = {};

    tasks.forEach(task => {

        if (!subjectHours[task.subject]) {

            subjectHours[task.subject] = 0;
        }

        subjectHours[task.subject] +=
            Number(task.hours);
    });

    const labels =
        Object.keys(subjectHours);

    const values =
        Object.values(subjectHours);

    if (energyChart) {

        energyChart.destroy();
    }

    energyChart =
        new Chart(
            chart,
            {
                type: "line",
                data: {
                    labels: labels,
                    datasets: [{
                        label:
                            "Today's Study Hours",
                        data:
                            values,
                        tension:
                            0.35,
                        fill:
                            false
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            }
        );
}

/* ===================================
   SCHEDULE VIEW
=================================== */

function renderSchedule(tasks) {

    const container =
        document.getElementById(
            "scheduleContainer"
        );

    if (!container) {
        return;
    }

    const hourHeight =
        64;

    const now =
        new Date();

    const currentHour =
        now.getHours();

    const currentMinute =
        now.getMinutes();

    const currentTimeTop =
        (currentHour + currentMinute / 60) * hourHeight;

    let rowsHtml =
        "";

    for (let hour = 0; hour < 24; hour++) {

        rowsHtml += `

            <div
                class="calendar-row"
                style="height: ${hourHeight}px;">

                <div class="calendar-time">

                    ${formatHour(hour)}

                </div>

                <div class="calendar-line"></div>

            </div>

        `;
    }

    let taskHtml =
        "";

    let currentStartHour =
        9;

    tasks.forEach((task) => {

        const duration =
            Number(task.hours);

        const top =
            currentStartHour * hourHeight;

        const height =
            duration * hourHeight;

        taskHtml += `

            <div
                class="schedule-task-card"
                style="
                    top: ${top}px;
                    height: ${height}px;
                ">

                <div class="schedule-task-title">

                    ${task.subject}

                </div>

                <div class="schedule-task-meta">

                    ${duration} hrs • ${task.status}

                </div>

            </div>

        `;

        currentStartHour +=
            duration;
    });

    container.innerHTML = `

        <div
            class="schedule-grid"
            style="height: ${24 * hourHeight}px;">

            ${rowsHtml}

            <div
                class="current-time-line"
                style="top: ${currentTimeTop}px;">
            </div>

            ${taskHtml}

        </div>

    `;

    requestAnimationFrame(() => {

        const currentLine =
            container.querySelector(
                ".current-time-line"
            );

        if (!currentLine) {
            return;
        }

        const targetScrollTop =
            currentLine.offsetTop -
            container.clientHeight / 2;

        container.scrollTo({
            top: targetScrollTop,
            behavior: "smooth"
        });
    });

    initializeChart(
        tasks.slice(0, 5)
    );
}

function scrollToCurrentTime() {

    const container =
        document.getElementById(
            "scheduleContainer"
        );

    if (!container) {
        return;
    }

    const currentLine =
        container.querySelector(
            ".current-time-line"
        );

    if (!currentLine) {
        return;
    }

    const targetScrollTop =
        currentLine.offsetTop -
        container.clientHeight / 2;

    container.scrollTo({
        top: targetScrollTop,
        behavior: "smooth"
    });
}

let deadlineCalendar;


function initializeDeadlineCalendar() {


const calendarEl =
    document.getElementById(
        "deadlineCalendar"
    );

if (!calendarEl)
    return;

deadlineCalendar =
    new FullCalendar.Calendar(

        calendarEl,

        {

            initialView: "dayGridMonth",

            height: 320,

            headerToolbar: {

                left: "prev,next",

                center: "title",

                right: ""

            },

            dateClick(info) {

                document.getElementById(
                    "examDate"
                ).value =
                    info.dateStr;

                document.getElementById(
                    "selectedDeadline"
                ).innerHTML =

                    "Deadline: <strong>" +
                    info.dateStr +
                    "</strong>";
            }
        }

    );

deadlineCalendar.render();

}

/* ===================================
   APP START
=================================== */

window.onload = async () => {

    const savedTheme =
        localStorage.getItem(
            "theme"
        ) || "light";

    if (savedTheme === "dark") {

        document.body.classList.add(
            "dark-theme"
        );

    } else {

        document.body.classList.remove(
            "dark-theme"
        );
    }

    const selectedRadio =
        document.querySelector(
            `input[value="${savedTheme}"]`
        );

    if (selectedRadio) {

        selectedRadio.checked =
            true;
    }

    initializeCalendar();

    await loadDashboard();

    await loadTasks();

    await loadCompletionRecommendation();
};