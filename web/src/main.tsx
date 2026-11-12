import React,{useState,useRef,useEffect} from "react";import{createRoot}from"react-dom/client";import{Bot,Send,Plus,ShieldCheck,Database,BookOpen,Activity,Sparkles}from"lucide-react";import "./style.css";
import DashboardPanel from "./DashboardPanel";
import MarkdownMessage from "./MarkdownMessage";
import RelatedSources from "./RelatedSources";
import ChatHistory,{type Conversation} from "./ChatHistory";
import {CognitoUserPool} from "amazon-cognito-identity-js";
import AuthPanel from "./AuthPanel";
const API_BASE="https://ws9dklzhac.execute-api.ap-southeast-2.amazonaws.com";
const API_URL=API_BASE+"/chat";
const pool=new CognitoUserPool({UserPoolId:"ap-southeast-2_m2kScaTa8",ClientId:"1r0se3b4uieonrfnqj30lt3kd7"});
function currentToken():Promise<string>{
  return new Promise((resolve,reject)=>{
    const user=pool.getCurrentUser();
    if(!user)return reject(new Error("Please sign in."));
    user.getSession((err:Error|null,session:any)=>{
      if(err||!session?.isValid())return reject(err||new Error("Session expired. Sign in again."));
      resolve(session.getIdToken().getJwtToken());
    });
  });
}

type Msg={role:"user"|"assistant";content:string};const welcome:Msg={role:"assistant",content:"Welcome to TeamOps AI. I can investigate live Glue executions, correlate CloudWatch errors, and retrieve ETL runbooks. What would you like to investigate?"};
function App(){const[activeTab,setActiveTab]=useState<"chat"|"diagnostics"|"knowledge">("chat");const[messages,setMessages]=useState<Msg[]>([welcome]);const[input,setInput]=useState("");const[busy,setBusy]=useState(false);const[error,setError]=useState("");const[session,setSession]=useState<string|null>(null);
const sessionRef=useRef<string|null>(null);
const[conversations,setConversations]=useState<Conversation[]>([]);
const[historyLoading,setHistoryLoading]=useState(false);
const[historyError,setHistoryError]=useState("");
const[opening,setOpening]=useState(false);
const busyRef=useRef(false);
async function historyRequest(path:string,method="GET"){
  const token=await currentToken();
  const r=await fetch(API_BASE+path,{method,headers:{"Authorization":"Bearer "+token}});
  const data=await r.json();
  if(!r.ok)throw new Error(data.error||"History request failed");
  return data;
}
async function loadHistory(){
  setHistoryLoading(true);
  try{
    const data=await historyRequest("/conversations");
    setConversations(data.conversations||[]);
    setHistoryError("");
  }catch(e){setHistoryError(e instanceof Error?e.message:"Could not load history");}
  finally{setHistoryLoading(false);}
}
async function openConversation(id:string){
  if(busyRef.current||opening)return;
  setOpening(true);setError("");
  try{
    const data=await historyRequest("/conversations/"+encodeURIComponent(id));
    sessionRef.current=data.sessionId;
    setSession(data.sessionId);
    setMessages(data.messages?.length?data.messages:[welcome]);
    setActiveTab("chat");
  }catch(e){setHistoryError(e instanceof Error?e.message:"Could not load conversation");}
  finally{setOpening(false);}
}
async function deleteConversation(id:string){
  if(busyRef.current||opening)return;
  if(!window.confirm("Delete this conversation from your chat history? This cannot be undone."))return;
  try{
    await historyRequest("/conversations/"+encodeURIComponent(id),"DELETE");
    setConversations(previous=>previous.filter(item=>item.sessionId!==id));
    if(sessionRef.current===id){
      sessionRef.current=null;setSession(null);setMessages([welcome]);
    }
    setHistoryError("");
  }catch(e){setHistoryError(e instanceof Error?e.message:"Could not delete conversation");}
}

const[loggedIn,setLoggedIn]=useState(false);
useEffect(()=>{
  const current=pool.getCurrentUser();
  if(!current)return;
  current.getSession((err:Error|null,session:any)=>{
    if(err||!session?.isValid())return;
    const groups=session.getIdToken().decodePayload()["cognito:groups"];
    const approved=Array.isArray(groups) && groups.includes("teamops-users");
    if(approved)setLoggedIn(true);
    else current.signOut();
  });
},[]);
useEffect(()=>{if(loggedIn)void loadHistory();},[loggedIn]);
function logout(){
  pool.getCurrentUser()?.signOut();
  sessionRef.current=null;setSession(null);setMessages([welcome]);
  setLoggedIn(false);setError("");setConversations([]);setHistoryError("");
}
async function send(value=input){const text=value.trim();if(!text||busyRef.current||opening)return;busyRef.current=true;const next:Msg[]=[...messages,{role:"user",content:text}];setMessages(next);setInput("");setError("");setBusy(true);try{const token=await currentToken();const activeSession=sessionRef.current;
const r=await fetch(API_URL,{method:"POST",headers:{"Content-Type":"application/json","Authorization":"Bearer "+token},body:JSON.stringify({message:text,...(activeSession?{sessionId:activeSession}:{})})});const data=await r.json();if(!r.ok)throw new Error(data.error||data.detail||"Request failed");
if(data.sessionId){sessionRef.current=data.sessionId;setSession(data.sessionId);}
void loadHistory();
setMessages([...next,{role:"assistant",content:data.answer||"No response returned."}]);}catch(e){setError(e instanceof Error?e.message:"Connection failed");}finally{setBusy(false);busyRef.current=false;}}function fresh(){if(busyRef.current||opening)return;sessionRef.current=null;setSession(null);setMessages([welcome]);setError("");setActiveTab("chat");}if(!loggedIn)return <AuthPanel pool={pool} onSignedIn={()=>setLoggedIn(true)}/>;
return <div className="app"><aside><div className="brand"><span className="logo"><Bot size={22}/></span><div><b>TeamOps AI</b><small>Cloud operations · ETL intelligence</small></div></div><button className="new" onClick={fresh}><Plus size={17}/> New conversation</button><ChatHistory conversations={conversations} activeSession={session} loading={historyLoading} disabled={busy||opening} onOpen={openConversation} onDelete={deleteConversation}/>
{historyError&&<p className="history-error" role="alert">{historyError}</p>}
<div className="section workspace-title">WORKSPACE</div><button className={"nav "+(activeTab==="chat"?"active":"")} onClick={()=>setActiveTab("chat")}><Activity size={18}/> AI Assistant</button><button className={"nav "+(activeTab==="diagnostics"?"active":"")} onClick={()=>setActiveTab("diagnostics")}><Database size={18}/> Diagnostics</button><button className={"nav "+(activeTab==="knowledge"?"active":"")} onClick={()=>setActiveTab("knowledge")}><BookOpen size={18}/> Knowledge Base</button><div className="bottom"><ShieldCheck size={16}/> Authenticated <button onClick={logout} style={{marginLeft:8}}>Sign out</button></div></aside><main>{activeTab==="chat"?<><header><div className="header-copy"><span className="header-mark"><Sparkles size={23}/></span><div><div className="header-eyebrow">Enterprise AI · Cloud operations</div><h1>AI Operations Assistant</h1><p>From incident signals to evidence-grounded recovery</p></div></div><span className="pill"><i/> AgentCore connected via API</span></header><div className="chat"><div className="messages">{messages.map((m,i)=><div className={"message "+m.role} key={i}><div className="avatar">{m.role==="assistant"?"AI":"You"}</div><div className="bubble">{m.role==="assistant"?<><MarkdownMessage content={m.content}/>{i>0&&messages[i-1]?.role==="user"&&<RelatedSources key={`${session||"new"}-${i}`} query={messages[i-1].content} getToken={currentToken}/>}</>:m.content}</div></div>)}{busy&&<div className="message assistant"><div className="avatar">AI</div><div className="bubble">Investigating…</div></div>}</div></div><div className="composer">{messages.length===1&&<div className="suggestions">{["Investigate latest Glue failure","Explain a Redshift COPY error","Find an ETL recovery runbook"].map(s=><button onClick={()=>send(s)} key={s}>{s}</button>)}</div>}{error&&<p className="error">{error}</p>}<form onSubmit={e=>{e.preventDefault();send()}}><input aria-label="Message" placeholder="Ask about Glue runs, CloudWatch logs, or an ETL runbook…" value={input} onChange={e=>setInput(e.target.value)}/><button disabled={busy||!input.trim()} aria-label="Send"><Send size={18}/></button></form><small>Answers may contain synthetic data. Verify actions before applying to live systems.</small></div></> : <DashboardPanel tab={activeTab} getToken={currentToken} />}</main></div>}createRoot(document.getElementById("root")!).render(<React.StrictMode><App/></React.StrictMode>);