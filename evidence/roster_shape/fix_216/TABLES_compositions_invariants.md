## Compositions, lineup points, forced picks (one process, one code version)

| format | seat | arm | composition | lineup pts | vs BASE_ON | control lineup | forced (`fills_required_slot`) | overrode pure argmax | missing dedicated | unfillable | QB rounds | replay gate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 12T_ppr | 1 | BASE_ON | TE8 RB3 WR2 QB1 | 1987 | +0 | 2211 | 3 | 3 | - | - | [14] | MATCH |
| 12T_ppr | 1 | BASE_OFF | TE11 RB3 | 1528 | -459 | 2211 | 0 | 0 | {'WR': 2, 'QB': 1} | ['QB', 'WR'] | [] |  |
| 12T_ppr | 1 | FIX_ON | WR7 TE3 RB2 QB2 | 2296 | +309 | 2234 | 0 | 0 | - | - | [8, 9] |  |
| 12T_ppr | 1 | FIX_OFF | WR7 TE3 RB2 QB2 | 2296 | +309 | 2234 | 0 | 0 | - | - | [8, 9] |  |
| 12T_ppr | 6 | BASE_ON | TE8 RB3 WR2 QB1 | 1899 | +0 | 2187 | 3 | 3 | - | - | [13] | MATCH |
| 12T_ppr | 6 | BASE_OFF | TE11 RB3 | 1465 | -434 | 2187 | 0 | 0 | {'WR': 2, 'QB': 1} | ['QB', 'WR'] | [] |  |
| 12T_ppr | 6 | FIX_ON | WR8 TE3 RB2 QB1 | 2239 | +340 | 2187 | 0 | 0 | - | - | [8] |  |
| 12T_ppr | 6 | FIX_OFF | WR8 TE3 RB2 QB1 | 2239 | +340 | 2187 | 0 | 0 | - | - | [8] |  |
| 12T_ppr | 12 | BASE_ON | RB9 TE2 WR2 QB1 | 1884 | +0 | 2232 | 3 | 1 | - | - | [14] | MATCH |
| 12T_ppr | 12 | BASE_OFF | RB9 TE3 WR1 QB1 | 1704 | -180 | 2232 | 0 | 0 | {'WR': 1} | ['WR'] | [14] |  |
| 12T_ppr | 12 | FIX_ON | WR8 RB4 TE1 QB1 | 2209 | +325 | 2227 | 0 | 0 | - | - | [8] |  |
| 12T_ppr | 12 | FIX_OFF | WR8 RB4 TE1 QB1 | 2209 | +325 | 2227 | 0 | 0 | - | - | [8] |  |
| 12T_ppr_SF | 1 | BASE_ON | TE6 QB4 RB3 WR2 | 2469 | +0 | 2530 | 1 | 1 | - | - | [6, 7, 8, 9] | MATCH |
| 12T_ppr_SF | 1 | BASE_OFF | TE7 QB4 RB3 WR1 | 2335 | -135 | 2530 | 0 | 0 | {'WR': 1} | ['WR'] | [6, 7, 8, 9] |  |
| 12T_ppr_SF | 1 | FIX_ON | WR8 RB3 TE2 QB2 | 2592 | +123 | 2530 | 0 | 0 | - | - | [6, 7] |  |
| 12T_ppr_SF | 1 | FIX_OFF | WR8 RB3 TE2 QB2 | 2592 | +123 | 2530 | 0 | 0 | - | - | [6, 7] |  |
| 12T_ppr_SF | 6 | BASE_ON | TE7 QB4 RB2 WR2 | 2357 | +0 | 2466 | 2 | 2 | - | - | [6, 7, 8, 9] | MATCH |
| 12T_ppr_SF | 6 | BASE_OFF | TE9 QB4 RB2 | 2097 | -260 | 2466 | 0 | 0 | {'WR': 2} | ['WR'] | [6, 7, 8, 9] |  |
| 12T_ppr_SF | 6 | FIX_ON | WR8 TE3 RB2 QB2 | 2520 | +163 | 2466 | 0 | 0 | - | - | [6, 7] |  |
| 12T_ppr_SF | 6 | FIX_OFF | WR8 TE3 RB2 QB2 | 2520 | +163 | 2466 | 0 | 0 | - | - | [6, 7] |  |
| 12T_ppr_SF | 12 | BASE_ON | TE5 QB5 RB3 WR2 | 2277 | +0 | 2548 | 1 | 1 | - | - | [2, 6, 7, 9, 10] | MATCH |
| 12T_ppr_SF | 12 | BASE_OFF | TE6 QB5 RB3 WR1 | 2158 | -119 | 2548 | 0 | 0 | {'WR': 1} | ['WR'] | [2, 6, 7, 9, 10] |  |
| 12T_ppr_SF | 12 | FIX_ON | WR7 RB4 TE2 QB2 | 2442 | +165 | 2547 | 0 | 0 | - | - | [2, 6] |  |
| 12T_ppr_SF | 12 | FIX_OFF | WR7 RB4 TE2 QB2 | 2442 | +165 | 2547 | 0 | 0 | - | - | [2, 6] |  |

## Invariant 2 -- best remaining QB's price at each of my turns (1QB), FIX_ON

- 12T_ppr seat 1 BASE_ON: r1: OPEN bpa 43.9 final 48.1; r2: OPEN bpa 0.0 final 4.0; r3: OPEN bpa 0.0 final 4.0; r4: OPEN bpa 0.0 final 4.0; r5: OPEN bpa 0.0 final 4.0; r6: OPEN bpa 0.0 final 4.0; r7: OPEN bpa 0.0 final 4.0; r8: OPEN bpa 0.0 final 4.0; r9: OPEN bpa 0.0 final 4.0; r10: OPEN bpa 0.0 final 6.2; r11: OPEN bpa 0.0 final 6.2; r12: OPEN bpa 0.0 final 4.9; r13: OPEN bpa 0.0 final 4.9; r14: OPEN bpa 0.0 final 3.4
- 12T_ppr seat 1 FIX_ON: r1: OPEN bpa 43.9 final 48.1; r2: OPEN bpa 0.0 final 4.0; r3: OPEN bpa 0.0 final 4.0; r4: OPEN bpa 0.0 final 4.0; r5: OPEN bpa 0.0 final 4.0; r6: OPEN bpa 0.0 final 4.0; r7: OPEN bpa 0.0 final 4.0; r8: OPEN bpa 0.0 final 4.0; r9: filled bpa -11.2 final -11.2; r10: filled bpa -199.6 final -197.3; r11: filled bpa -199.6 final -194.0; r12: filled bpa -199.6 final -195.3; r13: filled bpa -199.6 final -195.4; r14: filled bpa -199.6 final -196.9
- 12T_ppr seat 6 BASE_ON: r1: OPEN bpa 43.9 final 47.9; r2: OPEN bpa 12.7 final 16.4; r3: OPEN bpa 0.0 final 4.0; r4: OPEN bpa 0.0 final 4.0; r5: OPEN bpa 0.0 final 4.0; r6: OPEN bpa 0.0 final 4.0; r7: OPEN bpa 0.0 final 4.0; r8: OPEN bpa 0.0 final 4.0; r9: OPEN bpa 0.0 final 4.0; r10: OPEN bpa 0.0 final 2.9; r11: OPEN bpa 0.0 final 5.9; r12: OPEN bpa 0.0 final 5.2; r13: OPEN bpa 0.0 final 4.6; r14: filled bpa -233.4 final -229.6
- 12T_ppr seat 6 FIX_ON: r1: OPEN bpa 43.9 final 47.9; r2: OPEN bpa 12.7 final 16.4; r3: OPEN bpa 0.0 final 4.0; r4: OPEN bpa 0.0 final 4.0; r5: OPEN bpa 0.0 final 4.0; r6: OPEN bpa 0.0 final 4.0; r7: OPEN bpa 0.0 final 4.0; r8: OPEN bpa 0.0 final 4.0; r9: filled bpa -21.4 final -22.0; r10: filled bpa -89.5 final -92.3; r11: filled bpa -199.6 final -194.3; r12: filled bpa -199.6 final -195.0; r13: filled bpa -199.6 final -195.7; r14: filled bpa -199.6 final -196.5
- 12T_ppr seat 12 BASE_ON: r1: OPEN bpa 24.3 final 27.4; r2: OPEN bpa 24.3 final 27.4; r3: OPEN bpa 0.0 final 4.0; r4: OPEN bpa 0.0 final 4.0; r5: OPEN bpa 0.0 final 4.0; r6: OPEN bpa 0.0 final 4.0; r7: OPEN bpa 0.0 final 4.0; r8: OPEN bpa 0.0 final 4.0; r9: OPEN bpa 0.0 final 3.6; r10: OPEN bpa 0.0 final 3.6; r11: OPEN bpa 0.0 final 5.6; r12: OPEN bpa 0.0 final 5.6; r13: OPEN bpa 0.0 final 4.2; r14: OPEN bpa 0.0 final 4.1
- 12T_ppr seat 12 FIX_ON: r1: OPEN bpa 24.3 final 27.4; r2: OPEN bpa 24.3 final 27.4; r3: OPEN bpa 0.0 final 4.0; r4: OPEN bpa 0.0 final 4.0; r5: OPEN bpa 0.0 final 4.0; r6: OPEN bpa 0.0 final 4.0; r7: OPEN bpa 0.0 final 4.0; r8: OPEN bpa 0.0 final 4.0; r9: filled bpa -39.0 final -39.1; r10: filled bpa -39.0 final -35.7; r11: filled bpa -199.6 final -194.6; r12: filled bpa -199.6 final -194.7; r13: filled bpa -199.6 final -196.1; r14: filled bpa -199.6 final -196.1

## Invariant 4/5 -- most-drafted bench position, league WR-TE gap and ledger WR-TE gap by round (FIX_ON)

| format | seat | round | mine before | chosen | league gap WR-TE | ledger gap WR-TE (what the board orders on) | displacement by position |
|---|---|---|---|---|---|---|---|
| 12T_ppr | 1 | 1 | - | RB Jahmyr Gibbs (232.93) | 43.56 | 43.56 | - |
| 12T_ppr | 1 | 2 | RB1 | TE Brock Bowers (142.0) | 43.56 | 43.56 | - |
| 12T_ppr | 1 | 3 | RB1 TE1 | TE Trey McBride (129.02) | 43.56 | 43.56 | - |
| 12T_ppr | 1 | 4 | TE2 RB1 | RB Javonte Williams (79.02) | 42.36 | 42.36 | - |
| 12T_ppr | 1 | 5 | RB2 TE2 | TE Tyler Warren (70.64) | 42.36 | 42.36 | - |
| 12T_ppr | 1 | 6 | TE3 RB2 | WR Jalen Coker (11.24) | 51.0 | -31.42 | {'RB': -68.09, 'TE': -82.42} |
| 12T_ppr | 1 | 7 | TE3 RB2 WR1 | WR DK Metcalf (5.46) | 51.0 | -31.42 | {'RB': -68.09, 'TE': -82.42} |
| 12T_ppr | 1 | 8 | TE3 RB2 WR2 | QB Patrick Mahomes (4.0) | 53.6 | -28.02 | {'WR': -0.8, 'RB': -68.09, 'TE': -82.42} |
| 12T_ppr | 1 | 9 | TE3 RB2 WR2 QB1 | QB Jordan Love (-11.24) | 53.6 | -28.02 | {'WR': -0.8, 'RB': -68.09, 'TE': -82.42} |
| 12T_ppr | 1 | 10 | TE3 RB2 WR2 QB2 | WR Marvin Harrison (-18.54) | 53.6 | -28.02 | {'WR': -0.8, 'RB': -68.09, 'TE': -82.42} |
| 12T_ppr | 1 | 11 | TE3 WR3 RB2 QB2 | WR Jakobi Meyers (-22.34) | 53.6 | -28.02 | {'WR': -0.8, 'RB': -68.09, 'TE': -82.42} |
| 12T_ppr | 1 | 12 | WR4 TE3 RB2 QB2 | WR Devaughn Vele (-51.32) | 67.81 | -28.02 | {'WR': -0.8, 'RB': -90.35, 'TE': -96.63} |
| 12T_ppr | 1 | 13 | WR5 TE3 RB2 QB2 | WR KC Concepcion (-52.44) | 67.81 | -28.02 | {'WR': -0.8, 'RB': -90.35, 'TE': -96.63} |
| 12T_ppr | 1 | 14 | WR6 TE3 RB2 QB2 | WR De'Zhaun Stribling (-83.9) | 93.96 | -28.02 | {'WR': -0.8, 'RB': -119.0, 'TE': -122.78} |
| 12T_ppr | 6 | 1 | - | RB Jonathan Taylor (176.08) | 43.56 | 43.56 | - |
| 12T_ppr | 6 | 2 | RB1 | TE Brock Bowers (141.97) | 43.56 | 43.56 | - |
| 12T_ppr | 6 | 3 | RB1 TE1 | RB Jeremiyah Love (106.59) | 43.56 | 43.56 | - |
| 12T_ppr | 6 | 4 | RB2 TE1 | TE Colston Loveland (92.09) | 43.56 | 43.56 | - |
| 12T_ppr | 6 | 5 | RB2 TE2 | TE Tyler Warren (70.59) | 42.36 | 42.36 | - |
| 12T_ppr | 6 | 6 | TE3 RB2 | WR Davante Adams (23.33) | 51.41 | -31.01 | {'RB': -74.03, 'TE': -82.42} |
| 12T_ppr | 6 | 7 | TE3 RB2 WR1 | WR Emeka Egbuka (6.06) | 49.73 | -32.69 | {'RB': -74.03, 'TE': -82.42} |
| 12T_ppr | 6 | 8 | TE3 RB2 WR2 | QB Patrick Mahomes (4.0) | 44.52 | -30.36 | {'WR': -7.54, 'RB': -74.03, 'TE': -82.42} |
| 12T_ppr | 6 | 9 | TE3 RB2 WR2 QB1 | WR Brian Thomas (-14.25) | 38.99 | -30.36 | {'WR': -13.07, 'RB': -74.03, 'TE': -82.42} |
| 12T_ppr | 6 | 10 | TE3 WR3 RB2 QB1 | WR Michael Pittman (-13.21) | 53.6 | -28.82 | {'RB': -74.03, 'TE': -82.42} |
| 12T_ppr | 6 | 11 | WR4 TE3 RB2 QB1 | WR Wan'Dale Robinson (-23.91) | 53.6 | -28.82 | {'RB': -74.03, 'TE': -82.42} |
| 12T_ppr | 6 | 12 | WR5 TE3 RB2 QB1 | WR Rashid Shaheed (-44.49) | 67.81 | -28.82 | {'RB': -82.95, 'TE': -96.63} |
| 12T_ppr | 6 | 13 | WR6 TE3 RB2 QB1 | WR Cooper Kupp (-63.55) | 67.81 | -28.82 | {'RB': -95.07, 'TE': -96.63} |
| 12T_ppr | 6 | 14 | WR7 TE3 RB2 QB1 | WR De'Zhaun Stribling (-79.45) | 93.96 | -28.82 | {'RB': -119.0, 'TE': -122.78} |
| 12T_ppr | 12 | 1 | - | TE Brock Bowers (141.96) | 43.56 | 43.56 | - |
| 12T_ppr | 12 | 2 | TE1 | RB De'Von Achane (139.14) | 43.56 | 43.56 | - |
| 12T_ppr | 12 | 3 | TE1 RB1 | RB Kenneth Walker (99.54) | 43.56 | 43.56 | - |
| 12T_ppr | 12 | 4 | RB2 TE1 | RB Omarion Hampton (94.27) | 43.56 | 43.56 | - |
| 12T_ppr | 12 | 5 | RB3 TE1 | RB Quinshon Judkins (58.25) | 42.02 | 42.02 | - |
| 12T_ppr | 12 | 6 | RB4 TE1 | WR Malik Nabers (37.23) | 42.02 | -18.48 | {'TE': -60.5, 'RB': -67.37} |
| 12T_ppr | 12 | 7 | RB4 TE1 WR1 | WR Rome Odunze (8.27) | 34.48 | -26.02 | {'TE': -60.5, 'RB': -67.37} |
| 12T_ppr | 12 | 8 | RB4 WR2 TE1 | QB Patrick Mahomes (4.0) | 34.48 | -20.81 | {'WR': -5.21, 'TE': -60.5, 'RB': -67.37} |
| 12T_ppr | 12 | 9 | RB4 WR2 TE1 QB1 | WR Michael Pittman (-12.55) | 27.95 | -20.81 | {'WR': -11.74, 'TE': -60.5, 'RB': -67.37} |
| 12T_ppr | 12 | 10 | RB4 WR3 TE1 QB1 | WR Courtland Sutton (-10.63) | 43.56 | -16.94 | {'TE': -60.5, 'RB': -67.37} |
| 12T_ppr | 12 | 11 | RB4 WR4 TE1 QB1 | WR Tre Tucker (-35.8) | 53.6 | -16.94 | {'TE': -70.54, 'RB': -71.07} |
| 12T_ppr | 12 | 12 | WR5 RB4 TE1 QB1 | WR Rashid Shaheed (-40.6) | 53.6 | -16.94 | {'TE': -70.54, 'RB': -71.07} |
| 12T_ppr | 12 | 13 | WR6 RB4 TE1 QB1 | WR Cooper Kupp (-59.95) | 78.52 | -16.94 | {'TE': -95.46, 'RB': -91.69} |
| 12T_ppr | 12 | 14 | WR7 RB4 TE1 QB1 | WR De'Zhaun Stribling (-75.39) | 78.52 | -16.94 | {'TE': -95.46, 'RB': -91.69} |
| 12T_ppr_SF | 1 | 1 | - | RB Jahmyr Gibbs (241.72) | 52.4 | 52.4 | - |
| 12T_ppr_SF | 1 | 2 | RB1 | TE Brock Bowers (151.92) | 52.4 | 52.4 | - |
| 12T_ppr_SF | 1 | 3 | RB1 TE1 | RB James Cook (142.2) | 52.4 | 52.4 | - |
| 12T_ppr_SF | 1 | 4 | RB2 TE1 | RB Omarion Hampton (103.16) | 52.4 | 52.4 | - |
| 12T_ppr_SF | 1 | 5 | RB3 TE1 | TE Colston Loveland (102.63) | 52.4 | 52.4 | - |
| 12T_ppr_SF | 1 | 6 | RB3 TE2 | QB C.J. Stroud (91.39) | 52.06 | 52.06 | - |
| 12T_ppr_SF | 1 | 7 | RB3 TE2 QB1 | QB Malik Willis (82.78) | 52.06 | 52.06 | - |
| 12T_ppr_SF | 1 | 8 | RB3 TE2 QB2 | WR Rome Odunze (13.43) | 44.05 | -58.53 | {'QB': -82.14, 'TE': -102.58, 'RB': -99.41} |
| 12T_ppr_SF | 1 | 9 | RB3 TE2 QB2 WR1 | WR Jordan Addison (6.52) | 44.05 | -58.53 | {'QB': -82.14, 'TE': -102.58, 'RB': -99.41} |
| 12T_ppr_SF | 1 | 10 | RB3 TE2 QB2 WR2 | WR Courtland Sutton (-10.53) | 37.0 | -55.32 | {'WR': -10.26, 'TE': -102.58, 'RB': -99.41} |
| 12T_ppr_SF | 1 | 11 | RB3 WR3 TE2 QB2 | WR Marvin Harrison (-15.95) | 52.4 | -50.18 | {'RB': -99.41, 'TE': -102.58} |
| 12T_ppr_SF | 1 | 12 | WR4 RB3 TE2 QB2 | WR Devaughn Vele (-49.08) | 66.61 | -50.18 | {'RB': -110.51, 'TE': -116.79} |
| 12T_ppr_SF | 1 | 13 | WR5 RB3 TE2 QB2 | WR KC Concepcion (-50.2) | 66.61 | -50.18 | {'RB': -110.51, 'TE': -116.79} |
| 12T_ppr_SF | 1 | 14 | WR6 RB3 TE2 QB2 | WR De'Zhaun Stribling (-81.42) | 92.76 | -50.18 | {'RB': -139.16, 'TE': -142.94} |
| 12T_ppr_SF | 1 | 15 | WR7 RB3 TE2 QB2 | WR Makai Lemon (-85.59) | 92.76 | -50.18 | {'RB': -139.16, 'TE': -142.94} |
| 12T_ppr_SF | 6 | 1 | - | RB Jonathan Taylor (184.79) | 52.4 | 52.4 | - |
| 12T_ppr_SF | 6 | 2 | RB1 | TE Brock Bowers (151.98) | 52.4 | 52.4 | - |
| 12T_ppr_SF | 6 | 3 | RB1 TE1 | TE Trey McBride (138.88) | 52.4 | 52.4 | - |
| 12T_ppr_SF | 6 | 4 | TE2 RB1 | RB Omarion Hampton (107.04) | 52.4 | 52.4 | - |
| 12T_ppr_SF | 6 | 5 | RB2 TE2 | TE Colston Loveland (101.75) | 52.4 | 52.4 | - |
| 12T_ppr_SF | 6 | 6 | TE3 RB2 | QB C.J. Stroud (91.4) | 56.28 | 56.28 | - |
| 12T_ppr_SF | 6 | 7 | TE3 RB2 QB1 | QB Malik Willis (82.88) | 55.87 | 55.87 | - |
| 12T_ppr_SF | 6 | 8 | TE3 RB2 QB2 | WR DJ Moore (12.56) | 52.94 | -54.51 | {'QB': -82.14, 'TE': -107.45, 'RB': -94.19} |
| 12T_ppr_SF | 6 | 9 | TE3 RB2 QB2 WR1 | WR Carnell Tate (4.6) | 48.92 | -58.53 | {'QB': -82.14, 'RB': -94.19, 'TE': -107.45} |
| 12T_ppr_SF | 6 | 10 | TE3 RB2 QB2 WR2 | WR Brian Thomas (-13.94) | 57.27 | -50.18 | {'RB': -94.19, 'QB': -82.14, 'TE': -107.45} |
| 12T_ppr_SF | 6 | 11 | TE3 WR3 RB2 QB2 | WR Wan'Dale Robinson (-24.39) | 57.27 | -50.18 | {'RB': -94.19, 'TE': -107.45} |
| 12T_ppr_SF | 6 | 12 | WR4 TE3 RB2 QB2 | WR Rashid Shaheed (-44.97) | 66.61 | -50.18 | {'RB': -103.11, 'TE': -116.79} |
| 12T_ppr_SF | 6 | 13 | WR5 TE3 RB2 QB2 | WR Cooper Kupp (-64.03) | 73.75 | -50.18 | {'TE': -123.93, 'RB': -115.23} |
| 12T_ppr_SF | 6 | 14 | WR6 TE3 RB2 QB2 | WR De'Zhaun Stribling (-79.93) | 92.76 | -50.18 | {'RB': -129.91, 'TE': -142.94} |
| 12T_ppr_SF | 6 | 15 | WR7 TE3 RB2 QB2 | WR Jordyn Tyson (-88.7) | 92.76 | -50.18 | {'RB': -140.46, 'TE': -142.94} |
| 12T_ppr_SF | 12 | 1 | - | TE Brock Bowers (151.72) | 52.4 | 52.4 | - |
| 12T_ppr_SF | 12 | 2 | TE1 | QB Brock Purdy (149.48) | 52.4 | 52.4 | - |
| 12T_ppr_SF | 12 | 3 | TE1 QB1 | RB Jeremiyah Love (119.45) | 52.4 | 52.4 | - |
| 12T_ppr_SF | 12 | 4 | TE1 QB1 RB1 | RB Kenneth Walker (108.2) | 52.4 | 52.4 | - |
| 12T_ppr_SF | 12 | 5 | RB2 TE1 QB1 | RB Javonte Williams (83.73) | 52.4 | 52.4 | - |
| 12T_ppr_SF | 12 | 6 | RB3 TE1 QB1 | QB Malik Willis (82.79) | 52.4 | 52.4 | - |
| 12T_ppr_SF | 12 | 7 | RB3 QB2 TE1 | TE George Kittle (56.41) | 49.73 | 49.73 | {'QB': -82.14} |
| 12T_ppr_SF | 12 | 8 | RB3 TE2 QB2 | WR Alec Pierce (19.8) | 49.73 | -12.11 | {'RB': -58.67, 'QB': -82.14, 'TE': -61.84} |
| 12T_ppr_SF | 12 | 9 | RB3 TE2 QB2 WR1 | WR Carnell Tate (4.57) | 44.05 | -17.79 | {'QB': -82.14, 'RB': -58.67, 'TE': -61.84} |
| 12T_ppr_SF | 12 | 10 | RB3 TE2 QB2 WR2 | WR Chris Godwin (-2.48) | 44.05 | -17.32 | {'WR': -0.47, 'QB': -82.14, 'RB': -58.67, 'TE': -61.84} |
| 12T_ppr_SF | 12 | 11 | RB3 WR3 TE2 QB2 | WR Tre Tucker (-41.8) | 52.4 | -9.44 | {'TE': -61.84, 'RB': -60.67} |
| 12T_ppr_SF | 12 | 12 | WR4 RB3 TE2 QB2 | WR Rashid Shaheed (-43.12) | 52.4 | -9.44 | {'TE': -61.84, 'RB': -60.67} |
| 12T_ppr_SF | 12 | 13 | WR5 RB3 TE2 QB2 | WR Cooper Kupp (-63.07) | 77.32 | -9.44 | {'RB': -76.74, 'TE': -86.76} |
| 12T_ppr_SF | 12 | 14 | WR6 RB3 TE2 QB2 | RB J.K. Dobbins (-75.97) | 77.32 | -9.44 | {'RB': -76.74, 'TE': -86.76} |
| 12T_ppr_SF | 12 | 15 | WR6 RB4 TE2 QB2 | WR Dontayvion Wicks (-100.93) | 110.92 | -9.44 | {'RB': -47.51, 'TE': -120.36} |

## Bench picks (beyond the starting slots) per seat: today vs fix, backstop OFF

| format | seat | BASE_OFF bench composition | FIX_OFF bench composition | FIX_OFF most-drafted bench position |
|---|---|---|---|---|
| 12T_ppr | 1 | TE6 | WR5 QB1 | ('WR', 5) |
| 12T_ppr | 6 | TE6 | WR6 | ('WR', 6) |
| 12T_ppr | 12 | RB3 TE1 WR1 QB1 | WR6 | ('WR', 6) |
| 12T_ppr_SF | 1 | TE5 WR1 | WR6 | ('WR', 6) |
| 12T_ppr_SF | 6 | TE6 | WR6 | ('WR', 6) |
| 12T_ppr_SF | 12 | TE4 QB1 WR1 | WR5 RB1 | ('WR', 5) |
