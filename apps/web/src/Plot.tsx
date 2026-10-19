import {useEffect,useRef} from 'react';
export function Plot({data,title=''}:{data:Record<string,unknown>[];title?:string}){
 const ref=useRef<HTMLDivElement>(null);
 useEffect(()=>{let disposed=false;let cleanup:(()=>void)|undefined;void import('plotly.js-basic-dist-min').then(({default:plotly})=>{if(disposed||!ref.current)return;const el=ref.current;void plotly.react(el,data,{title:{text:title},height:330,paper_bgcolor:'#0e151e',plot_bgcolor:'#0e151e',font:{color:'#a6b8cb'},margin:{l:55,r:25,b:45,t:45},colorway:['#7dd8b5','#70a9e7','#d9b26d']},{responsive:true,displaylogo:false});cleanup=()=>plotly.purge(el)});return()=>{disposed=true;cleanup?.()}},[data,title]);
 return <div role="img" aria-label={title||'Biểu đồ phân tích'} ref={ref}/>;
}
