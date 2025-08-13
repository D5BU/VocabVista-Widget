with open("oxford3000.txt", "r", encoding="utf-8") as file:
    for line in file :
        line = line.strip()
        if not line:
            continue
        if "-" in line:
            word, meaning = line.split(" - ", 1)
        else:
            word, meaning = line, "(No meaning provided)"

        print(f"Word: {word}")
        print(f"Meaning: {meaning}")
        print(" - " * 40)
        