with open("test_results.txt", "rb") as f:
    print(f.read().decode("utf-16le", errors="replace"))
