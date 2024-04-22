# Overview
- This is my first trying to crawl data using API and transform it for analyzing purpose.
- The data content is about salary for IT positions collected via website [luog](https://luongthang.net/), in which users will input their salary by roles and levels
- Purpose: Collect all inputs of salary of all IT companies, all roles and levels have been input to summarize the salary base range for some common IT roles by number of YoE, get some insights regarding the fluctuation of salary in case of the market downsizing.

# Technique
- Call API https://server.luongthang.net/companies, which contains information of company name, average salary, number of YoE, compensations
- Flatten and normalize all json fields and do transformation (covert data types, fill null values)
- Collect some basic statistical figures on the crawed data (will update soon)
- Visualize data (will update soon).

