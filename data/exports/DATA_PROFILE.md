# SDGW 1914-1919 Data Profile for Multi-Parameter Search
Generated: 2026-02-16 19:20:58

## Purpose

This report profiles each searchable field to determine the best UI control
for multi-parameter search queries. Fields are analyzed for cardinality,
null rates, and value distributions.

## UI Control Recommendations

| UI Control | When to Use | Example Fields |
|---|---|---|
| **dropdown** | <= 50 unique values | Rank Group |
| **searchable_dropdown** | 51-500 unique values | Battalion, Rank |
| **autocomplete** | 501-5000 unique values | Birth Town, Death Location |
| **free_text_search** | > 5000 unique values | Surname, Christian Names |
| **date_range_picker** | Date fields | Death Date |

---

## Field Summary

| Table | Field | Unique Values | Null Rate | Suggested UI Control |
|---|---|---|---|---|
| OFFICERS | SURNAME | 12,448 | 0.0% | free_text_search |
| OFFICERS | CHRST_NAME | 23,520 | 0.0% | free_text_search |
| OFFICERS | INITIALS | 3,982 | 0.0% | autocomplete |
| OFFICERS | DECORATION | 69 | 90.7% | searchable_dropdown |
| OFFICERS | RANK | 508 | 0.0% | autocomplete |
| OFFICERS | RANK_ID | 7 | 0.0% | dropdown |
| OFFICERS | BAT_ID | 481 | 0.0% | searchable_dropdown |
| OFFICERS | DEATH_DATE | 1,901 | 0.0% | date_range_picker |
| OFFICERS | D_TRUEDATE | 1,769 | 0.0% | date_range_picker |
| OFFICERS | ADDNL_TEXT | 6,307 | 64.4% | free_text_search |
| SOLDIERS | SURNAME | 47,118 | 0.0% | free_text_search |
| SOLDIERS | CHRST_NAME | 56,832 | 0.0% | free_text_search |
| SOLDIERS | INITIALS | 4,447 | 0.0% | autocomplete |
| SOLDIERS | NUMBER | 250,816 | 0.0% | free_text_search |
| SOLDIERS | RANK | 538 | 0.1% | autocomplete |
| SOLDIERS | RANK_ID | 4 | 0.1% | dropdown |
| SOLDIERS | BAT_ID | 721 | 0.0% | autocomplete |
| SOLDIERS | BORN_TOWN | 85,373 | 10.8% | free_text_search |
| SOLDIERS | ENLST_LOC | 24,787 | 0.2% | free_text_search |
| SOLDIERS | ENLST_PLC | 53,611 | 51.7% | free_text_search |
| SOLDIERS | DEATH_DATE | 2,020 | 0.0% | date_range_picker |
| SOLDIERS | D_TRUEDATE | 1,934 | 0.0% | date_range_picker |
| SOLDIERS | DEATH_LOC | 137 | 0.1% | searchable_dropdown |
| SOLDIERS | ADDNL_TEXT | 120,260 | 78.9% | free_text_search |
| SD_RANKS | Rank Group | 4 | 0.0% | dropdown |
| SD_RANKS | Rank New | 114 | 0.0% | searchable_dropdown |
| SD_RANKS | Rank Original | 539 | 0.0% | autocomplete |
| SD_Battalions | Name | 720 | 0.1% | autocomplete |
| OD_Battalions | Name | 480 | 0.0% | searchable_dropdown |

---

## OFFICERS

### SURNAME

- **Total records:** 41,846
- **Non-empty:** 41,846
- **Empty/null:** 0 (0.0%)
- **Unique values:** 12,448 (cardinality: 29.75%)
- **Value length:** min=3, max=30, avg=6.6
- **Suggested UI control:** `free_text_search`

**Top 20 values:**

| Value | Count | % of Total |
|---|---|---|
| SMITH | 400 | 0.96% |
| JONES | 247 | 0.59% |
| BROWN | 245 | 0.59% |
| WILSON | 219 | 0.52% |
| TAYLOR | 218 | 0.52% |
| WILLIAMS | 204 | 0.49% |
| DAVIES | 148 | 0.35% |
| SCOTT | 139 | 0.33% |
| EVANS | 132 | 0.32% |
| HALL | 129 | 0.31% |
| ROBINSON | 129 | 0.31% |
| ANDERSON | 127 | 0.30% |
| WALKER | 126 | 0.30% |
| THOMAS | 125 | 0.30% |
| ROBERTSON | 120 | 0.29% |
| CAMPBELL | 118 | 0.28% |
| THOMPSON | 117 | 0.28% |
| WOOD | 114 | 0.27% |
| WATSON | 112 | 0.27% |
| WHITE | 111 | 0.27% |

### CHRST_NAME

- **Total records:** 41,846
- **Non-empty:** 41,846
- **Empty/null:** 0 (0.0%)
- **Unique values:** 23,520 (cardinality: 56.21%)
- **Value length:** min=1, max=61, avg=13.0
- **Suggested UI control:** `free_text_search`

**Top 20 values:**

| Value | Count | % of Total |
|---|---|---|
| JOHN | 611 | 1.46% |
| WILLIAM | 531 | 1.27% |
| JAMES | 373 | 0.89% |
| GEORGE | 270 | 0.65% |
| THOMAS | 243 | 0.58% |
| ROBERT | 235 | 0.56% |
| ARTHUR | 194 | 0.46% |
| FRANK | 169 | 0.40% |
| HAROLD | 168 | 0.40% |
| CHARLES | 162 | 0.39% |
| ALEXANDER | 141 | 0.34% |
| WILLIAM HENRY | 133 | 0.32% |
| HENRY | 126 | 0.30% |
| HARRY | 119 | 0.28% |
| EDWARD | 118 | 0.28% |
| HERBERT | 117 | 0.28% |
| DAVID | 109 | 0.26% |
| ERNEST | 107 | 0.26% |
| FREDERICK | 104 | 0.25% |
| JOSEPH | 104 | 0.25% |

### INITIALS

- **Total records:** 41,846
- **Non-empty:** 41,846
- **Empty/null:** 0 (0.0%)
- **Unique values:** 3,982 (cardinality: 9.52%)
- **Value length:** min=1, max=15, avg=3.0
- **Suggested UI control:** `autocomplete`

**Top 20 values:**

| Value | Count | % of Total |
|---|---|---|
| J | 1,166 | 2.79% |
| A | 790 | 1.89% |
| W | 738 | 1.76% |
| H | 728 | 1.74% |
| R | 580 | 1.39% |
| G | 509 | 1.22% |
| E | 436 | 1.04% |
| F | 421 | 1.01% |
| J H | 415 | 0.99% |
| C | 391 | 0.93% |
| W H | 382 | 0.91% |
| T | 320 | 0.76% |
| D | 307 | 0.73% |
| J A | 303 | 0.72% |
| J C | 278 | 0.66% |
| S | 278 | 0.66% |
| C H | 273 | 0.65% |
| J W | 271 | 0.65% |
| A C | 266 | 0.64% |
| G H | 264 | 0.63% |

### DECORATION

- **Total records:** 41,846
- **Non-empty:** 3,902
- **Empty/null:** 37,944 (90.7%)
- **Unique values:** 69 (cardinality: 0.16%)
- **Value length:** min=2, max=36, avg=2.7
- **Suggested UI control:** `searchable_dropdown`

**Top 20 values:**

| Value | Count | % of Total |
|---|---|---|
| MC | 2,679 | 6.40% |
| DSO | 577 | 1.38% |
| DSO, MC | 121 | 0.29% |
| MM | 82 | 0.20% |
| VC | 77 | 0.18% |
| DCM | 50 | 0.12% |
| CMG | 38 | 0.09% |
| MC & BAR | 32 | 0.08% |
| CMG, DSO | 29 | 0.07% |
| CB | 25 | 0.06% |
| MVO | 23 | 0.05% |
| MC, MM | 15 | 0.04% |
| VC, MC | 14 | 0.03% |
| OBE | 13 | 0.03% |
| MC, DCM | 12 | 0.03% |
| TD | 12 | 0.03% |
| VC, DSO | 8 | 0.02% |
| MBE | 8 | 0.02% |
| VC, DSO, MC | 8 | 0.02% |
| CB, CMG | 7 | 0.02% |

### RANK

- **Total records:** 41,846
- **Non-empty:** 41,837
- **Empty/null:** 9 (0.0%)
- **Unique values:** 508 (cardinality: 1.21%)
- **Value length:** min=2, max=26, avg=5.6
- **Suggested UI control:** `autocomplete`

**Top 20 values:**

| Value | Count | % of Total |
|---|---|---|
| 2/LT | 13,250 | 31.66% |
| LT | 6,577 | 15.72% |
| 2/LT (TP) | 5,827 | 13.92% |
| CAPT | 4,340 | 10.37% |
| LT (TP) | 1,941 | 4.64% |
| CAPT (TP) | 1,448 | 3.46% |
| TEMP 2/LT | 1,417 | 3.39% |
| MAJOR | 946 | 2.26% |
| T/2/LT | 711 | 1.70% |
| TEMP LT | 443 | 1.06% |
| T/LT | 381 | 0.91% |
| LT-COL | 351 | 0.84% |
| TEMP CAPT | 342 | 0.82% |
| T/CAPT | 246 | 0.59% |
| LT (A/CAPT) | 236 | 0.56% |
| T/LT (A/CAPT) | 203 | 0.49% |
| MAJOR (TP) | 185 | 0.44% |
| REV | 160 | 0.38% |
| LT (T/CAPT) | 151 | 0.36% |
| A/CAPT | 133 | 0.32% |

### RANK_ID

- **Total records:** 41,846
- **Non-empty:** 41,837
- **Empty/null:** 9 (0.0%)
- **Unique values:** 7 (cardinality: 0.02%)
- **Value length:** min=1, max=3, avg=1.0
- **Suggested UI control:** `dropdown`

**Top 20 values:**

| Value | Count | % of Total |
|---|---|---|
| 1 | 31,112 | 74.35% |
| 2 | 7,856 | 18.77% |
| 3 | 2,463 | 5.89% |
| 6 | 306 | 0.73% |
| 4 | 97 | 0.23% |
| 5 | 2 | 0.00% |
| 999 | 1 | 0.00% |

### BAT_ID

- **Total records:** 41,846
- **Non-empty:** 41,846
- **Empty/null:** 0 (0.0%)
- **Unique values:** 481 (cardinality: 1.15%)
- **Value length:** min=1, max=3, avg=2.1
- **Suggested UI control:** `searchable_dropdown`

**Top 20 values:**

| Value | Count | % of Total |
|---|---|---|
| 392 | 9,815 | 23.46% |
| 1 | 5,959 | 14.24% |
| 4 | 2,495 | 5.96% |
| 2 | 1,701 | 4.06% |
| 3 | 1,378 | 3.29% |
| 226 | 1,295 | 3.09% |
| 225 | 1,233 | 2.95% |
| 8 | 1,059 | 2.53% |
| 17 | 999 | 2.39% |
| 19 | 996 | 2.38% |
| 18 | 989 | 2.36% |
| 16 | 971 | 2.32% |
| 12 | 840 | 2.01% |
| 5 | 790 | 1.89% |
| 220 | 661 | 1.58% |
| 221 | 608 | 1.45% |
| 10 | 590 | 1.41% |
| 9 | 558 | 1.33% |
| 6 | 520 | 1.24% |
| 15 | 389 | 0.93% |

### DEATH_DATE

- **Total records:** 41,846
- **Non-empty:** 41,846
- **Empty/null:** 0 (0.0%)
- **Unique values:** 1,901 (cardinality: 4.54%)
- **Value length:** min=8, max=14, avg=8.0
- **Suggested UI control:** `date_range_picker`

**Top 20 values:**

| Value | Count | % of Total |
|---|---|---|
| 01/07/16 | 1,005 | 2.40% |
| 25/09/15 | 507 | 1.21% |
| 21/03/18 | 502 | 1.20% |
| 31/07/17 | 390 | 0.93% |
| 03/05/17 | 323 | 0.77% |
| 23/04/17 | 314 | 0.75% |
| 22/03/18 | 299 | 0.71% |
| 15/09/16 | 252 | 0.60% |
| 24/03/18 | 229 | 0.55% |
| 16/08/17 | 227 | 0.54% |
| 09/05/15 | 225 | 0.54% |
| 09/04/17 | 223 | 0.53% |
| 20/09/17 | 208 | 0.50% |
| 23/03/18 | 205 | 0.49% |
| 30/11/17 | 204 | 0.49% |
| 09/10/17 | 202 | 0.48% |
| 27/05/18 | 202 | 0.48% |
| 28/03/18 | 194 | 0.46% |
| 03/09/16 | 187 | 0.45% |
| 20/11/17 | 171 | 0.41% |

### D_TRUEDATE

- **Total records:** 41,846
- **Non-empty:** 41,846
- **Empty/null:** 0 (0.0%)
- **Unique values:** 1,769 (cardinality: 4.23%)
- **Value length:** min=17, max=17, avg=17.0
- **Suggested UI control:** `date_range_picker`

**Top 20 values:**

| Value | Count | % of Total |
|---|---|---|
| 07/01/16 00:00:00 | 1,005 | 2.40% |
| 09/25/15 00:00:00 | 507 | 1.21% |
| 03/21/18 00:00:00 | 502 | 1.20% |
| 07/31/17 00:00:00 | 390 | 0.93% |
| 05/03/17 00:00:00 | 323 | 0.77% |
| 04/23/17 00:00:00 | 314 | 0.75% |
| 03/22/18 00:00:00 | 302 | 0.72% |
| 09/15/16 00:00:00 | 252 | 0.60% |
| 03/24/18 00:00:00 | 229 | 0.55% |
| 08/16/17 00:00:00 | 227 | 0.54% |
| 05/09/15 00:00:00 | 225 | 0.54% |
| 04/09/17 00:00:00 | 223 | 0.53% |
| 03/23/18 00:00:00 | 213 | 0.51% |
| 09/20/17 00:00:00 | 208 | 0.50% |
| 11/30/17 00:00:00 | 204 | 0.49% |
| 10/09/17 00:00:00 | 202 | 0.48% |
| 05/27/18 00:00:00 | 202 | 0.48% |
| 03/28/18 00:00:00 | 195 | 0.47% |
| 09/03/16 00:00:00 | 187 | 0.45% |
| 11/20/17 00:00:00 | 171 | 0.41% |

### ADDNL_TEXT

- **Total records:** 41,846
- **Non-empty:** 14,909
- **Empty/null:** 26,937 (64.4%)
- **Unique values:** 6,307 (cardinality: 15.07%)
- **Value length:** min=2, max=54, avg=13.7
- **Suggested UI control:** `free_text_search`

**Top 20 values:**

| Value | Count | % of Total |
|---|---|---|
| [Territorial]  | 956 | 2.28% |
| (AND R F C) | 496 | 1.19% |
| (AND R A F) | 443 | 1.06% |
| (GEN LIST) | 351 | 0.84% |
| (ATT 2/BN) | 219 | 0.52% |
| (ATT 1ST BN) | 184 | 0.44% |
| (ATT 2 BN) | 183 | 0.44% |
| (ATT 2ND BN) | 173 | 0.41% |
| (ATT 1/BN) | 154 | 0.37% |
| (ATT R F C) | 135 | 0.32% |
| (ATT 1 BN) | 133 | 0.32% |
| (IN GERMAN HANDS) | 116 | 0.28% |
| (AND M G C) | 108 | 0.26% |
| (ATT M G C) | 87 | 0.21% |
| (ATT 9 BN) | 87 | 0.21% |
| (P OF W) | 78 | 0.19% |
| (ATT 8/BN) | 78 | 0.19% |
| (ATT R A F) | 75 | 0.18% |
| (R F C) | 74 | 0.18% |
| (ATT 9/BN) | 73 | 0.17% |

## SOLDIERS

### SURNAME

- **Total records:** 661,960
- **Non-empty:** 661,960
- **Empty/null:** 0 (0.0%)
- **Unique values:** 47,118 (cardinality: 7.12%)
- **Value length:** min=2, max=24, avg=6.3
- **Suggested UI control:** `free_text_search`

**Top 20 values:**

| Value | Count | % of Total |
|---|---|---|
| SMITH | 9,802 | 1.48% |
| JONES | 5,785 | 0.87% |
| BROWN | 4,653 | 0.70% |
| TAYLOR | 4,174 | 0.63% |
| WILLIAMS | 3,671 | 0.55% |
| WILSON | 3,237 | 0.49% |
| DAVIES | 2,630 | 0.40% |
| JOHNSON | 2,394 | 0.36% |
| EVANS | 2,268 | 0.34% |
| WALKER | 2,267 | 0.34% |
| WHITE | 2,210 | 0.33% |
| WRIGHT | 2,197 | 0.33% |
| THOMPSON | 2,129 | 0.32% |
| ROBERTS | 2,061 | 0.31% |
| ROBINSON | 2,008 | 0.30% |
| WOOD | 1,963 | 0.30% |
| HALL | 1,963 | 0.30% |
| GREEN | 1,925 | 0.29% |
| TURNER | 1,896 | 0.29% |
| CLARK | 1,887 | 0.29% |

### CHRST_NAME

- **Total records:** 661,960
- **Non-empty:** 661,932
- **Empty/null:** 28 (0.0%)
- **Unique values:** 56,832 (cardinality: 8.59%)
- **Value length:** min=1, max=45, avg=8.8
- **Suggested UI control:** `free_text_search`

**Top 20 values:**

| Value | Count | % of Total |
|---|---|---|
| WILLIAM | 41,191 | 6.22% |
| JOHN | 37,704 | 5.70% |
| JAMES | 27,890 | 4.21% |
| THOMAS | 22,704 | 3.43% |
| GEORGE | 22,199 | 3.35% |
| ROBERT | 12,753 | 1.93% |
| CHARLES | 12,185 | 1.84% |
| JOSEPH | 12,000 | 1.81% |
| ARTHUR | 11,950 | 1.81% |
| HARRY | 11,437 | 1.73% |
| ALBERT | 9,316 | 1.41% |
| FREDERICK | 9,162 | 1.38% |
| FRANK | 8,698 | 1.31% |
| EDWARD | 8,326 | 1.26% |
| HENRY | 8,209 | 1.24% |
| ERNEST | 8,071 | 1.22% |
| ALFRED | 7,866 | 1.19% |
| WALTER | 7,320 | 1.11% |
| HERBERT | 5,895 | 0.89% |
| DAVID | 5,584 | 0.84% |

### INITIALS

- **Total records:** 661,960
- **Non-empty:** 661,932
- **Empty/null:** 28 (0.0%)
- **Unique values:** 4,447 (cardinality: 0.67%)
- **Value length:** min=1, max=11, avg=1.8
- **Suggested UI control:** `autocomplete`

**Top 20 values:**

| Value | Count | % of Total |
|---|---|---|
| J | 81,299 | 12.28% |
| W | 51,821 | 7.83% |
| A | 43,508 | 6.57% |
| H | 35,135 | 5.31% |
| T | 25,156 | 3.80% |
| F | 25,067 | 3.79% |
| G | 24,220 | 3.66% |
| R | 22,229 | 3.36% |
| E | 21,827 | 3.30% |
| C | 17,199 | 2.60% |
| S | 12,841 | 1.94% |
| P | 11,234 | 1.70% |
| D | 10,711 | 1.62% |
| J W | 7,910 | 1.19% |
| M | 7,242 | 1.09% |
| W H | 7,008 | 1.06% |
| W J | 6,702 | 1.01% |
| A E | 6,210 | 0.94% |
| J H | 5,970 | 0.90% |
| L | 5,828 | 0.88% |

### NUMBER

- **Total records:** 661,960
- **Non-empty:** 661,844
- **Empty/null:** 116 (0.0%)
- **Unique values:** 250,816 (cardinality: 37.89%)
- **Value length:** min=1, max=14, avg=5.3
- **Suggested UI control:** `free_text_search`

**Top 20 values:**

| Value | Count | % of Total |
|---|---|---|
| 2206 | 37 | 0.01% |
| 1883 | 37 | 0.01% |
| 2121 | 36 | 0.01% |
| 2535 | 35 | 0.01% |
| 1829 | 34 | 0.01% |
| 2250 | 34 | 0.01% |
| 2426 | 34 | 0.01% |
| 2192 | 33 | 0.00% |
| 2329 | 33 | 0.00% |
| 2010 | 33 | 0.00% |
| 2306 | 32 | 0.00% |
| 2399 | 32 | 0.00% |
| 2558 | 32 | 0.00% |
| 2176 | 32 | 0.00% |
| 2270 | 32 | 0.00% |
| 2092 | 32 | 0.00% |
| 1598 | 32 | 0.00% |
| 1473 | 31 | 0.00% |
| 2089 | 31 | 0.00% |
| 1975 | 31 | 0.00% |

### RANK

- **Total records:** 661,960
- **Non-empty:** 661,179
- **Empty/null:** 781 (0.1%)
- **Unique values:** 538 (cardinality: 0.08%)
- **Value length:** min=3, max=29, avg=6.6
- **Suggested UI control:** `autocomplete`

**Top 20 values:**

| Value | Count | % of Total |
|---|---|---|
| PRIVATE | 447,685 | 67.63% |
| L/CPL | 46,771 | 7.07% |
| RIFLEMAN | 34,621 | 5.23% |
| GUNNER | 25,029 | 3.78% |
| SERGT. | 24,495 | 3.70% |
| CPL. | 23,315 | 3.52% |
| DVR. | 9,991 | 1.51% |
| SPR. | 9,910 | 1.50% |
| GDSN. | 5,854 | 0.88% |
| A/CPL. | 5,250 | 0.79% |
| L/SGT | 4,867 | 0.74% |
| A/SGT. | 3,503 | 0.53% |
| BDR. | 2,479 | 0.37% |
| C.S.M. | 2,059 | 0.31% |
| PIONEER | 1,891 | 0.29% |
| A/L/CPL. | 1,560 | 0.24% |
| A/BDR. | 1,502 | 0.23% |
| RFN. (L/CORP.) | 957 | 0.14% |
| TPR. | 629 | 0.10% |
| DRUMMER | 607 | 0.09% |

### RANK_ID

- **Total records:** 661,960
- **Non-empty:** 661,178
- **Empty/null:** 782 (0.1%)
- **Unique values:** 4 (cardinality: 0.00%)
- **Value length:** min=1, max=1, avg=1.0
- **Suggested UI control:** `dropdown`

**Top 20 values:**

| Value | Count | % of Total |
|---|---|---|
| 1 | 538,520 | 81.35% |
| 2 | 83,843 | 12.67% |
| 3 | 35,250 | 5.33% |
| 4 | 3,565 | 0.54% |

### BAT_ID

- **Total records:** 661,960
- **Non-empty:** 661,960
- **Empty/null:** 0 (0.0%)
- **Unique values:** 721 (cardinality: 0.11%)
- **Value length:** min=1, max=3, avg=3.0
- **Suggested UI control:** `autocomplete`

**Top 20 values:**

| Value | Count | % of Total |
|---|---|---|
| 807 | 78,930 | 11.92% |
| 109 | 78,536 | 11.86% |
| 110 | 74,054 | 11.19% |
| 115 | 29,462 | 4.45% |
| 116 | 25,693 | 3.88% |
| 114 | 24,957 | 3.77% |
| 117 | 24,333 | 3.68% |
| 118 | 21,068 | 3.18% |
| 120 | 18,088 | 2.73% |
| 112 | 16,333 | 2.47% |
| 753 | 14,140 | 2.14% |
| 113 | 13,968 | 2.11% |
| 121 | 11,933 | 1.80% |
| 122 | 9,819 | 1.48% |
| 163 | 8,552 | 1.29% |
| 157 | 8,237 | 1.24% |
| 159 | 8,114 | 1.23% |
| 111 | 7,601 | 1.15% |
| 162 | 7,103 | 1.07% |
| 187 | 6,303 | 0.95% |

### BORN_TOWN

- **Total records:** 661,960
- **Non-empty:** 590,711
- **Empty/null:** 71,249 (10.8%)
- **Unique values:** 85,373 (cardinality: 12.90%)
- **Value length:** min=3, max=80, avg=15.2
- **Suggested UI control:** `free_text_search`

**Top 20 values:**

| Value | Count | % of Total |
|---|---|---|
| LIVERPOOL | 8,994 | 1.36% |
| BIRMINGHAM | 7,579 | 1.14% |
| MANCHESTER | 7,118 | 1.08% |
| GLASGOW | 6,520 | 0.98% |
| LEEDS | 4,755 | 0.72% |
| EDINBURGH | 3,883 | 0.59% |
| HULL | 3,463 | 0.52% |
| NOTTINGHAM | 3,365 | 0.51% |
| DUBLIN | 3,279 | 0.50% |
| SHEFFIELD | 2,918 | 0.44% |
| LONDON | 2,877 | 0.43% |
| LEICESTER | 2,440 | 0.37% |
| NEWCASTLE-ON-TYNE | 2,273 | 0.34% |
| SALFORD, LANCS | 2,245 | 0.34% |
| SUNDERLAND | 1,992 | 0.30% |
| BRADFORD, YORKS | 1,914 | 0.29% |
| BRADFORD | 1,854 | 0.28% |
| BRISTOL | 1,695 | 0.26% |
| DUNDEE | 1,664 | 0.25% |
| BLACKBURN, LANCS | 1,584 | 0.24% |

### ENLST_LOC

- **Total records:** 661,960
- **Non-empty:** 660,445
- **Empty/null:** 1,515 (0.2%)
- **Unique values:** 24,787 (cardinality: 3.74%)
- **Value length:** min=3, max=100, avg=11.9
- **Suggested UI control:** `free_text_search`

**Top 20 values:**

| Value | Count | % of Total |
|---|---|---|
| LONDON  | 21,592 | 3.26% |
| GLASGOW | 12,040 | 1.82% |
| MANCHESTER | 10,874 | 1.64% |
| BIRMINGHAM | 8,369 | 1.26% |
| LIVERPOOL  | 8,353 | 1.26% |
| MANCHESTER  | 7,545 | 1.14% |
| LONDON | 7,456 | 1.13% |
| BIRMINGHAM  | 6,333 | 0.96% |
| SHEFFIELD | 6,157 | 0.93% |
| NEWCASTLE-ON-TYNE | 5,637 | 0.85% |
| LEEDS | 5,564 | 0.84% |
| LIVERPOOL | 5,150 | 0.78% |
| EDINBURGH | 4,759 | 0.72% |
| BRISTOL | 4,704 | 0.71% |
| HULL | 4,284 | 0.65% |
| GLASGOW  | 4,199 | 0.63% |
| BELFAST | 3,610 | 0.55% |
| LEICESTER | 3,516 | 0.53% |
| NOTTINGHAM | 3,439 | 0.52% |
| EDINBURGH  | 3,164 | 0.48% |

### ENLST_PLC

- **Total records:** 661,960
- **Non-empty:** 319,617
- **Empty/null:** 342,343 (51.7%)
- **Unique values:** 53,611 (cardinality: 8.10%)
- **Value length:** min=2, max=49, avg=13.3
- **Suggested UI control:** `free_text_search`

**Top 20 values:**

| Value | Count | % of Total |
|---|---|---|
| LIVERPOOL | 6,013 | 0.91% |
| GLASGOW | 2,928 | 0.44% |
| MANCHESTER | 2,346 | 0.35% |
| BIRMINGHAM | 2,280 | 0.34% |
| EDINBURGH | 1,862 | 0.28% |
| LEEDS | 1,406 | 0.21% |
| LONDON | 1,346 | 0.20% |
| ISLINGTON | 1,035 | 0.16% |
| BATTERSEA | 1,010 | 0.15% |
| WALTHAMSTOW | 970 | 0.15% |
| FULHAM | 915 | 0.14% |
| DUBLIN | 907 | 0.14% |
| SHEFFIELD | 853 | 0.13% |
| BRADFORD | 831 | 0.13% |
| BERMONDSEY | 824 | 0.12% |
| BELFAST | 811 | 0.12% |
| CAMBERWELL | 740 | 0.11% |
| NOTTINGHAM | 705 | 0.11% |
| BETHNAL GREEN | 701 | 0.11% |
| BRISTOL | 699 | 0.11% |

### DEATH_DATE

- **Total records:** 661,960
- **Non-empty:** 661,877
- **Empty/null:** 83 (0.0%)
- **Unique values:** 2,020 (cardinality: 0.31%)
- **Value length:** min=7, max=29, avg=8.0
- **Suggested UI control:** `date_range_picker`

**Top 20 values:**

| Value | Count | % of Total |
|---|---|---|
| 01/07/16 | 17,227 | 2.60% |
| 25/09/15 | 9,151 | 1.38% |
| 21/03/18 | 7,454 | 1.13% |
| 31/07/17 | 5,633 | 0.85% |
| 03/05/17 | 5,547 | 0.84% |
| 15/09/16 | 4,715 | 0.71% |
| 23/04/17 | 4,256 | 0.64% |
| 09/04/17 | 3,888 | 0.59% |
| 09/05/15 | 3,709 | 0.56% |
| 16/08/17 | 3,496 | 0.53% |
| 22/03/18 | 3,479 | 0.53% |
| 03/09/16 | 3,360 | 0.51% |
| 20/09/17 | 3,163 | 0.48% |
| 28/03/18 | 3,123 | 0.47% |
| 04/10/17 | 2,945 | 0.44% |
| 09/10/17 | 2,909 | 0.44% |
| 30/11/17 | 2,859 | 0.43% |
| 23/03/18 | 2,807 | 0.42% |
| 26/10/17 | 2,485 | 0.38% |
| 28/04/17 | 2,396 | 0.36% |

### D_TRUEDATE

- **Total records:** 661,960
- **Non-empty:** 661,874
- **Empty/null:** 86 (0.0%)
- **Unique values:** 1,934 (cardinality: 0.29%)
- **Value length:** min=17, max=17, avg=17.0
- **Suggested UI control:** `date_range_picker`

**Top 20 values:**

| Value | Count | % of Total |
|---|---|---|
| 07/01/16 00:00:00 | 17,234 | 2.60% |
| 09/25/15 00:00:00 | 9,154 | 1.38% |
| 03/21/18 00:00:00 | 7,457 | 1.13% |
| 07/31/17 00:00:00 | 5,633 | 0.85% |
| 05/03/17 00:00:00 | 5,547 | 0.84% |
| 09/15/16 00:00:00 | 4,719 | 0.71% |
| 04/23/17 00:00:00 | 4,271 | 0.65% |
| 04/09/17 00:00:00 | 3,888 | 0.59% |
| 05/09/15 00:00:00 | 3,709 | 0.56% |
| 08/16/17 00:00:00 | 3,497 | 0.53% |
| 03/22/18 00:00:00 | 3,480 | 0.53% |
| 09/03/16 00:00:00 | 3,360 | 0.51% |
| 09/20/17 00:00:00 | 3,163 | 0.48% |
| 03/28/18 00:00:00 | 3,123 | 0.47% |
| 10/04/17 00:00:00 | 2,945 | 0.44% |
| 10/09/17 00:00:00 | 2,909 | 0.44% |
| 11/30/17 00:00:00 | 2,859 | 0.43% |
| 03/23/18 00:00:00 | 2,812 | 0.42% |
| 10/26/17 00:00:00 | 2,485 | 0.38% |
| 04/28/17 00:00:00 | 2,396 | 0.36% |

### DEATH_LOC

- **Total records:** 661,960
- **Non-empty:** 661,236
- **Empty/null:** 724 (0.1%)
- **Unique values:** 137 (cardinality: 0.02%)
- **Value length:** min=4, max=35, avg=15.5
- **Suggested UI control:** `searchable_dropdown`

**Top 20 values:**

| Value | Count | % of Total |
|---|---|---|
| France & Flanders | 552,471 | 83.46% |
| Home | 32,554 | 4.92% |
| Gallipoli | 18,779 | 2.84% |
| Mesopotamia | 12,511 | 1.89% |
| Egypt | 9,069 | 1.37% |
| Salonika | 6,438 | 0.97% |
| British Expeditionary Force | 5,969 | 0.90% |
| At Sea | 4,521 | 0.68% |
| Palestine | 3,279 | 0.50% |
| India | 2,711 | 0.41% |
| Balkans | 2,000 | 0.30% |
| E.E.F. | 1,718 | 0.26% |
| Persian Gulf | 1,604 | 0.24% |
| Dardanelles | 1,453 | 0.22% |
| Italy | 1,262 | 0.19% |
| East Africa | 757 | 0.11% |
| Germany | 569 | 0.09% |
| Malta | 542 | 0.08% |
| Mediterranean | 462 | 0.07% |
| Mesopotamian Expeditionary Force | 455 | 0.07% |

### ADDNL_TEXT

- **Total records:** 661,960
- **Non-empty:** 139,630
- **Empty/null:** 522,330 (78.9%)
- **Unique values:** 120,260 (cardinality: 18.17%)
- **Value length:** min=2, max=125, avg=29.6
- **Suggested UI control:** `free_text_search`

**Top 20 values:**

| Value | Count | % of Total |
|---|---|---|
| M.M. | 5,734 | 0.87% |
| D.C.M. | 1,452 | 0.22% |
| OR SINCE. | 339 | 0.05% |
| (I.W.T., R.E.). | 104 | 0.02% |
| (126TH FIELD COY., R.E.). | 104 | 0.02% |
| D.C.M., M.M. | 92 | 0.01% |
| (1/3RD KENT FIELD COY., R.E.). | 88 | 0.01% |
| (12TH FIELD COY., R.E.). | 86 | 0.01% |
| (56TH FIELD COY., R.E.). | 83 | 0.01% |
| (2ND FIELD COY., R.E.). | 79 | 0.01% |
| (7TH FIELD COY., R.E.). | 78 | 0.01% |
| (BASE SIGNAL DEPOT, R.E.). | 76 | 0.01% |
| (130TH FIELD COY., R.E.). | 76 | 0.01% |
| (72ND FIELD COY., R.E.). | 75 | 0.01% |
| (Listed as serving at the time of death with the above batta... | 73 | 0.01% |
| (175TH TUNN. COY., R.E.). | 73 | 0.01% |
| POSTED 2/4TH LONDON REGT. | 72 | 0.01% |
| (11TH FIELD COY., R.E.). | 71 | 0.01% |
| (97TH FIELD COY., R.E.). | 70 | 0.01% |
| (90TH FIELD COY., R.E.). | 66 | 0.01% |

## SD_RANKS

### Rank Group

- **Total records:** 547
- **Non-empty:** 547
- **Empty/null:** 0 (0.0%)
- **Unique values:** 4 (cardinality: 0.73%)
- **Value length:** min=8, max=16, avg=10.4
- **Suggested UI control:** `dropdown`

**Top 20 values:**

| Value | Count | % of Total |
|---|---|---|
| Sergeants | 203 | 37.11% |
| Warrant Officers | 123 | 22.49% |
| Corporals | 119 | 21.76% |
| Privates | 102 | 18.65% |

### Rank New

- **Total records:** 547
- **Non-empty:** 547
- **Empty/null:** 0 (0.0%)
- **Unique values:** 114 (cardinality: 20.84%)
- **Value length:** min=3, max=36, avg=15.9
- **Suggested UI control:** `searchable_dropdown`

**Top 20 values:**

| Value | Count | % of Total |
|---|---|---|
| Sergeant | 34 | 6.22% |
| Corporal | 32 | 5.85% |
| Company Sergeant Major | 24 | 4.39% |
| Lance Corporal | 23 | 4.20% |
| Quarter Master Sergeant | 23 | 4.20% |
| Staff Sergeant | 19 | 3.47% |
| Sergeant Major | 19 | 3.47% |
| Lance Sergeant | 17 | 3.11% |
| Regimental Sergeant Major | 16 | 2.93% |
| Colour Sergeant | 15 | 2.74% |
| Staff Sergeant Major | 15 | 2.74% |
| Bombardier | 14 | 2.56% |
| Lance Bombardier | 12 | 2.19% |
| Shoeing Smith | 10 | 1.83% |
| Private | 9 | 1.65% |
| Signaller | 9 | 1.65% |
| Shoeing Smith Corporal | 9 | 1.65% |
| Company Quarter Master Sergeant | 9 | 1.65% |
| Drummer | 8 | 1.46% |
| Farrier Quarter Master Sergeant | 8 | 1.46% |

### Rank Original

- **Total records:** 547
- **Non-empty:** 547
- **Empty/null:** 0 (0.0%)
- **Unique values:** 539 (cardinality: 98.54%)
- **Value length:** min=3, max=29, avg=9.6
- **Suggested UI control:** `autocomplete`

**Top 20 values:**

| Value | Count | % of Total |
|---|---|---|
| SADDLER | 2 | 0.37% |
| CPL. | 2 | 0.37% |
| SADDLER-CPL. | 2 | 0.37% |
| A/C.S.M. | 2 | 0.37% |
| C.S.M. | 2 | 0.37% |
| R.Q.M.S. | 2 | 0.37% |
| A/R.S.M. | 2 | 0.37% |
| R.S.M. | 2 | 0.37% |
| ARMR./PTE. | 1 | 0.18% |
| ARTIFICER | 1 | 0.18% |
| BAND BOY | 1 | 0.18% |
| BANDSMAN | 1 | 0.18% |
| BDN. | 1 | 0.18% |
| BOY | 1 | 0.18% |
| BGLR | 1 | 0.18% |
| BGR | 1 | 0.18% |
| BUGLER | 1 | 0.18% |
| BUGLR. | 1 | 0.18% |
| CADET | 1 | 0.18% |
| CYCLIST | 1 | 0.18% |

## SD_Battalions

### Name

- **Total records:** 721
- **Non-empty:** 720
- **Empty/null:** 1 (0.1%)
- **Unique values:** 720 (cardinality: 99.86%)
- **Value length:** min=5, max=76, avg=29.5
- **Suggested UI control:** `autocomplete`

**Top 20 values:**

| Value | Count | % of Total |
|---|---|---|
| 78th Training Reserve Battalion. | 1 | 0.14% |
| 79th Training Reserve Battalion. | 1 | 0.14% |
| 3rd (Reserve) Battalion. | 1 | 0.14% |
| 4th (Reserve) Battalion Seaforth Highlanders. | 1 | 0.14% |
| 5th Battalion Seaforth Highlanders. | 1 | 0.14% |
| 39th T.R. Battalion. | 1 | 0.14% |
| 4th Garrison Battalion. | 1 | 0.14% |
| 5th Garrison Battalion. | 1 | 0.14% |
| 6th Garrison Battalion. | 1 | 0.14% |
| 5/6th Battalion. | 1 | 0.14% |
| 3/7th Battalion. | 1 | 0.14% |
| 1/1st Welsh Horse, Yeomanry. | 1 | 0.14% |
| 2/1st Welsh Horse Yeomanry. | 1 | 0.14% |
| 5th Battalion Super. Co. | 1 | 0.14% |
| 7/8th Battalion. | 1 | 0.14% |
| 11th Garrison Battalion. | 1 | 0.14% |
| Indian Depot. | 1 | 0.14% |
| 1/4 Battalion. | 1 | 0.14% |
| 1/1st Bucks Battalion. | 1 | 0.14% |
| 2/1st Bucks Battalion. | 1 | 0.14% |

## OD_Battalions

### Name

- **Total records:** 480
- **Non-empty:** 480
- **Empty/null:** 0 (0.0%)
- **Unique values:** 480 (cardinality: 100.00%)
- **Value length:** min=3, max=78, avg=19.1
- **Suggested UI control:** `searchable_dropdown`

**Top 20 values:**

| Value | Count | % of Total |
|---|---|---|
| Battalion Not Shown | 1 | 0.21% |
| 1st Battalion | 1 | 0.21% |
| 2nd Battalion | 1 | 0.21% |
| 3rd Battalion | 1 | 0.21% |
| 4th Battalion | 1 | 0.21% |
| 5th Battalion | 1 | 0.21% |
| 2/1 Battalion | 1 | 0.21% |
| 9th Battalion | 1 | 0.21% |
| 13th Battalion | 1 | 0.21% |
| 12th Battalion | 1 | 0.21% |
| 16th Battalion | 1 | 0.21% |
| 11th Battalion | 1 | 0.21% |
| 14th Battalion | 1 | 0.21% |
| 17th Battalion | 1 | 0.21% |
| 15th Battalion | 1 | 0.21% |
| 7th Battalion | 1 | 0.21% |
| 10th Battalion | 1 | 0.21% |
| 6th Battalion | 1 | 0.21% |
| 8th Battalion | 1 | 0.21% |
| 20th Battalion | 1 | 0.21% |

---

## Multi-Parameter Search UI Recommendations

Based on the data profile above, the search UI should include:

### Primary Search Fields
1. **Surname** (free text) - high cardinality, primary search vector
2. **Christian/First Name** (free text) - high cardinality, refinement
3. **Service Number** (free text) - exact lookup for soldiers

### Filter Dropdowns
4. **Rank** (searchable dropdown) - medium cardinality from ranks table
5. **Battalion** (searchable dropdown) - medium cardinality from battalions
6. **Rank Group** (dropdown) - low cardinality grouping

### Location Filters
7. **Birth Town** (autocomplete) - medium-high cardinality
8. **Enlistment Location** (autocomplete) - medium-high cardinality
9. **Death Location** (autocomplete) - medium cardinality

### Date Filters
10. **Death Date** (date range picker) - allow from/to range

### Record Type
11. **Officer/Soldier toggle** - binary filter

### Query Behavior
- All filters are AND-combined (narrowing)
- Empty filters are ignored (show all)
- Case-insensitive text matching
- Partial matching on text fields (LIKE prefix%)
- Exact matching on dropdowns and service number
