import {useEffect,useRef,useState} from 'react';
import type Plotly from 'plotly.js-basic-dist-min';
import {useAppearance} from './theme/store';
import {fontFamilies} from './theme/tokens';
import {ErrorState} from './ui/feedback';
export function Plot({data,title=''}:{data:Record<string,unknown>[];title?:string}){
 const ref=useRef<HTMLDivElement>(null),library=useRef<typeof Plotly|null>(null);const [error,setError]=useState<unknown>(null);const appearance=useAppearance();
 useEffect(()=>{const element=ref.current!;const resize=new ResizeObserver(()=>{if(library.current)library.current.Plots.resize(element)});resize.observe(element);return()=>{resize.disconnect();library.current?.purge(element)}},[]);
 useEffect(()=>{let cancelled=false;void import('plotly.js-basic-dist-min').then(async({default:plotly})=>{if(cancelled||!ref.current)return;library.current=plotly;if(document.fonts)await document.fonts.load(`${appearance.fontSize}px ${fontFamilies[appearance.font]}`);if(cancelled)return;const c=appearance.colors;await plotly.react(ref.current,data.map((trace,index)=>({uid:'series-'+index,...trace})),{uirevision:title||'plot',title:{text:title},height:330,paper_bgcolor:c.panel,plot_bgcolor:c.panel,font:{family:fontFamilies[appearance.font],size:appearance.fontSize,color:c.secondary},xaxis:{gridcolor:c.border,zerolinecolor:c.borderStrong},yaxis:{gridcolor:c.border,zerolinecolor:c.borderStrong},hoverlabel:{bgcolor:c.raised,bordercolor:c.border,font:{family:fontFamilies[appearance.font],color:c.text}},margin:{l:60,r:25,b:45,t:45},colorway:[c.series1,c.series2,c.series3,c.series4]},{responsive:true,displaylogo:false});if(!cancelled)setError(null)}).catch(error=>{if(!cancelled)setError(error)});return()=>{cancelled=true}},[data,title,appearance]);
 return <><ErrorState error={error}/><div role="img" aria-label={title||'Biểu đồ phân tích'} ref={ref}/></>;
}
