const sections=["UK","WORLD","TECHNOLOGY","AVIATION","FORMULA 1","GAMING","SCIENCE","BUSINESS","ENTERTAINMENT"];
const $=id=>document.getElementById(id);
const sectionList=$("sectionList");
const briefing=$("briefing"), archive=$("archive"), status=$("status");

sections.forEach(s=>{
  const b=document.createElement("button"); b.className="section"; b.dataset.section=s; b.textContent=s;
  sectionList.appendChild(b);
});

function renderMarkdown(md){
  briefing.innerHTML=marked.parse(md,{mangle:false,headerIds:false});
  status.textContent="";
  document.querySelectorAll(".briefing h2").forEach(h=>{
    const name=h.textContent.trim().toUpperCase();
    if(sections.includes(name)) h.dataset.section=name;
  });
}

async function loadToday(){
  status.textContent="Loading briefing…";
  try{
    const r=await fetch("briefing.md?"+Date.now());
    if(!r.ok) throw new Error("Briefing unavailable");
    renderMarkdown(await r.text());
  }catch(e){status.textContent="Could not load today's briefing."}
}

function showSection(section){
  document.querySelectorAll(".section").forEach(b=>b.classList.toggle("active",b.dataset.section===section));
  const headings=[...document.querySelectorAll(".briefing h2")];
  if(section==="all"){headings.forEach(h=>h.style.display=""); document.querySelectorAll(".briefing h3").forEach(h=>h.style.display=""); return}
  let visible=false;
  headings.forEach(h=>{
    const match=h.dataset.section===section;
    h.style.display=match?"":"none";
    let n=h.nextElementSibling;
    while(n && n.tagName!=="H2"){n.style.display=match?"":"none"; n=n.nextElementSibling}
    if(match) visible=true;
  });
  if(!visible) status.textContent="No stories found in this section.";
}

async function loadArchive(){
  try{
    const r=await fetch("archive.json?"+Date.now());
    const items=await r.json();
    $("archiveList").innerHTML=items.map(x=>`<div class="archive-card" data-file="${x.file}"><strong>${x.date}</strong><span>Open briefing</span></div>`).join("");
    document.querySelectorAll(".archive-card").forEach(card=>card.onclick=async()=>{
      archive.classList.add("hidden"); briefing.classList.remove("hidden"); $("sidebar").classList.remove("hidden");
      status.textContent="Loading…";
      const r=await fetch("data/"+card.dataset.file); renderMarkdown(await r.text());
      window.scrollTo({top:0,behavior:"smooth"});
    });
  }catch(e){$("archiveList").textContent="No archive available yet."}
}

document.querySelectorAll(".nav-item").forEach(b=>b.onclick=()=>{
  document.querySelectorAll(".nav-item").forEach(x=>x.classList.remove("active")); b.classList.add("active");
  const today=b.dataset.view==="today";
  briefing.classList.toggle("hidden",!today); $("sidebar").classList.toggle("hidden",!today); archive.classList.toggle("hidden",today);
  if(today) loadToday(); else loadArchive();
});

document.addEventListener("click",e=>{if(e.target.matches(".section")) showSection(e.target.dataset.section)});

$("themeToggle").onclick=()=>{
  const dark=document.documentElement.dataset.theme==="dark";
  document.documentElement.dataset.theme=dark?"":"dark";
  localStorage.setItem("terrabrief-theme",dark?"light":"dark");
};
if(localStorage.getItem("terrabrief-theme")==="dark") document.documentElement.dataset.theme="dark";
loadToday();
