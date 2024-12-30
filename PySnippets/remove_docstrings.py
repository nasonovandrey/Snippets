import sys

def remove_multiline_comments(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    in_comment = False
    cleaned_lines = []

    for line in lines:
        if not in_comment:
            if line.strip().startswith("'''") or line.strip().startswith('"""'):
                in_comment = True
                if line.strip().endswith("'''") or line.strip().endswith('"""'):  # single-line comment
                    in_comment = False
                else:
                    continue  # skip line
        else:
            if line.strip().endswith("'''") or line.strip().endswith('"""'):
                in_comment = False
            continue  # skip line
        cleaned_lines.append(line)

    with open(file_path, 'w', encoding='utf-8') as file:
        file.writelines(cleaned_lines)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <file-path>")
        sys.exit(1)
    file_path = sys.argv[1]
    remove_multiline_comments(file_path)

