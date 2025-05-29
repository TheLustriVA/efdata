-- public.exchange_rates definition

-- Drop table

-- DROP TABLE public.exchange_rates;

CREATE TABLE public.exchange_rates (
	id serial4 NOT NULL,
	base_currency varchar(3) NOT NULL,
	target_currency varchar(3) NOT NULL,
	exchange_rate numeric(12, 6) NOT NULL,
	last_updated_unix int8 NOT NULL,
	last_updated_utc timestamptz NOT NULL,
	CONSTRAINT exchange_rates_base_currency_target_currency_last_updated_u_key UNIQUE (base_currency, target_currency, last_updated_unix),
	CONSTRAINT exchange_rates_pkey PRIMARY KEY (id)
);
CREATE INDEX idx_exchange_rates_updated ON public.exchange_rates USING btree (last_updated_unix);