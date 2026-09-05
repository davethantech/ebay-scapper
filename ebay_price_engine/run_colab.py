import getpass, os, subprocess, sys
from pathlib import Path

def main():
    print("="*72); print("eBay AU + US DESCRIPTION-FIRST PRICING ENGINE"); print("="*72)
    root=Path(__file__).resolve().parent; os.chdir(root)
    subprocess.run([sys.executable,"-m","pip","install","-q","-r","requirements.txt"],check=True)
    client_id=input("eBay Production App ID: ").strip(); client_secret=getpass.getpass("eBay Production Client Secret: ").strip()
    if not client_id or not client_secret:raise SystemExit("Both eBay credentials are required.")
    os.environ["EBAY_CLIENT_ID"]=client_id; os.environ["EBAY_CLIENT_SECRET"]=client_secret
    try:from google.colab import files
    except ImportError:raise SystemExit("This launcher is for Google Colab.")
    uploaded=files.upload()
    if not uploaded:raise SystemExit("No file uploaded.")
    name=next(iter(uploaded)); input_path=Path(name).resolve(); output_path=root/"results.xlsx"; checkpoint=root/"checkpoint.json"
    subprocess.run([sys.executable,"-m","app.cli",str(input_path),"--output",str(output_path),"--checkpoint",str(checkpoint)],check=True,env=os.environ.copy())
    files.download(str(output_path)); print(f"Completed: {output_path}")

if __name__=="__main__":main()
