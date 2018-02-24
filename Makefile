clean:
	rm -rf .cache .eggs *.egg-info .idea
	find . -type d -name __pycache__ -prune -exec rm -rf {} \;
	find . -type f -name "*.pyc" -prune -exec rm {} \;
	rm -f tests/xml/upnp/IGD.xml .coverage
