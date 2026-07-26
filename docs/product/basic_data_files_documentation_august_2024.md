# United States Environmental Protection Agency
## TOXICS RELEASE INVENTORY (TRI) -  BASIC DATA FILES DOCUMENTATION

### Updated for RY 2023
#### August 2024

---

## **AN OVERVIEW OF TRI BASIC DATA FILES**

Industrial facilities that meet Toxics Release Inventory (TRI) Program reporting requirements submit their data to EPA using either the Reporting Form R or Form A. Each "Basic" data file contains the 100 most-requested data fields from the TRI reporting form, including the quantities of toxic chemicals released into the environment on site at facilities; the quantities transferred off site to other facilities; and summary data concerning releases, recycling, energy recovery and treatment. 

There are four types of basic data files: 

- 1) The “state data files” contain data for one state, district or U.S. territory for each calendar year. For example, the 2016 Alabama state data file has all the data for Alabama-located facilities that submitted TRI data for calendar year 2016. 

- 2) The “national data files” contain all the TRI data for the United States for a specific calendar year. This includes data for all 50 states and the six U.S. districts and territories (i.e., American Samoa, District of Columbia, Guam, Northern Mariana Islands, Puerto Rico and the Virgin Islands). 

- 3) The “federal facility data files” contain data for all government-owned federal sites for a specific calendar year. 

- 4) The “tribal data files” contain data for all facilities located on tribal lands that submitted TRI data for a specific calendar year. 

## WHAT’S IN THIS DOCUMENT

The rest of this document is organized as a four-column data table. It describes what information you will find when you download and open any of the TRI Basic data files.

| Column | Description |
| --- | --- |
| Number (No.) | The sequential number of the data element in the record |
| Field Name | The name of the data element (Note: these names correspond to the column headings in the data files themselves.) |
| Data Type | ‘C’ for character data (alphanumeric)<br>‘N’ for numeric data<br>‘D’ for date |
| Description | A brief description of what the data element represents and where on the TRI reporting form it is reported (i.e., reference). Also included is an indication of the maximum length of the data element. For numeric data, comma notation is used for numbers that may contain decimals. For example, a “maximum length” value of “22,7” indicates that the number can be 22 digits long with 7 digits to the right of the decimal point. |

When you open any of the Basic data files, you’ll see that the contents are delimited by commas, meaning a comma is placed between each data element. The first row of each file contains column headers, which correspond to the “field names” in this document.

*Example data file rows (figure from original document):*

| YEAR | TRI_FACILITY_ID    | FRS_ID       | FACILITY_NAME         |
|------|--------------------|--------------|-----------------------|
| 2016 | 32206PRTCN151TA    | 110031019083 | PORT CONSOLIDATED INC |
| 2016 | 322185MCXX11611    | 110009078425 | SEMCO                 |
| 2016 | 33605CTGPTSOLMC    | 110027973263 | CITGO PETROLEUM CORP  |
| 2016 | 33411CNSLD17825    | 110000493029 | PORT CONSOLIDATED INC |
| 2016 | 334305GRSP12815    | 110000917624 | SUGAR SUPPLY INC      |

**REMINDER:** Quantities of dioxin and dioxin-like compounds are in grams. Quantities of all other TRI chemicals are reported in pounds. Facilities cannot use range codes to report quantities for dioxin and dioxin-like compounds and other Persistent Bioaccumulative Toxics (PBTs). For a list of PBT chemicals see “Appendix B - Persistent Bioaccumulative Toxics (PBTs).”

## HELPFUL RESOURCES FOR USERS OF DOWNLOADABLE DATA FILES

When using any of the downloadable TRI data files, it will be helpful for users to refer to the TRI Reporting Form R, 
the TRI Reporting Forms & Instructions document, and the Envirofacts TRI data model. The Reporting Forms & Instructions
document and sample reporting forms are available online in the GuideME application at 
[www.epa.gov/tri/guideme](https://www.epa.gov/tri/guideme). The Envirofacts TRI data model is found at 
[https://www.epa.gov/enviro/tri-model](https://www.epa.gov/enviro/tri-model). These resources provide useful context 
and have additional details about certain data elements.

## **ZEROES IN THE DATA** 

The TRI Basic Data Files are intended to be loaded into spreadsheets, databases and statistical applications. Some of these tools require that numeric data fields be populated with a number (and not a blank) for the tool to work correctly. For instance, to calculate a total for a spreadsheet column, all rows in that column must contain a number and not be blank. 

Considering this, the TRI Program has inserted zeroes into the TRI Basic Data Files in places where numeric data fields were blank. There are three reasons why a numeric data field on a TRI reporting form may be blank. The first is facilities that report “NA” or “Not Applicable” for a quantity on the Form R. Reporting “NA” means that the release or waste management quantity is not possible for that facility. For example, if a facility is not located near a water body, it will not have the ability to release any of the chemical to water. Therefore, in section 5.3 of the Reporting Form R, the facility would enter “NA” for on-site water releases. The <u>TRI Reporting Forms and Instructions</u> contain more information on the use of “NA” in TRI reporting. 

The second case where zeroes appear instead of blanks occurs when facilities do not respond to quantity questions on the Form R, leaving them blank. This was primarily an issue prior to the TRI Electronic Reporting Rule, when the TRI Program still accepted paper reporting forms. The TRI-MEweb reporting software, however, doesn’t allow blanks in the reporting of quantity data; facilities are required to enter a number or indicate “NA.” 

The third case occurs when facilities submit a Form A Certification Statement (also referred to as a Form A). Form A allows facilities otherwise meeting EPCRA Section 313 reporting thresholds the option to certify that, for a particular chemical, they do not exceed 500 pounds for the total annual reportable amount and that their amounts manufactured, processed, or otherwise used do not exceed one million pounds. Form A only requires facilities to identify themselves and list the qualified chemicals(s) they are reporting. Facilities do not have to report any release or other waste management information (normally reported in Part II of the Form R) for the chemical(s). The Basic Data file record will contain zeroes for all release and other management quantities from a Form A. Field 49, “Form Type” indicates if a form is a Form A or a Form R.  See <u>the TRI Reporting Forms and Instructions</u> for more information on the Form A. 


|**No.**|**Field Name**|**Type**| **Description**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
|---|---|---|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|1|YEAR|C| Calendar year in which the reported activities occurred.<br>Source: TRI_REPORTING_FORM.REPORTING_YEAR<br>Reference: Part I, Section 1<br> _Maximum Length_: 4                                                                                                                                                                                                                                                                                                                                                                                                                |
|2|TRIFID|C| The unique TRI facility identification number assigned to<br>each facility for TRI reporting purposes.<br> _NOTE_:  _The content of this field isnotchanged to match_<br> _facility ownership, or zip code changes. Rather, the TRI_<br> _Facility ID identifies a specific geographical location which_<br> _is also identified by the latitude and longitude of that_<br> _location._<br> _Reference_: Part I, Section 4.1<br> _Maximum Length_: 15                                                                                                                           |
|3|FRS ID|C| Unique identification number assigned by EPA’s Facility<br>Registry Service (FRS) to the TRI facility. The FRS is a<br>centrally managed EPA database that identifies facilities,<br>sites, or places subject to environmental regulations or<br>of environmental interest. Using the FRS ID, data users<br>can link data from different EPA programs together.<br> _Maximum Length_: 12                                                                                                                                                                                     |
|4|FACILITY NAME|C| Name of the reporting facility.<br>_Reference_: Part I, Section 4.1<br>_Maximum Length_: 62                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
|5|STREET ADDRESS|C| Street address of the reporting facility.<br>_Reference_: Part I, Section 4.1<br>_Maximum_ _Length_: 62                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
|6|CITY|C| City in which the reporting facility is located.<br>_Reference_: Part I, Section 4.1<br>_Maximum Length_: 28                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
|7|COUNTY|C| County in which the reporting facility is located.<br>_Reference_: Part I, Section 4.1<br>_Maximum Length_: 50                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
|8|STATE|C| Two-letter state code of the reporting facility.<br>_Reference_: Part I, Section 4.1<br>_Maximum Length_: 2                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
|9|ZIP|C| ZIP code of the reporting facility.<br>_Reference_: Part I, Section 4.1<br>_Maximum Length_: 9                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
|10|BIA|C| Three-letter Bureau of Indian Affairs (BIA) code indicating<br>the tribe on whose land the reporting facility is located.<br>_Maximum Length_: 3                                                                                                                                                                                                                                                                                                                                                                                                                              |
|11|TRIBE|C| Name of the tribe on whose land the reporting facility is located.<br>_Maximum Length_:  350                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
|12|LATITUDE|N| The latitude value that best represents the facility<br>according to EPA’s Facility Registry System (FRS). Format:<br>2-digit whole number followed by a decimal point and 6 digits.<br>_Note: In RY 2005, EPA stopped collecting the latitude value and began obtaining it from FRS._<br>_Maximum Length_:  9,6                                                                                                                                                                                                                                                              |
|13|LONGITUDE|N| The longitude value that best represents the facility<br>according to EPA’s Facility Registry System (FRS). Format:<br>3-digit whole number followed by 6 digits.<br>_Note: In RY 2005, EPA stopped collecting the longitude value and began obtaining it from FRS._<br>_Maximum Length_:  10,6                                                                                                                                                                                                                                                                               |
|14|HORIZONTAL DATUM|C| The horizontal datum used in determining the latitude and<br>longitude coordinates. Allowed values: NAD27, NAD83 and WGS84.<br>_Maximum Length_:  5                                                                                                                                                                                                                                                                                                                                                                                                                           |
|15|PARENT CO NAME|C| Name of the corporation or other business entity that<br>controls the reporting facility.<br>_Reference_:  Part I, Section 5.1<br>_Maximum Length_:  60                                                                                                                                                                                                                                                                                                                                                                                                                        |
|16|PARENT CO DB NUM|C| Unique identification number assigned by Dun and<br>Bradstreet to the parent company of the reporting facility.<br>_Reference_:  Part I, Section 5.2<br>_Maximum Length_:  9                                                                                                                                                                                                                                                                                                                                                                                                   |
|17|STANDARDIZED PARENT COMPANY NAME|C| A data field developed by EPA that is intended to best<br>reflect the current ultimate U.S. parent company of the facility.<br>_Reference_:  Assigned by EPA                                                                                                                                                                                                                                                                                                                                                                                                                  |
|18|FOREIGN PARENT CO NAME|C| Name of the foreign corporation that owns the facility if<br>there is a higher-level parent company outside of the United States.<br>_Reference_:  Part I, Section 5.3                                                                                                                                                                                                                                                                                                                                                                                                        |
|19|FOREIGN PARENT CO D&B NUM|C| Unique identification number assigned by Dun and<br>Bradstreet to the foreign parent company of the reporting facility, if one exists.<br>_Reference_:  Part I, Section 5.4                                                                                                                                                                                                                                                                                                                                                                                                   |
|20|STND FOREIGN PARENT CO|C| A data field developed by EPA that is intended to best<br>reflect the current foreign parent company of the facility.<br>_Reference_:  Assigned by EPA                                                                                                                                                                                                                                                                                                                                                                                                                        |
|21|FEDERAL FACILITY IND|C| Flag indicating whether the facility is federally owned and<br>operated.<br>Yes = federal; no = non-federal<br>_Reference_: Part I Section 4.2c<br>_Maximum Length_: 3                                                                                                                                                                                                                                                                                                                                                                                                         |
|22|INDUSTRY SECTOR CODE|C| North American Industry Classification System (NAICS)<br>code used to identify the facility’s sector. This<br>categorization is primarily used to classify, analyze, and<br>show industrial trends within TRI data.<br>_Maximum Length_: 4                                                                                                                                                                                                                                                                                                                                    |
|23|INDUSTRY SECTOR|C| The industry or sector (e.g., Coal Mining, Metal Mining,<br>Electrical Utilities, etc.) a facility belongs to. This<br>categorization is primarily used to classify, analyze, and<br>show industrial trends within TRI data.<br>_Maximum Length_: 120                                                                                                                                                                                                                                                                                                                         |
|24|PRIMARY SIC|C| Primary 4-digit Standard Industrial Classification (SIC)<br>code._Note: SIC codes were reported by facilities from RY_<br>_1987 through 2005._<br>_Reference_: Part I, Section 4.5a<br>_Maximum Length_: 4                                                                                                                                                                                                                                                                                                                                                                     |
|25|SIC 2|C| Second 4-digit Standard Industrial Classification (SIC) code<br>entered by facility._Note: SIC codes were reported by_<br>_facilities from RY 1987 through 2005._<br>_Reference_: Part I, Section 4.5b<br>_Maximum Length_: 4                                                                                                                                                                                                                                                                                                                                                  |
|26|SIC 3|C| Third four-digit Standard Industrial Classification (SIC) code<br>entered by facility. _Note: SIC codes were reported by_<br>_facilities from RY 1987 through 2005._<br>_Reference_: Part I, Section 4.5c<br>_Maximum Length_: 4                                                                                                                                                                                                                                                                                                                                               |
|27|SIC 4|C| Fourth four-digit Standard Industrial Classification (SIC)<br>code entered by facility._Note: SIC codes were reported by_<br>_facilities from RY 1987 through 2005._<br>_Reference_: Part I, Section 4.5d<br>_Maximum Length_: 4                                                                                                                                                                                                                                                                                                                                               |
|28|SIC 5|C| Fifth four-digit Standard Industrial Classification (SIC) code<br>entered by facility._Note: SIC codes were reported by_<br>_facilities from RY 1987 through 2005_.<br>_Reference_: Part I, Section 4.5d<br>_Maximum Length_: 4                                                                                                                                                                                                                                                                                                                                                |
|29|SIC 6|C| Six four-digit Standard Industrial Classification (SIC) code<br>entered by facility._Note: SIC codes were reported by_<br>_facilities from RY 1987 through 2005._<br>_Reference_: Part I, Section 4.5d<br>_Maximum Length_: 4                                                                                                                                                                                                                                                                                                                                                  |
|30|PRIMARY NAICS|C| Primary 6-digit North American Standard Industry<br>Classification System (NAICS) code. This represents the<br>main business activity at the facility._Note: From RY 2006_<br>_to the present, NAICS codes reported by facilities from RY_<br>_2006 to present. Prior to RY 2006, NAICS codes were_<br>_assigned by EPA._<br>_Reference_: Part I, Section 4.5a<br>_Maximum Length_: 6                                                                                                                                                                                          |
|31|NAICS 2|C| Second 6-digit North American Standard Industry<br>Classification System (NAICS) code entered by facility.<br>_Note: NAICS codes reported by facilities from RY 2006 to_<br>_present. Prior to RY 2006, NAICS codes were assigned by_<br>_EPA._<br>_Reference_: Part I, Section 4.5b<br>_Maximum Length_: 6                                                                                                                                                                                                                                                                    |
|32|NAICS 3|C| Third 6-digit North American Standard Industry<br>Classification System (NAICS) code entered by facility.<br>_Note: NAICS codes reported by facilities from RY 2006 to_<br>_present. Prior to RY 2006, NAICS codes were assigned by_<br>_EPA._<br>_Reference_: Part I, Section 4.5b<br>_Maximum Length_: 6                                                                                                                                                                                                                                                                     |
|33|NAICS 4|C| Fourth 6-digit North American Standard Industry<br>Classification System (NAICS) code entered by facility.<br>_Note: NAICS codes reported by facilities from RY 2006 to_<br>_present. Prior to RY 2006, NAICS codes were assigned by_<br>_EPA._<br>_Reference_: Part I, Section 4.5b<br>_Maximum Length_: 6                                                                                                                                                                                                                                                                    |
|34|NAICS 5|C| Fifth 6-digit North American Standard Industry<br>Classification<br>System (NAICS) code entered by facility._Note: NAICS_<br>_codes reported by facilities from RY 2006 to present._<br>_Prior to RY 2006, NAICS codes were assigned by EPA._<br>_Reference_: Part I, Section 4.5b<br>_Maximum Length_: 6                                                                                                                                                                                                                                                                      |
|35|NAICS 6|C| Sixth 6-digit North American Standard Industry Classification<br>System (NAICS) code entered by facility.<br>_Note: NAICS codes reported by facilities from RY 2006 to present._<br>_Prior to RY 2006, NAICS codes were assigned by EPA._<br>_Reference_:  Part I, Section 4.5b<br>_Maximum Length_:  6                                                                                                                                                                                                                                                                        |
|36|DOC_CTRL_NUM|C| Unique identification number assigned to each TRI form<br>submission. Format: TTYYNNNNNNNNN, where:<br>TT = document type; YY = reporting year; NNNNNNNNN= assigned number<br>_Reference_:  NA (System-generated)<br>_Maximum Length_:  13                                                                                                                                                                                                                                                                                                                                     |
|37|CHEMICAL|C| Name of the chemical as listed on the TRI chemical list, or<br>generic name, if the chemical is claimed as a trade secret.<br>_Reference_:  Part II, Section 1.2 or Part II, Section 1.3<br>_Maximum Length_:  70                                                                                                                                                                                                                                                                                                                                                              |
|38|ELEMENTAL METAL INCLUDED IND|N| Flag indicating whether the facility submitted a combined<br>reporting form for a metal compound and the corresponding elemental metal.<br>TRI started collecting this data element beginning with RY 2018.<br>VALUES:<br>YES = combined form for both an elemental metal and a metal compound containing the same elemental metal.<br>NO = only metal compound reported<br>_Reference_:  Part II, Section 1.2<br>_Maximum Length_:  3                                                                                                                                         |
|39|TRI CHEMICAL /COMPOUND ID|C| TRI Chemical ID is an internal program number that<br>uniquely identifies chemical or category codes (for compounds).<br>The number is the same as the CAS number but with a different format<br>(no dashes and left padded with zeroes for non-compounds).<br>Format: 9999999999 (Chemicals), N999 (Compounds).<br>_Note: I_CHEM_ID 9999999999 is sanitized for trade secret submissions._<br>_Reference_:  Part II, Section 1.1<br>_Maximum Length_:  10                                                                                                                     |
|40|CAS NUMBER|C| Unique numerical identifier assigned by the Chemical<br>Abstracts Service to every chemical substance.<br>_Note: CAS number 9999999999 is for sanitized trade secret submissions._<br>_Reference_:  NA<br>_Maximum Length_:  12                                                                                                                                                                                                                                                                                                                                                |
|41|SRS ID|C| The Substance Registry System (SRS) identification<br>number.This is a unique identifier assigned to a<br>substance for internal tracking within EPA systems. See<br>https://cdxapps.epa.gov/oms-substance-registry-<br>services/searchfor more information.<br>_Reference_: NA<br>_Maximum Length_: 9                                                                                                                                                                                                                                                                         |
|42|CLEAN AIR ACT CHEMICAL|C| Flag indicating whether the chemical is listed as a<br>hazardous<br>air pollutant under the Clean Air Act (CAA).<br>Yes = CAAC; No = Non-CAAC<br>_Maximum Length_: 3                                                                                                                                                                                                                                                                                                                                                                                                          |
|43|CLASSIFICATION|C| Indicates the classification of the chemical. Chemicals can<br>be classified as either a dioxin or dioxin-like compound, a<br>Persistent, Bioaccumulative and Toxic chemical, or a<br>general EPCRA Section 313 chemical.<br>Values: {TRI, PBT, DIOXIN} where:<br>TRI = General EPCRA Section 313 chemical<br>PBT = Persistent Bioaccumulative and Toxic chemical<br>DIOXIN = Dioxin or dioxin-like compound<br>_Reference_: NONE<br>_Maximum Length_: 6                                                                                                                       |
|44|METAL|C| Flag indicating whether the chemical is a metal with TRI<br>reporting restrictions.<br>Yes = Metal with reporting restrictions<br>No = TRI chemical without reporting restrictions<br>_Maximum Length_: 3                                                                                                                                                                                                                                                                                                                                                                     |
|45|METAL CATEGORY|C| Category of metal. Values are either 1, 2, 3, or 4. See<br>“Appendix A: Chemical Classifications: Metals” for a list of<br>metals in each of the four categories.<br>_Reference_: NA<br>_Maximum Length_: 1                                                                                                                                                                                                                                                                                                                                                                    |
|46|CARCINOGEN|C| Flag indicating whether the chemical is classified as a<br>carcinogen by the Occupational Safety and Health<br>Administration (OSHA).<br>Yes = CARC<br>No = Non-CARC<br>See “Appendix B: Chemical Classifications – Carcinogens”<br>for a list of TRI chemicals classified as OSHA carcinogens.<br>_Maximum_Length: 3                                                                                                                                                                                                                                                        |
|47|PBT|C| Flag indicating a chemical as a persistent, bioaccumulative,<br>toxic (PBT) chemical.<br>Values: Yes = Chemical is a PBT; No = Chemical is not a PBT<br>_Reference_: NA<br>_Maximum Length_: 3                                                                                                                                                                                                                                                                                                                                                                                 |
|48|PFAS|C| Flag identifying a chemical as a per- and polyfluoroalkyl<br>substance (PFAS). PFAS chemicals were added to TRI in<br>reporting year 2020.<br>VALUES: YES = Chemical is a PFAS; NO = Chemical NOT a<br>PFAS<br>_Reference_: NA<br>_Maximum Length_: 3                                                                                                                                                                                                                                                                                                                         |
|49|FORM TYPE|C| Indicates whether the facility submitted a Reporting Form<br>R or Form A Certification Statement.<br>R = Form R<br>A = Form A Certification Statement<br>_Reference_: Type of Form Used<br>_Maximum Length_: 1                                                                                                                                                                                                                                                                                                                                                                 |
|50|UNIT OF MEASURE|C| Indicates the unit of measure used to quantify the<br>chemical. Dioxin and dioxin-like compounds are reported<br>in grams, while all other TRI chemicals are reported in<br>pounds. Values: {Pounds, Grams}<br>_Reference_: NA<br>_Maximum Length_: 6                                                                                                                                                                                                                                                                                                                          |
|51|5.1 – FUGITIVE AIR|N| An estimate of the total quantity of the toxic chemical<br>released as fugitive air emissions at the reporting facility.<br>_Source_: TRI_RELEASE_QTY.TOTAL_RELEASE<br>_Where_: ENVIRONMENTAL_MEDIUM = ‘AIR FUG’<br>_Reference_: Part II, Section 5.1.A<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                                                |
|52|5.2 – STACK AIR|N| An estimate of the total quantity of the chemical released<br>as stack (point source) air emissions at the reporting<br>facility.<br>_Reference_: Part II, Section 5.2.A<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                                                                                                                             |
|53|5.3 – WATER|N| An estimate of the total quantity of the chemical released<br>on site as surface water discharges.<br>_Reference_: Part II, Section 5.3<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                                                                                                                                                              |
|54|5.4 – UNDERGROUND|N| An estimate of the total quantity of the chemical injected<br>on site at the facility into underground injection wells.<br>_Note: This data element was reported from RY 1987_<br>_through 1995. In RY 1996, it was replaced by_<br>_“UNDERGROUND CLASS I” and_<br>_“UNDERGROUND CLASS II-V.”_<br>_Reference_: Part II, Section 5.4.1<br>_Maximum Length_: 22,7                                                                                                                                                                                                                |
|55|5.4.1 – UNDERGROUND<br>CLASS I|N| An estimate of the total quantity of the chemical injected<br>on site at the facility into Class I wells.<br>_Reference_: Part II, Section 5.4.1A<br>_Maximum_ _Length_: 22,7                                                                                                                                                                                                                                                                                                                                                                                                  |
|56|5.4.2 – UNDERGROUND<br>CLASS II-V|N| An estimate of the total quantity of the chemical injected<br>on site at the facility into Class II-V wells.<br>_Reference_: Part II, Section 5.4.2.A<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                                                                                                                                               |
|57|5.5.1 – LANDFILLS|N| An estimate of the total quantity of the chemical released to<br>landfills at the facility._Note: This data element was_<br>_reported from RY 1987 through 1995. In RY 1996, it was_<br>_replaced by “ON-SITE RCRA SUBTITLE C LANDFILLS” and_<br>_“OTHER LANDFILLS.”_<br>_Reference_: Part II, Section 5.5.1<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                         |
|58|5.5.1A – RCRA C LANDFILLS|N| An estimate of the total quantity of the chemical<br>released to RCRA Subtitle C landfills at the facility.<br>_Reference_: Part II, Section 5.5.1A.A<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                                                                                                                                                |
|59|5.5.1B – OTHER LANDFILLS|N| An estimate of the total quantity of the chemical released<br>to other on-site (non-RCRA Subtitle C) landfills.<br>_Reference_: Part II, Section 5.5.1B.A<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                                                                                                                                            |
|60|5.5.2 – LAND TREATMENT|N| An estimate of the quantity of the chemical disposed of<br>through land treatment/application farming at the facility.<br>_Reference_: Part II, Section 5.5.2.A<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                                                                                                                                      |
|61|5.5.3 – SURFACE<br>IMPOUNDMENT|N| An estimate of the total quantity of the chemical released<br>into surface impoundments at the facility._Note: this data_<br>_element was reported from RY 1987 through 2002. In RY_<br>_2003, it was replaced by “RCRA C SURFACE_<br>_IMPOUNDMENT” and “OTHER SURFACE IMPOUNDMENT.”_<br>_Reference_: Part II, Section 5.5.3. col. A<br>_Maximum Length_: 22,7                                                                                                                                                                                                                 |
|62|5.5.3A – RCRA SURFACE<br>IMPOUNDMENT|N| An estimate of the total quantity of the chemical released<br>into RCRA Subtitle C surface impoundments at the facility.<br>This field was added in RY 2003.<br>_Reference_: Part II, Section 5.5.3A col. A<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                                                                                          |
|63|5.5.3B – OTHER SURFACE<br>IMPOUNDMENT|N| An estimate of the total quantity of the chemical released<br>into other (non-RCRA Subtitle C) surface impoundments at<br>the facility. This field was added in RY 2003.<br>_Reference_: Part II, Section 5.5.3B col. A<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                                                                              |
|64|5.5.4 – OTHER DISPOSAL|N| An estimate of the total quantity of the chemical<br>released to other disposal units (other than landfills, land<br>treatment, and surface impoundments) at the facility.<br>_Reference_: Part II, Section 5.5.4 col. A<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                                                                             |
|65|ON-SITE RELEASE TOTAL|N| Total quantity of the chemical released to the air, water,<br>and land at the facility. This is the sum of rows #51 through<br>#64.<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                                                                                                                                                                 |
|66|6.1 – POTW – TRANSFERS<br>FOR RELEASE|N| The total quantity of the chemical reported as transferred<br>off site to a POTW for release or disposal. See “Appendix E:<br>POTW Release and Treatment Calculations” for details<br>regarding this calculation.<br>_Reference_: Part II, Section 6.1<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                                               |
|67|6.1 – POTW – TRANSFERS<br>FOR TREATMENT|N| The total quantity of the chemical reported as transferred<br>off site to a POTW for further treatment. See “Appendix E:<br>POTW Release and Treatment Calculations” for details<br>regarding this calculation.<br>_Reference_: Part II, Section 6.1<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                                                 |
|68|POTW – TOTAL TRANSFERS|N| This is the total amount of the chemical that was<br>transferred to a POTW. Sum of rows #66 and #67.<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                                                                                                                                                                                                |
|69|6.2 – M10|N| The total quantity of the chemical reported as transferred<br>off site for disposal using code “M10: Storage Only.”<br>_Reference_: Part II, Section 6.2A<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                                                                                                                                            |
|70|6.2 – M41|N| The total quantity of a metal or metal compound reported<br>as transferred off site for solidification/stabilization using<br>disposal transfer code “M41: Solidification/Stabilization -<br>Metals and Metal Category Compounds Only.”<br>_Reference_: Part II, Section 6.2A<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                        |
|71|6.2 – M62|N| The total quantity of a metal or metal compound reported as<br>transferred off site for wastewater treatment not at POTWs<br>using disposal transfer code M62: “Wastewater Treatment (Excluding POTWs) – Metals and Metal Compounds Only.”<br>_Reference_:  Part II, Section 6.2A<br>_Maximum Length_:  22,7                                                                                                                                                                                                                                                                   |
|72|6.2 – M40 METAL|N| Total quantity of the chemical reported as transferred off<br>site for disposal using the code “M40: Solidification/Stabilization”<br>when the chemical is a type 1 metal (Row #45, METAL CATEGORY = 1)<br>or the chemical is Vanadium (Fume or Dust) or Vanadium (Except when contained in an alloy).<br>_NOTE: When a metal is reported under M40 it’s considered a release/disposal because a metal can’t be treated._<br>_Reference_:  Part II, Section 6.2A<br>_Maximum Length_:  22,7                                                                                    |
|73|6.2 – M61 METAL|N| Total quantity of the chemical reported as transferred off<br>site for disposal using the code “M61: Wastewater Treatment (Excluding POTWs)”<br>when the chemical is a type 1 metal (Row #45: METAL CATEGORY = 1)<br>or the chemical is Vanadium (Fume or Dust) or Vanadium (Except when contained in an alloy).<br>_NOTE: When a metal is reported under M61 it’s considered a release/disposal because a metal can’t be treated._<br>_Reference_:  Part II, Section 6.2A<br>_Maximum Length_:  22,7                                                                          |
|74|6.2 – M71|N| The total quantity of the chemical reported as transferred<br>off site for disposal using the code “M71: Underground Injection.”<br>_Note: Effective for RY 2003, code M71 was deleted and replaced with codes M81_<br>_(Underground Injection to Class I Wells) and M82 (Underground Injection to Class II-V Wells)._<br>_Reference_:  Part II, Section 6.2A<br>_Maximum Length_:  22,7                                                                                                                                                                                       |
|75|6.2 – M81|N| Total quantity of the chemical reported as transferred off<br>site for disposal using code “M81: Underground Injection to Class I Wells.”<br>This field was added in RY 2003.<br>_Reference_:  Part II, Section 6.2A<br>_Maximum Length_:  22,7                                                                                                                                                                                                                                                                                                                                |
|76|6.2 – M82|N| Total quantity of the chemical reported as transferred off<br>site for disposal using code “M82: Underground Injection to Class IIV Wells.”<br>This field was added in RY 2003.<br>_Reference_:  Part II, Section 6.2A<br>_Maximum Length_:  22,7                                                                                                                                                                                                                                                                                                                              |
|77|6.2 – M72|N| The total quantity of the chemical reported as transferred<br>off site for disposal using the code “M72: Landfills/Disposal Surface Impoundments.”<br>_Note: Effective for RY 2002, code M72 was deleted and replaced with code M63 (Surface_<br>_Impoundment), M64 (Other Landfills), and M65 (RCRA Subtitle C Landfills)._<br>_Reference_:  Part II, Section 6.2A<br>_Maximum Length_:  22,7                                                                                                                                                                                 |
|78|6.2 – M63|N| The total quantity of the chemical reported as transferred<br>off site for disposal using the code “M63: Surface Impoundment.”<br>_Note: Effective for RY 2003, code M63 was deleted and replaced with_<br>_code M66 (RCRA Subtitle C Surface Impoundment) and code M67 (Other Surface Impoundments)._<br>_Reference_:  Part II, Section 6.2A<br>_Maximum Length_:  22,7                                                                                                                                                                                                       |
|79|6.2 – M66|N| Total quantity of the chemical reported as transferred off<br>site for disposal using code “M66: RCRA Subtitle C Surface Impoundments.”<br>This field was added in RY 2003.<br>_Reference_:  Part II, Section 6.2A<br>_Maximum Length_:  22,7                                                                                                                                                                                                                                                                                                                                  |
|80|6.2 – M67|N| Total quantity of the chemical reported as transferred off<br>site for disposal using code “M67: Other Surface Impoundments.”<br>This field was added in RY 2003.<br>_Reference_:  Part II, Section 6.2A<br>_Maximum Length_:  22,7                                                                                                                                                                                                                                                                                                                                            |
|81|6.2 – M64|N| Total quantity of the chemical reported as transferred off<br>site for disposal using code “M64: Other Landfills.” This field was added in RY 2002.<br>_Reference_:  Part II, Section 6.2A<br>_Maximum Length_:  22,7                                                                                                                                                                                                                                                                                                                                                          |
|82|6.2 – M65|N| Total quantity of the chemical reported as transferred<br>off site for disposal using code “M65: RCRA Subtitle C Landfills.”<br>This field was added in RY 2002.<br>_Reference_:  Part II, Section 6.2A<br>_Maximum Length_:  22,7                                                                                                                                                                                                                                                                                                                                             |
|83|6.2 – M73|N| Total quantity of the chemical reported as transferred off<br>site for disposal using code “M73: Land Treatment.”<br>_Reference_:  Part II, Section 6.2A<br>_Maximum Length_:  22,7                                                                                                                                                                                                                                                                                                                                                                                            |
|84|6.2 – M79|N| Total quantity of the chemical reported as transferred off<br>site for disposal using code “M79: Other Land Disposal.”<br>_Reference_:  Part II, Section 6.2A<br>_Maximum Length_:  22,7                                                                                                                                                                                                                                                                                                                                                                                       |
|85|6.2 – M90|N| Total quantity of the chemical reported as transferred off<br>site for disposal using code “M90: Other Off-Site<br>Management.”<br>_Reference_: Part II, Section 6.2A<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                                                                                                                                |
|86|6.2 – M94|N| Total quantity of the chemical reported as transferred off<br>site for disposal using code “M94: Transfer to Waste<br>Broker for Disposal.”<br>_Reference_: Part II, Section 6.2A<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                                                                                                                    |
|87|6.2 – M99|N| Total quantity of the chemical reported as transferred off<br>site for disposal using code “M99: Unknown.”<br>_Reference_: Part II, Section 6.2A<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                                                                                                                                                     |
|88|OFF-SITE RELEASE TOTAL|N| Total quantity of the toxic chemical reported as transferred<br>to off-site locations for release or disposal. Sum of rows<br>#66 + (#69 through #87).<br>_Reference_: Part II, Section 6.2<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                                                                                                          |
|89|6.2 – M20|N| Total quantity of the chemical reported as transferred off<br>site for recycling using the code “M20: Solvents/Organics<br>Recovery.”<br>_Reference_: Part II, Section 6.2A<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                                                                                                                          |
|90|6.2 – M24|N| Total quantity of the chemical reported as transferred off<br>site for recycling using the code “M24: Metals Recovery.”<br>_Reference_: Part II, Section 6.2A<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                                                                                                                                        |
|91|6.2 – M26|N| Total quantity of the chemical reported as transferred off<br>site for recycling using the code “M26: Other Reuse or<br>Recovery.”<br>_Reference_: Part II, Section 6.2A<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                                                                                                                             |
|92|6.2 – M28|N| Total quantity of the chemical reported as transferred off<br>site for recycling using the code “M28: Acid Regeneration.”<br>_Reference_: Part II, Section 6.2A<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                                                                                                                                      |
|93|6.2 – M93|N| Total quantity of the chemical reported as transferred off<br>site to recycling using the code “M93: Transfer to Waste Broker - Recycling.”<br>_Reference_:  Part II, Section 6.2A<br>_Maximum Length_:  22,7                                                                                                                                                                                                                                                                                                                                                                  |
|94|OFF-SITE RECYCLED TOTAL|N| Total quantity of the toxic chemical reported as transferred<br>to off-site locations for recycling. Sum of rows #89 through<br>#93.<br>_Reference_: Part II, Section 6.2<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                                                                                                                            |
|95|6.2 – M56|N| Total quantity of the chemical reported as transferred off<br>site to energy recovery using the code “M56: Energy<br>Recovery.”<br>_Reference_: Part II, Section 6.2A<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                                                                                                                                |
|96|6.2 – M92|N| Total quantity of the chemical reported as transferred off<br>site to energy recovery using the code “M92: Transfer to<br>Waste Broker - Energy Recovery.”<br>_Reference_: Part II, Section 6.2A<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                                                                                                     |
|97|OFF-SITE ENERGY<br>RECOVERY TOTAL|N| Total quantity of the toxic chemical reported as<br>transferred to off-site locations for energy recovery. Sum<br>of rows #95 and #96.<br>_Reference_: Part II, Section 6.2<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                                                                                                                          |
|98|6.2 – M40 NON-METAL|N| Total quantity of the non-metal chemical reported as<br>transferred off site for treatment using the code “M40:<br>Solidification/Stabilization.” A chemical is considered a<br>non-metal when it is NOT a type 1 metal (Row #45, METAL<br>CATEGORY ≠ 1) and the chemical is NOT Vanadium (Fume<br>or Dust) and NOT Vanadium (Except when contained in an<br>alloy)._NOTE: When a non-metal is reported under M40,_<br>_it’s considered to be treated and is included in in the OFF-_<br>_SITE TREATED TOTAL._<br>_Reference_: Part II, Section 6.2A<br>_Maximum Length_: 22,7 |
|99|6.2 – M50|N| Total quantity of the chemical reported as transferred off<br>site for treatment using the code “M50:<br>Incineration/Thermal Treatment.”<br>_Reference_: Part II, Section 6.2A<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                                                                                                                      |
|100|6.2 – M54|N| Total quantity of the chemical reported as transferred off<br>site for treatment using the code “M54:<br>Incineration/Insignificant Fuel Value.”<br>_Reference_: Part II, Section 6.2A<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                                                                                                               |
|101|6.2 – M61 NON-METAL|N| Total quantity of the chemical reported as transferred off<br>site to treatment using the code M61: “Wastewater<br>Treatment (Excluding POTWs).” A chemical is considered a<br>non-metal when it is NOT a type 1 metal (Row #45, METAL<br>CATEGORY ≠ 1) and the chemical is NOT Vanadium (Fume<br>or Dust) and NOT Vanadium (Except when contained in an<br>alloy)._NOTE: When a non-metal is reported under M61,_<br>_it’s considered to be treated and is included in in the OFF-_<br>_SITE TREATED TOTAL._<br>_Reference_: Part II, Section 6.2A<br>_Maximum Length_: 22,7  |
|102|6.2 – M69|N| Total quantity of the chemical reported as transferred off<br>site for treatment using the code “M69: Other Waste<br>Treatment.”<br>_Reference_: Part II, Section 6.2A<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                                                                                                                               |
|103|6.2 – M95|N| Total quantity of the chemical reported as transferred off<br>site for treatment using the code “M95: Transfer to Waste<br>Broker - Waste Treatment.”<br>_Reference_: Part II, Section 6.2A<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                                                                                                          |
|104|OFF-SITE TREATED TOTAL|N| Total quantity of the chemical reported as transferred off<br>site for treatment. The sum of rows #67 + (#98 through<br>#103).<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                                                                                                                                                                      |
|105|6.2 – UNCLASSIFIED|N| Total quantity of the chemical reported as transfer off-site<br>as unclassified. This includes chemicals reported using<br>code “M91: Transfers to Waste Broker” and other<br>transfers that did not contain a specific transfer code.<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                                                              |
|106|6.2 – TOTAL TRANSFER|N| Total quantity of the chemical reported as transferred off<br>site.  Sum of rows #88, #94, #97 and #104._Maximum_<br>_Length_: 22,7                                                                                                                                                                                                                                                                                                                                                                                                                                           |
|107|TOTAL RELEASES|N| The total on- and off-site releases from sections 5 and 6<br>of the Form R. The value for this field equals On-site<br>Release Total (row #65) + Off-site Release Total (row<br>#88).<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                                                                                                               |
|108|8.1 - RELEASES|N| Amount of total on- and off-site releases as reported in<br>Section 8, Source Reduction and Recycling Activities /<br>Pollution Prevention._Note: Reported from RY 1987_<br>_through 2002._<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                                                                                                         |
|109|8.1A – ON-SITE CONTAINED RELEASES|N| Total quantity of on-site disposal to Class I underground<br>injection wells, RCRA Subtitle C landfills and other landfills.<br>_Note: Beginning in RY 2003, the total releases in Section 8_<br>_of the Form R were broken up into four subcategories (rows #109-#112)._<br>_Reference_:  Part II, Section 8.1A<br>_Maximum Length_:  22,7                                                                                                                                                                                                                                    |
|110|8.1B – ON-SITE OTHER RELEASES|N| Other on-site disposal or release amounts not covered in section 8.1A of the reporting form.<br>_Note: Beginning in RY 2003, the total releases in Section 8_<br>_of the Form R were broken up into four subcategories (rows #109-#112)._<br>_Reference_:  Part II, Section 8.1B<br>_Maximum Length_:  22,7                                                                                                                                                                                                                                                                    |
|111|8.1C – OFF-SITE CONTAINED RELEASES|N| Total quantity of off-site disposal to Class I underground<br>injection wells, RCRA Subtitle C landfills and other landfills.<br>_Note: Beginning in RY 2003, the total releases in Section 8_<br>_of the Form R were broken up into four subcategories (rows #109-#112)._<br>_Reference_:  Part II, Section 8.1C<br>_Maximum Length_:  22,7                                                                                                                                                                                                                                   |
|112|8.1D – OFF-SITE OTHER RELEASES|N| Other off-site disposal or release amounts not covered in Section 8.1 of the reporting form.<br>_Note: Beginning in RY 2003, the total releases in Section 8_<br>_of the Form R were broken up into four subcategories (rows #109-#112)._<br>_Reference_:  Part II, Section 8.1D<br>_Maximum Length_:  22,7                                                                                                                                                                                                                                                                    |
|113|8.2 – ENERGY RECOVERY ON SITE|N| The total quantity of the toxic chemical burned on site for energy recovery.<br>_Reference_:  Part II, Section 8.2<br>_Maximum Length_:  22,7                                                                                                                                                                                                                                                                                                                                                                                                                                  |
|114|8.3 – ENERGY RECOVERY OFF SITE|N| The total quantity of the toxic chemical sent off site to be burned for energy recovery.<br>_Reference_:  Part II, Section 8.3<br>_Maximum Length_:  22,7                                                                                                                                                                                                                                                                                                                                                                                                                      |
|115|8.4 – RECYCLING ON SITE|N| The total quantity of the toxic chemical recycled on site at the facility.<br>_Reference_:  Part II, Section 8.4<br>_Maximum Length_:  22,7                                                                                                                                                                                                                                                                                                                                                                                                                                    |
|116|8.5 – RECYCLING OFF SITE|N| The total quantity of the toxic chemical sent off site for recycling.<br>_Reference_:  Part II, Section 8.5<br>_Maximum Length_:  22,7                                                                                                                                                                                                                                                                                                                                                                                                                                         |
|117|8.6 – TREATMENT ON SITE|N| The total quantity of the toxic chemical treated on site at<br>the facility.<br>_Reference_: Part II, Section 8.6<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                                                                                                                                                                                    |
|118|8.7 – TREATMENT OFF SITE|N| The total quantity of the toxic chemical sent off site for<br>treatment (including transfers to POTWs).<br>_Reference_: Part II, Section 8.7<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                                                                                                                                                         |
|119|PRODUCTION WASTE<br>(8.1 – 8.7)|N| The total quantity of production-related waste<br>containing the chemical. This is the sum of the quantities<br>in Section 8.1 through 8.7 of the Form R (rows #109<br>through #118).<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                                                                                                               |
|120|8.8 – ONE-TIME RELEASE|N| The total quantity of the chemical released into the<br>environment or transferred off site due to eventsnot<br>associatedwith routine production processes.<br>_Reference_: Part II, Section 8.8<br>_Maximum Length_: 22,7                                                                                                                                                                                                                                                                                                                                                    |
|121|PROD_RATIO_OR_<br>ACTIVITY|C| Indicates whether the value reported in Section 8.9 (see<br>row #122) is a production ratio value or an activity index<br>value.<br>_Reference_: Part II, Section 8.9<br>_Maximum Length_: 10                                                                                                                                                                                                                                                                                                                                                                                  |
|122|8.9 – PRODUCTION RATIO|N| The ratio of production or activity in the reporting year<br>divided by production or activity in the previous year.<br>Activity index is based on a variable other than<br>production that is the primary influence on the quantity<br>of the reported TRI chemical.<br>_Reference_: Part II, Section 8.9<br>_Maximum Length_: 9,2                                                                                                                                                                                                                                            |



# APPENDIX A – Chemical Classification - Metals 

Category 1 Metals  (Metal_Ind = ‘1’) 

|Chemical|CAS#|TRI Chemical ID|
|---|---|---|
|ANTIMONY|7440-36-0|007440360|
|ANTIMONY COMPOUNDS|N010|N010|
|ARSENIC|7440-38-2|007440382|
|ARSENIC COMPOUNDS|N020|N020|
|BERYLLIUM|7440-41-7|007440417|
|BERYLLIUM COMPOUNDS|N050|N050|
|CADMIUM|7440-43-9|007440439|
|CADMIUM COMPOUNDS|N078|N078|
|CHROMIUM|7440-47-3|007440473|
|CHROMIUM COMPOUNDS<br>(EXCEPT CHROMITE ORE MINED IN THE TRANSVAAL REGION)|N090|N090|
|COBALT|7440-48-4|007440484|
|COBALT COMPOUNDS|N096|N096|
|COPPER|7440-50-8|007440508|
|COPPER COMPOUNDS|N100|N100|
|LEAD|7439-92-1|007439921|
|LEAD COMPOUNDS|N420|N420|
|MANGANESE|7439-96-5|007439965|
|MANGANESE COMPOUNDS|N450|N450|
|MERCURY|7439-97-6|007439976|
|MERCURY COMPOUNDS|N458|N458|
|NICKEL|7440-02-0|007440020|
|NICKEL COMPOUNDS|N495|N495|
|SELENIUM|7782-49-2|007782492|
|SELENIUM COMPOUNDS|N725|N725|
|SILVER|7440-22-4|007440224|
|SILVER COMPOUNDS|N740|N740|
|THALLIUM|7440-28-0|007440280|
|THALLIUM COMPOUNDS|N760|N760|
|VANADIUM COMPOUNDS|N770|N770|
|ZINC COMPOUNDS|N982|N982|



# APPENDIX A – Chemical Classification - Metals (cont.) 

Category 2 Metals (Metal_Ind = ‘2’) 

|Chemical|CAS#|TRI Chemical ID|
|---|---|---|
|ALUMINUM OXIDE(FIBROUS FORMS)|1344-28-1|001344281|
|ALUMINUM PHOSPHIDE|20859-73-8|020859738|
|ASBESTOS(FRIABLE)|1332-21-4|001332214|
|BIS(TRIBUTYLTIN)OXIDE|56-35-9|000056359|
|BORON TRICHLORIDE|10294-34-5|010294345|
|BORON TRIFLUORIDE|7637-07-2|007637072|
|C.I. DIRECT BLUE 218|28407-37-6|028407376|
|C.I. DIRECT BROWN 95|16071-86-6|016071866|
|FENBUTATIN OXIDE|13356-08-6|013356086|
|FERBAM|14484-64-1|014484641|
|IRON PENTACARBONYL|13463-40-6|013463406|
|LITHIUM CARBONATE|554-13-2|000554132|
|MANEB|12427-38-2|012427382|
|METIRAM|9006-42-2|009006422|
|MOLYBDENUM TRIOXIDE|1313-27-5|001313275|
|OSMIUM TETROXIDE|20816-12-0|020816120|
|POTASSIUM BROMATE|7758-01-2|007758012|
|SODIUM NITRITE|7632-00-0|007632000|
|THORIUM DIOXIDE|1314-20-1|001314201|
|TITANIUM TETRACHLORIDE|7550-45-0|007550450|
|TRIBUTYLTIN FLUORIDE|1983-10-4|001983104|
|TRIBUTYLTIN METHACRYLATE|2155-70-6|002155706|
|TRIPHENYLTIN CHLORIDE|639-58-7|000639587|
|TRIPHENYLTIN HYDROXIDE|76-87-9|000076879|
|ZINEB|12122-67-7|012122677|



Category 3 Metals  (Metal_Ind = ‘3’) 

|Chemical|CAS#|TRI Chemical ID|
|---|---|---|
|BARIUM|7440-39-3|007440393|
|BARIUM COMPOUNDS|N040|N040|



Category 4 Metals  (Metal_Ind = ‘4’) 

|Chemical|CAS#|TRI Chemical ID|
|---|---|---|
|ALUMINUM( FUME OR DUST )|7429-90-5|007429905|
|VANADIUM( EXCEPT WHEN CONTAINED IN AN ALLOY )|7440-62-2|007440622|
|ZINC( FUME OR DUST )|7440-66-6|007440666|



# APPENDIX B - Persistent Bio-accumulative Toxics (PBTs) 

|Chemical Name|CAS Number|
|---|---|
|ALDRIN|309-00-2|
|BENZO(G H I)PERYLENE|191-24-2|
|CHLORDANE|57-74-9|
|DIOXIN AND DIOXIN-LIKE COMPOUNDS|N150|
|HEPTACHLOR|76-44-8|
|HEXABROMOCYCLODODECANE|N270|
|HEXACHLOROBENZENE|118-74-1|
|ISODRIN|465-73-6|
|LEAD|7439-92-1|
|LEAD COMPOUNDS|N420|
|MERCURY|7439-97-6|
|MERCURY COMPOUNDS|N458|
|METHOXYCHLOR|72-43-5|
|OCTACHLOROSTYRENE|29082-74-4|
|PENDIMETHALIN|40487-42-1|
|PENTACHLOROBENZENE|608-93-5|
|POLYCHLORINATED BIPHENYLS|1336-36-3|
|POLYCYCLIC AROMATIC COMPOUNDS|N590|
|TETRABROMOBISPHENOL A|79-94-7|
|TOXAPHENE|8001-35-2|
|TRIFLURALIN|1582-09-8|



# APPENDIX C - Dioxin and Dioxin-like Compound Data 

In reporting year (RY) 2000, the Toxics Release Inventory Program began collecting congener data for dioxin and dioxin-like compounds to better convey the relative toxicity of these chemicals being released or managed at facilities. From RY 2000 through 2007, Part II, Section 1.4 of the Reporting Form R asked facilities to specify the percentages of the 17 individual chemicals that make up a dioxin or dioxin-like compound for all media (air, water and land). 

In RY 2008, the TRI Program improved collection of dioxin and dioxin-like compounds data by introducing the Form R Schedule One. This supplemental form allows facilities to report quantities of each of the 17 dioxin congeners. 

Although useful, total releases are not the best measure of the actual toxicity of dioxin and dioxin-like compounds because each compound has its own level of toxicity. Both the original reporting of dioxin and dioxin-like congeners and the Form R Schedule One reporting allowed the TRI Program to calculate Toxic Equivalency (TEQ) values for each facility’s dioxin releases. TEQs are a weighted quantity measure based on the toxicity of each member of the dioxin and dioxin-like compounds category relative to the most toxic members of the category. The values allow for comparison of the toxicity of different combinations of dioxins and dioxin-like compounds, and help explain the relative toxicity of the TRI chemical release information. 

For more information about dioxin and dioxin-like chemical reporting and the calculation of TEQs, see <u>https://www.epa.gov/toxics-release-inventory-tri-program/dioxin-and-dioxin-compounds-toxicequivalencyinformation. To download dioxin data from the Form R Schedule One, visit https://www.epa.gov/toxicsrelease-inventory-tri-program/tri-dioxin-and-dioxin-compounds-and-teq-data-filescalendar.</u> 

# APPENDIX D – NAICS Code Assignments 

Until RY 2006, the TRI Program used Standard Industrial Codes (SIC) to identify each reporting facility’s industry sector. In RY 2006, the TRI Program began using North American Industry Classification System (NAICS) codes. 

To allow for analysis of data across years, the TRI Program assigned NAICS codes to each TRI submission from 1987 through 2005. The six methods used to assign NAICS codes and the number and percentages of assignments per method are shown in the table below. The “Order of Precedence” column indicates the order in which the methods were used to make an assignment. 

|Method|Order of<br>Precedence|Number of NAICS codes<br>Assigned via Method<br>(in Thousands)|Percentage Per<br>Method|
|---|---|---|---|
|Reported Data Used|1|821K|50%|
|SIC to NAICS Crosswalk|2|478K|29%|
|EPA Facility Registry System<br>(FRS)|3|190K|11%|
|Commercial Sources|4|113K|7%|
|Statistics|5|51K|3%|
|Other Methods|6|2K|Less than 1 %|



Reported Data Used – In this method, the primary NAICS code reported by each facility in RY 2006 was used to make an assignment to chemical submissions (Form Rs and Form As) for years 1987 to 2005. This method was only used under the following conditions: 

1. The RY 2006 chemical submitted had only one primary NAICS code reported 

2. The prior year submission(s) for the same chemical had only one primary SIC code consistently reported 

3. The SIC to NAICS Crosswalk (obtained for the U.S. Census Bureau) showed a one-to-one match between the reported SIC and NAICS codes 

This method was used to assign 50% of all NAICS codes. 

SIC to NAICS Crosswalk – In this method, the TRI Program used a crosswalk or lookup table that translated SIC codes into NAICS codes to assign a primary NAICS code to a pre-2006 TRI chemical submission. The primary SIC code reported on the TRI form was used to lookup the corresponding NAICS code. Not all SIC codes translated into only one NAICS code, so it was not possible to use this method to assign a NAICS code to each chemical submission. However, it was used to make 29% of all the assignments. 

EPA Facility Registry System (FRS) – In this method, the TRI Program used NAICS codes found in EPA’s Facility Registry System (FRS) to assign a primary NAICS code to each TRI chemical submission. This method was only 

used if FRS listed only one primary NAICS code for a facility.  11% of all assignments were made using this method. 

Commercial Sources - This method involved using various commercial services to verify NAICS code 

assignments. 7% of all assignments were made using this method. 

Statistics – For 3% of NAICS code assignments, the TRI Program used various statistical methods based on past and present data. 

Other Methods – Manual research (e.g., using Internet searches and other government agencies’ data) and personally contacting facilities helped the TRI Program assign NAICS codes to approximately 2,000 TRI submissions. 

# APPENDIX E – POTW Release and Treatment Calculations 

The calculation of POTW Releases and POTW Treatment is divided into two categories, those prior to and including reporting year (RY) 2013 and those in RY 2014 and after. 

For RY 2013 and before, to calculate the amount released at a POTW (POTW Release), simply multiply the total POTW transfer reported in section 6.1 of the Form R by 1.00 for all chemicals that are metals.  See “Appendix B – Chemical Classification – Metals” for a list of chemicals that are metals.  Prior to and including RY 2013, all POTW transfers for chemicals that were metals are considered 100% released. To calculate the POTW Treatment, subtract the POTW Release from the total POTW transfer. 

In RY 2014, the Toxics Release Inventory (TRI) program required all facilities to submit their data to EPA electronically (except for trade secret submissions) using the TRI-MEweb software.  Along with this change, the TRI program also changed the way it calculated POTW Releases and POTW Treatment as well as Off-site Releases in Section 8.1c and 8.1d of the Form R and off-site treatment of a chemical in section 8.7. 

The TRI-MEweb software allows facilities to specify three percentages regarding how their POTW transfers are managed.  They correspond to the “Source Reduction and Recycling Activities” in Section 8 of the Form R and are as follows: 

|Item|Description|Form R Section|
|---|---|---|
|A|Percentage released to Underground Injection Class I Wells, RCRA C Landfills and/or Other<br>Landfills.|8.1c|
|B|Percentage released to other media not specified in item A.|8.1d|
|C|Percentage not released, but treated in some manner.|8.7|



If a facility does provide these percentages, then the POTW Release amount is calculated by multiplying the amount of the transfer by the percentages provided in items A and B (above) and adding those two numbers together. Then, to calculate the POTW Treatment amount, subtract the POTW Release from the total POTW transfer. 

For example, if a facility reported a POTW transfer of 100 pounds and provided the following percentages below, the POTW Release would be 90 lbs and the POTW Treatment amount would be 10 pounds. 

|A|Percentage released to Underground Injection Class I Wells, RCRA C Landfills and/or<br>Other Landfills.|60%|
|---|---|---|
|B|Percentage released to other media not specific in item A.|30%|
|C|Percentage not released, but treated in some manner.|10%|



If the facility does not provide the percentages, then the POTW Release amount will be back calculated using the default percentages for each chemical (provided by EPA’s office of Water) and other data on the form R. See the “Default Chemical Percentages” below. 

The first step in this procedure is to calculate the Section 8.1c, 8.1d and 8.7 amounts on the Form R. These are done automatically via the TRI-MEweb software.  The procedure is as follows: 

Section 8.1c: Total Off-site Disposal to Class I Underground Injection Wells, RCRA Subtitle C Landfills, and Other Landfills is calculated as follows: 

- Section 6.1 (portion of transfer that is not treated for destruction and is ultimately disposed of in landfills or UIC Class I Wells – This is item A in the table above calculated by multiplying the transfer amount by the default percentage for the chemical for 8.1C) + Section 6.2 (quantities associated with M codes M64, M65 and M81) - Section 8.8 (catastrophic, remedial or one-time releases to off-site disposal to landfills or UIC Class I Wells) 

Section 8.1d: Total Other Off-site Disposal or Other Releases 

- Section 6.1 (portion of transfer that is not treated for destruction and is ultimately disposed of or otherwise released, other than disposal to landfills or UIC Class I Wells – This is item B in the table above calculated by multiplying the default percentages for the chemical for 8.1D) + Section 6.2 (quantities associated with M codes M10, M41, M62, M66, M67, M73, M79, M82, M90, M94, and M99) - Section 8.8 (catastrophic, remedial or one time releases for off-site disposal or other releases, other than disposal to landfills or UIC Class I Wells) 

Section 8.7: Quantity Treated Off-site 

- Section 6.1 (portion of transfer that is ultimately treated – This is item C as referred to in the table above calculated by multiplying the default percentages for the chemical for 8.7) + Section 6.2 (treatment) - Section 8.8 (off-site treatment) 

The next step is to check that following equation is true.  The equation will be true if there are no data quality errors within the form and no rounding of data was undertaken in Section 8.  The equation is: 

8.7 + 8.1c + 8.1d = 6.1 + 6.2 (release M-codes) + 6.2 (treatment M-codes). 

- Release M-codes are M10, M40, M41, M61, M62, M71, M81, M82, M72, M63, M66, M67, M64, M65, M73, M79, M90, M91, M94, M99 

- Treatment M-codes are M40, M50, M54, M61, M69, and M95. 

If the two values on either side of the equation are equal, POTW Release = 8.1c + 8.1d - 6.2 (release M-codes). Then, to calculate the POTW Treatment amount, subtract the POTW Release from the total POTW transfer. 

If the two values on either side of the equation are NOT equal, percentages cannot be back-calculated. The POTW Release is equal to the sum of the POTW transfer multiplied by the default release percentages of the chemical for 8.1C and 8.1D.  Then, to calculate the POTW Treatment amount, subtract the POTW Release from the total POTW transfer. 

## Default Chemical Percentages 

- 8.1C  - Releases/disposal to Landfills or UIC Class I Wells 
- 8.1D - All other releases/disposal not classified in 8.1C 
- 8.7 – Treatment 

|CAS#/Chemical<br>Category|Chemical|Default<br>% to 8.1C|Default<br>% to 8.1D|Default<br>% to 8.7|
|---|---|---|---|---|
|0004080313|1-(3-Chloroallyl)-3,5,7-triaza-1-azoniaadamantane chloride|1|55|44|
|0000354110|1,1,1,2-Tetrachloro-2-fluoroethane(HCFC-121a)|3|84|13|
|0000630206|1,1,1,2-Tetrachloroethane|3|82|15|
|0000071556|1,1,1-Trichloroethane|1|95|4|
|0000354143|1,1,2,2-Tetrachloro-1-fluoroethane(HCFC-121)|3|84|13|
|0000079345|1,1,2,2-Tetrachloroethane|2|78|20|
|0027905459|1,1,2,2-Tetrahydroperfluorodecyl acrylate|0|100|0|
|0017741605|1,1,2,2-Tetrahydroperfluorododecyl acrylate|0|100|0|
|0034362497|1,1,2,2-Tetrahydroperfluorohexadecyl acrylate|0|100|0|
|0034395249|1,1,2,2-Tetrahydroperfluorotetradecyl acrylate|0|100|0|
|0000079005|1,1,2-Trichloroethane|1|82|17|
|0013474889|1,1-Dichloro-1,2,2,3,3-pentafluoropropane(HCFC-225cc)|0|0|100|
|0000812044|1,1-Dichloro-1,2,2-trifluoroethane(HCFC-123b)|0|0|100|
|0111512562|1,1-Dichloro-1,2,3,3,3-pentafluoropropane(HCFC-225eb)|0|0|100|
|0001717006|1,1-Dichloro-1-fluoroethane(HCFC-141b)|1|96|3|
|0000057147|1,1-Dimethylhydrazine|1|25|74|
|0000096184|1,2,3-Trichloropropane|2|56|42|
|0000120821|1,2,4-Trichlorobenzene|19|22|59|
|0000095636|1,2,4-Trimethylbenzene|11|21|68|
|0000106887|1,2-Butylene oxide|0|27|73|
|0000096128|1,2-Dibromo-3-chloropropane|4|72|24|
|0000106934|1,2-Dibromoethane|1|60|39|
|0000422446|1,2-Dichloro-1,1,2,3,3-pentafluoropropane(HCFC-225bb)|0|0|100|
|0000354234|1,2-Dichloro-1,1,2-trifluoroethane(HCFC-123a)|1|98|1|
|0000431867|1,2-Dichloro-1,1,3,3,3-pentafluoropropane(HCFC-225da)|0|0|100|
|0001649087|1,2-Dichloro-1,1-difluoroethane(HCFC-132b)|1|97|2|
|0000095501|1,2-Dichlorobenzene|7|47|46|
|0000107062|1,2-Dichloroethane|1|64|35|
|0000540590|1,2-Dichloroethylene|1|74|25|
|0000078875|1,2-Dichloropropane|1|70|29|
|0000122667|1,2-Diphenylhydrazine|4|46|50|
|0000095545|1,2-Phenylenediamine|1|55|44|
|0000615281|1,2-Phenylenediamine dihydrochloride|0|0|100|
|0000106990|1,3-Butadiene|1|86|13|
|0000507551|1,3-Dichloro-1,1,2,2,3-pentafluoropropane(HCFC-225cb)|3|96|1|
|0136013791|1,3-Dichloro-1,1,2,3,3-pentafluoropropane(HCFC-225ea)|0|0|100|
|0000541731|1,3-Dichlorobenzene|8|47|45|
|0000542756|1,3-Dichloropropylene|1|44|55|
|0000108452|1,3-Phenylenediamine|1|55|44|
|0001120714|1,3-Propane sultone|1|29|70|
|0148240895|1,3-Propanediol, 2,2-bis[[(γ-ω-perfluoro-C10-20-alkyl)thio]methyl]<br>derivs., phosphates, ammonium salts|0|100|0|
|0148240851|1,3-Propanediol, 2,2-bis[[(γ-ω-perfluoro-C4-10-alkyl)thio]methyl]<br>derivs., phosphates, ammonium salts|0|100|0|
|0148240873|1,3-Propanediol, 2,2-bis[[(γ-ω-perfluoro-C6-12-alkyl)thio]methyl]<br>derivs., phosphates, ammonium salts|0|100|0|
|1078142105|1,3-Propanediol, 2,2-bis[[(γ-ω-perfluoro-C6-12-alkyl)thio]methyl]<br>derivs., polymers with 2,2-bis[[(γ-ω-perfluoro-C10-20-<br>alkyl)thio]methyl]-1,3-propanediol, 1,6-diisocyanato-2,2,4(or<br>2,4,4)-trimethylhexane, 2-heptyl-3,4-bis(9-isocyanatononyl)-1-<br>pentylcyclohexane and 2,2'-(methylimino)bis[ethanol]|0|100|0|
|0068515628|1,4-Benzenedicarboxylic acid, dimethyl ester, reaction products<br>with bis(2-hydroxyethyl)terephthalate, ethylene glycol, α-fluoro-<br>ω-(2-hydroxyethyl)poly(difluoromethylene),<br>hexakis(methoxymethyl)melamine and polyethylene glycol|0|100|0|
|0000764410|1,4-Dichloro-2-butene|1|84|15|
|0000106467|1,4-Dichlorobenzene|7|49|44|
|0000123911|1,4-Dioxane|1|55|44|
|0000624180|1,4-Phenylenediamine dihydrochloride|0|0|100|
|0000081492|1-Amino-2,4-dibromoanthraquinone|0|0|100|
|0000082280|1-Amino-2-methylanthraquinone|0|0|100|
|0035691657|1-Bromo-1-(bromomethyl)-1,3-propanedicarbonitrile|0|0|100|
|0000106945|1-Bromopropane|1|70|29|
|0000354256|1-Chloro-1,1,2,2-tetrafluoroethane(HCFC-124a)|0|99|1|
|0000075683|1-Chloro-1,1-difluoroethane(HCFC-142b)|1|98|1|
|0067906427|1-Decanesulfonic acid, 1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,10-<br>heneicosafluoro-, ammonium salt|0|100|0|
|0027619905|1-Decanesulfonyl chloride, 3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,10-<br>heptadecafluoro-|0|100|0|
|0000678397|1-Decanol, 3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,10-heptadecafluoro-|0|100|0|
|0027619916|1-Dodecanesulfonyl chloride,<br>3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,12-heneicosafluoro-|0|100|0|
|0000865861|1-Dodecanol, 3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,12-<br>heneicosafluoro-|0|100|0|
|0065104656|1-Eicosanol,<br>3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13,14,14,15,15,16<br>,16,17,17,18,18,19,19,20,20,20-heptatriacontafluoro-|0|100|0|
|0068555760|1-Heptanesulfonamide, 1,1,2,2,3,3,4,4,5,5,6,6,7,7,7-<br>pentadecafluoro-N-(2-hydroxyethyl)-N-methyl-|0|100|0|
|0068957620|1-Heptanesulfonamide, N-ethyl-1,1,2,2,3,3,4,4,5,5,6,6,7,7,7-<br>pentadecafluoro-|0|100|0|
|0068259074|1-Heptanesulfonic acid, 1,1,2,2,3,3,4,4,5,5,6,6,7,7,7-<br>pentadecafluoro-, ammonium salt|0|100|0|
|0070225159|1-Heptanesulfonic acid, 1,1,2,2,3,3,4,4,5,5,6,6,7,7,7-<br>pentadecafluoro-, compd. with 2,2'-iminobis[ethanol] (1:1)|0|100|0|
|0060270555|1-Heptanesulfonic acid, 1,1,2,2,3,3,4,4,5,5,6,6,7,7,7-<br>pentadecafluoro-, potassium salt|0|100|0|
|0000335717|1-Heptanesulfonyl fluoride, 1,1,2,2,3,3,4,4,5,5,6,6,7,7,7-<br>pentadecafluoro-|0|100|0|
|0060699516|1-Hexadecanol,<br>3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13,14,14,15,15,16<br>,16,16-nonacosafluoro-|0|100|0|
|0068555759|1-Hexanesulfonamide, 1,1,2,2,3,3,4,4,5,5,6,6,6-tridecafluoro-N-(2-<br>hydroxyethyl)-N-methyl-|0|100|0|
|0068259085|1-Hexanesulfonic acid, 1,1,2,2,3,3,4,4,5,5,6,6,6-tridecafluoro-,<br>ammonium salt|0|100|0|
|0070225160|1-Hexanesulfonic acid, 1,1,2,2,3,3,4,4,5,5,6,6,6-tridecafluoro-,<br>compd. with 2,2'-iminobis[ethanol] (1:1)|0|100|0|
|0003871996|1-Hexanesulfonic acid, 1,1,2,2,3,3,4,4,5,5,6,6,6-tridecafluoro-,<br>potassium salt|0|100|0|
|0017202414|1-Nonanesulfonic acid, 1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,9-<br>nonadecafluoro-, ammonium salt|0|100|0|
|0065104678|1-Octadecanol,<br>3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13,14,14,15,15,16<br>,16,17,17,18,18,18-tritriacontafluoro-|0|100|0|
|0024448097|1-Octanesulfonamide, 1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,8-<br>heptadecafluoro-N-(2-hydroxyethyl)-N-methyl-|0|100|0|
|0031506328|1-Octanesulfonamide, 1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,8-<br>heptadecafluoro-N-methyl-|0|100|0|
|0178094694|1-Octanesulfonamide, N-[3-(dimethyloxidoamino)propyl]-<br>1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,8-heptadecafluoro-, potassium salt|0|100|0|
|0002263094|1-Octanesulfonamide, N-butyl-1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,8-<br>heptadecafluoro-N-(2-hydroxyethyl)-|0|100|0|
|0067969691|1-Octanesulfonamide, N-ethyl-1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,8-<br>heptadecafluoro-N-[2-(phosphonooxy)ethyl]-, diammonium salt|0|100|0|
|0061660126|1-Octanesulfonamide, N-ethyl-1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,8-<br>heptadecafluoro-N-[3-(trimethoxysilyl)propyl]-|0|100|0|
|0029081569|1-Octanesulfonic acid, 1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,8-<br>heptadecafluoro-, ammonium salt|0|100|0|
|0070225148|1-Octanesulfonic acid, 1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,8-<br>heptadecafluoro-, compd. with 2,2'-iminobis[ethanol] (1:1)|0|100|0|
|0068555748|1-Pentanesulfonamide, 1,1,2,2,3,3,4,4,5,5,5-undecafluoro-N-(2-<br>hydroxyethyl)-N-methyl-|0|100|0|
|0068259096|1-Pentanesulfonic acid, 1,1,2,2,3,3,4,4,5,5,5-undecafluoro-,<br>ammonium salt|0|100|0|
|0070225171|1-Pentanesulfonic acid, 1,1,2,2,3,3,4,4,5,5,5-undecafluoro-,<br>compd. with 2,2'-iminobis[ethanol] (1:1)|0|100|0|
|0003872251|1-Pentanesulfonic acid, 1,1,2,2,3,3,4,4,5,5,5-undecafluoro-,<br>potassium salt|0|100|0|
|0070983607|1-Propanaminium, 2-hydroxy-N,N,N-trimethyl-, 3-[(γ-ω-perfluoro-<br>C6-20-alkyl)thio] derivs., chlorides|0|100|0|
|0038006745|1-Propanaminium, 3-[[(heptadecafluorooctyl)sulfonyl]amino]-<br>N,N,N- trimethyl-, chloride|0|100|0|
|1078715613|1-Propanaminium, 3-amino-N-(carboxymethyl)-N,N-dimethyl-, N-<br>[2-[(γ-ω-perfluoro-C4-20-alkyl)thio]acetyl] derivs., inner salts|0|100|0|
|0068555817|1-Propanaminium, N,N,N-trimethyl-3-<br>[[(pentadecafluoroheptyl)sulfonyl]amino]-, chloride|0|100|0|
|0067584581|1-Propanaminium, N,N,N-trimethyl-3-<br>[[(pentadecafluoroheptyl)sulfonyl]amino]-, iodide|0|100|0|
|0052166822|1-Propanaminium, N,N,N-trimethyl-3-<br>[[(tridecafluorohexyl)sulfonyl]amino]-, chloride|0|100|0|
|0068957584|1-Propanaminium, N,N,N-trimethyl-3-<br>[[(tridecafluorohexyl)sulfonyl]amino]-, iodide|0|100|0|
|0068957551|1-Propanaminium, N,N,N-trimethyl-3-<br>[[(undecafluoropentyl)sulfonyl]amino]-, chloride|0|100|0|
|0068957573|1-Propanaminium, N,N,N-trimethyl-3-<br>[[(undecafluoropentyl)sulfonyl]amino]-, iodide|0|100|0|
|0068187473|1-Propanesulfonic acid, 2-methyl-, 2-[[1-oxo-3-[(γ-ω-perfluoro-C4-<br>16-alkyl)thio]propyl]amino] derivs., sodium salts|0|100|0|
|0068758576|1-Tetradecanesulfonyl chloride,<br>3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13,14,14,14-<br>pentacosafluoro-|0|100|0|
|0039239775|1-Tetradecanol,<br>3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13,14,14,14-<br>pentacosafluoro-|0|100|0|
|0003296900|2,2-Bis(bromomethyl)-1,3-propanediol|0|0|100|
|0128903219|2,2-Dichloro-1,1,1,3,3-pentafluoropropane(HCFC-225aa)|0|0|100|
|0000306832|2,2-Dichloro-1,1,1-trifluoroethane(HCFC-123)|1|98|1|
|0002655154|2,3,5-Trimethylphenyl methylcarbamate|0|0|100|
|0000422480|2,3-dichloro-1,1,1,2,3-pentafluoropropane(HCFC-225ba)|0|0|100|
|0000078886|2,3-Dichloropropene|1|67|32|
|0000095954|2,4,5-Trichlorophenol|13|25|62|
|0000088062|2,4,6-Trichlorophenol|9|9|82|
|0000094757|2,4-D|2|6|92|
|0001929733|2,4-D 2-butoxyethyl ester|12|1|87|
|0053404378|2,4-D 2-ethyl-4-methylpentyl ester|21|0|79|
|0001928434|2,4-D 2-ethylhexyl ester|22|0|78|
|0000094804|2,4-D butyl ester|15|1|84|
|0002971382|2,4-D chlorocrotyl ester|16|0|84|
|0000094111|2,4-D isopropyl ester|8|2|90|
|0001320189|2,4-Dpropyleneglycol butyl ether ester|15|0|85|
|0002702729|2,4-D sodium salt|2|6|92|
|0000094826|2,4-DB|0|0|100|
|0000615054|2,4-Diaminoanisole|0|0|100|
|0039156417|2,4-Diaminoanisole sulfate|0|0|100|
|0000095807|2,4-Diaminotoluene|1|55|44|
|0000120832|2,4-Dichlorophenol|3|5|92|
|0000105679|2,4-Dimethylphenol|1|23|76|
|0000051285|2,4-Dinitrophenol|1|24|75|
|0000121142|2,4-Dinitrotoluene|1|54|45|
|0000541537|2,4-Dithiobiuret|1|51|48|
|0000120365|2,4-DP|8|34|58|
|0000576261|2,6-Dimethylphenol|0|0|100|
|0000606202|2,6-Dinitrotoluene|2|53|45|
|0000087627|2,6-Xylidine|2|53|45|
|0025268773|2-[[(Heptadecafluorooctyl)sulfonyl]methylamino]ethyl acrylate|0|100|0|
|0000383073|2-[Butyl[(heptadecafluorooctyl)sulfonyl]amino]ethyl acrylate|0|100|0|
|0000423825|2-[Ethyl[(heptadecafluorooctyl)sulfonyl]amino]ethyl acrylate|0|100|0|
|0000376147|2-[Ethyl[(heptadecafluorooctyl)sulfonyl]amino]ethyl methacrylate|0|100|0|
|0000053963|2-Acetylaminofluorene|5|42|53|
|0000117793|2-Aminoanthraquinone|2|52|46|
|0000052517|2-Bromo-2-nitropropane-1,3-diol|0|0|100|
|0002837890|2-Chloro-1,1,1,2-tetrafluoroethane(HCFC-124)|0|99|1|
|0000075887|2-Chloro-1,1,1-trifluoroethane(HCFC-133a)|0|99|1|
|0000532274|2-Chloroacetophenone|0|0|100|
|0000110805|2-Ethoxyethanol|0|8|92|
|0000149304|2-Mercaptobenzothiazole|2|52|46|
|0000109864|2-Methoxyethanol|0|8|92|
|0000075865|2-Methyllactonitrile|0|0|100|
|0000109068|2-Methylpyridine|0|8|92|
|0000088755|2-Nitrophenol|1|59|40|
|0000079469|2-Nitropropane|1|26|73|
|0000090437|2-Phenylphenol|3|5|92|
|0068084628|2-Propenoic acid, 2-<br>[methyl[(pentadecafluoroheptyl)sulfonyl]amino]ethyl ester|0|100|0|
|0068867607|2-Propenoic acid, 2-<br>[[(heptadecafluorooctyl)sulfonyl]methylamino]ethyl ester,<br>polymer with 2-[methyl[(nonafluorobutyl)sulfonyl]amino]ethyl 2-<br>propenoate, 2-<br>[methyl[(pentadecafluoroheptyl)sulfonyl]amino]ethyl 2-<br>propenoate, 2-[methyl[(tridecafluorohexyl)sulfonyl]amino]ethyl<br>2-propenoate, 2-<br>[methyl[(undecafluoropentyl)sulfonyl]amino]ethyl 2-propenoate<br>and α-(1-oxo-2-propenyl)-ω-methoxypoly(oxy-1,2-ethanediyl)|0|100|0|
|0068298624|2-Propenoic acid, 2-<br>[butyl[(heptadecafluorooctyl)sulfonyl]amino]ethyl ester, telomer<br>with 2-[butyl[(pentadecafluoroheptyl)sulfonyl]amino]ethyl 2-<br>propenoate, methyloxirane polymer with oxirane di-2-<br>propenoate, methyloxirane polymer with oxirane mono-2-<br>propenoate and 1-octanethiol|0|100|0|
|0059071102|2-Propenoic acid, 2-<br>[ethyl[(pentadecafluoroheptyl)sulfonyl]amino]ethyl ester|0|100|0|
|0067584570|2-Propenoic acid, 2-<br>[methyl[(tridecafluorohexyl)sulfonyl]amino]ethyl ester|0|100|0|
|0067584569|2-Propenoic acid, 2-<br>[methyl[(undecafluoropentyl)sulfonyl]amino]ethyl ester|0|100|0|
|0150135572|2-Propenoic acid, 2-methyl-, 2-(dimethylamino)ethyl ester,<br>polymers with Bu acrylate, γ-ω-perfluoro-C8-14-alkyl acrylate and<br>polyethylene glycol monomethacrylate, 2,2'-azobis[2,4-<br>dimethylpentanenitrile]-initiated|0|100|0|
|0196316344|2-Propenoic acid, 2-methyl-, 2-(dimethylamino)ethyl ester,<br>polymers with γ-ω-perfluoro-C10-16-alkyl acrylate and vinyl<br>acetate, acetates|0|100|0|
|0068555919|2-Propenoic acid, 2-methyl-, 2-<br>[ethyl[(heptadecafluorooctyl)sulfonyl]amino]ethyl ester, polymer<br>with 2-[ethyl[(nonafluorobutyl)sulfonyl]amino]ethyl-methyl-2-<br>propenoate, 2-<br>[ethyl[(pentadecafluoroheptyl)sulfonyl]amino]ethyl 2-methyl-2-<br>propenoate, 2-[ethyl[(tridecafluorohexyl)sulfonyl]amino]ethyl 2-<br>methyl- 2-propenoate, 2-<br>[ethyl[(undecafluoropentyl)sulfonyl]amino]ethyl 2-methyl-2-<br>propenoate and octadecyl 2-methyl-2-propenoate|0|100|0|
|0068239430|2-Propenoic acid, 2-methyl-, 2-ethylhexyl ester, polymer with α-<br>fluoro-ω-[2-[(2-methyl-1-oxo-2-propen-1-<br>yl)oxy]ethyl]poly(difluoromethylene), 2-hydroxyethyl 2-methyl-2-<br>propenoate and N-(hydroxymethyl)-2-propenamide|0|100|0|
|0001996889|2-Propenoic acid, 2-methyl-, 3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,10-<br>heptadecafluorodecyl ester|0|100|0|
|0002144549|2-Propenoic acid, 2-methyl-,<br>3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,12-<br>heneicosafluorododecyl ester|0|100|0|
|0006014751|2-Propenoic acid, 2-methyl-,<br>3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13,14,14,14-<br>pentacosafluorotetradecyl ester|0|100|0|
|0004980534|2-Propenoic acid, 2-methyl-,<br>3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13,14,14,15,15,16<br>,16,16-nonacosafluorohexadecyl ester|0|100|0|
|0065605596|2-Propenoic acid, 2-methyl-, dodecyl ester, polymer with α-fluoro-<br>ω-[2-[(2-methyl-1-oxo-2-propen-1-<br>yl)oxy]ethyl]poly(difluoromethylene) and N-(hydroxymethyl)-2-<br>propenamide|0|100|0|
|0142636882|2-Propenoic acid, 2-methyl-, octadecyl ester, polymer with<br>3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,12-<br>heneicosafluorododecyl 2-propenoate,<br>3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,10-heptadecafluorodecyl 2-<br>propenoate and<br>3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13,14,14,14-<br>pentacosafluorotetradecyl 2-propenoate|0|100|0|
|0200513424|2-Propenoic acid, 2-methyl-, polymer with butyl 2-methyl-2-<br>propenoate, 3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,10-<br>heptadecafluorodecyl 2-propenoate, 2-hydroxyethyl 2-methyl-2-<br>propenoate and methyl 2-methyl-2-propenoate|0|100|0|
|0068227963|2-Propenoic acid, butyl ester, telomer with 2-<br>[[(heptadecafluorooctyl)sulfonyl]methylamino]ethyl 2-<br>propenoate, 2-[methyl[(nonafluorobutyl)sulfonyl]amino]ethyl 2-<br>propenoate, α-(2-methyl-1-oxo-2-propenyl)-ω-hydroxypoly(oxy-<br>1,4-butanediyl), α-(2-methyl-1-oxo-2-propenyl)-ω-[(2-methyl-1-<br>oxo-2-propenyl)oxy]poly(oxy-1,4-butanediyl), 2-<br>[methyl[(pentadecafluoroheptyl)sulfonyl]amino]ethyl 2-<br>propenoate, 2-[methyl[(tridecafluorohexyl)sulfonyl]amino]ethyl<br>2-propenoate, 2-<br>[methyl[(undecafluoropentyl)sulfonyl]amino]ethyl 2-propenoate<br>and 1-octanethiol|0|100|0|
|0065605585|2-Propenoic acid, esters, 2-methyl-, dodecyl ester, polymer with<br>α-fluoro-ω-[2-[(2-methyl-1-oxo-2-propen-1-<br>yl)oxy]ethyl]poly(difluoromethylene)|0|100|0|
|0000422560|3,3-Dichloro-1,1,1,2,2-pentafluoropropane(HCFC-225ca)|3|96|1|
|0000091941|3,3'-Dichlorobenzidine|9|32|59|
|0000612839|3,3'-Dichlorobenzidine dihydrochloride|9|32|59|
|0064969342|3,3'-Dichlorobenzidine sulfate|0|0|100|
|0000119904|3,3'-Dimethoxybenzidine|1|54|45|
|0020325400|3,3'-Dimethoxybenzidine dihydrochloride|1|55|44|
|0111984099|3,3'-Dimethoxybenzidine monohydrochloride|0|0|100|
|0000119937|3,3'-Dimethylbenzidine|1|23|76|
|0000612828|3,3'-Dimethylbenzidine dihydrochloride|0|0|100|
|0041766750|3,3'-Dimethylbenzidine dihydrofluoride|0|0|100|
|0001652637|3-[[(Heptadecafluorooctyl)sulfonyl]amino]-N,N,N-trimethyl-1-<br>propanaminium iodide|0|100|0|
|0000460355|3-Chloro-1,1,1-trifluoropropane(HCFC-253fb)|1|98|1|
|0000563473|3-Chloro-2-methyl-1-propene|1|93|6|
|0000542767|3-Chloropropionitrile|1|55|44|
|0055406536|3-Iodo-2-propynyl butylcarbamate|1|23|76|
|0000101804|4,4'-Diaminodiphenyl ether|1|24|75|
|0000080057|4,4'-Isopropylidenediphenol|5|14|81|
|0000101144|4,4'-Methylenebis(2-chloroaniline)|17|18|65|
|0000101611|4,4'-Methylenebis(N,N-dimethyl)benzenamine|0|0|100|
|0000101688|4,4'-Methylenedi(phenyl isocyanate)|0|0|100|
|0000101779|4,4'-Methylenedianiline|1|24|75|
|0000139651|4,4'-Thiodianiline|0|0|100|
|0000534521|4,6-Dinitro-o-cresol|2|53|45|
|0000060093|4-Aminoazobenzene|8|35|57|
|0000092671|4-Aminobiphenyl|3|47|50|
|0000060117|4-Dimethylaminoazobenzene|35|5|60|
|0000092933|4-Nitrobiphenyl|0|0|100|
|0000100027|4-Nitrophenol|0|93|7|
|0000099592|5-Nitro-o-anisidine|0|0|100|
|0000099558|5-Nitro-o-toluidine|1|54|45|
|0071751412|Abamectin|44|2|54|
|0030560191|Acephate|1|55|44|
|0000075070|Acetaldehyde|0|9|91|
|0000060355|Acetamide|0|8|92|
|0000067641|Acetone|0|0|100|
|0000075058|Acetonitrile|1|25|74|
|0000098862|Acetophenone|0|8|92|
|0062476599|Acifluorfen, sodium salt|12|25|63|
|0000107028|Acrolein|0|9|91|
|0000079061|Acrylamide|0|8|92|
|0000079107|Acrylic acid|0|8|92|
|0000107131|Acrylonitrile|0|9|91|
|0015972608|Alachlor|7|11|82|
|0068391082|Alcohols, C8-14,γ-ω-perfluoro|0|100|0|
|0000116063|Aldicarb|1|54|45|
|0000309002|Aldrin|62|1|37|
|0097659477|Alkenes, C8-14 α-, d-ω-perfluoro|0|100|0|
|0068188125|Alkyl iodides, C4-20,γ-ω-perfluoro|0|100|0|
|0000107186|Allyl alcohol|0|8|92|
|0000107051|Allyl chloride|1|85|14|
|0000107119|Allylamine|1|25|74|
|0000319846|alpha-Hexachlorocyclohexane|0|0|100|
|0000134327|alpha-Naphthylamine|1|24|75|
|0007429905|Aluminum(fume or dust)|66|34|0|
|0001344281|Aluminum oxide(fibrous forms)|2|98|0|
|0020859738|Aluminumphosphide|2|98|0|
|0000834128|Ametryn|4|45|51|
|0033089611|Amitraz|0|0|100|
|0000061825|Amitrole|1|55|44|
|0007664417|Ammonia|0|40|60|
|0006484522|Ammonium nitrate(solution)|0|0|100|
|0003825261|Ammoniumperfluorooctanoate|0|100|0|
|0007783202|Ammonium sulfate(solution)|0|0|100|
|0000101053|Anilazine|16|19|65|
|0000062533|Aniline|0|8|92|
|0000120127|Anthracene|31|8|61|
|0007440360|Antimony|32|68|0|
|N010|Antimonycompounds|32|68|0|
|0007440382|Arsenic|49|51|0|
|N020|Arsenic compounds|49|51|0|
|0001332214|Asbestos(friable)|0|0|100|
|0001912249|Atrazine|3|74|23|
|0007440393|Barium|69|31|0|
|N040|Barium compounds (except for barium sulfate (CAS No. 7727-43-<br>7))|69|31|0|
|0022781233|Bendiocarb|1|23|76|
|0001861401|Benfluralin|56|3|41|
|0017804352|Benomyl|1|49|50|
|0000098873|Benzal chloride|0|0|100|
|0000055210|Benzamide|0|0|100|
|0000071432|Benzene|1|23|76|
|0000092875|Benzidine|1|25|74|
|0000191242|Benzo[g,h,i]perylene|0|0|100|
|0000098077|Benzoic trichloride|0|0|100|
|0000098884|Benzoyl chloride|0|0|100|
|0000094360|Benzoylperoxide|5|3|92|
|0000100447|Benzyl chloride|1|27|72|
|0007440417|Beryllium|37|63|0|
|N050|Beryllium compounds|37|63|0|
|0000091598|beta-Naphthylamine|1|23|76|
|0000057578|beta-Propiolactone|0|0|100|
|0082657043|Bifenthrin|38|0|62|
|0000092524|Biphenyl|10|2|88|
|0000108601|Bis(2-chloro-1-methylethyl)ether|2|53|45|
|0000111911|Bis(2-chloroethoxy)methane|1|78|21|
|0000111444|Bis(2-chloroethyl)ether|2|78|20|
|0000103231|Bis(2-ethylhexyl)adipate|0|0|100|
|0000542881|Bis(chloromethyl)ether|0|0|100|
|0000056359|Bis(tributyltin)oxide|0|0|100|
|0010294345|Boron trichloride|2|98|0|
|0007637072|Boron trifluoride|2|98|0|
|0000314409|Bromacil|2|53|45|
|0053404196|Bromacil, lithium salt|0|0|100|
|0007726956|Bromine|2|98|0|
|0000353593|Bromochlorodifluoromethane(Halon 1211)|1|98|1|
|0000075252|Bromoform|2|57|41|
|0000074839|Bromomethane|0|80|20|
|0000075638|Bromotrifluoromethane(Halon 1301)|0|99|1|
|0001689845|Bromoxynil|6|13|81|
|0001689992|Bromoxynil octanoate|38|0|62|
|0000357573|Brucine|1|55|44|
|0068187257|Butanoic acid, 4-[[3-(dimethylamino)propyl]amino]-4-oxo-, 2(or<br>3)-[(γ-ω-perfluoro-C6-20-alkyl)thio] derivs.|0|100|0|
|0000141322|Butyl acrylate|1|9|90|
|0000085687|Butyl benzylphthalate|0|0|100|
|0000123728|Butyraldehyde|0|9|91|
|0002650182|C.I. Acid Blue 9, Diammonium Salt|0|0|100|
|0003844459|C.I. Acid Blue 9, Disodium Salt|0|0|100|
|0004680788|C.I. Acid Green 3|0|0|100|
|0006459945|C.I. Acid Red 114|0|0|100|
|0000569642|C.I. Basic Green 4|0|0|100|
|0000989388|C.I. Basic Red 1|0|0|100|
|0001937377|C.I. Direct Black 38|0|0|100|
|0028407376|C.I. Direct Blue 218|0|0|100|
|0002602462|C.I. Direct Blue 6|0|0|100|
|0016071866|C.I. Direct Brown 95|0|0|100|
|0002832408|C.I. Disperse Yellow 3|0|0|100|
|0000081889|C.I. Food Red 15|0|0|100|
|0003761533|C.I. Food Red 5|0|0|100|
|0014302137|C.I. Pigment Green 36|0|0|100|
|0001328536|C.I. Pigment Green 7|0|0|100|
|0003118976|C.I. Solvent Orange 7|0|0|100|
|0000842079|C.I. Solvent Yellow 14|0|0|100|
|0000097563|C.I. Solvent Yellow 3|0|0|100|
|0000492808|C.I. Solvent Yellow 34|2|50|48|
|0000128665|C.I. Vat Yellow 4|0|0|100|
|0007440439|Cadmium|68|32|0|
|N078|Cadmium compounds|68|32|0|
|0000156627|Calcium cyanamide|2|98|0|
|0000133062|Captan|1|23|76|
|0000063252|Carbaryl|1|12|87|
|0001563662|Carbofuran|1|7|92|
|0000075150|Carbon disulfide|1|87|12|
|0000056235|Carbon tetrachloride|2|88|10|
|0000463581|Carbonyl sulfide|0|84|16|
|0005234684|Carboxin|1|24|75|
|0000120809|Catechol|0|8|92|
|N230|Certainglycol ethers|0|8|92|
|0002439012|Chinomethionate|0|0|100|
|0000133904|Chloramben|0|0|100|
|0000057749|Chlordane|61|1|38|
|0000115286|Chlorendic acid|0|0|100|
|0090982324|Chlorimuron-ethyl|1|23|76|
|0007782505|Chlorine|2|98|0|
|0010049044|Chlorine dioxide|2|98|0|
|0000079118|Chloroacetic acid|0|8|92|
|0000108907|Chlorobenzene|2|39|59|
|0000510156|Chlorobenzilate|39|3|58|
|0000075456|Chlorodifluoromethane(HCFC-22)|1|88|11|
|0000075003|Chloroethane|1|85|14|
|0000067663|Chloroform|1|73|26|
|0000074873|Chloromethane|1|59|40|
|0000107302|Chloromethyl methyl ether|0|0|100|
|N084|Chlorophenols|54|4|42|
|0000076062|Chloropicrin|1|88|11|
|0000126998|Chloroprene|1|93|6|
|0063938103|Chlorotetrafluoroethane|0|0|100|
|0001897456|Chlorothalonil|3|18|79|
|0000075729|Chlorotrifluoromethane(CFC-13)|0|99|1|
|0005598130|Chlorpyrifos-methyl|0|0|100|
|0064902723|Chlorsulfuron|1|54|45|
|0007440473|Chromium|76|24|0|
|N090|Chromium compounds (except for chromite ore mined in the<br>Transvaal Region)|76|24|0|
|0068141026|Chromium(III) perfluorooctanoate|0|100|0|
|0007440484|Cobalt|32|68|0|
|N096|Cobalt compounds|32|68|0|
|0007440508|Copper|72|28|0|
|N100|Copper compounds|72|28|0|
|0008001589|Creosote|0|0|100|
|0001319773|Cresol(mixed isomers)|0|8|92|
|0004170303|Crotonaldehyde|0|10|90|
|0000098828|Cumene|7|13|80|
|0000080159|Cumene hydroperoxide|1|24|75|
|0000135206|Cupferron|0|0|100|
|0021725462|Cyanazine|2|76|22|
|N106|Cyanide compounds|2|98|0|
|0001134232|Cycloate|0|0|100|
|0000110827|Cyclohexane|6|19|75|
|0067584423|Cyclohexanesulfonic acid, decafluoro(pentafluoroethyl)-,<br>potassium salt|0|100|0|
|0068156070|Cyclohexanesulfonic acid, decafluoro(trifluoromethyl)-, potassium<br>salt|0|100|0|
|0068156014|Cyclohexanesulfonic acid, nonafluorobis(trifluoromethyl)-,<br>potassium salt|0|100|0|
|0003107184|Cyclohexanesulfonic acid, undecafluoro-,potassium salt|0|100|0|
|0000108930|Cyclohexanol|0|9|91|
|0068359375|Cyfluthrin|38|0|62|
|0068085858|Cyhalothrin|0|0|100|
|0000533744|Dazomet|0|3|97|
|0053404607|Dazomet, sodium salt|0|0|100|
|0001163195|Decabromodiphenyl oxide|62|1|37|
|0002043530|Decane, 1,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8-heptadecafluoro-10-iodo-|0|100|0|
|0013684565|Desmedipham|5|9|86|
|0000117817|Di(2-ethylhexyl) phthalate|38|0|62|
|0002303164|Diallate|21|14|65|
|0025376458|Diaminotoluene(mixed isomers)|1|78|21|
|0000333415|Diazinon|12|7|81|
|0000334883|Diazomethane|0|0|100|
|0000132649|Dibenzofuran|18|4|78|
|0000124732|Dibromotetrafluoroethane|2|97|1|
|0000084742|Dibutylphthalate|29|1|70|
|0001918009|Dicamba|1|53|46|
|0000099309|Dichloran|0|0|100|
|0090454185|Dichloro-1,1,2-trifluoroethane|0|0|100|
|0025321226|Dichlorobenzene(mixed isomers)|8|47|45|
|0000075274|Dichlorobromomethane|1|68|31|
|0000075718|Dichlorodifluoromethane(CFC-12)|0|99|1|
|0000075434|Dichlorofluoromethane(HCFC-21)|1|91|8|
|0000075092|Dichloromethane|1|44|55|
|0127564925|Dichloropentafluoropropane|3|96|1|
|0000097234|Dichlorophene|0|0|100|
|0000076142|Dichlorotetrafluoroethane(CFC-114)|2|97|1|
|0034077877|Dichlorotrifluoroethane|1|98|1|
|0000062737|Dichlorvos|1|25|74|
|0051338273|Diclofopmethyl|0|0|100|
|0000115322|Dicofol|44|2|54|
|0000077736|Dicyclopentadiene|7|84|9|
|0001464535|Diepoxybutane|1|25|74|
|0000111422|Diethanolamine|0|8|92|
|0038727558|Diethatyl ethyl|0|0|100|
|0000084662|Diethylphthalate|0|0|100|
|0000064675|Diethyl sulfate|0|5|95|
|0035367385|Diflubenzuron|13|6|81|
|0000101906|Diglycidyl resorcinol ether|1|25|74|
|0000094586|Dihydrosafrole|10|30|60|
|N120|Diisocyanates|0|0|100|
|0055290647|Dimethipin|1|55|44|
|0000060515|Dimethoate|1|55|44|
|0002524030|Dimethyl chlorothiophosphate|0|0|100|
|0000131113|Dimethylphthalate|0|8|92|
|0000077781|Dimethyl sulfate|0|3|97|
|0000124403|Dimethylamine|0|8|92|
|0002300665|Dimethylamine dicamba|1|54|45|
|0000079447|Dimethylcarbamoyl chloride|0|0|100|
|0000088857|Dinitrobutylphenol|12|54|34|
|0025321146|Dinitrotoluene(mixed isomers)|1|53|46|
|0039300453|Dinocap|0|0|100|
|N150|Dioxin and dioxin-like compounds|0|0|100|
|0000957517|Diphenamid|0|0|100|
|0000122394|Diphenylamine|7|12|81|
|0002164070|Dipotassium endothall|1|24|75|
|0000136458|Dipropyl isocinchomeronate|6|3|91|
|0000138932|Disodium cyanodithioimidocarbonate|0|0|100|
|0118400718|Disulfides, bis(γ-ω-perfluoro-C6-20-alkyl)|0|100|0|
|0000330541|Diuron|2|50|48|
|0002043541|Dodecane, 1,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10-<br>heneicosafluoro-12-iodo-|0|100|0|
|0002439103|Dodine|0|0|100|
|0028434006|d-trans-Allethrin|0|0|100|
|0000106898|Epichlorohydrin|1|55|44|
|0056773423|Ethanaminium, N,N,N-triethyl-, salt with<br>1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,8-heptadecafluoro-1-octanesulfonic<br>acid (1:1)|0|100|0|
|0065636353|Ethanaminium, N,N-diethyl-N-methyl-2-[(2-methyl-1-oxo-2-<br>propenyl)oxy]-, methyl sulfate, polymer with 2-ethylhexyl 2-<br>methyl-2-propenoate, α-fluoro-ω-[2-[(2-methyl-1-oxo-2-<br>propenyl)oxy]ethyl]poly(difluoromethylene), 2-hydroxyethyl 2-<br>methyl-2-propenoate and N-(hydroxymethyl)-2-propenamide|0|100|0|
|0182176529|Ethaneperoxoic acid, reaction products with<br>3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,10-heptadecafluorodecyl<br>thiocyanate and 3,3,4,4,5,5,6,6,7,7,8,8,8-tridecafluorooctyl<br>thiocyanate|0|100|0|
|0065530645|Ethanol, 2,2'-iminobis-, compd. with α,α'-[phosphinicobis(oxy-2,1-<br>ethanediyl)]bis[ω-fluoropoly(difluoromethylene)] (1:1)|0|100|0|
|0065530747|Ethanol, 2,2'-iminobis-, compd. with α-fluoro-ω-[2-<br>(phosphonooxy)ethyl]poly(difluoromethylene) (1:1)|0|100|0|
|0065530634|Ethanol, 2,2'-iminobis-, compd. with α-fluoro-ω-[2-<br>(phosphonooxy)ethyl]poly(difluoromethylene) (2:1)|0|100|0|
|0013194484|Ethoprop|10|29|61|
|0000140885|Ethyl acrylate|0|10|90|
|0000541413|Ethyl chloroformate|1|43|56|
|0000100414|Ethylbenzene|3|45|52|
|0000074851|Ethylene|0|92|8|
|0000107211|Ethyleneglycol|0|8|92|
|0000075218|Ethylene oxide|0|9|91|
|0000096457|Ethylene thiourea|1|55|44|
|N171|Ethylenebisdithiocarbamic acid, salts and esters|2|98|0|
|0000151564|Ethyleneimine|1|55|44|
|0000075343|Ethylidene dichloride|1|78|21|
|0000052857|Famphur|0|0|100|
|0072623779|Fattyacids, C6-18,perfluoro, ammonium salts|0|100|0|
|0072968388|Fattyacids, C7-13,perfluoro, ammonium salts|0|100|0|
|0178535234|Fattyacids, linseed-oil,γ-ω-perfluoro-C8-14-alkyl esters|0|100|0|
|0060168889|Fenarimol|0|0|100|
|0013356086|Fenbutatin oxide|0|0|100|
|0066441234|Fenoxaprop-ethyl|0|0|100|
|0072490018|Fenoxycarb|0|0|100|
|0039515418|Fenpropathrin|0|0|100|
|0000055389|Fenthion|0|0|100|
|0051630581|Fenvalerate|0|0|100|
|0014484641|Ferbam|0|0|100|
|0069806504|Fluazifop-butyl|0|0|100|
|0002164172|Fluometuron|2|52|46|
|0007782414|Fluorine|2|98|0|
|0000051218|Fluorouracil|1|55|44|
|0069409945|Fluvalinate|0|0|100|
|0000133073|Folpet|2|20|78|
|0072178020|Fomesafen|3|47|50|
|0000050000|Formaldehyde|0|8|92|
|0000064186|Formic acid|0|8|92|
|0000076131|Freon 113(CFC-113)|3|96|1|
|0000110009|Furan|0|0|100|
|0000556525|Glycidol|0|0|100|
|0055910106|Glycine, N-[(heptadecafluorooctyl)sulfonyl]-N-propyl-, potassium<br>salt|0|100|0|
|0002991517|Glycine, N-ethyl-N-[(heptadecafluorooctyl)sulfonyl]-, potassium<br>salt|0|100|0|
|0067584627|Glycine, N-ethyl-N-[(pentadecafluoroheptyl)sulfonyl]-, potassium<br>salt|0|100|0|
|0067584536|Glycine, N-ethyl-N-[(tridecafluorohexyl)sulfonyl]-, potassium salt|0|100|0|
|0067584525|Glycine, N-ethyl-N-[(undecafluoropentyl)sulfonyl]-, potassium salt|0|100|0|
|0000076448|Heptachlor|50|1|49|
|N270|Hexabromocyclododecane|0|6|94|
|0000087683|Hexachloro-1,3-butadiene|45|23|32|
|0000118741|Hexachlorobenzene|60|2|38|
|0000077474|Hexachlorocyclopentadiene|44|11|45|
|0000067721|Hexachloroethane|18|56|26|
|0001335871|Hexachloronaphthalene|0|0|100|
|0000070304|Hexachlorophene|62|1|37|
|0065510556|Hexadecane,<br>1,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13,14,14<br>-nonacosafluoro-16-iodo-|0|100|0|
|0013252136|Hexafluoropropylene oxide dimer acid|0|100|0|
|0062037803|Hexafluoropropylene oxide dimer acid ammonium salt|0|100|0|
|0000680319|Hexamethylphosphoramide|0|0|100|
|0135228603|Hexane, 1,6-diisocyanato-, homopolymer, γ-ω-perfluoro-C6-20-<br>alc.-blocked|0|100|0|
|0051235042|Hexazinone|19|16|65|
|0067485294|Hydramethylnon|53|0|47|
|0000302012|Hydrazine|0|15|85|
|0010034932|Hydrazine sulfate(1:1)|2|98|0|
|0007647010|Hydrochloric acid (acid aerosols including mists, vapors, gas, fog,<br>and other airborne forms of any particle size)|0|0|100|
|0000074908|Hydrogen cyanide|2|98|0|
|0007664393|Hydrogen fluoride|2|98|0|
|0007783064|Hydrogen sulfide|0|0|100|
|0000123319|Hydroquinone|0|8|92|
|0035554440|Imazalil|15|21|64|
|0013463406|Ironpentacarbonyl|0|0|100|
|0000078842|Isobutyraldehyde|0|9|91|
|0000465736|Isodrin|62|1|37|
|0025311711|Isofenphos|0|0|100|
|0000078795|Isoprene|0|0|100|
|0000067630|Isopropyl alcohol (only persons who manufacture by the strong<br>acid process are subject, no supplier notification)|0|0|100|
|0000120581|Isosafrole|7|36|57|
|0077501634|Lactofen|31|0|69|
|0007439921|Lead|63|37|0|
|N420|Lead compounds|63|37|0|
|0000058899|Lindane|13|24|63|
|0000330552|Linuron|5|41|54|
|0029457725|Lithium(perfluorooctane)sulfonate|0|100|0|
|0000554132|Lithium carbonate|2|98|0|
|0000121755|Malathion|1|7|92|
|0000108316|Maleic anhydride|0|0|100|
|0000109773|Malononitrile|1|55|44|
|0012427382|Maneb|2|98|0|
|0007439965|Manganese|39|61|0|
|N450|Manganese compounds|39|61|0|
|0000108394|m-Cresol|0|8|92|
|0000099650|m-Dinitrobenzene|1|54|45|
|0000093652|Mecoprop|5|42|53|
|0000108781|Melamine|0|0|100|
|0007439976|Mercury|69|31|0|
|N458|Mercurycompounds|69|31|0|
|0000150505|Merphos|22|0|78|
|0000126987|Methacrylonitrile|1|27|72|
|0000137428|Metham sodium|0|27|73|
|0000067561|Methanol|0|8|92|
|0020354261|Methazole|0|0|100|
|0002032657|Methiocarb|0|0|100|
|0000094746|Methoxone|6|39|55|
|0003653483|Methoxone sodium salt|1|25|74|
|0000072435|Methoxychlor|45|2|53|
|0000096333|Methyl acrylate|0|9|91|
|0000079221|Methyl chlorocarbonate|0|1|99|
|0000078933|Methyl ethyl ketone|0|0|100|
|0000060344|Methyl hydrazine|1|25|74|
|0000074884|Methyl iodide|1|78|21|
|0000108101|Methyl isobutyl ketone|0|9|91|
|0000624839|Methyl isocyanate|0|0|100|
|0000556616|Methyl isothiocyanate|0|0|100|
|0000080626|Methyl methacrylate|0|10|90|
|0000298000|Methylparathion|2|6|92|
|0000376272|Methylperfluorooctanoate|0|100|0|
|0001634044|Methyl tert-butyl ether|1|60|39|
|0000074953|Methylene bromide|1|61|38|
|0000093152|Methyleugenol|0|0|100|
|0009006422|Metiram|0|0|100|
|0021087649|Metribuzin|1|54|45|
|0007786347|Mevinphos|0|0|100|
|0000090948|Michler's ketone|0|0|100|
|0002212671|Molinate|0|0|100|
|0001313275|Molybdenum trioxide|2|98|0|
|0000076153|Monochloropentafluoroethane(CFC-115)|1|98|1|
|0000150685|Monuron|0|0|100|
|0000505602|Mustardgas|0|0|100|
|0000108383|m-Xylene|3|18|79|
|0088671890|Myclobutanil|9|32|59|
|0000121697|N,N-Dimethylaniline|2|53|45|
|0000068122|N,N-Dimethylformamide|0|8|92|
|0000142596|Nabam|0|10|90|
|0000300765|Naled|1|25|74|
|0000091203|Naphthalene|4|6|90|
|0000071363|n-Butyl alcohol|0|8|92|
|0000117840|n-Dioctylphthalate|0|0|100|
|0001691992|N-Ethyl-N-(2-hydroxyethyl)perfluorooctanesulfonamide|0|100|0|
|0000110543|n-Hexane|9|53|38|
|0007440020|Nickel|38|62|0|
|N495|Nickel compounds|38|62|0|
|N503|Nicotine and salts|2|98|0|
|0001929824|Nitrapyrin|7|36|57|
|N511|Nitrate compounds (water dissociable; reportable only when in<br>aqueous solution)|0|10|90|
|0007697372|Nitric acid|0|0|100|
|0000139139|Nitrilotriacetic acid|0|8|92|
|0000098953|Nitrobenzene|0|8|92|
|0001836755|Nitrofen|0|0|100|
|0000051752|Nitrogen mustard|0|0|100|
|0000055630|Nitroglycerin|1|24|75|
|0000075525|Nitromethane|0|0|100|
|0000872504|N-Methyl-2-pyrrolidone|0|8|92|
|0000924425|N-Methylolacrylamide|0|8|92|
|0000055185|N-Nitrosodiethylamine|0|0|100|
|0000062759|N-Nitrosodimethylamine|0|0|100|
|0000924163|N-Nitrosodi-n-butylamine|0|0|100|
|0000621647|N-Nitrosodi-n-propylamine|1|54|45|
|0000086306|N-Nitrosodiphenylamine|5|42|53|
|0004549400|N-Nitrosomethylvinylamine|9|51|40|
|0000059892|N-Nitrosomorpholine|0|0|100|
|0000759739|N-Nitroso-N-ethylurea|1|55|44|
|0000684935|N-Nitroso-N-methylurea|1|55|44|
|0016543558|N-Nitrosonornicotine|0|0|100|
|0000100754|N-Nitrosopiperidine|1|55|44|
|N530|Nonylphenol|60|2|38|
|N535|Nonylphenol Ethoxylates|60|2|38|
|0027314132|Norflurazon|0|0|100|
|0000090040|o-Anisidine|1|25|74|
|0000134292|o-Anisidine hydrochloride|0|0|100|
|0000095487|o-Cresol|0|8|92|
|0002234131|Octachloronaphthalene|62|1|37|
|0029082744|Octachlorostyrene|0|0|100|
|0016517116|Octadecanoic acid,pentatriacontafluoro-|0|100|0|
|0000335660|Octanoyl fluoride,pentadecafluoro-|0|100|0|
|0000528290|o-Dinitrobenzene|1|54|45|
|0000091236|o-Nitroanisole|0|0|100|
|0000088722|o-Nitrotoluene|0|0|100|
|0019044883|Oryzalin|3|49|48|
|0020816120|Osmium tetroxide|2|98|0|
|0000095534|o-Toluidine|0|94|6|
|0000636215|o-Toluidine hydrochloride|1|54|45|
|0019666309|Oxadiazon|40|3|57|
|0000301122|Oxydemeton-methyl|0|0|100|
|0042874033|Oxyfluorfen|39|3|58|
|0000095476|o-Xylene|3|16|81|
|0010028156|Ozone|2|98|0|
|0000104949|p-Anisidine|0|0|100|
|0000123637|Paraldehyde|1|55|44|
|0001910425|Paraquat dichloride|1|55|44|
|0000056382|Parathion|9|2|89|
|0000106478|p-Chloroaniline|1|54|45|
|0000095692|p-Chloro-o-toluidine|0|0|100|
|0000104121|p-Chlorophenyl isocyanate|0|0|100|
|0000120718|p-Cresidine|1|54|45|
|0000106445|p-Cresol|0|8|92|
|0000100254|p-Dinitrobenzene|1|54|45|
|0001114712|Pebulate|0|0|100|
|0040487421|Pendimethalin|47|1|52|
|0000608935|Pentachlorobenzene|0|0|100|
|0000076017|Pentachloroethane|6|75|19|
|0000087865|Pentachlorophenol|54|4|42|
|0071608601|Pentanoic acid, 4,4-bis[(γ-ω-perfluoro-C8-20-alkyl)thio] derivs.|0|100|0|
|0000057330|Pentobarbital sodium|2|53|45|
|0000079210|Peracetic acid|0|8|92|
|0000594423|Perchloromethyl mercaptan|0|0|100|
|0000335762|Perfluorodecanoic acid|0|100|0|
|0000307551|Perfluorododecanoic acid|0|100|0|
|0000355464|Perfluorohexanesulfonic acid|0|100|0|
|0000375951|Perfluorononanoic acid|0|100|0|
|0001763231|Perfluorooctane sulfonic acid|0|100|0|
|0000335671|Perfluorooctanoic acid|0|100|0|
|0021652584|Perfluorooctyl Ethylene|0|100|0|
|0000307357|Perfluorooctylsulfonyl fluoride|0|100|0|
|0067905195|Perfluoropalmitic acid|0|100|0|
|0000376067|Perfluorotetradecanoic acid|0|100|0|
|0052645531|Permethrin|38|0|62|
|0000085018|Phenanthrene|32|6|62|
|0000108952|Phenol|0|8|92|
|0000077098|Phenolphthalein|0|0|100|
|0026002802|Phenothrin|38|0|62|
|0000057410|Phenytoin|2|51|47|
|0000075445|Phosgene|0|0|100|
|0007803512|Phosphine|2|98|0|
|0068412691|Phosphinic acid, bis(perfluoro-C6-12-alkyl)derivs.|0|100|0|
|0068412680|Phosphonic acid,perfluoro-C6-12-alkyl derivs.|0|100|0|
|0007664382|Phosphoric acid|0|0|100|
|0074499448|Phosphoric acid, γ-ω-perfluoro-C8-16-alkyl esters, compds. with<br>diethanolamine|0|100|0|
|0012185103|Phosphorus(yellow or white)|60|40|0|
|0000085449|Phthalic anhydride|0|1|99|
|0001918021|Picloram|2|90|8|
|0000088891|Picric acid|1|78|21|
|0000051036|Piperonyl butoxide|39|3|58|
|0029232937|Pirimiphos-methyl|0|0|100|
|0000100016|p-Nitroaniline|1|54|45|
|0000156105|p-Nitrosodiphenylamine|0|0|100|
|0065530623|Poly(difluoromethylene), α,α'-[phosphinicobis(oxy-2,1-<br>ethanediyl)]bis[ω-fluoro-|0|100|0|
|0065530703|Poly(difluoromethylene), α,α'-[phosphinicobis(oxy-2,1-<br>ethanediyl)]bis[ω-fluoro-, ammonium salt|0|100|0|
|0123171686|Poly(difluoromethylene), α-[2-(acetyloxy)-3-<br>[(carboxymethyl)dimethylammonio]propyl]-ω-fluoro-, inner salt|0|100|0|
|0065530838|Poly(difluoromethylene), α-[2-[(2-carboxyethyl)thio]ethyl]-ω-<br>fluoro-|0|100|0|
|0065530690|Poly(difluoromethylene), α-[2-[(2-carboxyethyl)thio]ethyl]-ω-<br>fluoro-, lithium salt|0|100|0|
|0065530598|Poly(difluoromethylene), α-fluoro-ω-(2-hydroxyethyl)-, 2-hydroxy-<br>1,2,3-propanetricarboxylate (3:1)|0|100|0|
|0065605563|Poly(difluoromethylene), α-fluoro-ω-(2-hydroxyethyl)-,<br>dihydrogen 2-hydroxy-1,2,3-propanetricarboxylate|0|100|0|
|0065605574|Poly(difluoromethylene), α-fluoro-ω-(2-hydroxyethyl)-, hydrogen<br>2-hydroxy-1,2,3-propanetricarboxylate|0|100|0|
|0065530612|Poly(difluoromethylene), α-fluoro-ω-[2-(phosphonooxy)ethyl]-|0|100|0|
|0095144120|Poly(difluoromethylene), α-fluoro-ω-[2-(phosphonooxy)ethyl]-,<br>ammonium salt|0|100|0|
|0065530725|Poly(difluoromethylene), α-fluoro-ω-[2-(phosphonooxy)ethyl]-,<br>diammonium salt|0|100|0|
|0065530714|Poly(difluoromethylene), α-fluoro-ω-[2-(phosphonooxy)ethyl]-,<br>monoammonium salt|0|100|0|
|0065605734|Poly(difluoromethylene), α-fluoro-ω-[2-[(1-oxo-2-<br>propenyl)oxy]ethyl]-, homopolymer|0|100|0|
|0065530656|Poly(difluoromethylene), α-fluoro-ω-[2-[(1-<br>oxooctadecyl)oxy]ethyl]-|0|100|0|
|0065530667|Poly(difluoromethylene), α-fluoro-ω-[2-[(2-methyl-1-oxo-2-<br>propenyl)oxy]ethyl]-|0|100|0|
|0080010373|Poly(difluoromethylene), α-fluoro-ω-[2-sulphoethyl)-|0|100|0|
|0029117086|Poly(oxy-1,2-ethanediyl), α-[2-<br>[ethyl[(heptadecafluorooctyl)sulfonyl]amino]ethyl]-ω-hydroxy-|0|100|0|
|0068958612|Poly(oxy-1,2-ethanediyl), α-[2-<br>[ethyl[(heptadecafluorooctyl)sulfonyl]amino]ethyl]-ω-methoxy-|0|100|0|
|0068298817|Poly(oxy-1,2-ethanediyl), α-[2-<br>[ethyl[(pentadecafluoroheptyl)sulfonyl]amino]ethyl]-ω-hydroxy-|0|100|0|
|0068958601|Poly(oxy-1,2-ethanediyl), α-[2-<br>[ethyl[(pentadecafluoroheptyl)sulfonyl]amino]ethyl]-ω-methoxy-|0|100|0|
|0056372237|Poly(oxy-1,2-ethanediyl), α-[2-<br>[ethyl[(tridecafluorohexyl)sulfonyl]amino]ethyl]-ω-hydroxy-|0|100|0|
|0068298806|Poly(oxy-1,2-ethanediyl), α-[2-<br>[ethyl[(undecafluoropentyl)sulfonyl]amino]ethyl]-ω-hydroxy-|0|100|0|
|0065545804|Poly(oxy-1,2-ethanediyl), α-hydro-ω-hydroxy-, ether with α-<br>fluoro-ω-(2-hydroxyethyl)poly(difluoromethylene) (1:1)|0|100|0|
|0070983594|Poly(oxy-1,2-ethanediyl), α-methyl-ω-hydroxy-, 2-hydroxy-3-[(γ-<br>ω-perfluoro-C6-20-alkyl)thio]propyl ethers|0|100|0|
|0037338480|Poly[oxy(methyl-1,2-ethanediyl)], α-[2-<br>[ethyl[(heptadecafluorooctyl)sulfonyl]amino]ethyl]-ω-hydroxy-|0|100|0|
|0068259392|Poly[oxy(methyl-1,2-ethanediyl)], α-[2-<br>[ethyl[(pentadecafluoroheptyl)sulfonyl]amino]ethyl]-ω-hydroxy-|0|100|0|
|0068259381|Poly[oxy(methyl-1,2-ethanediyl)], α-[2-<br>[ethyl[(tridecafluorohexyl)sulfonyl]amino]ethyl]-ω-hydroxy-|0|100|0|
|0068310178|Poly[oxy(methyl-1,2-ethanediyl)], α-[2-<br>[ethyl[(undecafluoropentyl)sulfonyl]amino]ethyl]-ω-hydroxy-|0|100|0|
|N575|Polybrominated biphenyls|0|0|100|
|N583|Polychlorinated alkanes(C10-C13)|0|0|100|
|0001336363|Polychlorinated biphenyls|61|1|38|
|N590|Polycyclic aromatic compounds|92|7|1|
|0007758012|Potassium bromate|2|98|0|
|0000128030|Potassium dimethyldithiocarbamate|1|28|71|
|0000137417|Potassium N-methyldithiocarbamate|0|27|73|
|0002795393|Potassiumperfluorooctanesulfonate|0|100|0|
|0000106503|p-Phenylenediamine|1|55|44|
|0041198087|Profenofos|0|0|100|
|0007287196|Prometryn|11|56|33|
|0023950585|Pronamide|10|30|60|
|0001918167|Propachlor|1|24|75|
|0238420809|Propanedioic acid, mono(γ-ω-perfluoro-C8-12-alkyl) derivs., bis[4-<br>(ethenyloxy)butyl] esters|0|100|0|
|0238420683|Propanedioic acid, mono(γ-ω-perfluoro-C8-12-alkyl) derivs., di-me<br>esters|0|100|0|
|0000709988|Propanil|4|44|52|
|0002312358|Propargite|42|44|14|
|0000107197|Propargyl alcohol|0|8|92|
|0031218834|Propetamphos|0|0|100|
|0060207901|Propiconazole|9|32|59|
|0000123386|Propionaldehyde|0|9|91|
|0000114261|Propoxur|0|8|92|
|0000115071|Propylene|0|91|9|
|0000075569|Propylene oxide|0|9|91|
|0000075558|Propyleneimine|1|25|74|
|0000106423|p-Xylene|3|19|78|
|0000110861|Pyridine|0|8|92|
|0061798683|Pyridinium, 1-(3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,10-<br>heptadecafluorodecyl)-, salt with 4-methylbenzenesulfonic acid<br>(1:1)|0|100|0|
|0000091225|Quinoline|1|24|75|
|0000106514|Quinone|1|59|40|
|0000082688|Quintozene|43|11|46|
|0076578148|Quizalofop-ethyl|0|0|100|
|0010453868|Resmethrin|0|0|100|
|0000078488|S,S,S-Tributyltrithiophosphate|37|0|63|
|0000081072|Saccharin (only persons who manufacture are subject, no supplier<br>notification)|1|25|74|
|0000094597|Safrole|8|34|58|
|0000078922|sec-Butyl alcohol|0|8|92|
|0007782492|Selenium|44|56|0|
|N725|Selenium compounds|44|56|0|
|0074051802|Sethoxydim|0|0|100|
|0000759944|S-Ethyl dipropylthiocarbamate|5|41|54|
|0083048651|Silane, (3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,10-<br>heptadecafluorodecyl)trimethoxy-|0|100|0|
|0078560448|Silane, trichloro(3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,10-<br>heptadecafluorodecyl)-|0|100|0|
|0125476713|Silicic acid (H4SiO4), disodium salt, reaction products with<br>chlorotrimethylsilane and 3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,10-<br>heptadecafluoro-1-decanol|0|100|0|
|0143372547|Siloxanes and Silicones, (3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,10-<br>heptadecafluorodecyl)oxy Me, hydroxy Me, Me octyl, ethers with<br>polyethylene glycol mono-Me ether|0|100|0|
|0007440224|Silver|66|34|0|
|N740|Silver compounds|66|34|0|
|0000122349|Simazine|2|77|21|
|0026628228|Sodium azide|2|98|0|
|0001982690|Sodium dicamba|1|53|46|
|0000128041|Sodium dimethyldithiocarbamate|1|28|71|
|0000062748|Sodium fluoroacetate|1|25|74|
|0001310732|Sodium hydroxide(solution)|0|0|100|
|0007632000|Sodium nitrite|2|98|0|
|0000132274|Sodium o-phenylphenoxide|0|0|100|
|0000131522|Sodiumpentachlorophenate|0|0|100|
|0000335955|Sodiumperfluorooctanoate|0|100|0|
|0007757826|Sodium sulfate(solution)|0|0|100|
|N746|Strychnine and salts|2|98|0|
|0000100425|Styrene|2|13|85|
|0000096093|Styrene oxide|1|25|74|
|0004151502|Sulfluramid|0|100|0|
|0180582790|Sulfonic acids, C6-12-alkane, γ-ω-perfluoro, ammonium salts|0|100|0|
|0007664939|Sulfuric acid (acid aerosols including mists, vapors, gas, fog, and<br>other airborne forms of any particle size)|0|0|100|
|0002699798|Sulfuryl fluoride|2|98|0|
|0035400432|Sulprofos|0|0|100|
|0034014181|Tebuthiuron|2|77|21|
|0003383968|Temephos|38|0|62|
|0005902512|Terbacil|0|0|100|
|0000100210|Terephthalic acid|0|0|100|
|0000075650|tert-Butyl alcohol|1|55|44|
|0000079947|Tetrabromobisphenol A|0|0|100|
|0000127184|Tetrachloroethylene|6|87|7|
|0000961115|Tetrachlorvinphos|7|11|82|
|0000064755|Tetracycline hydrochloride|1|55|44|
|0030046312|Tetradecane,<br>1,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12-<br>pentacosafluoro-14-iodo-|0|100|0|
|0000116143|Tetrafluoroethylene|0|0|100|
|0007696120|Tetramethrin|0|0|100|
|0000509148|Tetranitromethane|0|0|100|
|0007440280|Thallium|54|46|0|
|N760|Thallium compounds|54|46|0|
|0000148798|Thiabendazole|2|51|47|
|0000062555|Thioacetamide|1|55|44|
|0028249776|Thiobencarb|8|35|57|
|0097553952|Thiocyanic acid,γ-ω-perfluoro-C4-20-alkyl esters|0|100|0|
|0059669260|Thiodicarb|1|24|75|
|0068140216|Thiols, C10-20,γ-ω-perfluoro|0|100|0|
|0068140181|Thiols, C4-10,γ-ω-perfluoro|0|100|0|
|1078712885|Thiols, C4-20, γ-ω-perfluoro, telomers with acrylamide and acrylic<br>acid, sodium salts|0|100|0|
|0068140205|Thiols, C6-12,γ-ω-perfluoro|0|100|0|
|0070969470|Thiols, C8-20,γ-ω-perfluoro, telomers with acrylamide|0|100|0|
|0023564069|Thiophanate-ethyl|0|0|100|
|0023564058|Thiophanate-methyl|1|25|74|
|0000079196|Thiosemicarbazide|1|55|44|
|0000062566|Thiourea|1|25|74|
|0000137268|Thiram|1|24|75|
|0001314201|Thorium dioxide|90|10|0|
|0013463677|Titanium dioxide|0|0|100|
|0007550450|Titanium tetrachloride|2|98|0|
|0000108883|Toluene|1|23|76|
|0026471625|Toluene diisocyanate(mixed isomers)|2|1|97|
|0000584849|Toluene-2,4-diisocyanate|2|1|97|
|0000091087|Toluene-2,6-diisocyanate|2|1|97|
|0008001352|Toxaphene|62|1|37|
|0010061026|trans-1,3-Dichloropropene|1|31|68|
|0000110576|trans-1,4-Dichloro-2-butene|2|27|71|
|0043121433|Triadimefon|3|48|49|
|0002303175|Triallate|35|5|60|
|0000068768|Triaziquone|0|0|100|
|0101200480|Tribenuron-methyl|2|22|76|
|0001983104|Tributyltin fluoride|0|0|100|
|0002155706|Tributyltin methacrylate|0|0|100|
|0000052686|Trichlorfon|0|8|92|
|0000076028|Trichloroacetyl chloride|0|0|100|
|0000079016|Trichloroethylene|1|93|6|
|0000075694|Trichlorofluoromethane(CFC-11)|1|98|1|
|0057213691|Triclopyr-triethylammonium salt|1|25|74|
|0000121448|Triethylamine|1|56|43|
|0001582098|Trifluralin|57|3|40|
|0026644462|Triforine|0|0|100|
|0000639587|Triphenyltin chloride|0|0|100|
|0000076879|Triphenyltin hydroxide|14|86|0|
|0000126727|Tris(2,3-dibromopropyl) phosphate|0|0|100|
|0000072571|Trypan blue|1|55|44|
|0000051796|Urethane|1|55|44|
|0007440622|Vanadium(except when contained in an alloy)|32|68|0|
|N770|Vanadium compounds|32|68|0|
|0050471448|Vinclozolin|0|0|100|
|0000108054|Vinyl acetate|0|11|89|
|0000593602|Vinyl bromide|0|0|100|
|0000075014|Vinyl chloride|0|92|8|
|0000075025|Vinyl fluoride|0|0|100|
|0000075354|Vinylidene chloride|1|91|8|
|N874|Warfarin and salts|3|97|0|
|0001330207|Xylene(mixed isomers)|3|17|80|
|0007440666|Zinc(fume or dust)|66|34|0|
|N982|Zinc compounds|66|34|0|
|0012122677|Zineb|0|2|98|



