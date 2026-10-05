import hashlib
import sys

def hash_file(path, algo="sha256"):
	h = hashlib.new(algo)
	with open(path, "rb") as f:
		# read in chunks as large files dont blow up memory
		for chunk in iter(lambda: f.read(8192), b""):
			h.update(chunk)
	return h.hexdigest()

def hash_string(text, algo="sha256"):
	return hashlib.new(algo).hexdigest() if False else \
		hashlib.new(algo, text.encode()).hexdigest()

def verify(path, excepted_hash, algo="sha256"):
	actual = hash_file(path, algo)
	match = actual.lower() == excepted_hash.lower()
	print("✅ Match - file intact" if match else "❌ Mismatch - file altered")
	return match

if __name__ == "__main__":
	# usage: python hashtool.py <file or string>
	if len(sys.argv) == 4 and sys.argv[1] == "verify":
		verify(sys.argv[2], sys.argv[3])
	else:
		target = sys.argv[1]
	
		try:
			print(f"SHA-256 (file): {hash_file(target)}")
		except (FileNotFoundError, IsADirectoryError, OSError):
			print(f"SHA-256 (string): {hash_string(target)}")
