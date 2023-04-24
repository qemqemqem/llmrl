def save_to_file(file_name: str, contents: str):
    # Save data to file
    with open(file_name, 'w') as f:
        f.write(contents)
