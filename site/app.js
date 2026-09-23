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

function defaults(){
  const p={};
  sections.forEach(s=>{
    p[s]=true;
    topics[s].forEach(x=>p[s+"::"+x]=true);
  });
  return p;
}
function getPrefs(){
  try{return {...defaults(),...JSON.parse(localStorage.getItem(storageKey)||"{}")}}
  catch(e){return defaults()}
}
let preferences=getPrefs();

function save(){
  localStorage.setItem(storageKey,JSON.stringify(preferences));
  applyPreferences();
}

function addPreference(key,label,sub=false,parent=null){
  const row=document.createElement("label");
  row.className="preference-row"+(sub?" subtopic":"");
  const box=document.createElement("input");
  box.type="checkbox";
  box.checked=preferences[key]!==false;
  box.dataset.preference=key;
  if(parent)box.dataset.parent=parent;
  box.onchange=()=>{
    preferences[key]=box.checked;
    if(!sub){
      topics[label].forEach(x=>preferences[label+"::"+x]=box.checked);
      buildPreferences();
    }
    save();
    currentView="all";
    resetSectionButtons();
  };
  row.append(box,document.createTextNode(label));
  return row;
}

function buildPreferences(){
  preferenceList.innerHTML="";
  sections.forEach(s=>{
    const group=document.createElement("div");
    group.className="preference-group";
    group.appendChild(addPreference(s,s));
    topics[s].forEach(x=>group.appendChild(addPreference(s+"::"+x,x,true,s));
    preferenceList.appendChild(group);
  });
}

sections.forEach(s=>{
  const b=document.createElement("button");
  b.className="section";
  b.dataset.section=s;
  b.textContent=s;
  sectionList.appendChild(b);
});

function renderMarkdown(md){
  briefing.innerHTML=marked.parse(md,{mangle:false,headerIds:false});
  status.textContent="";
  currentView="all";
  applyPreferences();
  resetSectionButtons();
}

function categoryForHeading(h){
  return sections.find(s=>s.toUpperCase()===h.textContent.trim().toUpperCase())||null;
}

function subcategoryForHeading(h,category){
  return category && topics[category].find(s=>s.toUpperCase()===h.textContent.trim().toUpperCase())||null;
}

function elementBelongsToCategory(el){
  let node=el.previousElementSibling;
  while(node){
    if(node.tagName==="H1")return categoryForHeading(node);
    node=node.previousElementSibling;
  }
  return null;
}

function elementBelongsToSubcategory(el){
  let node=el.previousElementSibling;
  while(node){
    if(node.tagName==="H2"){
      const category=elementBelongsToCategory(node);
      const sub=subcategoryForHeading(node,category);
      if(sub)return {category,sub};
    }
    if(node.tagName==="H1")break;
    node=node.previousElementSibling;
  }
  return null;
}

function applyPreferences(){
  const children=[...briefing.children];

  children.forEach(el=>{
    if(el.tagName==="H1"){
      const category=categoryForHeading(el);
      if(category){
        el.dataset.tbCategory=category;
        el.style.display=preferences[category]===false?"none":"";
      }
    }
  });

  children.forEach(el=>{
    if(el.tagName==="H2"){
      const category=elementBelongsToCategory(el);
      const sub=subcategoryForHeading(el,category);
      if(sub){
        el.dataset.tbCategory=category;
        el.dataset.tbSubcategory=sub;
        const visible=preferences[category]!==false&&preferences[category+"::"+sub]!==false;
        el.style.display=visible?"":"none";
        let n=el.nextElementSibling;
        while(n&&n.tagName!=="H2"&&n.tagName!=="H1"){
          n.style.display=visible?"":"none";
          n=n.nextElementSibling;
        }
      }
    }
  });

  // Re-hide category content after subcategory processing.
  children.forEach(el=>{
    const category=el.dataset.tbCategory||elementBelongsToCategory(el);
    if(category&&preferences[category]===false)el.style.display="none";
  });
}

let currentView="all";

function resetSectionButtons(){
  document.querySelectorAll(".section").forEach(b=>{
    b.classList.toggle("active",b.dataset.section===currentView);
  });
}

function showSection(section){
  currentView=section;
  resetSectionButtons();

  [...briefing.children].forEach(el=>el.style.display="none");

  if(section==="all"){
    // Clear display overrides left by another browse view before applying
    // the user's topic preferences again.
    [...briefing.children].forEach(el=>el.style.display="");
    applyPreferences();
    return;
  }

  if(section==="TOP STORIES"){
    const top=[...briefing.children].find(
      x=>x.tagName==="H2"&&x.textContent.trim().toUpperCase()==="TOP STORIES"
    );
    if(!top)return;

    top.style.display="";
    let n=top.nextElementSibling;
    while(n&&n.tagName!=="H1"){
      n.style.display="";
      n=n.nextElementSibling;
    }
    return;
  }

  const category=sections.find(s=>s.toUpperCase()===section.toUpperCase());
  if(!category)return;

  const heading=[...briefing.children].find(
    x=>x.tagName==="H1"&&categoryForHeading(x)===category
  );
  if(!heading)return;

  heading.style.display=preferences[category]===false?"none":"";
  let n=heading.nextElementSibling;
  while(n&&n.tagName!=="H1"){
    n.style.display=preferences[category]===false?"none":"";
    n=n.nextElementSibling;
  }
}

async function loadToday(){
  status.textContent="Loading briefing…";
  try{
    const r=await fetch("briefing.md?"+Date.now(),{cache:"no-store"});
    if(!r.ok)throw Error();
    renderMarkdown(await r.text());
  }catch(e){
    status.textContent="Could not load today's briefing.";
  }
}

async function loadArchive(){
  const list=$("archiveList");
  list.textContent="Loading previous briefings…";

  try{
    const r=await fetch("archive.json?"+Date.now(),{cache:"no-store"});
    if(!r.ok)throw Error("archive index unavailable");
    const items=await r.json();

    if(!Array.isArray(items)||items.length===0){
      list.textContent="No previous briefings available yet.";
      return;
    }

    list.innerHTML=items.map(x=>
      '<div class="archive-card" data-file="'+encodeURIComponent(x.file)+'">'+
      '<strong>'+x.date+'</strong><span>Open briefing</span></div>'
    ).join("");

    list.querySelectorAll(".archive-card").forEach(card=>{
      card.onclick=async()=>{
        const file=decodeURIComponent(card.dataset.file);
        status.textContent="Loading briefing…";

        try{
          const r=await fetch("data/"+encodeURIComponent(file)+"?"+Date.now(),{cache:"no-store"});
          if(!r.ok)throw Error("briefing unavailable");
          const md=await r.text();

          archive.classList.add("hidden");
          briefing.classList.remove("hidden");
          $("sidebar").classList.remove("hidden");
          renderMarkdown(md);
          window.scrollTo({top:0,behavior:"smooth"});
        }catch(e){
          status.textContent="Could not load this briefing.";
        }
      };
    });
  }catch(e){
    list.textContent="Could not load the previous briefings.";
  }
}

document.querySelectorAll(".nav-item").forEach(b=>{
  b.onclick=()=>{
    document.querySelectorAll(".nav-item").forEach(x=>x.classList.remove("active"));
    b.classList.add("active");
    const today=b.dataset.view==="today";
    briefing.classList.toggle("hidden",!today);
    $("sidebar").classList.toggle("hidden",!today);
    archive.classList.toggle("hidden",today);
    if(today)loadToday();
    else loadArchive();
  };
});

document.addEventListener("click",e=>{
  if(e.target.matches(".section"))showSection(e.target.dataset.section);
});

$("selectAll").onclick=()=>{
  Object.keys(preferences).forEach(k=>preferences[k]=true);
  buildPreferences();
  save();
  showSection("all");
};

$("selectNone").onclick=()=>{
  Object.keys(preferences).forEach(k=>preferences[k]=false);
  buildPreferences();
  save();
  showSection("all");
};

$("themeToggle").onclick=()=>{
  const dark=document.documentElement.dataset.theme==="dark";
  document.documentElement.dataset.theme=dark?"":"dark";
  localStorage.setItem("terrabrief-theme",dark?"light":"dark");
};

if(localStorage.getItem("terrabrief-theme")==="dark")
  document.documentElement.dataset.theme="dark";

buildPreferences();
loadToday();
