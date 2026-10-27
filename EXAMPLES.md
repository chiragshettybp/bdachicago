# Real Chicago 311 Examples — Instant Reference

Real values from the [311 Service Requests dataset](https://data.cityofchicago.org/Service-Requests/311-Service-Requests/v6vf-nfxy/about_data).
Counts are from the Socrata metadata snapshot (dataset keeps growing; proportions matter more than exact numbers).

## Dataset facts

- 14.9M rows, 39 columns; each row is one service request (`SR_NUMBER` is unique)
- New 311 system launched **12/18/2018**; legacy records flagged in `LEGACY_RECORD`
- Requests date from **2018-07-01** onward
- 311 INFORMATION ONLY CALLS are usually entered with the 311 Center's address

## Top 20 real request types (SR_TYPE → SR_SHORT_CODE → OWNER_DEPARTMENT)

| # | SR_TYPE | Short code | Owner department | Real count |
|---|---|---|---|---|
| 1 | 311 INFORMATION ONLY CALL | 311IOC | 311 City Services | 4,921,249 |
| 2 | Aircraft Noise Complaint | AVN | Aviation | 2,389,257 |
| 3 | Graffiti Removal Request | GRAF | Streets and Sanitation | 679,929 |
| 4 | Pothole in Street Complaint | PHF | CDOT - Department of Transportation | 405,198 |
| 5 | Street Light Out Complaint | SFD | CDOT - Department of Transportation | 383,743 |
| 6 | Garbage Cart Maintenance | SIE | Streets and Sanitation | 365,054 |
| 7 | Rodent Baiting/Rat Complaint | SGA | Streets and Sanitation | 360,908 |
| 8 | Abandoned Vehicle Complaint | SKA | Streets and Sanitation | 312,633 |
| 9 | Tree Trim Request (NO LONGER BEING ACCEPTED) | SEF | Streets and Sanitation | 295,013 |
| 10 | Tree Debris Clean-Up Request | SEL | Streets and Sanitation | 191,042 |
| 11 | Weed Removal Request | SCP | Streets and Sanitation | 190,997 |
| 12 | Traffic Signal Out Complaint | SFB | CDOT - Department of Transportation | 176,755 |
| 13 | Building Violation | BBA | DOB - Buildings | 158,130 |
| 14 | Sign Repair Request - All Other Signs | PCE | CDOT - Department of Transportation | 151,149 |
| 15 | Blue Recycling Cart | SRRC | Streets and Sanitation | 144,786 |
| 16 | Tree Emergency | SEC | Streets and Sanitation | 140,044 |
| 17 | Tree Removal Inspection | SEE | Streets and Sanitation | 133,579 |
| 18 | Water Lead Test Kit Request | WCA2 | DWM - Department of Water Management | 110,504 |
| 19 | Sanitation Code Violation | SCB | Streets and Sanitation | 105,107 |
| 20 | Dead Animal Pick-Up Request | SGQ | Streets and Sanitation | 101,460 |

## Real owner departments

| Department | Real count |
|---|---|
| 311 City Services | 4,921,249 |
| Streets and Sanitation | 3,551,640 |
| Aviation | 2,389,257 |
| CDOT - Department of Transportation | 1,577,392 |
| DWM - Department of Water Management | 571,160 |
| DOB - Buildings | 299,779 |
| Animal Care and Control | 267,542 |
| BACP - Business Affairs and Consumer Protection | 93,210 |
| Finance | 43,912 |
| Outside Agencies | 26,439 |
| Health | 25,924 |
| City Clerk's Office | 23,449 |
| Department of Housing | 2,305 |
| Fire | 2,272 |

## Real statuses

| Status | Real count |
|---|---|
| Completed | 13,396,331 (~97%) |
| Open | 203,948 (~1.5%) |
| Canceled | 197,921 (~1.4%) |

## Real origins

| Origin | Real count |
|---|---|
| Phone Call | 7,877,036 (~57%) |
| Internet | 3,737,762 (~27%) |
| Mobile Device | 1,049,664 (~7.6%) |
| Mass Entry | 527,547 |
| Alderman's Office | 437,981 |
| Salesforce Mobile App | 34,356 |
| Generated In House | 25,977 |
| City Department | 5,066 |
| E-Mail | 4,731 |
| Walk-in | 952 |

## Real recurring addresses

| Address | Real count | What it is |
|---|---|---|
| 2111 W Lexington ST | 4,911,660 | The 311 Center — used by INFORMATION ONLY CALLS |
| 10510 W ZEMKE RD | 2,387,834 | O'Hare Airport — used by Aircraft Noise Complaints |
| 4400 W THOME AVE | 6,345 | City facility |
| 10000 W OHARE AIRPORT | 2,318 | O'Hare |

## Real ZIP codes (most frequent)

`60612, 60666, 60628, 60617, 60629, 60632, 60618, 60620, 60647, 60623, 60619, 60609, 60608, 60634, 60643, 60639, 60641, 60636, 60638, 60630`

(60612 = 311 Center, 60666 = O'Hare)

## Real street names (most frequent)

`Lexington, ZEMKE, WESTERN, ASHLAND, KEDZIE, MILWAUKEE, HALSTED, DAMEN, CALIFORNIA, MICHIGAN, PULASKI, ARCHER, CLARK, PAULINA, STATE, CAMPBELL, INDIANA, BELMONT, ALBANY, RACINE`

## Seasonal patterns (real-world behavior)

- **Potholes** spike in late winter/spring (freeze-thaw, March peak)
- **Rat complaints** peak in summer
- **Tree debris** peaks in fall (storms)
- **Aircraft noise** is flat year-round
- **Information-only calls** happen every day, closed within minutes

## Ready-to-use dashboard URLs (sample data)

All of these are also one click away on the dashboard's **Page 3 · Real
examples**: http://127.0.0.1:5000/?page=examples

- http://127.0.0.1:5000/?client_id=Pothole+in+Street+Complaint
- http://127.0.0.1:5000/?client_id=Rodent+Baiting%2FRat+Complaint
- http://127.0.0.1:5000/?client_id=311+INFORMATION+ONLY+CALL
- http://127.0.0.1:5000/?client_id=Aircraft+Noise+Complaint
- http://127.0.0.1:5000/?client_id=Graffiti+Removal+Request
- http://127.0.0.1:5000/?page=year&year=2024&metric=requests&top_k=10
- http://127.0.0.1:5000/?page=year&year=2024&metric=avg_resolution_days&top_k=13

## Example CSV rows (real format)

```csv
SR_NUMBER,SR_TYPE,SR_SHORT_CODE,CREATED_DEPARTMENT,OWNER_DEPARTMENT,STATUS,ORIGIN,CREATED_DATE,LAST_MODIFIED_DATE,CLOSED_DATE,STREET_ADDRESS,CITY,STATE,ZIP_CODE
SR23-00123456,311 INFORMATION ONLY CALL,311IOC,311 City Services,311 City Services,Completed,Phone Call,2023-06-21T12:53:16,2023-06-21T13:02:44,2023-06-21T13:02:44,2111 W LEXINGTON ST,Chicago,IL,60612
SR23-00123457,Pothole in Street Complaint,PHF,,CDOT - Department of Transportation,Completed,Internet,2023-03-14T08:15:00,2023-03-17T10:30:00,2023-03-17T10:30:00,2800 W DIVERSEY AVE,Chicago,IL,60647
SR23-00123458,Rodent Baiting/Rat Complaint,SGA,,Streets and Sanitation,Open,Mobile Device,2023-07-09T19:42:00,2023-07-09T19:42:00,,1600 W PRATT AVE,Chicago,IL,60626
SR23-00123459,Aircraft Noise Complaint,AVN,,Aviation,Completed,Internet,2023-11-02T03:10:00,2023-11-02T03:25:00,2023-11-02T03:25:00,10510 W ZEMKE RD,Chicago,IL,60666
SR23-00123460,Graffiti Removal Request,GRAF,Alderman,Streets and Sanitation,Completed,Alderman's Office,2023-05-30T09:05:00,2023-06-02T14:12:00,2023-06-02T14:12:00,3200 N MILWAUKEE AVE,Chicago,IL,60641
```

## Where these live in the project

- Sample generator using all of the above: `scripts/make_sample_csv.py`
- Save the real dataset CSV to: `data/source/311_Service_Requests.csv`
