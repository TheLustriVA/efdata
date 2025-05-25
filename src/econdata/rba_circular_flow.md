---
title: RBA Circular FThe Reserve Bank of Australia's Circular Flow Model - Framework and Open Data Sources for Macroeconomic Modelling
date: 2025-05-25
tags: []
---

This report details the Reserve Bank of Australia's (RBA) framework for the macroeconomic circular flow model and identifies open, freely accessible data sources, primarily Application Programming Interfaces (APIs) and web-scrapable resources, for acquiring the datasets necessary to model this flow.

## 1. The Reserve Bank of Australia's Macroeconomic Circular Flow Model: Definition and Core Components

The circular flow of income model is a fundamental concept in macroeconomics, illustrating the continuous movement of money, resources, and goods and services within an economy. The Reserve Bank of Australia provides a clear framework for understanding these interactions.

### 1.1. RBA's Official Definition and Visual Framework

The RBA defines the circular flow model as a depiction of "the flow of money and goods and services between different sectors of the economy".1 The primary sectors identified in the RBA's educational material are:

- Household sector: Individuals in the economy.

- Firms sector: Businesses in the economy.

- Financial sector: Banks and other financial institutions.

- Government sector: National, state, and local government.

- Overseas sector: Encompasses economic transactions with the rest of the world.

The core flows illustrated in the RBA's model include 1:

- Income: Money received by households (e.g., wages from firms, rent, and interest from the financial sector).

- Expenditure: The purchase of goods and services by households from firms.

- Economic resources: Inputs such as land, labour, and capital (machinery, buildings, equipment) that flow from households to firms for use in production.

- Output: Goods or services produced by firms to be sold.

- Savings (S): Money saved by households, which flows to the Financial sector.

- Investment (I): Money the Financial sector lends to Firms for spending on capital goods like machinery, buildings, and equipment.

- Taxation (T): Money paid by Households and Firms to the Government sector.

- Government expenditure (G): Money the government spends on public goods and services, which flows to Firms (as payments for goods/services) and Households (as wages or benefits).

- Imports (M): Goods and services produced by businesses in other countries and sold to Australia, resulting in a payment flow out of Australia.

- Exports (X): Goods and services produced by Firms in Australia and sold to other countries, resulting in a payment flow into Australia.

The RBA provides a simplified visual diagram where solid arrows indicate the flow of money through these sectors.1 This diagram serves as the primary visual representation for the RBA's basic model. A similar, more generic representation is also produced by institutions like the Federal Reserve Bank of St. Louis, which reinforces the fundamental concepts of money typically flowing clockwise and goods, services, and resources flowing counter-clockwise in such diagrams.2 The RBA's educational material offers a foundational, though simplified, model which is the essential starting point for identifying the components that require quantification for a macroeconomic model.

### 1.2. Conceptual Underpinnings: Leakages and Injections

While the RBA's basic diagram 1 illustrates the flows, a more developed understanding, consistent with standard macroeconomic theory, incorporates the concepts of "leakages" (withdrawals from the primary income-expenditure flow) and "injections" (additions to this flow).3

- Leakages from the circular flow are:

- Savings (S): Income not spent on consumption but channeled to the financial sector.

- Taxation (T): Income transferred to the government sector.

- Imports (M): Expenditure on goods and services produced overseas.

- Injections into the circular flow are:

- Investment (I): Expenditure by firms on capital goods, often financed through the financial sector.

- Government Spending (G): Expenditure by the government on goods, services, and transfers.

- Exports (X): Expenditure by foreign entities on domestically produced goods and services.

For the economy to be in equilibrium, the total sum of leakages must equal the total sum of injections. In a five-sector model (households, firms, financial, government, and overseas sectors), this equilibrium condition is represented by the identity:

S+T+M=I+G+X.3

This identity is crucial for validating any comprehensive model of the circular flow. Although the RBA's educational PDF 1 does not explicitly use the terms "leakages" and "injections," these are standard macroeconomic terms that accurately describe the flows depicted to and from the financial, government, and overseas sectors in their model. Understanding this relationship is important for structuring data collection to ensure all sides of the economic ledger are adequately covered and for verifying the internal consistency of a constructed model.

### 1.3. RBA's Broader Macroeconomic Modeling Context (MARTIN and DINGO)

The RBA's publicly presented circular flow model serves as an introductory framework. For policy analysis and forecasting, the RBA utilizes more sophisticated macroeconomic models, principally its macroeconometric model MARTIN and its dynamic stochastic general equilibrium (DSGE) model DINGO.4 These models, while not explicitly labeled as "circular flow models" in RBA publications, analyze the impact of monetary policy and other economic shocks on sectors and flows that are direct counterparts to the components of the circular flow.4

Key sectors and their interactions analyzed within these advanced models include 4:

- Households: Their consumption and savings decisions, dwelling investment, and cash flow responses to interest rate changes are critical.

- Businesses (Firms): Business investment decisions are a key focus.

- Financial Sector: This sector facilitates the transmission of monetary policy, primarily through its impact on interest rates. While not always explicitly modeled with a full "credit channel," the supply of credit is acknowledged as a transmission mechanism.

- International Sector (Rest of the World): Interactions occur through trade (imports and exports) and capital flows, significantly influenced by the exchange rate.

The Government sector's public demand is often treated as exogenous in specific monetary policy simulations within these models, meaning its behavior is assumed rather than determined by the model's internal dynamics in those exercises.4

The RBA's models emphasize several key transmission channels through which monetary policy affects economic activity and inflation; these channels essentially describe the dynamics of the circular flow 4:

- The Exchange Rate Channel: Directly impacts net exports (X-M) and inflation.

- Asset Prices and Wealth Channel: Affects household consumption and business/dwelling investment.

- Savings and Investment Channel: Influences household consumption (via incentives to save) and business/dwelling investment (via borrowing costs).

- Cash Flow Channel: Impacts household consumption by altering disposable income through debt servicing costs and interest earnings.

The RBA's detailed models, such as MARTIN, suggest that the exchange rate and the savings and investment channels are particularly prominent in the transmission of monetary policy to the broader economy. For instance, the exchange rate is noted as an important channel, especially for inflation, and net trade (driven by exchange rate and demand effects) can explain a significant portion of GDP changes in the short term.4 Conversely, while individual household cash flows are sensitive to interest rate changes, the aggregate cash flow channel is considered to play a relatively smaller role in overall GDP impact within these models, partly due to offsetting effects between borrowers and savers.4 This understanding, derived from the RBA's more complex analytical tools, can inform the prioritization of data for a comprehensive circular flow model, suggesting a greater emphasis on data related to trade, exchange rates, investment, and savings.

## 2. Data Requirements for Modeling the Circular Flow

To quantitatively model the RBA's circular flow framework, its conceptual components must be mapped to measurable economic variables. These variables are typically found in national accounts statistics.

### 2.1. Mapping Model Components to Measurable Economic Variables

The translation from the RBA's model components 1 to specific economic variables is as follows:

- Household Sector:

- Income (Y): Key variables include Gross Household Disposable Income and Compensation of Employees. These represent the total income available to households after taxes and transfers, and the income earned from labor, respectively.

- Expenditure (C): This corresponds to Household Final Consumption Expenditure (HFCE), which measures spending by households on goods and services.

- Savings (S): Measured by Household Net Saving (which is Gross Saving minus Consumption of Fixed Capital by households) or derived as the residual from disposable income after consumption.

- Firms Sector:

- Output: Represented by Gross Domestic Product (GDP) at market prices, or Gross Value Added (GVA) at basic prices, often disaggregated by industry. GVA measures the value of output less the value of intermediate consumption.

- Investment (I): This primarily refers to Gross Fixed Capital Formation (GFCF) by the private sector. GFCF includes expenditure on dwellings, non-dwelling construction (buildings, infrastructure), machinery and equipment, and intellectual property products (e.g., software, R&D).

- Government Sector:

- Taxation (T): Includes various categories such as Taxes on income, Taxes on production and imports (e.g., GST, excise duties), and other taxes collected by all levels of government.

- Government Expenditure (G): Comprises Government Final Consumption Expenditure (GFCE) (spending on public services like health and education) and Government Gross Fixed Capital Formation (public investment in infrastructure, etc.).

- Financial Sector:

- This sector acts as an intermediary, channeling savings into investment. Direct "flow" data through this sector for a simple model is less common than measuring aggregate savings and investment themselves. Its influence is also captured through variables like interest rates (on deposits and loans) and credit aggregates (growth in lending to households and businesses) 5, which affect saving and investment decisions.

- Overseas Sector:

- Exports (X): Exports of Goods and Services measures the value of domestically produced goods and services sold to foreign residents.

- Imports (M): Imports of Goods and Services measures the value of foreign-produced goods and services purchased by domestic residents.

- Net Exports (NX or X-M): The difference between exports and imports, also known as the trade balance.

The RBA's simplified model 1 often requires significant disaggregation for practical modeling. For instance, "Investment (I)" is not a single data point but is composed of various private and public components, further broken down by asset type (dwellings, non-dwelling construction, machinery and equipment, etc.). National accounts statistics provide this necessary level of detail. Similarly, "Income" can be disaggregated into compensation of employees, gross operating surplus, and gross mixed income to better understand its sources.

The interconnectedness of these components is fundamental. For example, household income (Y) is allocated to consumption (C), savings (S), and net taxes (Taxes paid minus government transfers received). Therefore, the data collected must allow for the modeling of these interdependencies. Changes in one component, such as Compensation of Employees, will directly influence Household Final Consumption Expenditure and Household Net Saving.

The following table provides a mapping of the core components from the RBA's circular flow model to their corresponding standard economic data variables.

Table 1: Core Components of the RBA Circular Flow Model and Corresponding Data Variables

|   |   |   |   |
|---|---|---|---|
|Sector|RBA Model Flow (from )|Specific Economic Variable|Typical Data Source (Primary)|
|Household Sector|Income|Gross Household Disposable Income; Compensation of Employees|ABS National Accounts|
||Expenditure|Household Final Consumption Expenditure (HFCE)|ABS National Accounts|
||Savings (S)|Household Net Saving; Gross Saving (Households)|ABS National Accounts|
|Firms Sector|Output|Gross Domestic Product (GDP); Gross Value Added (GVA) by Industry|ABS National Accounts|
||Investment (I)|Gross Fixed Capital Formation (GFCF) - Private (by asset type: Dwellings, Machinery & Equipment, etc.)|ABS National Accounts|
|Government Sector|Taxation (T)|Taxes on Income; Taxes on Production and Imports; Other taxes|ABS Government Finance Statistics|
||Government Expenditure (G)|Government Final Consumption Expenditure (GFCE); Gross Fixed Capital Formation - Public|ABS National Accounts; ABS GFS|
|Financial Sector|Facilitates S & I|Interest Rates (various); Credit Aggregates; Monetary Aggregates|RBA Statistical Tables|
|Overseas Sector|Exports (X)|Exports of Goods and Services|ABS International Trade Statistics|
||Imports (M)|Imports of Goods and Services|ABS International Trade Statistics|
||Payment for Exports (flow of money in)|Value of Exports of Goods and Services|ABS International Trade Statistics|
||Payment for Imports (flow of money out)|Value of Imports of Goods and Services|ABS International Trade Statistics|
||(Net Exports: X-M)|Balance on Goods and Services|ABS International Trade Statistics|
|Overall Economy|Economic Resources (Labour, Capital from Households to Firms)|Labour Force Statistics (Employment, Hours Worked); Capital Stock estimates|ABS Labour Force; ABS Nat. Accounts|
||Income (Wages, Rent, Interest from Firms/Financial to HH)|Compensation of Employees; Gross Mixed Income & Gross Operating Surplus (components of GDP(I)); Interest & Dividend Income|ABS National Accounts|

## 3. Open Data Sources: APIs and Web-Scrapable Resources for Australian Macroeconomic Data

Acquiring the necessary data for modeling Australia's circular flow involves accessing information from primary official sources, predominantly the Reserve Bank of Australia (RBA) and the Australian Bureau of Statistics (ABS). The methods of access vary, ranging from sophisticated APIs to direct downloads of data tables.

### 3.1. Primary Official Sources

- Reserve Bank of Australia (RBA): The RBA is a key source for financial and monetary statistics critical for understanding the financial sector's role and the impact of monetary policy on the circular flow. These include data on interest rates, credit aggregates, monetary aggregates, and exchange rates. While the RBA has some specific APIs, such as for securitisation data 6 (which is not directly relevant for general circular flow modeling), much of its macroeconomic data is disseminated through statistical tables available on its website.5 A general, comprehensive SDMX-style API for all its statistical tables, akin to what the ABS offers, is not apparent. Therefore, for many RBA series, direct download or programmatic scraping of these tables is the most viable open access method.

- Australian Bureau of Statistics (ABS): The ABS is the principal agency for collecting and disseminating a wide array of economic statistics, forming the backbone for any macroeconomic model of Australia. This includes comprehensive National Accounts (GDP, income, expenditure, saving, investment), International Trade statistics, and Government Finance Statistics (GFS). The ABS has been progressively enhancing its data dissemination methods, offering several APIs, including the ABS Indicator API for headline figures and the more detailed ABS Data API (Beta) which uses the Statistical Data and Metadata Exchange (SDMX) standard.8 Additionally, data is available through its website via tools like the ABS Data Explorer and as downloadable files (e.g., CSV, XLSX) for specific publications.12

This division of labor is quite clear: the ABS provides the bulk of National Accounts, Trade, and GFS data, increasingly with API options, while the RBA provides crucial financial market data often through web tables. A comprehensive model will necessitate tapping into both institutions.

### 3.2. Data Access Landscape: APIs vs. Web Scraping

The choice between using APIs and web scraping (or direct file downloads) depends on the availability and format of the data:

- APIs: Offer structured, machine-readable access to data and are ideal for automating data retrieval and updates. The ABS is actively encouraging API usage, indicating a strategic direction towards this mode of dissemination.14 This suggests that API-based methods for ABS data should be prioritized where available, as they are likely to be better maintained and more stable in the long run. Both the ABS Indicator API and the ABS Data API (Beta) are designed for machine-to-machine contact.9

- Web Scraping/Direct Download: This approach becomes necessary when data is primarily available in formats like CSV or XLSX tables on websites, or when an API does not cover the specific granularity or historical depth required. This is common for many RBA statistical tables 5 and for certain detailed ABS releases, such as the annual Government Finance Statistics.12 While effective, this method may require more maintenance to adapt to changes in website structure or file locations.

A hybrid data acquisition strategy is often the most practical approach. APIs are preferred for their robustness and efficiency when available. However, for datasets not exposed via suitable APIs, programmatic downloading of files or scraping structured web tables remains a necessary alternative.

## 4. Detailed Guide to Accessing Datasets

This section provides specific guidance on accessing the required datasets from the RBA and ABS, detailing relevant tables, API endpoints, and methods.

### 4.1. Reserve Bank of Australia (RBA) Data (Web-Scrapable Tables)

The RBA's "Statistical Tables" webpage serves as the central repository for a wide range of economic and financial data.5 Data is typically organized by category, and most tables offer direct download links to XLSX or CSV files, making automated downloading (a form of web scraping) relatively straightforward.

- Locating Data: Navigate to the RBA website's statistics section. The "Statistical Tables" page lists data by categories such as "Money and Credit Statistics," "Interest Rates," and "Exchange Rates."

- Relevant Tables for Circular Flow Components:

- Financial Aggregates (relevant to Savings (S) and Investment (I) flows and financial sector intermediation):

- Table D1: Growth in Selected Financial Aggregates

- Table D2: Lending and Credit Aggregates

- Table D3: Monetary Aggregates

- Table D4: Debt Securities Outstanding

- (Source: 5)

- Interest Rates (influencing Savings (S) and Investment (I) decisions):

- Table F1: Interest Rates and Yields – Money Market – Daily

- Table F1.1: Interest Rates and Yields – Money Market – Monthly

- Table F4: Advertised Deposit Rates

- Table F5: Indicator Lending Rates (key for borrowing costs)

- Table F6: Housing Lending Rates

- Table F7: Business Lending Rates

- (Source: 5)

- Exchange Rates (influencing Exports (X) and Imports (M)):

- Table F11: Exchange Rates – Historical – Daily and Monthly

- Table F11.1: Exchange Rates – Daily - 2023 to Current (example year, actual will be current)

- Table F15: Real Exchange Rate Measures

- (Source: 5)

- Data Formats and Access:  
    Most RBA statistical tables provide "Data" links that point directly to downloadable files, typically in XLSX and CSV formats.5 For example, the data for Table D1 can be accessed via a URL like <https://www.rba.gov.au/statistics/tables/csv/d1-data.csv.5>

- Web Scraping Guidance:

1. Identify the base URL for the RBA's statistical tables section.

2. For each required table, locate the direct link to the CSV or XLSX file. These URLs are generally stable but should be periodically verified.

3. Develop scripts (e.g., using Python libraries like requests and pandas) to programmatically download these files.

4. Parse the downloaded files to extract the necessary time series data. Regular checks for changes in URL structure or file formats are advisable, although the RBA's direct file links tend to be consistent over time.

Table 2: Summary of Key RBA Statistical Tables for Circular Flow Data

|   |   |   |   |   |
|---|---|---|---|---|
|RBA Table ID|Table Title|Circular Flow Relevance|Example Direct CSV Link (Illustrative Structure)|Example Direct XLSX Link (Illustrative Structure)|
|D1|Growth in Selected Financial Aggregates|Savings (S), Investment (I) proxies, Financial Flows|.../csv/d1-data.csv|.../xls/d01hist.xlsx|
|D2|Lending and Credit Aggregates|Investment (I) financing, Financial Flows|.../csv/d2-data.csv|.../xls/d02hist.xlsx|
|D3|Monetary Aggregates|Money Supply, Financial Sector activity|.../csv/d3-data.csv|.../xls/d03hist.xlsx|
|F1.1|Interest Rates and Yields – Money Market – Monthly|Cost of borrowing/return on savings (influences S, I)|.../csv/f1.1-data.csv|.../xls/f01hist.xlsx|
|F5|Indicator Lending Rates|Cost of borrowing for firms/households (influences I, C)|.../csv/f5-data.csv|.../xls/f05hist.xlsx|
|F11|Exchange Rates – Historical|Valuation of X, M; International competitiveness|(Historical data often grouped by year or in larger files)|(Historical data often grouped by year or in larger files)|
|F11.1|Exchange Rates – Daily - Current|Valuation of X, M; International competitiveness|.../csv/f11.1-data.csv|.../xls-hist/2023-current.xls (example year)|
|F15|Real Exchange Rate Measures|Real valuation of X, M; Terms of Trade impact|.../csv/f15-data.csv|.../xls/f15hist.xlsx|

Note: Base URL for links is <https://www.rba.gov.au/statistics/tables/>. Actual file names and paths should be verified from 5 and the RBA website.

### 4.2. Australian Bureau of Statistics (ABS) Data

The ABS offers a hierarchy of data access methods, from simple APIs for headline figures to more complex APIs for detailed data, and direct downloads for specific publications.

#### 4.2.1. ABS Indicator API (Headline Statistics)

- Purpose: This API provides quick access to headline economic statistics, including key aggregates for National Accounts (Expenditure on Gross Domestic Product - GDP) and International Trade in Goods and Services.10 It is suitable for obtaining high-level data for components like Consumption (C), Investment (I), Government Spending (G), Exports (X), and Imports (M).

- Endpoint: The base URL is <https://indicator.api.abs.gov.au.10>

- To get data: GET /v1/data/{dataflowIdentifier}/{format}

- To get metadata: GET /v1/metadata/{dataflowIdentifier}/{format}

- Authentication: An API Key is required. This key must be included as a header in API requests: "x-api-key: YOUR_API_KEY".10 The process for obtaining an API key involves reading the terms of use and submitting a request form as outlined on the ABS website.10

- Data Formats: Data is available in JSON, CSV, and XML.10 Metadata is available in JSON and XML.

- Key Dataflows for Circular Flow Model:

- GDPE_H: Australian National Accounts, Expenditure on Gross Domestic Product (GDP).10 This dataflow provides headline figures for total household consumption, government consumption, gross fixed capital formation, exports, and imports.

- ITGS_H: International Trade in Goods and Services.10 This dataflow provides headline figures for total exports and imports of goods and services.

- Accessing Specific Series: To understand the structure of data within these dataflows (i.e., the specific series available, their dimension codes, measures, and adjustments), it is essential to query the metadata endpoint. For example, for GDPE_H, one would query GET <https://indicator.api.abs.gov.au/v1/metadata/GDPE_H/json> (substituting YOUR_API_KEY in the header).

- Note on Metadata Access: Direct access to the metadata endpoints for GDPE_H 16 and ITGS_H 17 was not available during the compilation of this report. Users must query these live endpoints themselves to get the precise current structure.

- Based on typical National Accounts structures and the nature of the Indicator API (headline figures), the GDPE_H dataflow likely includes dimensions such as:

- MEASURE_ITEM or SERIES_ID: Distinguishing between components like Household final consumption expenditure, Government final consumption expenditure, Gross fixed capital formation (total or broad private/public), Exports of goods and services, and Imports of goods and services.

- MEASURE_TYPE or PRICE_BASIS: Codes for Current Prices (e.g., A2302300A) and Chain Volume Measures (e.g., A2302302X).

- ADJUSTMENT_TYPE or SEASADJ: Codes for Seasonally Adjusted (e.g., 20) and Original (e.g., 10).

- FREQUENCY: Likely fixed to Quarterly (e.g., Q).

- REGION: Likely fixed to Australia (e.g., AUS).

- Similarly, for ITGS_H, dimensions would distinguish between Exports and Imports, Goods and Services, and different price/adjustment measures.

- Example Query (Conceptual for GDPE_H data in JSON): GET <https://indicator.api.abs.gov.au/v1/data/GDPE_H/json> (with API key). This retrieves all series within the GDPE_H dataflow. Filtering to a specific series (e.g., Household Final Consumption Expenditure, Chain Volume Measures, Seasonally Adjusted) requires parsing the response based on the codes identified from the metadata. The Indicator API is designed for simplicity, often providing pre-selected headline series rather than deep filtering capabilities in the data request itself.

Table 3: Key ABS Indicator API Dataflows for Macroeconomic Modeling

|   |   |   |   |   |
|---|---|---|---|---|
|Dataflow ID|Dataflow Name|Relevant Circular Flow Components|Key Series Expected (Examples)|Available Formats|
|GDPE_H|Expenditure on Gross Domestic Product (GDP)|C, I, G, X, M|Total Household Consumption, Total Government Consumption, Total Gross Fixed Capital Formation, Total Exports of G&S, Total Imports of G&S (Current Prices, CVM, Seas Adj.)|JSON, CSV, XML|
|ITGS_H|International Trade in Goods and Services|X, M|Total Exports of Goods, Total Imports of Goods, Total Exports of Services, Total Imports of Services (Current Prices, CVM, Seas Adj.)|JSON, CSV, XML|

#### 4.2.2. ABS Data API (Beta) (Detailed Statistics via SDMX)

- Purpose: This API provides machine-to-machine access to a wide range of detailed ABS statistics using the SDMX (Statistical Data and Metadata Exchange) standard. It is suitable for obtaining granular data for National Accounts (including income components, detailed expenditure, savings, and investment breakdowns), International Trade (by commodity and partner country), and potentially some Government Finance Statistics, although GFS is often provided in spreadsheets.8

- Endpoint: The base endpoint is <https://api.data.abs.gov.au>. Data queries typically follow the path /rest/data/{dataflowIdentifier}/{dataKey}.9

- Authentication: Authentication is optional for the Data API (Beta). However, for production systems or applications, registering for an API key is strongly encouraged. This key helps the ABS identify requests and assist with any issues.9

- Data Formats: The API supports SDMX-ML (XML-based format for SDMX), SDMX-JSON, and SDMX-CSV.9

- Understanding SDMX and Discovering Data:

- Dataflow Identifier (dataflowIdentifier): This identifies the specific dataset. The format is typically {agencyId},{flowId},{version}, for example, ABS,CPI,1.0.0. ABS is the agency ID. flowId is the unique identifier for the dataset (e.g., CPI for Consumer Price Index). version specifies the version of the dataflow (e.g., 1.0.0). The agency ID and version are sometimes optional, defaulting to ABS and latest respectively.20

- Listing all Dataflows: To discover available flowIds, one can query the dataflow endpoint: GET <https://data.api.abs.gov.au/rest/dataflow/ABS> (or /rest/dataflow).21 This returns a list of all dataflows, which is crucial for identifying the specific flowId for datasets like National Accounts or International Trade.

- Data Key (dataKey): This part of the URL path filters the data to specific series within a dataflow. It is a dot-separated list of dimension codes (e.g., M1.AUS.Q). The order of dimensions in the dataKey must match the order defined in the dataset's Data Structure Definition (DSD). Wildcarding (leaving a dimension empty, e.g., M1..Q) and the OR operator (+ for multiple codes within a dimension, e.g., M1+M2.AUS.Q) are supported.20

- ABS Data Explorer: The ABS Data Explorer (accessible via the ABS website, e.g.13) is an invaluable web tool for browsing datasets. Critically, for many datasets, it can generate the API data query (including the dataflowIdentifier and dataKey) for a user's selected table view.13 This significantly simplifies the process of constructing valid API requests for the Data API (Beta).

- Query Parameters: Additional query parameters can refine the request, such as startPeriod and endPeriod for time ranges, detail (e.g., full, dataonly, serieskeysonly, nodata) to control the amount of metadata returned, and dimensionAtObservation (e.g., TIME_PERIOD for time series view, AllDimensions for a flat list).20

- Finding Relevant Dataflows for Circular Flow Components:

- National Accounts (Income, Detailed Expenditure, Savings, Investment):

- Use the ABS Data Explorer. Search for terms like "Australian System of National Accounts," "National Income, Expenditure and Product," "Household Income," "Capital Formation," "Final Consumption Expenditure."

- Relevant ABS Catalogue numbers (useful as keywords or for context when browsing Data Explorer or the list of dataflows):

- 5204.0: Australian System of National Accounts.24

- 5206.0: Australian National Accounts: National Income, Expenditure and Product.24

- Example (Conceptual): After using Data Explorer to identify a dataflow for detailed National Income (e.g., its flowId might be NA_MAIN_AGGS giving a dataflowIdentifier like ABS,NA_MAIN_AGGS,1.0.0), a dataKey would be constructed by specifying codes for dimensions such as Account Type (e.g., Income), Series Type (e.g., Compensation of Employees), Sector (e.g., Households), Adjustment Type (e.g., Seasonally Adjusted), and Region (e.g., Australia). The Data Explorer helps identify these dimension codes.

- International Trade (Detailed Goods/Services, Partners, etc.):

- Use the ABS Data Explorer. Search for "International Trade in Goods and Services."

- Relevant ABS Catalogue number: 5368.0 (International Trade in Goods and Services, Australia).24

- Example (Conceptual): A dataflow for detailed international trade (e.g., ABS,ITGS_DETAILED,1.0.0) would allow dataKey construction specifying dimensions for Flow Type (Export/Import), Commodity Code (e.g., SITC or HS), Country, etc.

- Government Finance Statistics (Taxation Revenue, Detailed Government Spending):

- Use the ABS Data Explorer to search for "Government Finance Statistics."

- Relevant ABS Catalogue number: 5512.0 (Government Finance Statistics, Annual).12

- Note: While detailed GFS data is often provided via XLSX downloads 12, it is essential to check the Data Explorer or the full dataflow list (/rest/dataflow/ABS) to see if any GFS components are available via the Data API (Beta). If not, web scraping of the spreadsheets (Section 4.2.3) is the primary alternative.

The ABS Data API (Beta) is powerful due to its coverage of detailed statistics. However, it requires a degree of familiarity with SDMX concepts. The ABS Data Explorer is the recommended starting point for users to visually identify desired datasets and then obtain the corresponding API query structure, significantly lowering the barrier to using this comprehensive API.

Table 4: Discovering ABS Data API (Beta) Dataflows for Circular Flow Components

|   |   |   |   |   |
|---|---|---|---|---|
|Circular Flow Component|Relevant ABS Publication/Catalogue (Example)|Keywords for Data Explorer / Dataflow List Search|Example Variables Sought (Illustrative)|Notes on dataKey Construction (Illustrative)|
|Household Income (Y)|5206.0 (Nat. Income, Exp. & Prod.)|"National Income", "Household Income", "Compensation of Employees", "Gross Mixed Income", "Property Income"|Wages & Salaries, Profits, Dividends received by Households|Dimensions: Income Type, Sector (Households), Measure (Current Prices), Adjustment (Seasonally Adjusted/Original), Region (Australia), Frequency (Quarterly).|
|Household Consumption (C) - Detailed|5206.0 (Nat. Income, Exp. & Prod.)|"Household Final Consumption Expenditure", "Consumption by purpose"|HFCE by COICOP categories (e.g., Food, Housing, Transport)|Dimensions: Expenditure Type (HFCE), COICOP Category, Measure (Current Prices/CVM), Adjustment (Seasonally Adjusted/Original), Region (Australia), Frequency (Quarterly).|
|Household Savings (S)|5206.0 (Nat. Income, Exp. & Prod.), 5204.0 (Aust. System of Nat. Acc.)|"Household Saving", "Net Saving", "Gross Saving"|Household Gross Saving, Household Net Saving Ratio|Dimensions: Account Item (Saving), Sector (Households), Measure (Current Prices), Adjustment (Seasonally Adjusted/Original), Region (Australia), Frequency (Quarterly/Annual).|
|Private Investment (I) - Detailed|5206.0 (Nat. Income, Exp. & Prod.), 5625.0 (Private New Capital Exp.)|"Gross Fixed Capital Formation", "Private Investment", "Dwellings", "Machinery and Equipment", "Non-dwelling"|GFCF Private by Asset Type (Dwellings, Non-Dwelling Construction, M&E, Intellectual Property), GFCF by Industry|Dimensions: Investment Type (GFCF), Sector (Private), Asset Type, Industry, Measure (Current Prices/CVM), Adjustment (Seasonally Adjusted/Original), Region, Frequency.|
|Government Spending (G) - Detailed (if in Data API)|5512.0 (Gov. Finance Statistics) - Check Data Explorer if available via API|"Government Final Consumption Expenditure", "Government Investment", "GFS Expenses", "COFOG"|GFCE by COFOG, Government GFCF by purpose/level of government|Dimensions: Expenditure Type, COFOG/Purpose, Level of Government, Measure (Current Prices), Adjustment (Original), Region, Frequency (Annual/Quarterly).|
|Taxation (T) - Detailed (if in Data API)|5512.0 (Gov. Finance Statistics) - Check Data Explorer if available via API|"Taxation Revenue", "Taxes on Income", "Taxes on Production and Imports", "GFS Revenue"|Taxes on Income (Individuals, Companies), GST, Excise Duties by level of government|Dimensions: Revenue Type (Taxation), Tax Type, Level of Government, Measure (Current Prices), Adjustment (Original), Region, Frequency (Annual/Quarterly).|
|Exports (X) & Imports (M) - Detailed|5368.0 (Intl. Trade in G&S)|"International Trade", "Exports", "Imports", "Goods", "Services", "Commodity", "Partner Country"|Exports/Imports of Goods by SITC/HS Commodity Code, Exports/Imports of Services by Service Type, Trade by Partner Country/Country Group|Dimensions: Flow (Export/Import), Trade Type (Goods/Services), Commodity Code, Service Type, Partner Country, Measure (Current Prices/CVM), Adjustment (Seas Adj/Orig), Frequency.|

#### 4.2.3. ABS Web-Scrapable Data (Supplementary, e.g., GFS)

For some datasets, particularly highly detailed Government Finance Statistics or historical series not yet fully integrated into the newer API structures, direct spreadsheet downloads remain the most practical open access method.

- Government Finance Statistics (GFS):

- The ABS "Government Finance Statistics, Annual" publication (associated with catalogue number 5512.0) provides extensive data primarily through XLSX downloads.12

- The "Data downloads" section of the relevant ABS publication webpage (e.g., for the latest GFS Annual release) lists numerous specific tables. For instance, "Table 130. General government - Commonwealth" would provide data for federal government spending and taxation, while "Table 939. General government - Australia - all levels of government" offers aggregate figures.12

- Acquiring this data involves programmatically downloading these XLSX files from their known URLs (which are generally stable per release) and then parsing the spreadsheets to extract the required time series.

- ABS Time Series Directory (Fallback for locating spreadsheets):

- If specific series are not found via the Data API or Indicator API, or if a user prefers to locate the original spreadsheet files, the ABS Time Series Directory can be used as a metadata search tool.24

- The base URL for queries is: <https://abs.gov.au/servlet/TSSearchServlet>?

- The primary parameter for finding spreadsheets related to a publication is catno= (e.g., catno=5206.0 for National Accounts publications, catno=5368.0 for International Trade publications).

- The API returns an XML response containing metadata for matching time series, including `<TableURL>` or `<ProductURL>` tags. These URLs link to the ABS web pages where the downloadable time series spreadsheets (typically XLSX) are located. This directory does not provide the data directly but helps in locating the files.

The hierarchy of ABS data access suggests a tiered approach: start with the Indicator API for ease of use with headline figures; progress to the Data API (Beta) using the Data Explorer for detailed, structured data access; and use direct downloads/scraping for specific publications like GFS or as a fallback. API key management is crucial for the Indicator API and recommended for the Data API. A foundational understanding of SDMX principles (dataflows, DSDs, dimensions, measures) greatly aids in utilizing the more comprehensive Data API, and the ABS Data Explorer is a key tool in bridging the gap by helping users generate the necessary API query structures. The trade-off between data granularity and ease of access is evident: RBA tables and ABS XLSX downloads offer high detail but require more manual setup or custom scraping, while the ABS Indicator API is simpler but offers less granular data. The ABS Data API (Beta) sits in between, offering high detail programmatically but with a steeper learning curve.

## 5. Consolidated Data Acquisition Strategy and Recommendations

Successfully modeling the RBA's circular flow requires a methodical approach to data acquisition, leveraging the strengths of each identified source while being mindful of their characteristics.

### 5.1. Recommended Sources per Circular Flow Component

A consolidated strategy, mapping each component of the circular flow to its most appropriate data source, is as follows:

- Household Final Consumption Expenditure (C):

- Headline Aggregates (Total C, Current Prices, Chain Volume Measures, Seasonally Adjusted): ABS Indicator API, dataflow GDPE_H.

- Detailed Components (e.g., by purpose/COICOP): ABS Data API (Beta). Discover specific dataflow and data key using ABS Data Explorer, searching with keywords like "Household Final Consumption Expenditure" or referencing ABS Catalogue 5206.0.

- Private Gross Fixed Capital Formation (I):

- Headline Aggregates (Total Private GFCF): ABS Indicator API, dataflow GDPE_H.

- Detailed Components (by asset type like Dwellings, Machinery & Equipment; by industry): ABS Data API (Beta). Discover using ABS Data Explorer, searching "Gross Fixed Capital Formation," "Private New Capital Expenditure," or Cat. 5206.0, 5625.0.

- Influencing Factors (Interest Rates): RBA Statistical Tables (F-series, e.g., F1.1, F5, F7) via direct CSV/XLSX download.5

- Government Final Consumption Expenditure (G) and Government GFCF:

- Headline Aggregates (Total GFCE, Total Public GFCF): ABS Indicator API, dataflow GDPE_H.

- Detailed Components (by level of government, purpose/COFOG): Primarily ABS Government Finance Statistics annual publication (Cat. 5512.0) via XLSX downloads.12 Check ABS Data Explorer for any GFS dataflows in the Data API (Beta) as a secondary option.

- Exports of Goods and Services (X) and Imports of Goods and Services (M):

- Headline Aggregates (Total X, Total M, Goods/Services breakdown): ABS Indicator API, dataflows GDPE_H (for totals within GDP) and ITGS_H (for goods/services breakdown).

- Detailed Components (by commodity SITC/HS, by partner country, by service type): ABS Data API (Beta). Discover using ABS Data Explorer, searching "International Trade in Goods and Services" or Cat. 5368.0.

- Influencing Factors (Exchange Rates): RBA Statistical Tables (F-series, e.g., F11, F11.1, F15) via direct CSV/XLSX download.5

- Household Income (Y) (e.g., Compensation of Employees, Gross Mixed Income, Property Income):

- Detailed Components: ABS Data API (Beta). Discover using ABS Data Explorer, searching "National Income, Expenditure and Product," "Household Income Account," "Compensation of Employees," or Cat. 5206.0, 5204.0.

- Household Savings (S):

- Household Net Saving / Gross Saving: ABS Data API (Beta). Discover using ABS Data Explorer, searching "Household Income Account," "National Accounts," or Cat. 5206.0, 5204.0.

- Broader Financial Aggregates (proxy for financial system flows): RBA Statistical Tables (D-series, e.g., D1, D2, D3) via direct CSV/XLSX download.5

- Taxation Revenue (T):

- Detailed Components (by type of tax, level of government): Primarily ABS Government Finance Statistics annual publication (Cat. 5512.0) via XLSX downloads.12 Check ABS Data Explorer for any GFS dataflows in the Data API (Beta) as a secondary option.

### 5.2. Workflow Recommendations

A structured workflow will streamline data acquisition:

1. API Key Acquisition:

   1. Register for and obtain an API key for the ABS Indicator API. This is mandatory for access.10

   2. Consider registering for an API key for the ABS Data API (Beta) if planning extensive or production use, as this is recommended by the ABS.9

2. Retrieve Headline Aggregates:

   1. Utilize the ABS Indicator API (GDPE_H, ITGS_H) to fetch headline quarterly figures for C, I (total), G (total), X (total), and M (total). This provides a consistent, high-level overview.

3. Access Detailed ABS Data via Data API (Beta):

   1. Use the ABS Data Explorer online tool to search for and identify specific detailed datasets required (e.g., disaggregated income, consumption by type, investment by asset, trade by commodity/country).

   2. The Data Explorer can often generate the dataflowIdentifier and dataKey structure for the selected data view.

   3. Construct and execute queries against the ABS Data API (Beta) using these identifiers and keys. Retrieve metadata first to understand dimensions and codes.

4. Acquire RBA Financial and Monetary Data:

   1. Identify the relevant RBA Statistical Tables (D-series for financial aggregates, F-series for interest and exchange rates) from the RBA website.5

   2. Develop scripts to programmatically download the linked CSV or XLSX files.

5. Obtain Government Finance Statistics (GFS):

   1. Access the latest ABS "Government Finance Statistics, Annual" publication page (related to Cat. 5512.0).12

   2. Develop scripts to download the detailed XLSX tables for taxation revenue and government expenditure by various classifications.

   3. As a secondary check, use the ABS Data Explorer to see if any GFS dataflows have become available through the Data API (Beta).

6. Data Alignment and Preparation:

   1. Frequency Harmonization: National Accounts data is typically quarterly. International Trade data is often monthly (requiring aggregation to quarterly). GFS and some RBA series may be annual or monthly. Convert all data to a consistent frequency (e.g., quarterly) for the model.

- Price Basis: Ensure consistency in using current prices versus chain volume measures. Chain volume measures are preferred for analyzing real economic growth.

- Seasonal Adjustment: Decide on using seasonally adjusted, trend, or original data, and apply consistently. Seasonally adjusted data is generally preferred for macroeconomic modeling to remove regular seasonal fluctuations.

- Definitions and Coverage: Carefully check definitions of variables from different sources to ensure comparability.

### 5.3. Considerations for Model Maintenance

Building a data pipeline for the circular flow model is an ongoing process:

- Data Revisions: Macroeconomic data is subject to frequent revisions by statistical agencies as more complete information becomes available. The RBA notes its tables are subject to revisions 5, and ABS data also undergoes regular updates. Implement a process to regularly refresh datasets and incorporate these revisions.

- API and Source Changes: APIs, especially those in "Beta" status like the ABS Data API 9, can evolve. Endpoints, parameters, or data structures might change. It is important to monitor announcements from the ABS and RBA regarding their data services.

- Structural Changes in Data Presentation: The ABS is phasing out traditional catalogue numbers.14 Relying on searches by publication title or keywords within the ABS Data Explorer for discovering dataflows is a more robust long-term strategy.

- Metadata Reliance: For all API-based sources, particularly the SDMX-compliant ABS Data API, the retrieval and understanding of metadata (dimension names, codes, units of measure, concept definitions) are as critical as retrieving the numerical data itself. Changes in metadata can impact data interpretation and query construction.

- Data Integration Challenges: The most significant ongoing task will be the integration of data from these disparate sources. This involves not only technical aspects of data ingestion but also conceptual harmonization of definitions, classifications, and reference periods to ensure a coherent and internally consistent dataset for the model.

The dynamic nature of economic data and the platforms that disseminate it necessitates building an adaptable and regularly maintained data pipeline. Favoring programmatic discovery of dataflows and series where possible, and implementing checks for data consistency over time, will contribute to the model's long-term viability and accuracy.

Table 5: API/Web Source Quick Reference Guide

|   |   |   |   |   |   |
|---|---|---|---|---|---|
|Circular Flow Component|Sub-component Example|Recommended Source|API/Table Endpoint or Identifier|Key Parameters/Data Key Info (Illustrative)|Notes|
|Household Consumption (C)|Total, Seas Adj., Chain Vol.|ABS Indicator API|GDPE_H|Access via dataflow; specific series identified by codes within response (e.g., for HFCE, CVM, SA)|Requires API Key.|
||By Purpose (e.g., Food), Seas Adj., CVM|ABS Data API (Beta)|Discover flowId via Data Explorer (e.g., from Cat. 5206.0)|dataKey with codes for HFCE, COICOP category, CVM, SA, Australia, Quarterly.|API Key recommended. Use Data Explorer to find flowId and dataKey structure.|
|Private Investment (I)|Total Private GFCF, Seas Adj., CVM|ABS Indicator API|GDPE_H|Access via dataflow; series for GFCF components.|Requires API Key.|
||GFCF by Asset (Dwellings), Seas Adj., CVM|ABS Data API (Beta)|Discover flowId via Data Explorer (e.g., from Cat. 5206.0, 5625.0)|dataKey with codes for GFCF, Private, Asset Type (Dwellings), CVM, SA, Australia, Quarterly.|API Key recommended.|
|Government Spending (G)|Total Gov. Cons. & Inv., Seas Adj., CVM|ABS Indicator API|GDPE_H|Access via dataflow; series for GFCE & Public GFCF.|Requires API Key.|
||Detailed GFCE by COFOG, Current Prices, Original|ABS GFS XLSX Download|Cat. 5512.0 (Annual) - Specific table (e.g., Table 130 for Commonwealth)|Parse XLSX file.|Check Data Explorer for API availability first.|
|Exports (X)|Total Exports of G&S, Seas Adj., CVM|ABS Indicator API|GDPE_H (total in GDP), ITGS_H (G&S breakdown)|Access via dataflow.|Requires API Key.|
||Exports of Goods by Commodity, Current Prices, Original|ABS Data API (Beta)|Discover flowId via Data Explorer (e.g., from Cat. 5368.0)|dataKey with codes for Export, Goods, SITC/HS Code, Current Prices, Original, Australia, Monthly/Quarterly.|API Key recommended.|
|Imports (M)|Total Imports of G&S, Seas Adj., CVM|ABS Indicator API|GDPE_H (total in GDP), ITGS_H (G&S breakdown)|Access via dataflow.|Requires API Key.|
||Imports of Services by Type, Current Prices, Original|ABS Data API (Beta)|Discover flowId via Data Explorer (e.g., from Cat. 5368.0)|dataKey with codes for Import, Services, Service Type Code, Current Prices, Original, Australia, Monthly/Quarterly.|API Key recommended.|
|Household Income (Y)|Compensation of Employees, Seas Adj., Current Prices|ABS Data API (Beta)|Discover flowId via Data Explorer (e.g., from Cat. 5206.0)|dataKey with codes for Comp. of Employees, Current Prices, SA, Australia, Quarterly.|API Key recommended.|
|Household Savings (S)|Net Saving, Seas Adj., Current Prices|ABS Data API (Beta)|Discover flowId via Data Explorer (e.g., from Cat. 5206.0)|dataKey with codes for Household Net Saving, Current Prices, SA, Australia, Quarterly.|API Key recommended.|
|Taxation (T)|Taxes on Income - Individuals, Current Prices, Original|ABS GFS XLSX Download|Cat. 5512.0 (Annual) - Specific table (e.g., for relevant level of gov.)|Parse XLSX file.|Check Data Explorer for API availability first.|
|Interest Rates|Indicator Lending Rate - Business|RBA Statistical Table|Table F7 (.../csv/f7-data.csv)|Direct download/scrape.|Monthly data.|
|Exchange Rates|AUD/USD Daily|RBA Statistical Table|Table F11.1 (.../csv/f11.1-data.csv)|Direct download/scrape.|Daily data.|

## 6. Conclusion

The Reserve Bank of Australia's circular flow model provides a conceptual map of the intricate economic interactions between households, firms, the government, financial institutions, and the overseas sector.1 Key flows include income, expenditure, savings, investment, taxation, government spending, imports, and exports. For empirical modeling, these conceptual flows must be translated into measurable economic variables, primarily sourced from Australia's National Accounts, International Trade statistics, and Government Finance Statistics.

The primary providers of this data are the Reserve Bank of Australia, for financial market indicators like interest and exchange rates 5, and the Australian Bureau of Statistics, for the comprehensive suite of economic statistics.9 Accessing this data requires a hybrid strategy. The ABS offers increasingly sophisticated API access: the Indicator API provides headline figures for GDP components and trade 10, while the more extensive Data API (Beta) allows for detailed queries of datasets using the SDMX standard.9 The ABS Data Explorer is an essential tool for navigating the Data API (Beta) by helping to identify specific dataflows and construct queries.13

For RBA data and certain detailed ABS statistics (notably Government Finance Statistics 12), direct download of CSV or XLSX files from their respective websites, or programmatic scraping of these files, remains the most viable open-access method.

Successfully constructing and maintaining a quantitative model of Australia's circular flow necessitates careful attention to data source selection, API key management where required, understanding of data structures (particularly SDMX for ABS APIs), and robust processes for data integration and alignment (e.g., frequency conversion, price basis consistency). Given that economic data is subject to revision and data dissemination methods evolve 5, an adaptable data acquisition pipeline and ongoing vigilance regarding source changes are crucial for the long-term accuracy and relevance of any such model.

## Works cited

1. <www.rba.gov.au>, accessed May 23, 2025, [https://www.rba.gov.au/education/resources/illustrators/pdf/circular-flow-model.pdf](https://www.rba.gov.au/education/resources/illustrators/pdf/circular-flow-model.pdf)

2. Circular Flow Model | Economic Lowdown - YouTube, accessed May 23, 2025, [https://m.youtube.com/watch?v=2wM0jHL6TQs&pp=ygUVI2FwZ292ZXJubWVudGNpcmN1bGFy](https://m.youtube.com/watch?v=2wM0jHL6TQs&pp=ygUVI2FwZ292ZXJubWVudGNpcmN1bGFy)

3. Circular Flow Of Income - Think Insights, accessed May 23, 2025, [https://thinkinsights.net/strategy/circular-flow-income](https://thinkinsights.net/strategy/circular-flow-income)

4. Monetary Policy Transmission through the Lens of the RBA's Models ..., accessed May 23, 2025, [https://www.rba.gov.au/publications/bulletin/2025/apr/monetary-policy-transmission-through-the-lens-of-the-rbas-models.html](https://www.rba.gov.au/publications/bulletin/2025/apr/monetary-policy-transmission-through-the-lens-of-the-rbas-models.html)

5. Statistical Tables | RBA, accessed May 23, 2025, [https://www.rba.gov.au/statistics/tables/](https://www.rba.gov.au/statistics/tables/)

6. Securitisation System B2B API Technical Implementation Notes - Reserve Bank of Australia, accessed May 23, 2025, [https://www.rba.gov.au/securitisations/files/support-material/b2b-api-technical-implementation-notes-version-1.2.pdf](https://www.rba.gov.au/securitisations/files/support-material/b2b-api-technical-implementation-notes-version-1.2.pdf)

7. Statistics | RBA, accessed May 23, 2025, [https://www.rba.gov.au/statistics/](https://www.rba.gov.au/statistics/)

8. ABS Data API (Beta) | aga - Australian Government Architecture, accessed May 23, 2025, [https://architecture.digital.gov.au/abs-data-api-beta](https://architecture.digital.gov.au/abs-data-api-beta)

9. Data API | Australian Bureau of Statistics - ABS Beta, accessed May 23, 2025, [https://beta.abs.gov.au/about/abs-digital-products-and-services-catalogue/application-programming-interfaces/data-api.html](https://beta.abs.gov.au/about/abs-digital-products-and-services-catalogue/application-programming-interfaces/data-api.html)

10. Indicator API - Australian Bureau of Statistics, accessed May 23, 2025, [https://www.abs.gov.au/about/data-services/application-programming-interfaces-apis/indicator-api](https://www.abs.gov.au/about/data-services/application-programming-interfaces-apis/indicator-api)

11. raw.githubusercontent.com, accessed May 23, 2025, [https://raw.githubusercontent.com/apigovau/api-descriptions/master/abs/indicator.openapi.yaml](https://raw.githubusercontent.com/apigovau/api-descriptions/master/abs/indicator.openapi.yaml)

12. Government Finance Statistics, Annual, 2023-24 financial year, accessed May 23, 2025, [https://www.abs.gov.au/statistics/economy/government/government-finance-statistics-annual/latest-release](https://www.abs.gov.au/statistics/economy/government/government-finance-statistics-annual/latest-release)

13. Finding data - Australian Bureau of Statistics, accessed May 23, 2025, [https://www.abs.gov.au/about/data-services/data-explorer/data-explorer-user-guide/finding-data](https://www.abs.gov.au/about/data-services/data-explorer/data-explorer-user-guide/finding-data)

14. About our website | Australian Bureau of Statistics, accessed May 23, 2025, [https://www.abs.gov.au/welcome-new-abs-website](https://www.abs.gov.au/welcome-new-abs-website)

15. ABS Indicator API | aga - Australian Government Architecture, accessed May 23, 2025, [https://architecture.digital.gov.au/abs-indicator-api](https://architecture.digital.gov.au/abs-indicator-api)

16. accessed January 1, 1970, [https://indicator.api.abs.gov.au/v1/metadata/GDPE_H/json](https://indicator.api.abs.gov.au/v1/metadata/GDPE_H/json)

17. accessed January 1, 1970, [https://indicator.api.abs.gov.au/v1/metadata/ITGS_H/json](https://indicator.api.abs.gov.au/v1/metadata/ITGS_H/json)

18. raw.githubusercontent.com, accessed May 23, 2025, [https://raw.githubusercontent.com/apigovau/api-descriptions/gh-pages/abs/DataAPI.openapi.yaml](https://raw.githubusercontent.com/apigovau/api-descriptions/gh-pages/abs/DataAPI.openapi.yaml)

19. Data API user guide | Australian Bureau of Statistics, accessed May 23, 2025, [https://www.abs.gov.au/book/export/30556/print](https://www.abs.gov.au/book/export/30556/print)

20. Using the API | Australian Bureau of Statistics, accessed May 23, 2025, [https://www.abs.gov.au/about/data-services/application-programming-interfaces-apis/data-api-user-guide/using-api](https://www.abs.gov.au/about/data-services/application-programming-interfaces-apis/data-api-user-guide/using-api)

21. Worked Examples | Australian Bureau of Statistics, accessed May 23, 2025, [https://www.abs.gov.au/about/data-services/application-programming-interfaces-apis/data-api-user-guide/worked-examples](https://www.abs.gov.au/about/data-services/application-programming-interfaces-apis/data-api-user-guide/worked-examples)

22. Data Explorer - Australian Bureau of Statistics, accessed May 23, 2025, [https://www.abs.gov.au/about/data-services/data-explorer](https://www.abs.gov.au/about/data-services/data-explorer)

23. Aotearoa Data Explorer user guide | Stats NZ, accessed May 23, 2025, [https://www.stats.govt.nz/tools/aotearoa-data-explorer/ade-user-guide/](https://www.stats.govt.nz/tools/aotearoa-data-explorer/ade-user-guide/)

24. ABS Time Series Directory | Australian Bureau of Statistics, accessed May 23, 2025, [https://www.abs.gov.au/about/data-services/help/abs-time-series-directory](https://www.abs.gov.au/about/data-services/help/abs-time-series-directory)

25. Australian System of National Accounts, 2023-24 financial year, accessed May 23, 2025, [https://www.abs.gov.au/statistics/economy/national-accounts/australian-system-national-accounts/latest-release](https://www.abs.gov.au/statistics/economy/national-accounts/australian-system-national-accounts/latest-release)

26. Australian System of National Accounts, accessed May 23, 2025, [https://www.abs.gov.au/statistics/economy/national-accounts/australian-system-national-accounts](https://www.abs.gov.au/statistics/economy/national-accounts/australian-system-national-accounts)

27. Australian National Accounts: National Income, Expenditure and Product, December 2024, accessed May 23, 2025, [https://www.abs.gov.au/statistics/economy/national-accounts/australian-national-accounts-national-income-expenditure-and-product/latest-release](https://www.abs.gov.au/statistics/economy/national-accounts/australian-national-accounts-national-income-expenditure-and-product/latest-release)

28. International Trade in Goods and Services, Australia, May 2023 | Australian Bureau of Statistics, accessed May 23, 2025, [https://www.abs.gov.au/statistics/economy/international-trade/international-trade-goods/may-2023](https://www.abs.gov.au/statistics/economy/international-trade/international-trade-goods/may-2023)
