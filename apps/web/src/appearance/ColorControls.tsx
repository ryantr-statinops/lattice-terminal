import {useEffect,useId,useState} from 'react';
import {useAppearance,setColor} from '../theme/store';
import {colorGroups,colorLabels,contrast,presets,terminalColors,type ColorRole} from '../theme/tokens';
import {Button} from '../ui/buttons';
import {TextInput} from '../ui/fields';
import {InlineNotice} from '../ui/feedback';

function ColorField({role}:{role:ColorRole}){
  const p=useAppearance();
  const value=p.colors[role];
  const id=useId();
  const [draft,setDraft]=useState(value);
  useEffect(()=>setDraft(value),[value]);
  const valid=/^#[0-9a-f]{6}$/i.test(draft);
  const reset=p.preset==='custom'?terminalColors[role]:presets[p.preset].colors[role];

  return (
    <div className="color-row">
      <div style={{minWidth:0,flex:1}}>
        <label htmlFor={id} className="color-row-label">
          {colorLabels[role]}
        </label>
        {!valid&&<small id={id+'-error'} className="error" style={{display:'block',fontSize:10}}>HEX must contain # followed by 6 characters (0–9/A–F).</small>}
      </div>
      <div className="color-row-inputs">
        <input
          type="color"
          aria-label={colorLabels[role]+' — choose color'}
          value={value}
          onChange={e=>setColor(role,e.target.value)}
          style={{width:28,height:24,padding:1,cursor:'pointer'}}
        />
        <TextInput
          id={id}
          spellCheck={false}
          value={draft}
          maxLength={7}
          aria-invalid={!valid}
          aria-describedby={!valid?id+'-error':undefined}
          onChange={e=>{
            setDraft(e.target.value);
            if(/^#[0-9a-f]{6}$/i.test(e.target.value))setColor(role,e.target.value);
          }}
          style={{width:84,fontSize:12,fontFamily:'monospace'}}
        />
        <Button
          aria-label={'Reset '+colorLabels[role]}
          title={'Reset '+colorLabels[role]}
          onClick={()=>{
            setDraft(reset);
            setColor(role,reset);
          }}
          style={{padding:'2px 6px',fontSize:11}}
        >
          ↶
        </Button>
      </div>
    </div>
  );
}

export function ColorControls(){
  const {colors:c}=useAppearance();
  const pairs=[
    ...(['canvas','panel','raised','input'] as const).flatMap(bg=>
      (['text','secondary','muted'] as const).map(fg=>[colorLabels[fg]+' / '+colorLabels[bg],c[fg],c[bg]])
    ),
    ['Selected text / selection background',c.selectionText,c.selection],
    ...(['positive','negative','warning','info','accent'] as const).map(role=>[colorLabels[role]+' / panel',c[role],c.panel])
  ];
  const warnings=pairs.filter(([,fg,bg])=>contrast(fg,bg)<4.5);

  return (
    <>
      {warnings.length>0&&<InlineNotice tone="warning">Low contrast: {warnings.map(([name,fg,bg])=>`${name} (${contrast(fg,bg).toFixed(1)}:1)`).join('; ')}. You can keep this color.</InlineNotice>}
      {Object.entries(colorGroups).map(([name,roles])=>(
        <fieldset className="color-group" key={name} style={{padding:0,overflow:'hidden',marginBottom:12}}>
          <legend style={{padding:'0 8px',fontWeight:600}}>{name}</legend>
          <div className="settings-list" style={{margin:0,border:'none'}}>
            {roles.map(role=><ColorField key={role} role={role}/>)}
          </div>
        </fieldset>
      ))}
    </>
  );
}
