import {createContext,useContext,useId,type InputHTMLAttributes,type ReactNode,type SelectHTMLAttributes,type TextareaHTMLAttributes} from 'react';
const FieldContext=createContext<{id?:string;'aria-describedby'?:string;'aria-invalid'?:boolean}>({});
export function Field({label,hint,error,children}:{label:ReactNode;hint?:string;error?:string;children:ReactNode}){const id=useId();const description=error||hint;return <div className="field"><label htmlFor={id}>{label}</label><FieldContext.Provider value={{id,'aria-describedby':description?id+'-help':undefined,'aria-invalid':!!error||undefined}}>{children}</FieldContext.Provider>{description&&<small id={id+'-help'} className={error?'error':'muted'} role={error?'alert':undefined}>{description}</small>}</div>}
export function TextInput(props:InputHTMLAttributes<HTMLInputElement>){return <input {...useContext(FieldContext)} {...props}/>}
export function Select(props:SelectHTMLAttributes<HTMLSelectElement>){return <select {...useContext(FieldContext)} {...props}/>}
export function Textarea(props:TextareaHTMLAttributes<HTMLTextAreaElement>){return <textarea {...useContext(FieldContext)} {...props}/>}
export function Checkbox({label,...props}:InputHTMLAttributes<HTMLInputElement>&{label:ReactNode}){return <label className="checkbox"><input type="checkbox" {...props}/><span>{label}</span></label>}
