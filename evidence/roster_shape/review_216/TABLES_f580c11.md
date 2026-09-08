
## 12T_ppr  ['QB', 'RB', 'RB', 'WR', 'WR', 'TE', 'FLEX', 'FLEX', 'BN', 'BN', 'BN', 'BN', 'BN', 'BN']  pool 481  commit f580c11

| seat | arm | composition | lineup pts | roster pts | forced by feasibility_first (round pos) | QB taken (round, bpa at that state) |
|---|---|---|---|---|---|---|
| 1 | CURRENT | TE8 RB3 WR2 QB1 | 1987 | 3152 | r12 WR, r13 WR, r14 QB | [(14, 0.0)] |
| 1 | NOFEAS | TE11 RB3 | 1528 | 3138 | - | - |
| 1 | NEEDCAP | TE8 RB3 WR2 QB1 | 1987 | 3152 | r12 WR, r13 WR, r14 QB | [(14, 0.0)] |
| 1 | RFMLV_LEX | RB9 TE2 WR2 QB1 | 2128 | 3186 | r14 QB | [(14, 0.0)] |
| 1 | RFMLV_ADD | RB10 WR2 TE1 QB1 | 2017 | 3155 | r12 WR, r13 WR, r14 QB | [(14, 0.0)] |
| 1 | RAWMLV_LEX | TE7 RB3 WR3 QB1 | 2236 | 3223 | - | [(2, 0.0)] |
| 1 | control (seat 2) | RB6 WR5 QB2 TE1 | 2211 | - | - | - |
| 6 | CURRENT | TE8 RB3 WR2 QB1 | 1899 | 3054 | r12 WR, r13 QB, r14 WR | [(13, 0.0)] |
| 6 | NOFEAS | TE11 RB3 | 1465 | 3088 | - | - |
| 6 | NEEDCAP | TE8 RB3 WR2 QB1 | 1899 | 3054 | r12 WR, r13 QB, r14 WR | [(13, 0.0)] |
| 6 | RFMLV_LEX | RB6 TE4 WR3 QB1 | 2043 | 3108 | r14 QB | [(14, 0.0)] |
| 6 | RFMLV_ADD | TE9 RB2 WR2 QB1 | 1920 | 3053 | r12 WR, r13 WR, r14 QB | [(14, 0.0)] |
| 6 | RAWMLV_LEX | TE9 WR2 RB2 QB1 | 2199 | 3209 | - | [(2, 12.67999999999995)] |
| 6 | control (seat 7) | WR6 QB3 RB3 TE2 | 2187 | - | - | - |
| 12 | CURRENT | RB9 TE2 WR2 QB1 | 1884 | 3043 | r12 WR, r13 WR, r14 QB | [(14, 0.0)] |
| 12 | NOFEAS | RB9 TE3 WR1 QB1 | 1704 | 3046 | - | [(14, 0.0)] |
| 12 | NEEDCAP | RB9 TE2 WR2 QB1 | 1884 | 3043 | r12 WR, r13 WR, r14 QB | [(14, 0.0)] |
| 12 | RFMLV_LEX | TE5 RB4 WR4 QB1 | 2021 | 3113 | r14 QB | [(14, 0.0)] |
| 12 | RFMLV_ADD | RB8 TE3 WR2 QB1 | 1884 | 3049 | r13 WR, r14 QB | [(14, 0.0)] |
| 12 | RAWMLV_LEX | TE7 WR4 RB2 QB1 | 2144 | 3155 | - | [(1, 24.339999999999975)] |
| 12 | control (seat 1) | WR7 RB4 QB2 TE1 | 2232 | - | - | - |
- seat 1: NEEDCAP pick-for-pick identical to CURRENT: True; replay matches recorded #216 JSON: True
- seat 6: NEEDCAP pick-for-pick identical to CURRENT: True; replay matches recorded #216 JSON: True
- seat 12: NEEDCAP pick-for-pick identical to CURRENT: True; replay matches recorded #216 JSON: True

### Static: at CURRENT's own 14/15 states per seat (fixed phantoms), RF-MLV vs the board

| seat | states | rf top == board top | rank of board's top row under RF-MLV (per round) | of board's top-10 rows, how many change rank (per round) |
|---|---|---|---|---|
| 1 | 14 | 4 | [1, 0, 10, 0, 9, 6, 6, 5, 2, 2, 2, 1, 0, 0] | [2, 8, 9, 9, 8, 10, 10, 7, 10, 10, 8, 4, 0, 0] |
| 6 | 14 | 5 | [0, 0, 0, 0, 4, 7, 5, 2, 2, 2, 2, 0, 1, 1] | [2, 8, 4, 9, 9, 10, 10, 10, 10, 10, 9, 3, 3, 2] |
| 12 | 14 | 6 | [0, 0, 0, 1, 2, 9, 4, 4, 2, 2, 3, 0, 0, 0] | [2, 6, 6, 9, 9, 10, 10, 10, 9, 8, 10, 7, 0, 0] |

### QB pricing in CURRENT (best QB row's bpa per round; league QB starter demand per round)

- seat 1: bpa [43.9, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  demand [12.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]  need_bonus max on board 8.67  rows at NEED_BONUS_MAX 0  depth_exposure max 11.4
- seat 6: bpa [43.9, 12.7, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -233.4]
  demand [12.0, 6.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0]  need_bonus max on board 8.67  rows at NEED_BONUS_MAX 0  depth_exposure max 10.08
- seat 12: bpa [24.3, 24.3, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  demand [9.0, 9.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]  need_bonus max on board 8.67  rows at NEED_BONUS_MAX 0  depth_exposure max 7.68

### Replacement gap WR-TE (points) and my TE count, per round, CURRENT

- seat 1: [(1, 43.6, 0), (2, 43.6, 0), (3, 43.6, 1), (4, 42.4, 2), (5, 42.4, 2), (6, 51.0, 3), (7, 55.9, 4), (8, 50.2, 5), (9, 50.2, 5), (10, 52.2, 6), (11, 59.3, 7), (12, 36.5, 8), (13, 36.5, 8), (14, 112.1, 8)]
- seat 6: [(1, 43.6, 0), (2, 43.6, 0), (3, 43.6, 1), (4, 43.6, 1), (5, 42.4, 2), (6, 51.4, 3), (7, 54.6, 4), (8, 48.9, 4), (9, 50.2, 5), (10, 53.2, 6), (11, 53.2, 7), (12, 27.3, 8), (13, 26.7, 8), (14, 13.2, 8)]
- seat 12: [(1, 43.6, 0), (2, 43.6, 1), (3, 43.6, 1), (4, 43.6, 1), (5, 42.0, 1), (6, 42.0, 1), (7, 34.5, 1), (8, 34.5, 2), (9, 27.9, 2), (10, 27.9, 2), (11, 7.6, 2), (12, 7.6, 2), (13, -2.3, 2), (14, 74.9, 2)]

### Sequences

- CURRENT seat 1: r1 RB Jahmyr Gibbs 411.9 | r2 TE Brock Bowers 310.2 | r3 TE Trey McBride 300.9 | r4 RB Javonte Williams 260.0 | r5 TE Tyler Warren 245.1 | r6 TE George Kittle 224.5 | r7 TE Kyle Pitts 216.6 | r8 RB RJ Harvey 192.7 | r9 TE Dalton Kincaid 174.3 | r10 TE AJ Barner 179.5 | r11 TE Chig Okonkwo 177.6 | r12 WR Devaughn Vele 165.0* | r13 WR KC Concepcion 165.1* | r14 QB Michael Penix 129.0*
- NOFEAS seat 1: r1 RB Jahmyr Gibbs 411.9 | r2 TE Brock Bowers 310.2 | r3 TE Trey McBride 300.9 | r4 RB Javonte Williams 260.0 | r5 TE Tyler Warren 245.1 | r6 TE George Kittle 224.5 | r7 TE Kyle Pitts 216.6 | r8 RB RJ Harvey 192.7 | r9 TE Dalton Kincaid 174.3 | r10 TE AJ Barner 179.5 | r11 TE Chig Okonkwo 177.6 | r12 TE T.J. Hockenson 162.7 | r13 TE Brenton Strange 157.8 | r14 TE Greg Dulcich 124.3
- RFMLV_LEX seat 1: r1 RB Christian McCaffrey 413.2 | r2 TE Brock Bowers 310.2 | r3 RB Chase Brown 316.0 | r4 RB Javonte Williams 260.0 | r5 RB David Montgomery 259.9 | r6 WR Jalen Coker 222.9 | r7 WR DK Metcalf 217.1 | r8 RB Tony Pollard 186.3 | r9 RB Chuba Hubbard 185.6 | r10 TE Juwan Johnson 189.3 | r11 RB Jadarian Price 171.0 | r12 RB Jacory Croskey-Merritt 163.8 | r13 RB Jonathon Brooks 162.1 | r14 QB Michael Penix 129.0*
- RFMLV_ADD seat 1: r1 RB Jahmyr Gibbs 411.9 | r2 TE Brock Bowers 310.2 | r3 RB Chase Brown 316.0 | r4 RB Javonte Williams 260.0 | r5 RB David Montgomery 259.9 | r6 RB Bucky Irving 223.6 | r7 RB TreVeyon Henderson 214.6 | r8 RB Chuba Hubbard 185.6 | r9 RB Jadarian Price 171.0 | r10 RB Kenny Gainwell 177.0 | r11 RB Jordan Mason 165.8 | r12 WR Devaughn Vele 165.0* | r13 WR KC Concepcion 165.1* | r14 QB Michael Penix 129.0*
- RAWMLV_LEX seat 1: r1 RB Christian McCaffrey 413.2 | r2 QB Patrick Mahomes 328.6 | r3 RB Chase Brown 316.0 | r4 WR Terry McLaurin 261.1 | r5 RB Javonte Williams 260.0 | r6 WR Alec Pierce 225.5 | r7 TE George Kittle 224.5 | r8 WR Carnell Tate 207.2 | r9 TE Dallas Goedert 183.1 | r10 TE Dalton Schultz 184.3 | r11 TE Dalton Kincaid 174.3 | r12 TE T.J. Hockenson 162.7 | r13 TE Brenton Strange 157.8 | r14 TE Greg Dulcich 124.3
- CURRENT seat 6: r1 RB Jonathan Taylor 355.9 | r2 TE Brock Bowers 310.2 | r3 RB Jeremiyah Love 288.5 | r4 TE Colston Loveland 265.2 | r5 TE Tyler Warren 245.1 | r6 TE George Kittle 224.5 | r7 RB TreVeyon Henderson 214.6 | r8 TE Isaiah Likely 184.7 | r9 TE Dalton Kincaid 174.3 | r10 TE AJ Barner 179.5 | r11 TE Chig Okonkwo 177.6 | r12 WR Rashid Shaheed 170.2* | r13 QB Michael Penix 129.0* | r14 WR De'Zhaun Stribling 134.6*
- NOFEAS seat 6: r1 RB Jonathan Taylor 355.9 | r2 TE Brock Bowers 310.2 | r3 RB Jeremiyah Love 288.5 | r4 TE Colston Loveland 265.2 | r5 TE Tyler Warren 245.1 | r6 TE George Kittle 224.5 | r7 RB TreVeyon Henderson 214.6 | r8 TE Isaiah Likely 184.7 | r9 TE Dalton Kincaid 174.3 | r10 TE AJ Barner 179.5 | r11 TE Chig Okonkwo 177.6 | r12 TE Hunter Henry 172.7 | r13 TE Brenton Strange 157.8 | r14 TE Pat Freiermuth 137.7
- RFMLV_LEX seat 6: r1 RB Jonathan Taylor 355.9 | r2 TE Brock Bowers 310.2 | r3 RB Jeremiyah Love 288.5 | r4 TE Colston Loveland 265.2 | r5 WR Jayden Reed 248.2 | r6 WR Davante Adams 230.5 | r7 WR Parker Washington 215.1 | r8 RB Rachaad White 192.0 | r9 RB Tony Pollard 186.3 | r10 RB Chuba Hubbard 185.6 | r11 RB Jadarian Price 171.0 | r12 TE Hunter Henry 172.7 | r13 TE Brenton Strange 157.8 | r14 QB Michael Penix 129.0*
- RFMLV_ADD seat 6: r1 RB Jonathan Taylor 355.9 | r2 TE Brock Bowers 310.2 | r3 RB Jeremiyah Love 288.5 | r4 TE Colston Loveland 265.2 | r5 TE Tyler Warren 245.1 | r6 TE George Kittle 224.5 | r7 TE Harold Fannin 201.2 | r8 TE Dallas Goedert 183.1 | r9 TE Dalton Kincaid 174.3 | r10 TE Chig Okonkwo 177.6 | r11 TE Hunter Henry 172.7 | r12 WR Rashid Shaheed 170.2* | r13 WR Jalen Nailor 155.8* | r14 QB Michael Penix 129.0*
- RAWMLV_LEX seat 6: r1 WR Amon-Ra St. Brown 375.0 | r2 QB Caleb Williams 341.3 | r3 TE Trey McBride 300.9 | r4 RB Derrick Henry 274.1 | r5 RB Cam Skattebo 249.9 | r6 TE Sam LaPorta 230.8 | r7 TE Kyle Pitts 216.6 | r8 WR Khalil Shakir 210.7 | r9 TE Dallas Goedert 183.1 | r10 TE Dalton Schultz 184.3 | r11 TE Dalton Kincaid 174.3 | r12 TE Hunter Henry 172.7 | r13 TE Brenton Strange 157.8 | r14 TE Pat Freiermuth 137.7
- CURRENT seat 12: r1 TE Brock Bowers 310.2 | r2 RB De'Von Achane 318.2 | r3 RB Kenneth Walker 283.5 | r4 RB Omarion Hampton 280.5 | r5 RB Quinshon Judkins 233.2 | r6 RB Travis Etienne 231.9 | r7 TE Harold Fannin 201.2 | r8 RB RJ Harvey 192.7 | r9 RB Chuba Hubbard 185.6 | r10 RB Jadarian Price 171.0 | r11 RB Kenny Gainwell 177.0 | r12 WR Tre Tucker 180.2* | r13 WR Cooper Kupp 149.1* | r14 QB Michael Penix 129.0*
- NOFEAS seat 12: r1 TE Brock Bowers 310.2 | r2 RB De'Von Achane 318.2 | r3 RB Kenneth Walker 283.5 | r4 RB Omarion Hampton 280.5 | r5 RB Quinshon Judkins 233.2 | r6 RB Travis Etienne 231.9 | r7 TE Harold Fannin 201.2 | r8 RB RJ Harvey 192.7 | r9 RB Chuba Hubbard 185.6 | r10 RB Jadarian Price 171.0 | r11 RB Kenny Gainwell 177.0 | r12 TE Dallas Goedert 183.1 | r13 WR Cooper Kupp 149.1 | r14 QB Michael Penix 129.0
- RFMLV_LEX seat 12: r1 TE Brock Bowers 310.2 | r2 RB De'Von Achane 318.2 | r3 RB Kenneth Walker 283.5 | r4 WR DeVonta Smith 282.5 | r5 WR Ladd McConkey 244.3 | r6 WR Malik Nabers 242.8 | r7 WR Khalil Shakir 210.7 | r8 TE Harold Fannin 201.2 | r9 RB RJ Harvey 192.7 | r10 RB Rachaad White 192.0 | r11 TE Dallas Goedert 183.1 | r12 TE Dalton Kincaid 174.3 | r13 TE Darren Waller 148.4 | r14 QB Michael Penix 129.0*
- RFMLV_ADD seat 12: r1 TE Brock Bowers 310.2 | r2 RB De'Von Achane 318.2 | r3 RB Kenneth Walker 283.5 | r4 RB Omarion Hampton 280.5 | r5 RB Quinshon Judkins 233.2 | r6 RB Travis Etienne 231.9 | r7 TE Harold Fannin 201.2 | r8 RB RJ Harvey 192.7 | r9 RB Chuba Hubbard 185.6 | r10 RB Jadarian Price 171.0 | r11 WR Tre Tucker 180.2 | r12 TE Dallas Goedert 183.1 | r13 WR Cooper Kupp 149.1* | r14 QB Michael Penix 129.0*
- RAWMLV_LEX seat 12: r1 QB Brock Purdy 352.9 | r2 WR CeeDee Lamb 327.9 | r3 WR Zay Flowers 287.1 | r4 RB Kenneth Walker 283.5 | r5 WR Garrett Wilson 244.7 | r6 WR Ladd McConkey 244.3 | r7 RB Rhamondre Stevenson 202.4 | r8 TE Harold Fannin 201.2 | r9 TE Dallas Goedert 183.1 | r10 TE Dalton Schultz 184.3 | r11 TE Dalton Kincaid 174.3 | r12 TE AJ Barner 179.5 | r13 TE Darren Waller 148.4 | r14 TE Cade Otton 141.3

## 12T_ppr_SF  ['QB', 'RB', 'RB', 'WR', 'WR', 'TE', 'FLEX', 'FLEX', 'SUPER_FLEX', 'BN', 'BN', 'BN', 'BN', 'BN', 'BN']  pool 481  commit f580c11

| seat | arm | composition | lineup pts | roster pts | forced by feasibility_first (round pos) | QB taken (round, bpa at that state) |
|---|---|---|---|---|---|---|
| 1 | CURRENT | TE6 QB4 RB3 WR2 | 2469 | 3671 | r15 WR | [(6, 86.95999999999998), (7, 82.13999999999999), (8, 74.38999999999999), (9, 57.51999999999998)] |
| 1 | NOFEAS | TE7 QB4 RB3 WR1 | 2335 | 3659 | - | [(6, 86.95999999999998), (7, 82.13999999999999), (8, 74.38999999999999), (9, 57.51999999999998)] |
| 1 | NEEDCAP | TE6 QB4 RB3 WR2 | 2469 | 3671 | r15 WR | [(6, 86.95999999999998), (7, 82.13999999999999), (8, 74.38999999999999), (9, 57.51999999999998)] |
| 1 | RFMLV_LEX | TE7 WR4 RB2 QB2 | 2550 | 3492 | - | [(4, 92.17000000000002), (5, 86.95999999999998)] |
| 1 | RFMLV_ADD | RB5 TE4 QB4 WR2 | 2471 | 3649 | - | [(4, 92.17000000000002), (6, 82.13999999999999), (8, 74.38999999999999), (9, 57.51999999999998)] |
| 1 | RAWMLV_LEX | RB5 TE5 WR3 QB2 | 2532 | 3472 | - | [(3, 109.86000000000001), (4, 92.17000000000002)] |
| 1 | control (seat 2) | WR9 RB3 QB2 TE1 | 2530 | - | - | - |
| 6 | CURRENT | TE7 QB4 RB2 WR2 | 2357 | 3602 | r14 WR, r15 WR | [(6, 86.95999999999998), (7, 82.13999999999999), (8, 74.38999999999999), (9, 57.51999999999998)] |
| 6 | NOFEAS | TE9 QB4 RB2 | 2097 | 3604 | - | [(6, 86.95999999999998), (7, 82.13999999999999), (8, 74.38999999999999), (9, 57.51999999999998)] |
| 6 | NEEDCAP | TE7 QB4 RB2 WR2 | 2357 | 3602 | r14 WR, r15 WR | [(6, 86.95999999999998), (7, 82.13999999999999), (8, 74.38999999999999), (9, 57.51999999999998)] |
| 6 | RFMLV_LEX | TE7 RB3 WR3 QB2 | 2457 | 3424 | - | [(4, 100.64999999999998), (5, 82.13999999999999)] |
| 6 | RFMLV_ADD | TE7 QB4 RB2 WR2 | 2327 | 3562 | r14 WR, r15 WR | [(5, 86.95999999999998), (6, 82.13999999999999), (8, 74.38999999999999), (9, 57.51999999999998)] |
| 6 | RAWMLV_LEX | TE6 WR4 RB3 QB2 | 2480 | 3442 | - | [(2, 121.50999999999999), (3, 103.64999999999998)] |
| 6 | control (seat 7) | WR6 RB4 QB3 TE2 | 2466 | - | - | - |
| 12 | CURRENT | TE5 QB5 RB3 WR2 | 2277 | 3592 | r15 WR | [(2, 145.44), (6, 82.13999999999999), (7, 74.38999999999999), (9, 57.51999999999998), (10, 54.99000000000001)] |
| 12 | NOFEAS | TE6 QB5 RB3 WR1 | 2158 | 3578 | - | [(2, 145.44), (6, 82.13999999999999), (7, 74.38999999999999), (9, 57.51999999999998), (10, 54.99000000000001)] |
| 12 | NEEDCAP | TE5 QB5 RB3 WR2 | 2277 | 3592 | r15 WR | [(2, 145.44), (6, 82.13999999999999), (7, 74.38999999999999), (9, 57.51999999999998), (10, 54.99000000000001)] |
| 12 | RFMLV_LEX | TE7 QB3 RB3 WR2 | 2442 | 3475 | - | [(2, 145.44), (5, 82.13999999999999), (10, 74.38999999999999)] |
| 12 | RFMLV_ADD | TE5 QB5 RB3 WR2 | 2339 | 3584 | - | [(2, 145.44), (5, 82.13999999999999), (7, 74.38999999999999), (9, 57.51999999999998), (10, 54.99000000000001)] |
| 12 | RAWMLV_LEX | TE7 QB3 WR3 RB2 | 2463 | 3496 | - | [(1, 145.44), (2, 140.32), (10, 74.38999999999999)] |
| 12 | control (seat 1) | WR9 RB3 QB2 TE1 | 2548 | - | - | - |
- seat 1: NEEDCAP pick-for-pick identical to CURRENT: True; replay matches recorded #216 JSON: True
- seat 6: NEEDCAP pick-for-pick identical to CURRENT: True; replay matches recorded #216 JSON: True
- seat 12: NEEDCAP pick-for-pick identical to CURRENT: True; replay matches recorded #216 JSON: True

### Static: at CURRENT's own 14/15 states per seat (fixed phantoms), RF-MLV vs the board

| seat | states | rf top == board top | rank of board's top row under RF-MLV (per round) | of board's top-10 rows, how many change rank (per round) |
|---|---|---|---|---|
| 1 | 15 | 5 | [1, 0, 0, 4, 10, 0, 0, 4, 4, 2, 2, 1, 1, 1, 0] | [4, 4, 9, 10, 10, 7, 7, 10, 10, 8, 8, 7, 9, 5, 0] |
| 6 | 15 | 6 | [0, 0, 18, 0, 5, 0, 0, 6, 2, 2, 2, 2, 2, 2, 0] | [2, 7, 9, 4, 10, 8, 8, 10, 10, 8, 9, 10, 8, 3, 0] |
| 12 | 15 | 7 | [0, 0, 0, 0, 4, 0, 12, 1, 2, 2, 2, 2, 0, 1, 0] | [3, 6, 3, 7, 10, 9, 9, 10, 9, 9, 10, 10, 5, 9, 0] |

### QB pricing in CURRENT (best QB row's bpa per round; league QB starter demand per round)

- seat 1: bpa [165.0, 109.9, 109.9, 92.2, 92.2, 87.0, 82.1, 74.4, 57.5, None, None, None, None, None, None]
  demand [22.2, 10.8, 10.8, 2.7, 2.7, 1.85, 0.85, 0, 0, 0, 0, 0, 0, 0, 0]  need_bonus max on board 8.72  rows at NEED_BONUS_MAX 0  depth_exposure max 9.6
- seat 6: bpa [165.0, 121.1, 107.6, 100.6, 87.0, 87.0, 82.1, 74.4, 57.5, None, None, None, None, None, None]
  demand [22.2, 12.8, 8.8, 7.1, 1.85, 1.85, 0.85, 0, 0, 0, 0, 0, 0, 0, 0]  need_bonus max on board 8.72  rows at NEED_BONUS_MAX 0  depth_exposure max 7.56
- seat 12: bpa [145.4, 145.4, 99.7, 99.7, 82.1, 82.1, 74.4, 57.5, 57.5, 55.0, None, None, None, None, None]
  demand [19.2, 19.2, 6.1, 6.1, 0.85, 0.85, 0, 0, 0, 0, 0, 0, 0, 0, 0]  need_bonus max on board 8.72  rows at NEED_BONUS_MAX 0  depth_exposure max 8.52

### Replacement gap WR-TE (points) and my TE count, per round, CURRENT

- seat 1: [(1, 52.4, 0), (2, 52.4, 0), (3, 52.4, 1), (4, 52.4, 1), (5, 52.4, 1), (6, 52.1, 2), (7, 52.1, 2), (8, 44.0, 2), (9, 44.0, 2), (10, 35.2, 2), (11, 40.0, 3), (12, 12.4, 4), (13, 12.4, 4), (14, 25.5, 5), (15, 25.5, 6)]
- seat 6: [(1, 52.4, 0), (2, 52.4, 0), (3, 52.4, 1), (4, 52.4, 2), (5, 52.4, 2), (6, 56.3, 3), (7, 55.9, 3), (8, 52.9, 3), (9, 48.9, 3), (10, 43.9, 3), (11, 28.8, 4), (12, 23.8, 5), (13, 11.4, 6), (14, 30.6, 7), (15, 19.0, 7)]
- seat 12: [(1, 52.4, 0), (2, 52.4, 1), (3, 52.4, 1), (4, 52.4, 1), (5, 52.4, 1), (6, 52.4, 1), (7, 49.7, 1), (8, 49.7, 1), (9, 44.0, 2), (10, 44.0, 2), (11, 7.6, 2), (12, 12.5, 3), (13, 11.2, 4), (14, 11.2, 4), (15, 10.9, 5)]

### Sequences

- CURRENT seat 1: r1 RB Jahmyr Gibbs 411.9 | r2 TE Brock Bowers 310.2 | r3 RB James Cook 317.9 | r4 RB Omarion Hampton 280.5 | r5 TE Colston Loveland 265.2 | r6 QB C.J. Stroud 294.5 | r7 QB Malik Willis 289.6 | r8 QB Daniel Jones 281.9 | r9 QB Bryce Young 265.0 | r10 TE Isaiah Likely 184.7 | r11 TE Dallas Goedert 183.1 | r12 WR Devaughn Vele 165.0 | r13 TE T.J. Hockenson 162.7 | r14 TE Greg Dulcich 124.3 | r15 WR De'Zhaun Stribling 134.6*
- NOFEAS seat 1: r1 RB Jahmyr Gibbs 411.9 | r2 TE Brock Bowers 310.2 | r3 RB James Cook 317.9 | r4 RB Omarion Hampton 280.5 | r5 TE Colston Loveland 265.2 | r6 QB C.J. Stroud 294.5 | r7 QB Malik Willis 289.6 | r8 QB Daniel Jones 281.9 | r9 QB Bryce Young 265.0 | r10 TE Isaiah Likely 184.7 | r11 TE Dallas Goedert 183.1 | r12 WR Devaughn Vele 165.0 | r13 TE T.J. Hockenson 162.7 | r14 TE Greg Dulcich 124.3 | r15 TE Mike Gesicki 122.3
- RFMLV_LEX seat 1: r1 RB Christian McCaffrey 413.2 | r2 TE Brock Bowers 310.2 | r3 RB James Cook 317.9 | r4 QB Tyler Shough 299.7 | r5 QB C.J. Stroud 294.5 | r6 WR Garrett Wilson 244.7 | r7 WR Ladd McConkey 244.3 | r8 WR Michael Wilson 213.7 | r9 WR Rome Odunze 212.4 | r10 TE Juwan Johnson 189.3 | r11 TE Isaiah Likely 184.7 | r12 TE T.J. Hockenson 162.7 | r13 TE Brenton Strange 157.8 | r14 TE Greg Dulcich 124.3 | r15 TE Mike Gesicki 122.3
- RFMLV_ADD seat 1: r1 RB Jahmyr Gibbs 411.9 | r2 TE Brock Bowers 310.2 | r3 RB James Cook 317.9 | r4 QB Tyler Shough 299.7 | r5 RB Omarion Hampton 280.5 | r6 QB Malik Willis 289.6 | r7 TE Tucker Kraft 231.2 | r8 QB Daniel Jones 281.9 | r9 QB Bryce Young 265.0 | r10 RB RJ Harvey 192.7 | r11 RB Rachaad White 192.0 | r12 WR Devaughn Vele 165.0 | r13 WR KC Concepcion 165.1 | r14 TE Greg Dulcich 124.3 | r15 TE Mike Gesicki 122.3
- RAWMLV_LEX seat 1: r1 RB Christian McCaffrey 413.2 | r2 RB James Cook 317.9 | r3 QB Jordan Love 317.4 | r4 QB Tyler Shough 299.7 | r5 RB Omarion Hampton 280.5 | r6 WR Garrett Wilson 244.7 | r7 WR Ladd McConkey 244.3 | r8 WR Michael Wilson 213.7 | r9 TE Harold Fannin 201.2 | r10 RB Tony Pollard 186.3 | r11 RB Chuba Hubbard 185.6 | r12 TE T.J. Hockenson 162.7 | r13 TE Brenton Strange 157.8 | r14 TE Greg Dulcich 124.3 | r15 TE Mike Gesicki 122.3
- CURRENT seat 6: r1 RB Jonathan Taylor 355.9 | r2 TE Brock Bowers 310.2 | r3 TE Trey McBride 300.9 | r4 RB Omarion Hampton 280.5 | r5 TE Colston Loveland 265.2 | r6 QB C.J. Stroud 294.5 | r7 QB Malik Willis 289.6 | r8 QB Daniel Jones 281.9 | r9 QB Bryce Young 265.0 | r10 TE Dallas Goedert 183.1 | r11 TE Dalton Schultz 184.3 | r12 TE Hunter Henry 172.7 | r13 TE Brenton Strange 157.8 | r14 WR De'Zhaun Stribling 134.6* | r15 WR Jordyn Tyson 125.3*
- NOFEAS seat 6: r1 RB Jonathan Taylor 355.9 | r2 TE Brock Bowers 310.2 | r3 TE Trey McBride 300.9 | r4 RB Omarion Hampton 280.5 | r5 TE Colston Loveland 265.2 | r6 QB C.J. Stroud 294.5 | r7 QB Malik Willis 289.6 | r8 QB Daniel Jones 281.9 | r9 QB Bryce Young 265.0 | r10 TE Dallas Goedert 183.1 | r11 TE Dalton Schultz 184.3 | r12 TE Hunter Henry 172.7 | r13 TE Brenton Strange 157.8 | r14 TE Pat Freiermuth 137.7 | r15 TE Greg Dulcich 124.3
- RFMLV_LEX seat 6: r1 RB Jonathan Taylor 355.9 | r2 TE Brock Bowers 310.2 | r3 RB Jeremiyah Love 288.5 | r4 QB Trevor Lawrence 308.1 | r5 QB Malik Willis 289.6 | r6 WR Jayden Reed 248.2 | r7 TE Tucker Kraft 231.2 | r8 WR Parker Washington 215.1 | r9 WR Jordan Addison 209.9 | r10 RB Rachaad White 192.0 | r11 TE Dallas Goedert 183.1 | r12 TE Hunter Henry 172.7 | r13 TE Brenton Strange 157.8 | r14 TE Pat Freiermuth 137.7 | r15 TE Greg Dulcich 124.3
- RFMLV_ADD seat 6: r1 RB Jonathan Taylor 355.9 | r2 TE Brock Bowers 310.2 | r3 TE Trey McBride 300.9 | r4 RB Omarion Hampton 280.5 | r5 QB C.J. Stroud 294.5 | r6 QB Malik Willis 289.6 | r7 TE Tucker Kraft 231.2 | r8 QB Daniel Jones 281.9 | r9 QB Bryce Young 265.0 | r10 TE Dallas Goedert 183.1 | r11 TE Dalton Kincaid 174.3 | r12 TE Hunter Henry 172.7 | r13 TE Brenton Strange 157.8 | r14 WR Ryan Flournoy 139.0* | r15 WR Jordyn Tyson 125.3*
- RAWMLV_LEX seat 6: r1 WR Amon-Ra St. Brown 375.0 | r2 QB Jaxson Dart 329.0 | r3 QB Matthew Stafford 311.1 | r4 RB Kenneth Walker 283.5 | r5 RB Saquon Barkley 274.6 | r6 WR Jayden Reed 248.2 | r7 TE Tucker Kraft 231.2 | r8 WR DJ Moore 216.2 | r9 WR Khalil Shakir 210.7 | r10 RB Tony Pollard 186.3 | r11 TE Dallas Goedert 183.1 | r12 TE Hunter Henry 172.7 | r13 TE Brenton Strange 157.8 | r14 TE Pat Freiermuth 137.7 | r15 TE Greg Dulcich 124.3
- CURRENT seat 12: r1 TE Brock Bowers 310.2 | r2 QB Brock Purdy 352.9 | r3 RB Jeremiyah Love 288.5 | r4 RB Kenneth Walker 283.5 | r5 RB Javonte Williams 260.0 | r6 QB Malik Willis 289.6 | r7 QB Daniel Jones 281.9 | r8 TE George Kittle 224.5 | r9 QB Bryce Young 265.0 | r10 QB Aaron Rodgers 262.5 | r11 TE Dallas Goedert 183.1 | r12 TE Dalton Kincaid 174.3 | r13 WR Cooper Kupp 149.1 | r14 TE Darren Waller 148.4 | r15 WR Dontayvion Wicks 118.6*
- NOFEAS seat 12: r1 TE Brock Bowers 310.2 | r2 QB Brock Purdy 352.9 | r3 RB Jeremiyah Love 288.5 | r4 RB Kenneth Walker 283.5 | r5 RB Javonte Williams 260.0 | r6 QB Malik Willis 289.6 | r7 QB Daniel Jones 281.9 | r8 TE George Kittle 224.5 | r9 QB Bryce Young 265.0 | r10 QB Aaron Rodgers 262.5 | r11 TE Dallas Goedert 183.1 | r12 TE Dalton Kincaid 174.3 | r13 WR Cooper Kupp 149.1 | r14 TE Darren Waller 148.4 | r15 TE Mason Taylor 104.1
- RFMLV_LEX seat 12: r1 TE Brock Bowers 310.2 | r2 QB Brock Purdy 352.9 | r3 RB Jeremiyah Love 288.5 | r4 RB Kenneth Walker 283.5 | r5 QB Malik Willis 289.6 | r6 RB Javonte Williams 260.0 | r7 WR Alec Pierce 225.5 | r8 TE George Kittle 224.5 | r9 WR Carnell Tate 207.2 | r10 QB Daniel Jones 281.9 | r11 TE Dallas Goedert 183.1 | r12 TE Dalton Kincaid 174.3 | r13 TE Darren Waller 148.4 | r14 TE Cade Otton 141.3 | r15 TE Mason Taylor 104.1
- RFMLV_ADD seat 12: r1 TE Brock Bowers 310.2 | r2 QB Brock Purdy 352.9 | r3 RB Jeremiyah Love 288.5 | r4 RB Kenneth Walker 283.5 | r5 QB Malik Willis 289.6 | r6 RB Javonte Williams 260.0 | r7 QB Daniel Jones 281.9 | r8 TE George Kittle 224.5 | r9 QB Bryce Young 265.0 | r10 QB Aaron Rodgers 262.5 | r11 WR Tre Tucker 180.2 | r12 TE Dallas Goedert 183.1 | r13 WR Cooper Kupp 149.1 | r14 TE Darren Waller 148.4 | r15 TE Mason Taylor 104.1
- RAWMLV_LEX seat 12: r1 QB Brock Purdy 352.9 | r2 QB Jalen Hurts 347.8 | r3 TE Trey McBride 300.9 | r4 WR Chris Olave 298.3 | r5 WR Terry McLaurin 261.1 | r6 RB Javonte Williams 260.0 | r7 WR Alec Pierce 225.5 | r8 TE George Kittle 224.5 | r9 RB Rachaad White 192.0 | r10 QB Daniel Jones 281.9 | r11 TE Dallas Goedert 183.1 | r12 TE Dalton Kincaid 174.3 | r13 TE Darren Waller 148.4 | r14 TE Cade Otton 141.3 | r15 TE Mason Taylor 104.1
