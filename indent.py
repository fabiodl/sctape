import sys


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage {sys.argv[0]} file")
    else:
        with open(sys.argv[1]) as f:
            data=f.read()
        with open(sys.argv[2],"w") as f:            
            cnt=0
            for chunk in data.split():
                if chunk=="H":
                    cnt=15
                ret=" " if cnt % 16 != 15 else "\n"
                f.write(chunk+ret)
                cnt+=1
        
            
