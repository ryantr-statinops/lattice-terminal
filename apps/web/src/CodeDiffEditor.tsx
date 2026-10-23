import {useEffect,useRef} from 'react';
import * as monaco from 'monaco-editor/editor/editor.api';
import 'monaco-editor/languages/definitions/python/register';
import {useAppearance} from './theme/store';
import {fontFamilies} from './theme/tokens';

type Props = {
  path: string;
  original: string;
  modified: string;
  readOnly?: boolean;
  onModifiedChange?: (value: string) => void;
};

export default function CodeDiffEditor({path, original, modified, readOnly = false, onModifiedChange}: Props) {
  const appearance = useAppearance();
  const container = useRef<HTMLDivElement>(null);
  const diffEditor = useRef<monaco.editor.IStandaloneDiffEditor | null>(null);
  const originalModel = useRef<monaco.editor.ITextModel | null>(null);
  const modifiedModel = useRef<monaco.editor.ITextModel | null>(null);
  const listener = useRef(onModifiedChange);
  listener.current = onModifiedChange;

  useEffect(() => {
    if (!container.current) return;
    const editor = monaco.editor.createDiffEditor(container.current, {
      theme: 'kestrel',
      automaticLayout: true,
      readOnly,
      renderSideBySide: true,
      originalEditable: false,
      fontSize: appearance.editorSize,
      fontFamily: fontFamilies[appearance.font],
      padding: {top: 8},
      minimap: {enabled: false},
      scrollBeyondLastLine: false,
    });
    diffEditor.current = editor;

    return () => {
      editor.dispose();
      originalModel.current?.dispose();
      modifiedModel.current?.dispose();
      originalModel.current = null;
      modifiedModel.current = null;
      diffEditor.current = null;
    };
  }, [appearance.editorSize, appearance.font, readOnly]);

  useEffect(() => {
    const editor = diffEditor.current;
    if (!editor || !path) return;

    const lang = path.endsWith('.py') ? 'python' : path.endsWith('.json') ? 'json' : 'plaintext';
    const origUri = monaco.Uri.parse(`kestrel://diff-original/${encodeURI(path)}`);
    const modUri = monaco.Uri.parse(`kestrel://diff-modified/${encodeURI(path)}`);

    originalModel.current?.dispose();
    modifiedModel.current?.dispose();

    const orig = monaco.editor.createModel(original, lang, origUri);
    const mod = monaco.editor.createModel(modified, lang, modUri);
    originalModel.current = orig;
    modifiedModel.current = mod;

    editor.setModel({original: orig, modified: mod});

    const sub = mod.onDidChangeContent(() => {
      if (listener.current) {
        listener.current(mod.getValue());
      }
    });

    return () => sub.dispose();
  }, [path, original, modified]);

  return <div className="code-editor" aria-label="Code diff comparison" ref={container} />;
}
