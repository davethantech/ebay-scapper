import argparse, logging, pandas as pd
from .config import Config
from .engine import analyse_dataframe
from .output import write_excel

def main():
    p=argparse.ArgumentParser(description="Description-first eBay AU/US pricing engine")
    p.add_argument("input"); p.add_argument("--output",default="results.xlsx"); p.add_argument("--checkpoint",default="checkpoint.json")
    p.add_argument("--log-level",default="INFO",choices=["DEBUG","INFO","WARNING","ERROR"])
    a=p.parse_args(); logging.basicConfig(level=getattr(logging,a.log_level),format="%(asctime)s | %(levelname)s | %(message)s")
    df=pd.read_csv(a.input) if a.input.lower().endswith(".csv") else pd.read_excel(a.input)
    result=analyse_dataframe(df,Config.from_env(),a.checkpoint); write_excel(result,a.output)
    result.to_csv(a.output.rsplit('.',1)[0]+".csv",index=False)
    print(f"Completed {len(result)} rows -> {a.output}")
if __name__=="__main__": main()
