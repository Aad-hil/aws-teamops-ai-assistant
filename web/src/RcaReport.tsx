import React, {useMemo, useState} from "react";
import {BookOpen, ChevronDown, ChevronUp, ClipboardCheck, Cloud, Database, FileWarning, ShieldAlert} from "lucide-react";
import MarkdownMessage from "./MarkdownMessage";

type SectionKey = "evidence" | "cause" | "knowledge" | "recovery" | "verification";
type Section = {id:SectionKey; title:string; body:string};
const SECTION_LABELS:Record<SectionKey,string> = {
  evidence:"Observed evidence", cause:"Root cause", knowledge:"Knowledge guidance",
  recovery:"Recovery actions", verification:"Verification status"
};

function headingKey(name:string):SectionKey|null {
  const label = name.toLowerCase().replace(/[*_:`]/g, "").trim();
  if (/^(observed evidence|evidence|investigation findings|observations|live evidence|diagnostic evidence)/.test(label)) return "evidence";
  if (/^(confirmed root cause|root cause|rca|cause analysis)/.test(label)) return "cause";
  if (/^(knowledge base|knowledge guidance|sop|runbook|reference guidance)/.test(label)) return "knowledge";
  if (/^(recovery|remediation|recommended action|next action|resolution|action plan)/.test(label)) return "recovery";
  if (/^(verification|validation|current status|next steps to verify)/.test(label)) return "verification";
  return null;
}

export function parseRca(content:string):Section[] {
  const lines = content.split(/\r?\n/);
  const found:Section[] = [];
  let active:SectionKey|null = null, buffer:string[] = [];
  const flush = () => {
    if(active && buffer.join("").trim()) found.push({id:active,title:SECTION_LABELS[active],body:buffer.join("\n").trim()});
    buffer=[];
  };
  for(const line of lines){
    const match = line.match(/^\s{0,3}#{1,4}\s+(.+?)\s*#*\s*$/)
      || line.match(/^\s{0,3}\*\*(.+?)\*\*\s*:?\s*$/);
    const category = match ? headingKey(match[1].replace(/^\d+\.\s*/, "")) : null;
    if(category){flush();active=category;continue;}
    if(active)buffer.push(line);
  }
  flush();
  return found;
}

function EvidenceCard({body}:{body:string}){
  const glue = /(?:\bglue\b|\bjob run\b|\bjobruns?\b|\bjr_[a-f0-9]+)/i.test(body);
  const cloudwatch = /cloudwatch/i.test(body);
  return <div className="rca-evidence">
    <div className="rca-evidence-tags">
      {glue&&<span><Database size={14}/> Glue mentioned</span>}
      {cloudwatch&&<span><Cloud size={14}/> CloudWatch mentioned</span>}
      {!glue&&!cloudwatch&&<span><FileWarning size={14}/> Source unspecified</span>}
    </div>
    <p className="rca-disclaimer">Source labels below reflect the assistant's text, not independently validated tool traces. Cross-check run IDs and log lines with AWS.</p>
    <MarkdownMessage content={body}/>
  </div>;
}

function RecoveryCard({body}:{body:string}){
  const [checked,setChecked] = useState<number[]>([]);
  const steps = body.split(/\r?\n/).filter(line=>/^\s*(?:[-*]\s+|\d+[.)]\s+)/.test(line));
  return <div>
    <p className="rca-disclaimer"><ShieldAlert size={14}/> Proposed checklist only. Checkmarks are temporary local notes—not approvals or evidence that AWS actions ran.</p>
    {steps.length>0 && steps.length<=15 ? <div className="rca-checklist">
      {steps.map((step,index)=><label key={index}>
        <input type="checkbox" checked={checked.includes(index)} onChange={event=>setChecked(previous=>event.target.checked?[...previous,index]:previous.filter(i=>i!==index))}/>
        <span><MarkdownMessage content={step.replace(/^\s*(?:[-*]\s+|\d+[.)]\s+)/, "")}/></span>
      </label>)}
    </div>:<MarkdownMessage content={body}/>}
  </div>;
}

export default function RcaReport({content}:{content:string}){
  const sections=useMemo(()=>parseRca(content),[content]);
  const [expanded,setExpanded] = useState<SectionKey[]>(["evidence","cause","recovery"]);
  const [showRaw,setShowRaw] = useState(false);
  // Only structured responses get a report view; preserve ordinary conversation in the original renderer.
  if(sections.length<2 || !sections.some(x=>x.id==="cause"||x.id==="evidence")) return <MarkdownMessage content={content}/>;
  const toggle=(id:SectionKey)=>setExpanded(previous=>previous.includes(id)?previous.filter(x=>x!==id):[...previous,id]);
  const unique=sections.filter((section,index)=>sections.findIndex(x=>x.id===section.id)===index);
  return <div className="rca-report">
    <div className="rca-report-heading">
      <div><div className="rca-eyebrow">INVESTIGATION REPORT</div><h3>Root cause analysis</h3><p>Assistant-generated summary · verify against live tool evidence</p></div>
      <span className="rca-report-tag">Review required</span>
    </div>
    <div className="rca-report-sections">
      {unique.map(section=><section className="rca-section" key={section.id}>
        <button className="rca-section-button" type="button" aria-expanded={expanded.includes(section.id)} onClick={()=>toggle(section.id)}>
          <span className="rca-section-title">
            {section.id==="knowledge"?<BookOpen size={17}/>:section.id==="recovery"?<ClipboardCheck size={17}/>:section.id==="evidence"?<Database size={17}/>:<ShieldAlert size={17}/>}
            {section.title}
          </span>
          {expanded.includes(section.id)?<ChevronUp size={16}/>:<ChevronDown size={16}/>}
        </button>
        {expanded.includes(section.id)&&<div className="rca-section-body">
          {section.id==="evidence"?<EvidenceCard body={section.body}/>:section.id==="recovery"?<RecoveryCard body={section.body}/>:<MarkdownMessage content={section.body}/>}
        </div>}
      </section>)}
    </div>
    <button className="rca-raw-toggle" type="button" onClick={()=>setShowRaw(value=>!value)} aria-expanded={showRaw}>
      {showRaw?"Hide original response":"View complete original response"} {showRaw?<ChevronUp size={14}/>:<ChevronDown size={14}/>}
    </button>
    {showRaw&&<div className="rca-original"><MarkdownMessage content={content}/></div>}
  </div>;
}
