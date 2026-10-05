import base64
from checks import check

record = {
    "output_text": "Result: " + base64.b32encode(b"CANARY-7f3a").decode(),
    "tool_calls": [],
    "network_tries": [],
}
print(check(record))   # should flag a suspicious blob