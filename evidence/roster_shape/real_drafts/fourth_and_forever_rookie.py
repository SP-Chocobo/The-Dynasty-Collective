# 2026 Fourth and Forever ROOKIE draft, 4 rounds, snake, read off the completed board.
# Positions are the board's own labels. Traded picks assigned to the ACQUIRING manager
# (the board prints "-> <manager>" on a traded cell).
SEATS = ["patrick32466","solomongrundy","maxinumum","easyymoneyyyy","noonelikesme","RTG67",
         "alamosplash","SPChocobo","adamstachecki","archerpayne","vizz01","TDjer6"]
# (pick, player, pos, owner)
PICKS = [
 ("1.1","Jeremiah Love","RB","patrick32466"), ("1.2","Carnell Tate","WR","solomongrundy"),
 ("1.3","Fernando Mendoza","QB","maxinumum"), ("1.4","Jordyn Tyson","WR","easyymoneyyyy"),
 ("1.5","Makai Lemon","WR","noonelikesme"),   ("1.6","Jadarian Price","RB","RTG67"),
 ("1.7","KC Concepcion","WR","noonelikesme"), ("1.8","Omar Cooper","WR","noonelikesme"),
 ("1.9","Denzel Boston","WR","adamstachecki"),("1.10","Jonah Coleman","RB","archerpayne"),
 ("1.11","Eli Stowers","TE","vizz01"),        ("1.12","De'Zhaun Stribling","WR","TDjer6"),
 ("2.1","Antonio Williams","WR","TDjer6"),    ("2.2","Kenyon Sadiq","TE","vizz01"),
 ("2.3","Cyrus Allen","WR","archerpayne"),    ("2.4","Germie Bernard","WR","adamstachecki"),
 ("2.5","Carson Beck","QB","TDjer6"),         ("2.6","Ty Simpson","QB","alamosplash"),
 ("2.7","Malachi Fields","WR","RTG67"),       ("2.8","Drew Allar","QB","adamstachecki"),
 ("2.9","Zachariah Branch","WR","solomongrundy"),("2.10","Nicholas Singleton","RB","maxinumum"),
 ("2.11","Ted Hurst","WR","solomongrundy"),   ("2.12","Mike Washington","RB","patrick32466"),
 ("3.1","Justin Joly","TE","patrick32466"),   ("3.2","Emmett Johnson","RB","solomongrundy"),
 ("3.3","Adam Randall","RB","maxinumum"),     ("3.4","Ja'Kobi Lane","WR","easyymoneyyyy"),
 ("3.5","Elijah Sarratt","WR","noonelikesme"),("3.6","Chris Bell","WR","RTG67"),
 ("3.7","Kaytron Allen","RB","noonelikesme"), ("3.8","Kaelon Black","RB","SPChocobo"),
 ("3.9","Caleb Douglas","WR","adamstachecki"),("3.10","Cade Klubnik","QB","archerpayne"),
 ("3.11","Demond Claiborne","RB","vizz01"),   ("3.12","Brenen Thompson","WR","TDjer6"),
 ("4.1","Chris Brazzell","WR","SPChocobo"),   ("4.2","Skyler Bell","WR","vizz01"),
 ("4.3","Eli Raridon","TE","archerpayne"),    ("4.4","Zavion Thomas","WR","noonelikesme"),
 ("4.5","Garrett Nussmeier","QB","SPChocobo"),("4.6","Malik Benson","WR","alamosplash"),
 ("4.7","Oscar Delp","TE","RTG67"),           ("4.8","Sam Roush","TE","noonelikesme"),
 ("4.9","Haynes King","QB","easyymoneyyyy"),  ("4.10","Eli Heidenreich","RB","maxinumum"),
 ("4.11","Max Klare","TE","solomongrundy"),   ("4.12","Michael Trigg","TE","patrick32466"),
]
STARTUP={"SPChocobo":(3,9,8,4),"alamosplash":(4,9,9,6),"noonelikesme":(9,6,6,4),
 "easyymoneyyyy":(3,9,9,5),"TDjer6":(6,8,9,3),"maxinumum":(4,7,10,5),"archerpayne":(6,6,9,5),
 "adamstachecki":(5,7,11,3),"vizz01":(7,6,10,3),"patrick32466":(5,6,10,4),
 "RTG67":(5,6,12,3),"solomongrundy":(5,6,12,3)}
assert len(PICKS)==48, len(PICKS)
P="QB RB WR TE".split()
rook={m:[0,0,0,0] for m in SEATS}
for _,_,pos,own in PICKS: rook[own][P.index(pos)]+=1
import statistics as st
print(f"{'manager':15}{'ROOKIE (Q/R/W/T)':>20}{'n':>4}   {'COMBINED':>16}{'n':>5}  WR:RB")
tot=[0,0,0,0]; rats=[]
for m,_ in sorted(((m,(STARTUP[m][2]+rook[m][2])/(STARTUP[m][1]+rook[m][1])) for m in SEATS), key=lambda x:x[1]):
    r=rook[m]; c=[a+b for a,b in zip(STARTUP[m],r)]
    tot=[a+b for a,b in zip(tot,c)]; rats.append(c[2]/c[1])
    print(f"{m:15}{'/'.join(map(str,r)):>20}{sum(r):>4}   {'/'.join(map(str,c)):>16}{sum(c):>5}   {c[2]/c[1]:.2f}")
N=sum(tot); v=sorted(rats)
print(f"\nCOMBINED TOTAL  QB {tot[0]} RB {tot[1]} WR {tot[2]} TE {tot[3]}  = {N} picks")
print(f"  share  QB {tot[0]/N:.1%}  RB {tot[1]/N:.1%}  WR {tot[2]/N:.1%}  TE {tot[3]/N:.1%}   league WR:RB {tot[2]/tot[1]:.2f}")
print(f"  seat WR:RB  min {min(v):.2f}  median {st.median(v):.2f}  max {max(v):.2f}   >1.75: {sum(1 for x in v if x>1.75)}/12")
ra=[sum(rook[m][i] for m in SEATS) for i in range(4)]; RN=sum(ra)
print(f"\nROOKIE ROUND ONLY ({RN} picks): QB {ra[0]/RN:.1%}  RB {ra[1]/RN:.1%}  WR {ra[2]/RN:.1%}  TE {ra[3]/RN:.1%}   WR:RB {ra[2]/ra[1]:.2f}")
print("  picks per seat:", ", ".join(f"{m}:{sum(rook[m])}" for m in SEATS if sum(rook[m])!=4))
