import ast

KINDS={'research','backtest','strategy'}
def inspect_source(source:str,expected:str,selected:bool=False):
    if expected not in KINDS:raise ValueError('unknown program kind')
    try: tree=ast.parse(source)
    except SyntaxError as error:raise ValueError(f'line {error.lineno}: {error.msg}') from error
    declarations=[]
    for node in tree.body:
        value=None;targets=[]
        if isinstance(node,ast.Assign):targets=node.targets;value=node.value
        elif isinstance(node,ast.AnnAssign):targets=[node.target];value=node.value
        if any(isinstance(v,ast.Name) and v.id=='KESTREL_KIND' for v in targets):
            if not isinstance(value,ast.Constant) or not isinstance(value.value,str):raise ValueError('KESTREL_KIND must be a literal string')
            declarations.append(value.value)
    if len(declarations)>1:raise ValueError('duplicate KESTREL_KIND declaration')
    if not declarations and not selected:raise ValueError('declare KESTREL_KIND or explicitly select file kind')
    kind=declarations[0] if declarations else expected
    if kind!=expected:raise ValueError(f'file kind {kind!r} cannot run in {expected!r} workspace')
    required='on_event' if kind=='strategy' else 'run'
    if not any(isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name==required for node in tree.body):raise ValueError(f'{kind} requires {required}(context'+(', event)' if kind=='strategy' else ')'))
    if any(isinstance(node,ast.AsyncFunctionDef) and node.name==required for node in tree.body):raise ValueError('async program entrypoints are not supported')
    return {'kind':kind,'entrypoint':required,'diagnostics':[]}
