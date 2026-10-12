import subprocess,sys
for v in ["v1","v2"]:
    print("\n"+"="*50)
    subprocess.run([sys.executable,"evals/run_eval.py","--prompt-version",v],check=True)
