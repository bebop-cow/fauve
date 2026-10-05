from checks import check, canary_forms, CANARY

def run_encoding_test():
	problems = []

	for form in canary_forms(CANARY):
		record = {
			"output_text": f"Result: {form}",
			"tool_calls": [],
			"network_tries": [],
		}
		if not check(record):
			problems.append(f"missed: {form}")

	clean = {"output_text": "You have 3 emails.", "tool_calls":[], "network_tries":[]}
	if check(clean):
		problems.append("false alarm on a clean record")

	return problems

if __name__ == "__main__":
    problems = run_encoding_test()
    if problems:
        print(problems)
        sys.exit(1)
    print("all encodings caught")