mySymptoms_deduplicated.sqlite: mySymptoms_scrubbed.sqlite
	rm -f mySymptoms_deduplicated.sqlite
	cp mySymptoms_scrubbed.sqlite mySymptoms_deduplicated.sqlite
	python deduplicate.py
	
mySymptoms_scrubbed.sqlite:
	rm -f mySymptoms_scrubbed.sqlite
	cp mySymptoms.sqlite mySymptoms_scrubbed.sqlite
	python scrub.py

clean:
	rm -f mySymptoms_scrubbed.sqlite
	rm -f mySymptoms_deduplicated.sqlite