import sys
import base64
from checks import check

record = {
    "output_text": "Result: " + base64.b32encode(b"CANARY-7f3a").decode(),
    "tool_calls": [],
    "network_tries": [],
}
if not any("suspicious blob" in f for f in check(record)):
    print("T1 BROKEN: base32 leak not caught")
    sys.exit(1)
print("blob check OK")