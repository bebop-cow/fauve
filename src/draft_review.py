import re
from urllib.parse import urlparse

URL = re.compile(r"https?://[^\s)>\]]+", re.IGNORECASE)

def classify_url(url):
	p = urlparse(url)
	if p.query or p.fragment:
		return "carries_data"
	return "plain"

IMG = re.compile(r"!\[[^\]]*\]\([^)]*\)")


def review_draft(text):
	findings = []

	def fix(m):
		url = m.group(0)
		host = urlparse(url).netloc
		if classify_url(url) == "carries_data":
			findings.append(f"removed link to {host}: carries data")
			return "[link removed: carries data]"
		findings.append(f"unverified link to {host}")
		return url
	
	def drop_img(m):
		findings.append("image removed")
		return "[image removed]"

	text = IMG.sub(drop_img, text)
	return URL.sub(fix, text), findings