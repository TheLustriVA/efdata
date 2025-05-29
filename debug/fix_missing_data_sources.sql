-- Fix missing data sources in dim_data_source
-- These are required for the ETL process to work correctly

INSERT INTO rba_dimensions.dim_data_source 
(rba_table_code, csv_filename, table_description, data_category, primary_frequency, update_frequency)
VALUES
('A1', 'a1-data.csv', 'RBA Balance Sheet', 'Central Banking', 'Weekly', 'Weekly'),
('C1', 'c1-data.csv', 'Credit & Charge Cards', 'Payment Systems', 'Monthly', 'Monthly'),
('D2', 'd2-data.csv', 'Lending & Credit Aggregates', 'Credit & Monetary', 'Monthly', 'Monthly'),
('I3', 'i3-data.csv', 'Exchange Rates', 'Foreign Exchange', 'Daily', 'Daily')
ON CONFLICT (rba_table_code) DO NOTHING;

-- Verify all sources are now present
SELECT rba_table_code, csv_filename, table_description 
FROM rba_dimensions.dim_data_source 
ORDER BY rba_table_code;