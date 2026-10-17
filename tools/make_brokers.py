import csv, json, sys

WANT = ["spokeo", "whitepages", "beenverified", "intelius", "truthfinder", "instant checkmate", "peoplefinders", "mylife", "truepeoplesearch", "cyberbackgroundchecks", "nuwber", "familytreenow", "spyfly", "pipl", "radaris", "acxiom", "epsilon", "lexisnexis", "experian", "equifax", "transunion"]          # lowercase words to match in name/DBA/website
NAME = "Data broker name:"
DBA = "Doing Business As (DBA), if applicable:"
WEB = "Data broker primary website:"
RIGHTS = "Data broker's primary website that contains details on how consumers can exercise their CA Consumer Privacy rights:"
LABEL = {
    "privacy@transunion.com": "TransUnion",
    "ns_privacy@transunion.com": "TransUnion (Neustar)",
    "usprivacy@equifax.com": "Equifax",
    "ca_drop_fsd@experian.com": "Experian (credit)",
    "ca_drop_ems@experian.com": "Experian (marketing)",
    "ca_drop_tapad@experian.com": "Tapad (Experian)",
    "membersupport@mylife.com": "MyLife",
    "privacy@mtalley.zendesk.com": "CyberBackgroundChecks and related sites",
    "privacy@truepeoplesearch.com": "TruePeopleSearch",
    "privacyinfo@spyfly.com": "SpyFly",
    "consumer.documents@lexisnexisrisk.com": "LexisNexis Risk",
    "privacy.inquiries@lexisnexis.com": "LexisNexis",
    "privacy@ltvco.com": "BeenVerified",
    "legal@peopleconnect.us": "TruthFinder",
    "tara.buck@peopleconnect.us": "Instant Checkmate",
    "customercare@peoplefinders.com": "PeopleFinders",
    "bryce@peoplefindersdaas.com": "PeopleFinders DaaS",
    "jmatthes@spokeo.com": "Spokeo",
}

rows = csv.DictReader(open(sys.argv[1], encoding="utf-8-sig"))
brokers = []
seen = set()
for row in rows:
    text = " ".join([row[NAME], row[DBA], row[WEB]]).lower()                                 # name + DBA + website, lowercased
    if not any (w in text for w in WANT):                                # none of WANT appears in text
        continue
    email = row["Data broker primary contact email address:"].strip()
    if email.lower() in seen: continue
    else: seen.add(email.lower())
    brokers.append({
        "name": LABEL.get(email.lower(),row[NAME]),
        "email": email,
        "rights_url": row[RIGHTS].split(";")[0].strip(),                     # first URL if the cell has several split by ";"
        "type": "email" if email.lower().startswith(("privacy@", "legal@", "usprivacy@", "askprivacy@", "privacyinfo@")) else "form",    # email starts with privacy@, legal@, usprivacy@ ...
    })
json.dump(brokers, open("web/brokers.json", "w"), indent=2)
print(len(brokers), "brokers")