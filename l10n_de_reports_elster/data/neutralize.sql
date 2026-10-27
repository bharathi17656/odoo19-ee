INSERT INTO ir_config_parameter (key, value)
     VALUES ('l10n_de_reports_elster.elster_proxy_mode', 'test')
ON CONFLICT (key) DO UPDATE
        SET value = 'test';
