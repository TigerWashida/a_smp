const API_BASE = "http://localhost:8000";


/* ===================================
   DASHBOARD DATE STATE
=================================== */

let allTasksCache = [];

let selectedDashboardDate =
    getTodayDateString();

let taskPageMode =
    "date";


function getTodayDateString() {

    const today =
        new Date();

    return formatDateForAPI(
        today
    );
}


function formatDateForAPI(date) {

    const year =
        date.getFullYear();

    const month =
        String(
            date.getMonth() + 1
        ).padStart(
            2,
            "0"
        );

    const day =
        String(
            date.getDate()
        ).padStart(
            2,
            "0"
        );

    return `${year}-${month}-${day}`;
}


function getTasksForSelectedDashboardDate() {

    return allTasksCache.filter(task => {
        return task.deadline === selectedDashboardDate;
    });
}


function refreshDashboardScheduleForSelectedDate() {

    const filteredTasks =
        getTasksForSelectedDashboardDate();

    renderTaskList(
        filteredTasks
    );

    renderSchedule(
        filteredTasks
    );

    updateDashboardDateTitle();
}


function updateDashboardDateTitle() {

    const title =
        document.getElementById(
            "dashboardDateTitle"
        );

    const text =
        document.getElementById(
            "dashboardDateText"
        );

    if (!title || !text) {
        return;
    }

    if (selectedDashboardDate === getTodayDateString()) {

        title.innerText =
            "Today's Schedule";

        text.innerText =
            "Today";

    } else {

        title.innerText =
            "Selected Schedule";

        text.innerText =
            selectedDashboardDate;
    }
}


function changeDashboardDate(direction) {

    const parts =
        selectedDashboardDate.split("-");

    const date =
        new Date(
            Number(parts[0]),
            Number(parts[1]) - 1,
            Number(parts[2])
        );

    date.setDate(
        date.getDate() + direction
    );

    selectedDashboardDate =
        formatDateForAPI(
            date
        );

    refreshDashboardScheduleForSelectedDate();
}


function goToTodayDashboard() {

    selectedDashboardDate =
        getTodayDateString();

    refreshDashboardScheduleForSelectedDate();

    setTimeout(() => {

        scrollToCurrentTime();

    }, 100);
}


/* ===================================
   DEADLINE CALENDAR
   Used inside Create Study Plan modal
=================================== */

let deadlineCalendar;
let calendarOpen = false;


function toggleDeadlineCalendar() {

    const popup =
        document.getElementById(
            "deadlineCalendarPopup"
        );

    if (!popup) {
        return;
    }

    if (!deadlineCalendar) {

        initializeDeadlineCalendar();
    }

    calendarOpen = !calendarOpen;

    popup.classList.toggle(
        "hidden",
        !calendarOpen
    );

    if (calendarOpen && deadlineCalendar) {

        deadlineCalendar.updateSize();
    }
}


function initializeDeadlineCalendar() {

    const el =
        document.getElementById(
            "deadlineCalendar"
        );

    if (!el) {
        return;
    }

    deadlineCalendar =
        new FullCalendar.Calendar(
            el,
            {
                initialView:
                    "dayGridMonth",

                height:
                    280,

                headerToolbar: {
                    left:
                        "prev,next",
                    center:
                        "title",
                    right:
                        ""
                },

                dateClick(info) {

                    document.getElementById(
                        "examDate"
                    ).value =
                        info.dateStr;

                    const parts =
                        info.dateStr.split("-");

                    const date =
                        new Date(
                            Number(parts[0]),
                            Number(parts[1]) - 1,
                            Number(parts[2])
                        );

                    const formatted =
                        date.toLocaleDateString(
                            "en-GB",
                            {
                                day:
                                    "numeric",
                                month:
                                    "short",
                                year:
                                    "numeric"
                            }
                        );

                    document.getElementById(
                        "selectedDeadline"
                    ).innerHTML =
                        "📅 " + formatted;

                    toggleDeadlineCalendar();
                }
            }
        );

    deadlineCalendar.render();
}


/* ===================================
   NAVIGATION
=================================== */

function showPage(
    pageId,
    element
) {

    document.querySelectorAll(
        ".page"
    ).forEach(page => {

        page.classList.add(
            "hidden"
        );
    });

    document.getElementById(
        pageId
    ).classList.remove(
        "hidden"
    );

    document.querySelectorAll(
        ".nav-item"
    ).forEach(item => {

        item.classList.remove(
            "active"
        );
    });

    if (element) {

        element.classList.add(
            "active"
        );
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

function openModal() {

    document.getElementById(
        "studyModal"
    ).style.display =
        "flex";

    if (!deadlineCalendar) {

        initializeDeadlineCalendar();
    }

    setTimeout(() => {

        if (deadlineCalendar) {

            deadlineCalendar.updateSize();
        }

    }, 100);
}


function closeModal() {

    document.getElementById(
        "studyModal"
    ).style.display =
        "none";

    const popup =
        document.getElementById(
            "deadlineCalendarPopup"
        );

    if (popup) {

        popup.classList.add(
            "hidden"
        );
    }

    calendarOpen = false;
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
        hour >= 12
            ? "PM"
            : "AM";

    let displayHour =
        hour % 12;

    if (displayHour === 0) {

        displayHour = 12;
    }

    return `${displayHour}:00 ${period}`;
}


function getSlotStartHour(preferredSlot) {

    if (preferredSlot === "Morning") {

        return 9;
    }

    if (preferredSlot === "Afternoon") {

        return 13;
    }

    if (preferredSlot === "Evening") {

        return 18;
    }

    return 9;
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

        deadline:
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
                    method:
                        "POST",
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

        const data =
            await response.json();

        if (!response.ok) {

            showToast(
                "❌ " + data.detail
            );

            return;
        }

        console.log(
            data
        );

        closeModal();

        await loadDashboard();

        await loadTasks();

        await loadCompletionRecommendation();

        showToast(
            "✅ Study Plan Created Successfully"
        );

    } catch (error) {

        console.error(
            error
        );

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

            circle.style.background =
                `
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

        allTasksCache =
            tasks;

        refreshDashboardScheduleForSelectedDate();

        renderAllTasksPage(
            tasks
        );

        updateCalendarEvents(
            tasks
        );

    } catch (error) {

        console.error(
            "Task Error",
            error
        );
    }
}


function renderTaskList(tasks) {

    const tracker =
        document.getElementById(
            "taskTracker"
        );

    let html =
        "";

    const slotCurrentHours = {
        Morning: 9,
        Afternoon: 13,
        Evening: 18
    };

    tasks.forEach((task) => {

        const duration =
            Number(
                task.hours
            );

        const slot =
            task.preferred_slot;

        if (
            slotCurrentHours[slot] === undefined
        ) {

            slotCurrentHours[slot] =
                getSlotStartHour(
                    slot
                );
        }

        const startHour =
            slotCurrentHours[slot];

        const endHour =
            startHour + duration;

        const timeRange =
            `${formatHour(startHour)} - ${formatHour(endHour)}`;

        html += buildTaskCardHTML(
            task,
            timeRange
        );

        slotCurrentHours[slot] =
            endHour;
    });

    if (html === "") {

        html = `
            <p class="empty-message">
                No study sessions for this date.
            </p>
        `;
    }

    if (tracker) {

        tracker.innerHTML =
            html;
    }
}


function buildTaskCardHTML(
    task,
    timeRange
) {

    return `

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

                ${timeRange}

                <br>

                <small>
                    ${task.deadline}
                    •
                    ${task.preferred_slot}
                    •
                    ${task.status}
                </small>

            </div>

        </div>

    `;
}


function setTaskPageMode(mode) {

    taskPageMode =
        mode;

    const dateBtn =
        document.getElementById(
            "taskDateModeBtn"
        );

    const labelBtn =
        document.getElementById(
            "taskLabelModeBtn"
        );

    if (dateBtn && labelBtn) {

        dateBtn.classList.toggle(
            "active",
            mode === "date"
        );

        labelBtn.classList.toggle(
            "active",
            mode === "label"
        );
    }

    renderAllTasksPage(
        allTasksCache
    );
}


function renderAllTasksPage(tasks) {

    const allTasks =
        document.getElementById(
            "allTasksContainer"
        );

    if (!allTasks) {
        return;
    }

    if (!tasks || tasks.length === 0) {

        allTasks.innerHTML =
            `
            <p class="empty-message">
                No tasks created yet.
            </p>
            `;

        return;
    }

    if (taskPageMode === "date") {

        renderTasksGroupedByDate(
            tasks,
            allTasks
        );

    } else {

        renderTasksGroupedByLabel(
            tasks,
            allTasks
        );
    }
}


function renderTasksGroupedByDate(
    tasks,
    container
) {

    const grouped = {};

    tasks.forEach(task => {

        if (!grouped[task.deadline]) {

            grouped[task.deadline] =
                [];
        }

        grouped[task.deadline].push(
            task
        );
    });

    let html =
        "";

    Object.keys(grouped)
        .sort()
        .forEach(date => {

            html += `
                <div class="task-group">
                    <h3>
                        ${date}
                    </h3>
                </div>
            `;

            grouped[date].forEach(task => {

                html += buildTaskCardHTML(
                    task,
                    `${task.hours} hour(s)`
                );
            });
        });

    container.innerHTML =
        html;
}


function renderTasksGroupedByLabel(
    tasks,
    container
) {

    const grouped = {};

    tasks.forEach(task => {

        const label =
            task.subject;

        if (!grouped[label]) {

            grouped[label] =
                [];
        }

        grouped[label].push(
            task
        );
    });

    let html =
        "";

    Object.keys(grouped)
        .sort()
        .forEach(label => {

            html += `
                <div class="task-group">
                    <h3>
                        ${label}
                    </h3>
                </div>
            `;

            grouped[label].forEach(task => {

                html += buildTaskCardHTML(
                    task,
                    `${task.hours} hour(s)`
                );
            });
        });

    container.innerHTML =
        html;
}


async function updateTask(taskId) {

    try {

        const response =
            await fetch(
                `${API_BASE}/tasks/${taskId}`,
                {
                    method:
                        "PATCH"
                }
            );

        const data =
            await response.json();

        console.log(
            data
        );

        await loadTasks();

        await loadDashboard();

        await loadCompletionRecommendation();

    } catch (error) {

        console.error(
            error
        );
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

            recommendationDiv.innerHTML =
                `
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

    } catch (error) {

        console.error(
            error
        );

        const recommendationDiv =
            document.getElementById(
                "completionRecommendation"
            );

        if (recommendationDiv) {

            recommendationDiv.innerHTML =
                "No recommendation available yet.";
        }
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

    // messages.innerHTML += `

    //     <div class="message-row user-row">

    //         <div class="message-label">

    //             User

    //         </div>

    //         <div class="user-message">

    //             ${message}

    //         </div>

    //     </div>

    // `;

    messages.innerHTML += `

        <div class="message-row user-row">

            <div class="message-label">

                User

            </div>

            <div class="user-message">

                ${formatMarkdownText(message)}

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

    input.value =
        "";

    input.focus();

    try {

        const response =
            await fetch(
                `${API_BASE}/chat`,
                {
                    method:
                        "POST",
                    headers: {
                        "Content-Type":
                            "application/json"
                    },
                    body:
                        JSON.stringify({
                            query:
                                message
                        })
                }
            );

        // const data =
        //     await response.json();

        // document.getElementById(
        //     aiMessageId
        // ).innerHTML =
        //     data.response;

        // messages.scrollTop =
        //     messages.scrollHeight;
        const data =
            await response.json();

        document.getElementById(
            aiMessageId
        ).innerHTML =
            formatMarkdownText(data.response);

        messages.scrollTop =
            messages.scrollHeight;        

    } catch (error) {

        document.getElementById(
            aiMessageId
        ).innerHTML =
            "❌ Unable to get response.";

        console.error(
            error
        );
    }
}


/* ===================================
   CALENDAR
   Main schedule calendar
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

                height:
                    700,

                headerToolbar: {
                    left:
                        "prev,next today",
                    center:
                        "title",
                    right:
                        ""
                },

                dateClick(info) {

                    selectedDashboardDate =
                        info.dateStr;

                    refreshDashboardScheduleForSelectedDate();

                    showToast(
                        "Showing schedule for " + info.dateStr
                    );
                }
            }
        );

    calendar.render();
}


function updateCalendarEvents(tasks) {

    if (!calendar) {
        return;
    }

    calendar.removeAllEvents();

    tasks.forEach(task => {

        calendar.addEvent({
            title:
                `${task.subject} (${task.hours}h)`,
            start:
                task.deadline,
            allDay:
                true
        });
    });
}


/* ===================================
   CHART
=================================== */

let energyChart;


function initializeChart(
    tasks = []
) {

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

            subjectHours[task.subject] =
                0;
        }

        subjectHours[task.subject] +=
            Number(
                task.hours
            );
    });

    const labels =
        Object.keys(
            subjectHours
        );

    const values =
        Object.values(
            subjectHours
        );

    if (energyChart) {

        energyChart.destroy();
    }

    energyChart =
        new Chart(
            chart,
            {
                type:
                    "line",

                data: {
                    labels:
                        labels,

                    datasets: [{
                        label:
                            "Selected Day Study Hours",
                        data:
                            values,
                        tension:
                            0.35,
                        fill:
                            false
                    }]
                },

                options: {
                    responsive:
                        true,

                    maintainAspectRatio:
                        false,

                    plugins: {
                        legend: {
                            display:
                                true
                        }
                    },

                    scales: {
                        y: {
                            beginAtZero:
                                true
                        }
                    }
                }
            }
        );
}

/* ===================================
   MARKDOWN PARSER HELPER
=================================== */

function formatMarkdownText(text) {
    if (!text) return "";

    return text
        // Replace bold **text** with <strong>text</strong>
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        // Replace italic *text* or _text_ with <em>text</em>
        .replace(/\*(.*?)\*/g, "<em>$1</em>")
        // Replace newlines with <br> tags
        .replace(/\n/g, "<br>");
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

    const isToday =
        selectedDashboardDate === getTodayDateString();

    const now =
        new Date();

    const currentHour =
        now.getHours();

    const currentMinute =
        now.getMinutes();

    const currentTimeTop =
        (
            currentHour +
            currentMinute / 60
        ) * hourHeight;

    let rowsHtml =
        "";

    for (
        let hour = 0;
        hour < 24;
        hour++
    ) {

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

    const slotCurrentHours = {
        Morning: 9,
        Afternoon: 13,
        Evening: 18
    };

    tasks.forEach((task) => {

        const duration =
            Number(
                task.hours
            );

        const slot =
            task.preferred_slot;

        if (
            slotCurrentHours[slot] === undefined
        ) {

            slotCurrentHours[slot] =
                getSlotStartHour(
                    slot
                );
        }

        const startHour =
            slotCurrentHours[slot];

        const endHour =
            startHour + duration;

        const top =
            startHour * hourHeight;

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

                    ${formatHour(startHour)}
                    -
                    ${formatHour(endHour)}
                    •
                    ${duration} hrs
                    •
                    ${task.status}

                </div>

            </div>

        `;

        slotCurrentHours[slot] =
            endHour;
    });

    if (taskHtml === "") {

        taskHtml = `

            <div
                class="schedule-task-card"
                style="
                    top: ${9 * hourHeight}px;
                    height: ${hourHeight}px;
                ">

                <div class="schedule-task-title">

                    No study sessions

                </div>

                <div class="schedule-task-meta">

                    Select another date from the calendar

                </div>

            </div>

        `;
    }

    container.innerHTML =
        `

        <div
            class="schedule-grid"
            style="height: ${24 * hourHeight}px;">

            ${rowsHtml}

            ${isToday
                ? `
                    <div
                        class="current-time-line"
                        style="top: ${currentTimeTop}px;">
                    </div>
                `
                : ""}

            ${taskHtml}

        </div>

    `;

    requestAnimationFrame(() => {

        if (!isToday) {

            container.scrollTo({
                top:
                    8 * hourHeight,
                behavior:
                    "smooth"
            });

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
            top:
                targetScrollTop,
            behavior:
                "smooth"
        });
    });

    initializeChart(
        tasks.slice(
            0,
            5
        )
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
        top:
            targetScrollTop,
        behavior:
            "smooth"
    });
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