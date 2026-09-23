const topics = {
  "UK":["Politics & Government","Economy","Transport","Education","Public Safety"],
  "WORLD":["Europe","North America","Middle East","Asia-Pacific","Africa","International Organisations"],
  "TECHNOLOGY":["Artificial Intelligence","Microsoft","Apple","Google","Nvidia","Space","Cybersecurity"],
  "AVIATION":["Airlines","Aircraft","Airports","Safety","Aviation Industry"],
  "FORMULA 1":["Race Weekend","Teams","Drivers","Technical","F1 Business"],
  "GAMING":["Minecraft","Xbox","PlayStation","PC Gaming","Nintendo","Releases"],
  "SCIENCE":["Space","Physics","Biology","Climate","Environment"],
  "BUSINESS":["Markets","Companies","Finance","Energy"],
  "ENTERTAINMENT":["Film & TV","Music","Eurovision","Theme Parks","Events"]
};
const sections=Object.keys(topics);
const $=id=>document.getElementById(id);
const sectionList=$("sectionList"), preferenceList=$("preferenceList");
const briefing=$("briefing"), archive=$("archive"), status=$("status");
const storageKey="terrabrief-preferences";

function defaults(){const p={};sections.forEach(s=>{p[s]=true;topics[s].forEach(x=>p[s+"::"+x]=true)});return p}
function getPrefs(){try{return {...defaults(),...JSON.parse(localStorage.getItem(storageKey)||"{}")}}catch(e){return defaults()}}
let preferences=getPrefs();

function save(){localStorage.setItem(storageKey,JSON.stringify(preferences));applyPreferences()}

function addPreference(key,label,sub=false,parent=null){
  const row=document.createElement("label");row.className="preference-row"+(sub?" subtopic":"");
  const box=document.createElement("input");box.type="checkbox";box.checked=preferences[key]!==false;box.dataset.preference=key;
  if(parent) box.dataset.parent=parent;
  box.onchange=()=>{
    preferences[key]=box.checked;
    if(!sub){topics[label].forEach(x=>preferences[label+"::"+x]=box.checked);buildPreferences()}
    save();
  };
  row.append(box,document.createTextNode(label));return row;
}
function buildPreferences(){
  preferenceList.innerHTML="";
  sections.forEach(s=>{
    const group=document.createElement("div");group.className="preference-group";
    group.appendChild(addPreference(s,s));
    topics[s].forEach(x=>group.appendChild(addPreference(s+"::"+x,x,true,s)));
    preferenceList.appendChild(group);
  });
}
sections.forEach(s=>{const b=document.createElement("button");b.className="section";b.dataset.section=s;b.textContent=s;sectionList.appendChild(b)});

function renderMarkdown(md){briefing.innerHTML=marked.parse(md,{mangle:false,headerIds:false});status.textContent="";applyPreferences()}

function applyPreferences(){
  const hs=[...briefing.querySelectorAll("h1")];
  hs.forEach(h=>{
    const cat=sections.find(s=>s.toUpperCase()===h.textContent.trim().toUpperCase());
    if(!cat)return;
    const visible=preferences[cat]!==false;h.style.display=visible?"":"none";
    let n=h.nextElementSibling;while(n&&n.tagName!=="H1"){n.style.display=visible?"":"none";n=n.nextElementSibling}
  });
  [...briefing.querySelectorAll("h2")].forEach(h=>{
    const sub=h.textContent.trim();
    let cat=null,n=h.previousElementSibling;
    while(n){if(n.tagName==="H1"){cat=sections.find(s=>s.toUpperCase()===n.textContent.trim().toUpperCase());if(cat)break}n=n.previousElementSibling}
    if(!cat||!topics[cat].includes(sub))return;
    const visible=preferences[cat]!==false&&preferences[cat+"::"+sub]!==false;
    h.style.display=visible?"":"none";n=h.nextElementSibling;
    while(n&&n.tagName!=="H2"&&n.tagName!=="H1"){n.style.display=visible?"":"none";n=n.nextElementSibling}
  });
}

async function loadToday(){status.textContent="Loading briefing…";try{const r=await fetch("briefing.md?"+Date.now());if(!r.ok)throw Error();renderMarkdown(await r.text())}catch(e){status.textContent="Could not load today's briefing."}}

function showSection(section){
  document.querySelectorAll(".section").forEach(b=>b.classList.toggle("active",b.dataset.section===section));
  applyPreferences();
  if(section==="all")return;

  if(section==="TOP STORIES"){
    [...briefing.querySelectorAll("h1,h2,h3,p,ul,ol")].forEach(x=>x.style.display="none");
    const top=[...briefing.querySelectorAll("h2")].find(x=>x.textContent.trim().toUpperCase()==="TOP STORIES");
    if(!top)return;
    top.style.display="";
    let n=top.nextElementSibling;
    while(n&&n.tagName!=="H1"){
      n.style.display="";
      n=n.nextElementSibling;
    }
    return;
  }

  const h=[...briefing.querySelectorAll("h1")];
  h.forEach(x=>{
    const match=x.textContent.trim().toUpperCase()===section;
    const visible=match&&preferences[section]!==false;
    x.style.display=visible?"":"none";
    let n=x.nextElementSibling;
    while(n&&n.tagName!=="H1"){n.style.display=visible?"":"none";n=n.nextElementSibling}
  });
}

async function loadArchive(){try{const r=await fetch("archive.json?"+Date.now()),items=await r.json();$("archiveList").innerHTML=items.map(x=>'<div class="archive-card" data-file="'+x.file+'"><strong>'+x.date+'</strong><span>Open briefing</span></div>').join("");document.querySelectorAll(".archive-card").forEach(card=>card.onclick=async()=>{archive.classList.add("hidden");briefing.classList.remove("hidden");$("sidebar").classList.remove("hidden");status.textContent="Loading…";const r=await fetch("data/"+card.dataset.file);renderMarkdown(await r.text());window.scrollTo({top:0,behavior:"smooth"})})}catch(e){$("archiveList").textContent="No archive available yet."}}

document.querySelectorAll(".nav-item").forEach(b=>b.onclick=()=>{document.querySelectorAll(".nav-item").forEach(x=>x.classList.remove("active"));b.classList.add("active");const today=b.dataset.view==="today";briefing.classList.toggle("hidden",!today);$("sidebar").classList.toggle("hidden",!today);archive.classList.toggle("hidden",today);if(today)loadToday();else loadArchive()});
document.addEventListener("click",e=>{if(e.target.matches(".section"))showSection(e.target.dataset.section)});
$("selectAll").onclick=()=>{Object.keys(preferences).forEach(k=>preferences[k]=true);buildPreferences();save()};
$("selectNone").onclick=()=>{Object.keys(preferences).forEach(k=>preferences[k]=false);buildPreferences();save()};
$("themeToggle").onclick=()=>{const dark=document.documentElement.dataset.theme==="dark";document.documentElement.dataset.theme=dark?"":"dark";localStorage.setItem("terrabrief-theme",dark?"light":"dark")};
if(localStorage.getItem("terrabrief-theme")==="dark")document.documentElement.dataset.theme="dark";
buildPreferences();loadToday();