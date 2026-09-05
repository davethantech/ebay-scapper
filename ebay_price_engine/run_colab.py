import getpass, os, sys, subprocess
from pathlib import Path

def main():
    print("eBay AU + US DESCRIPTION-FIRST PRICING ENGINE")
    root=Path(__file__).resolve().parent; os.chdir(root)
    subprocess.run([sys.executable,"-m","pip","install","-q","-r","requirements.txt"],check=True)
    client_id=input("eBay Production App ID: ").strip()
    client_secret=getpass.getpass("eBay Production Client Secret: ").strip()
    if not client_id or not client_secret: raise SystemExit("Both eBay credentials are required.")
    os.environ["EBAY_CLIENT_ID"]=client_id; os.environ["EBAY_CLIENT_SECRET"]=client_secret
    try:
        from google.colab import files
    except ImportError:
        raise SystemExit("Run this launcher in Google Colab.")
    uploaded=files.upload()
    if not uploaded: raise SystemExit("No input file uploaded.")
    name=next(iter(uploaded)); input_path=Path(name).resolve()
    from app.cli import main as cli_main
    sys.argv=["app.cli",str(input_path),"--output",str(root/"results.xlsx"),"--checkpoint",str(root/"checkpoint.json")]
    cli_main()
    files.download(str(root/"results.xlsx"))
    print("Completed.")

if __name__=="__main__": main()
