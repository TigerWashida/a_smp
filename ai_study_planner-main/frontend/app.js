const state={calendar:null,preview:null,toastTimer:null,tasks:[]};
document.addEventListener("DOMContentLoaded",()=>{if(window.__studyMateOpenedDirectly)return;setupNavigation();setupPlanner();setupCalendar();setupPreviewActions();setupChat();setupTheme();setDefaultDeadline();refreshSavedData();});
async function api(path,options={}){
  let response;try{response=await fetch(path,{...options,headers:{"Content-Type":"application/json",...(options.headers||{})}});}catch{throw new Error("Network error. Check that StudyMate is running.");}
  let payload;try{payload=await response.json();}catch{throw new Error(response.ok?"The server returned invalid JSON.":"The server returned an unreadable error.");}
  if(!response.ok)throw new Error(payload.detail||"Request failed.");return payload;
}
function setupNavigation(){
  document.querySelectorAll(".nav-item").forEach(button=>button.addEventListener("click",()=>showPage(button.dataset.page)));
  document.getElementById("openCalendarPage").addEventListener("click",()=>showPage("calendar-page"));
}
function showPage(pageId){
  document.querySelectorAll(".page").forEach(page=>page.classList.toggle("hidden",page.id!==pageId));
  document.querySelectorAll(".nav-item").forEach(button=>button.classList.toggle("active",button.dataset.page===pageId));
  if(pageId==="calendar-page"&&state.calendar)setTimeout(()=>state.calendar.updateSize(),30);
}
function setupPlanner(){
  const dialog=document.getElementById("plannerDialog");
  document.querySelectorAll(".open-planner").forEach(button=>button.addEventListener("click",()=>dialog.showModal()));
  document.getElementById("closePlanner").addEventListener("click",()=>dialog.close());
  document.getElementById("cancelPlanner").addEventListener("click",()=>dialog.close());
  document.getElementById("plannerForm").addEventListener("submit",createPreview);
}
function setDefaultDeadline(){const value=new Date();value.setDate(value.getDate()+7);const field=document.getElementById("deadline");field.value=localDate(value);field.min=localDate(new Date());}
function setupCalendar(){
  state.calendar=new FullCalendar.Calendar(document.getElementById("calendar"),{
    initialView:"timeGridWeek",firstDay:1,nowIndicator:true,allDaySlot:false,slotMinTime:"00:00:00",slotMaxTime:"24:00:00",
    slotDuration:"00:30:00",snapDuration:"00:30:00",scrollTime:"08:00:00",height:"auto",editable:true,
    eventDurationEditable:false,eventStartEditable:true,headerToolbar:{left:"prev,next today",center:"title",right:"dayGridMonth,timeGridWeek,timeGridDay"},
    eventDrop:handleEventDrop
  });state.calendar.render();
}
async function createPreview(event){
  event.preventDefault();const button=document.getElementById("recommendButton");button.disabled=true;button.textContent="Finding open time…";
  const goal={subject:document.getElementById("subject").value,total_hours:Number(document.getElementById("totalHours").value),
    difficulty:document.getElementById("difficulty").value,preferred_slot:document.getElementById("preferredSlot").value,deadline:document.getElementById("deadline").value};
  try{clearPreviewEvents();state.preview=await api("/plan-previews",{method:"POST",body:JSON.stringify(goal)});
    state.preview.sessions.forEach(addPreviewEvent);renderPreviewPanel();document.getElementById("plannerDialog").close();
    showPage("calendar-page");state.calendar.gotoDate(state.preview.sessions[0].date);showToast("Recommendation ready. Drag any dashed session before accepting.");
  }catch(error){showToast(error.message,true);}finally{button.disabled=false;button.textContent="Get AI Recommendation";}
}
function addPreviewEvent(session){state.calendar.addEvent({id:"preview-"+session.preview_session_id,title:session.subject,start:session.date+"T"+session.start_time,end:session.date+"T"+session.end_time,classNames:["preview-event"],extendedProps:{kind:"preview",previewSessionId:session.preview_session_id}});}
function renderPreviewPanel(){
  const recommendation=state.preview.recommendation,panel=document.getElementById("previewPanel");panel.hidden=false;
  document.getElementById("recommendationText").textContent=recommendation.text;
  const badge=document.getElementById("recommendationMode");badge.textContent=recommendation.mode==="llm"?"Local AI":"Fallback";badge.classList.toggle("fallback",recommendation.mode==="fallback");
  const warning=document.getElementById("recommendationWarning");warning.hidden=!recommendation.warning;warning.textContent=recommendation.warning||"";
}
function setupPreviewActions(){document.getElementById("cancelPreview").addEventListener("click",cancelPreview);document.getElementById("acceptPlan").addEventListener("click",acceptPreview);}
async function acceptPreview(){
  if(!state.preview)return;const button=document.getElementById("acceptPlan");button.disabled=true;button.textContent="Saving…";
  try{const sessions=state.preview.sessions.map(item=>({preview_session_id:item.preview_session_id,date:item.date,start_time:item.start_time,end_time:item.end_time}));
    await api("/plan-previews/"+encodeURIComponent(state.preview.preview_id)+"/accept",{method:"POST",body:JSON.stringify({sessions})});
    cancelPreview();await refreshSavedData();showToast("Plan accepted and saved.");
  }catch(error){showToast(error.message,true);}finally{button.disabled=false;button.textContent="Accept Plan";}
}
function cancelPreview(){clearPreviewEvents();state.preview=null;document.getElementById("previewPanel").hidden=true;}
function clearPreviewEvents(){state.calendar.getEvents().filter(event=>event.extendedProps.kind==="preview").forEach(event=>event.remove());}
async function handleEventDrop(info){
  const start=info.event.start,end=info.event.end;if(!start||!end||localDate(start)!==localDate(end)){info.revert();showToast("Sessions must start and end on the same day.",true);return;}
  const moved={date:localDate(start),start_time:localTime(start),end_time:localTime(end)};
  if(info.event.extendedProps.kind==="preview"){
    const session=state.preview&&state.preview.sessions.find(item=>item.preview_session_id===info.event.extendedProps.previewSessionId);
    if(!session){info.revert();return;}Object.assign(session,moved);showToast("Preview moved. Accept the plan when it looks right.");return;
  }
  try{await api("/tasks/"+encodeURIComponent(info.event.id)+"/schedule",{method:"PATCH",body:JSON.stringify(moved)});await refreshSavedData(false);showToast("Session time updated.");}
  catch(error){info.revert();showToast(error.message,true);}
}
async function refreshSavedData(rebuildCalendar=true){
  try{const [dashboard,tasks]=await Promise.all([api("/dashboard"),api("/tasks")]);state.tasks=tasks;
    document.getElementById("goalCount").textContent=dashboard.goals;document.getElementById("pendingCount").textContent=dashboard.pending_tasks;
    document.getElementById("pendingHours").textContent=formatHours(dashboard.pending_hours);document.getElementById("completedCount").textContent=dashboard.completed_tasks;
    document.getElementById("accountGoalCount").textContent=dashboard.goals;document.getElementById("accountTaskCount").textContent=tasks.length;
    renderTasks(tasks);renderToday(tasks);renderCompletion(tasks);if(rebuildCalendar)renderSavedEvents(tasks);
  }catch(error){showToast(error.message,true);}
}
function renderSavedEvents(tasks){
  state.calendar.getEvents().filter(event=>event.extendedProps.kind==="saved").forEach(event=>event.remove());
  tasks.forEach(task=>state.calendar.addEvent({id:String(task.id),title:task.subject,start:task.date+"T"+task.start_time,end:task.date+"T"+task.end_time,
    editable:task.status!=="completed",classNames:task.status==="completed"?["completed-event"]:[],extendedProps:{kind:"saved"}}));
}
function renderTasks(tasks){renderTasksInto(document.getElementById("taskList"),tasks);renderTasksInto(document.getElementById("dashboardTaskList"),tasks.slice(0,5));}
function renderTasksInto(list,tasks){
  list.replaceChildren();const ordered=[...tasks].sort((a,b)=>(a.date+a.start_time).localeCompare(b.date+b.start_time));
  if(!ordered.length){const empty=document.createElement("p");empty.className="empty-state";empty.textContent="No saved sessions yet.";list.append(empty);return;}
  ordered.forEach(task=>{const card=document.createElement("article");card.className="task-card"+(task.status==="completed"?" completed":"");
    const details=document.createElement("div"),title=document.createElement("strong"),timing=document.createElement("span");title.textContent=task.subject;
    timing.textContent=task.date+" · "+displayTime(task.start_time)+"–"+displayTime(task.end_time);details.append(title,timing);
    const button=document.createElement("button");button.type="button";button.textContent=task.status==="completed"?"Reopen":"Complete";button.addEventListener("click",()=>toggleTask(task));
    card.append(details,button);list.append(card);});
}
function renderToday(tasks){
  const container=document.getElementById("todaySchedule"),today=localDate(new Date()),items=tasks.filter(task=>task.date===today).sort((a,b)=>a.start_time.localeCompare(b.start_time));container.replaceChildren();
  if(!items.length){const empty=document.createElement("div");empty.className="empty-state";const wrap=document.createElement("div"),icon=document.createElement("span"),copy=document.createElement("p");
    icon.textContent="📖";copy.textContent="No sessions scheduled today. Create a goal or use the week to plan ahead.";wrap.append(icon,copy);empty.append(wrap);container.append(empty);return;}
  items.forEach(task=>{const row=document.createElement("article");row.className="timeline-item";const time=document.createElement("div");time.className="timeline-time";time.textContent=displayTime(task.start_time);
    const card=document.createElement("div");card.className="timeline-card";const title=document.createElement("strong"),meta=document.createElement("span");title.textContent=task.subject;
    meta.textContent=task.hours+" hr · "+task.difficulty+" · "+task.status;card.append(title,meta);row.append(time,card);container.append(row);});
}
function renderCompletion(tasks){
  const completed=tasks.filter(task=>task.status==="completed").length,percent=tasks.length?Math.round(completed/tasks.length*100):0,circle=document.getElementById("completionCircle");
  circle.textContent=percent+"%";circle.style.background="conic-gradient(var(--success-color) "+(percent*3.6)+"deg, var(--border-color) 0deg)";
  document.getElementById("completionRecommendation").textContent=tasks.length?(completed===tasks.length?"All saved sessions are complete.":"Complete the next session to keep your plan moving."):"Create a study goal to begin.";
}
async function toggleTask(task){const status=task.status==="completed"?"pending":"completed";try{await api("/tasks/"+encodeURIComponent(task.id),{method:"PATCH",body:JSON.stringify({status})});await refreshSavedData();}catch(error){showToast(error.message,true);}}
function setupChat(){
  const window=document.getElementById("chatWindow");document.getElementById("chatToggle").addEventListener("click",()=>{window.hidden=!window.hidden;});
  document.getElementById("chatClose").addEventListener("click",()=>{window.hidden=true;});
  document.getElementById("chatForm").addEventListener("submit",async event=>{event.preventDefault();const input=document.getElementById("chatInput"),query=input.value.trim();if(!query)return;
    appendMessage(query,"user");input.value="";try{const payload=await api("/chat",{method:"POST",body:JSON.stringify({query,preview_id:state.preview?state.preview.preview_id:null})});
      appendMessage(payload.response,"assistant",payload.mode,payload.warning);}catch(error){appendMessage(error.message,"assistant","error");}});
}
function appendMessage(text,role,mode,warning){
  const container=document.getElementById("chatMessages"),row=document.createElement("div"),label=document.createElement("span"),message=document.createElement("div"),body=document.createElement("span");
  row.className="message-row "+(role==="user"?"user-row":"ai-row");label.className="message-label";label.textContent=role==="user"?"You":"StudyMate";message.className="message "+role;body.textContent=text;message.append(body);
  if(mode){const meta=document.createElement("small");meta.textContent=mode==="llm"?"Local AI":mode==="fallback"?"Fallback":"Error";if(warning)meta.textContent+=" · "+warning;message.append(meta);}
  row.append(label,message);container.append(row);container.scrollTop=container.scrollHeight;
}
function setupTheme(){
  const saved=localStorage.getItem("studymate-theme")||"dark";setTheme(saved);
  document.querySelectorAll('input[name="theme"]').forEach(input=>{input.checked=input.value===saved;input.addEventListener("change",()=>setTheme(input.value));});
}
function setTheme(value){document.body.classList.toggle("dark-theme",value==="dark");localStorage.setItem("studymate-theme",value);if(state.calendar)setTimeout(()=>state.calendar.updateSize(),30);}
function localDate(value){return value.getFullYear()+"-"+String(value.getMonth()+1).padStart(2,"0")+"-"+String(value.getDate()).padStart(2,"0");}
function localTime(value){return String(value.getHours()).padStart(2,"0")+":"+String(value.getMinutes()).padStart(2,"0");}
function displayTime(value){const parts=value.split(":").map(Number),suffix=parts[0]>=12?"PM":"AM",hour=parts[0]%12||12;return hour+":"+String(parts[1]).padStart(2,"0")+" "+suffix;}
function formatHours(value){const number=Number(value);return Number.isInteger(number)?String(number):number.toFixed(1);}
function showToast(message,error=false){const toast=document.getElementById("toast");toast.textContent=message;toast.className="toast"+(error?" error":"");toast.hidden=false;clearTimeout(state.toastTimer);state.toastTimer=setTimeout(()=>{toast.hidden=true;},4500);}
