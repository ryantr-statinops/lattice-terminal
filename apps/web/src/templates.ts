export function programTemplate(kind:string):string{
 if(kind==='backtest')return `KESTREL_KIND = "backtest"
from decimal import Decimal

def run(context):
    # Example for the labelled synthetic detailed tape only.
    def decide(view, event):
        if len(view.history) == 1:
            return [{"side": "buy", "limit_price": str(Decimal(event.ask) + 100), "quantity": "1"}]
        return []
    context.replay(decide)
`;
 if(kind==='strategy')return `KESTREL_KIND = "strategy"

def on_start(context):
    context.log("Strategy started; paper only")

def on_event(context, event):
    # Return LO intents; this contract is separate from Backtest.
    return []

def on_stop(context):
    context.log("Strategy stopped")
`;
 return `KESTREL_KIND = "research"

def run(context):
    context.log("Kestrel research")
    context.table("example", ["x", "y"], [[1, 2], [2, 4], [3, 6]])
    context.chart("example", [1, 2, 3], [2, 4, 6])
`;
}
