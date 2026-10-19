import {useEffect,useRef} from 'react';
import * as monaco from 'monaco-editor/editor/editor.api';
import 'monaco-editor/languages/definitions/python/register';
import EditorWorker from 'monaco-editor/editor/editor.worker?worker';

self.MonacoEnvironment={getWorker:()=>new EditorWorker()};
export default function CodeEditor({path,value,onChange}:{path:string;value:string;onChange:(value:string)=>void}){
 const container=useRef<HTMLDivElement>(null);const instance=useRef<monaco.editor.IStandaloneCodeEditor|null>(null);const listener=useRef(onChange);listener.current=onChange;const changing=useRef(false);const models=useRef(new Set<monaco.editor.ITextModel>());
 useEffect(()=>{if(!container.current)return;const editor=monaco.editor.create(container.current,{theme:'vs-dark',automaticLayout:true,minimap:{enabled:false},fontFamily:'JetBrains Mono, monospace',fontSize:13,scrollBeyondLastLine:false,padding:{top:16},tabSize:4});instance.current=editor;const subscription=editor.onDidChangeModelContent(()=>{if(!changing.current)listener.current(editor.getValue())});const owned=models.current;return()=>{subscription.dispose();editor.dispose();for(const model of owned)model.dispose();owned.clear();instance.current=null}},[]);
 useEffect(()=>{const editor=instance.current;if(!editor||!path)return;const uri=monaco.Uri.parse('kestrel://workspace/'+encodeURI(path));let model=monaco.editor.getModel(uri);if(!model){model=monaco.editor.createModel(value,path.endsWith('.py')?'python':path.endsWith('.json')?'json':'plaintext',uri);models.current.add(model)}changing.current=true;editor.setModel(model);if(model.getValue()!==value)model.setValue(value);changing.current=false},[path,value]);
 return <div className="code-editor" aria-label="Python editor" ref={container}/>;
}
