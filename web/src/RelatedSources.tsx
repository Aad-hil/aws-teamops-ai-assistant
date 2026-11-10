import React, {useState} from "react";
import {BookOpen,ChevronDown,ChevronUp} from "lucide-react";

const API = "https://ws9dklzhac.execute-api.ap-southeast-2.amazonaws.com";
type Source = {text:string;source_uri?:string;score?:number};
type Props = {query:string;getToken:()=>Promise<string>};

function sourceTitle(uri?:string):string {
  if(!uri)return "Knowledge document";
  const last=uri.split("/").filter(Boolean).pop()||uri;
  try{return decodeURIComponent(last);}catch{return last;}
}

export default function RelatedSources({query,getToken}:Props){
  const[opened,setOpened]=useState(false);
  const[loaded,setLoaded]=useState(false);
  const[loading,setLoading]=useState(false);
  const[sources,setSources]=useState<Source[]>([]);
  const[error,setError]=useState("");
  async function toggle(){
    if(opened){setOpened(false);return;}
    setOpened(true);
    if(loaded||loading)return;
    setLoading(true);setError("");
    try{
      const token=await getToken();
      const response=await fetch(API+"/knowledge",{
        method:"POST",
        headers:{"Content-Type":"application/json","Authorization":"Bearer "+token},
        body:JSON.stringify({query:query.slice(0,1000)})
      });
      const data=await response.json();
      if(!response.ok)throw new Error(data.error||"Knowledge search failed");
      setSources(Array.isArray(data.results)?data.results.filter((v:unknown)=>!!v&&typeof v==="object").slice(0,5):[]);
      setLoaded(true);
    }catch(e){setError(e instanceof Error?e.message:"Could not retrieve related sources");}
    finally{setLoading(false);}
  }
  return <div className="related-sources">
    <button type="button" className="related-sources-toggle" onClick={()=>void toggle()} aria-expanded={opened}>
      <BookOpen size={14}/> Related knowledge sources {opened?<ChevronUp size={14}/>:<ChevronDown size={14}/>}
    </button>
    {opened&&<div className="related-sources-content">
      <p className="related-sources-disclaimer">These documents are retrieved separately from the knowledge base using your question. They are not verified citations for the AI answer.</p>
      {loading&&<p role="status">Searching knowledge base…</p>}
      {error&&<div role="alert"><p>{error}</p><button type="button" onClick={()=>{setOpened(false);setLoaded(false);}}>Close and retry</button></div>}
      {loaded&&sources.length===0&&<p>No related documents found.</p>}
      {sources.map((source,index)=><article key={index} className="related-source-card">
        <b>{sourceTitle(source.source_uri)}</b>
        {typeof source.score==="number"&&<span className="related-source-score">Retrieval score: {source.score.toFixed(3)}</span>}
        <p>{source.text||"No extract available."}</p>
        {source.source_uri&&<small title={source.source_uri}>Source: {source.source_uri}</small>}
      </article>)}
    </div>}
  </div>;
}
