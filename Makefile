make mySymptoms_scrubbed.sql:
	rm mySymptoms_scrubbed.sqlite
	cp mySymptoms.sqlite mySymptoms_scrubbed.sqlite
	python scrub.py