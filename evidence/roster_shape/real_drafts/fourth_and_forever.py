# position sequences in PICK ORDER, as supplied by the owner. Q/R/W/T.
SEQ = {
 "TDjer6":        "QRRWWTRWTQWQTRWRRWWWRRWQQQ",
 "vizz01":        "QRRWWTRWWQWWTWWQTQRWRWRQQQ",
 "archerpayne":   "QRRWWTRWWQQTQRRWWTTQWWTRWQ",
 "adamstachecki": "QRRWWTTWRQQWWQRRWWRWRWTQWW",
 "alamosplash":   "QRRRWTRWWQQRTWWRRWTWWTTQRRWT",
 "RTG67":         "QRRWWTWWWQRQWRWTRWWQRQWWWT",
 "noonelikesme":  "QRRWWTTWTQRWQRWQTWRQRQQQQ",
 "easyymoneyyyy": "QRRWWTWRWQTRRWRWTWRRTTQRWW",
 "maxinumum":     "QRRWWTRWWQWRTWWWTRTQRWRWQT",
 "solomongrundy": "QRRWWTWWRQQWRWRQTWTWWQRWWW",
 "patrick32466":  "QRRWWTWRWQQTRTRWTWWQWWWRQ",
}
POS={"Q":"QB","R":"RB","W":"WR","T":"TE"}
FULL={  # the tallies already reported, incl. SPChocobo (from the board, no pick order)
 "SPChocobo":(3,9,8,4),"alamosplash":(4,9,9,6),"noonelikesme":(9,6,6,4),
 "easyymoneyyyy":(3,9,9,5),"TDjer6":(6,8,9,3),"maxinumum":(4,7,10,5),
 "archerpayne":(6,6,9,5),"adamstachecki":(5,7,11,3),"vizz01":(7,6,10,3),
 "patrick32466":(5,6,10,4),"RTG67":(5,6,12,3),"solomongrundy":(5,6,12,3)}
def cnt(s):
    return tuple(s.count(k) for k in "QRWT")
bad=[]
for m,s in SEQ.items():
    if cnt(s)!=FULL[m]: bad.append((m,cnt(s),FULL[m]))
if bad:
    print("SEQUENCE DOES NOT REPRODUCE THE TALLY -- fix before using:")
    for b in bad: print("  ",b)
    raise SystemExit(1)
print("all 11 sequences reproduce their tallies exactly.\n")
import statistics as st
for trim in (0,3,4,6):
    rats=[]; agg=[0,0,0,0]
    for m,s in SEQ.items():
        t=s[:len(s)-trim] if trim else s
        q,r,w,e=cnt(t)
        for i,v in enumerate((q,r,w,e)): agg[i]+=v
        rats.append((w/r if r else float('inf'),m))
    v=sorted(x[0] for x in rats)
    N=sum(agg)
    print(f"trim last {trim}:  n={N} picks over 11 seats   "
          f"QB {agg[0]/N:.1%} RB {agg[1]/N:.1%} WR {agg[2]/N:.1%} TE {agg[3]/N:.1%}"
          f"   league WR:RB {agg[2]/agg[1]:.2f}")
    print(f"            seat WR:RB  min {min(v):.2f}  median {st.median(v):.2f}  max {max(v):.2f}"
          f"   >1.75: {sum(1 for x in v if x>1.75)}/11")
