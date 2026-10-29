"""Entry point: generate data then validate it."""
import argparse, json
from .generator import generate
from .config import DEFAULT_SCALE, STARTER_SCALE, SEED
from .validation import validate

def main():
    p=argparse.ArgumentParser(); p.add_argument('--starter',action='store_true'); p.add_argument('--seed',type=int,default=SEED); p.add_argument('--assets',type=int); p.add_argument('--shipments',type=int); p.add_argument('--custody-events',type=int); args=p.parse_args()
    scale=(STARTER_SCALE if args.starter else DEFAULT_SCALE).copy()
    for key,val in [('assets',args.assets),('shipments',args.shipments),('custody_events',args.custody_events)]:
        if val is not None: scale[key]=val
    generate(scale,args.seed); result=validate(); print(json.dumps(result,indent=2))
if __name__=='__main__': main()
