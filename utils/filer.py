def save_to_file(file_name: str, contents: str):
    # Save data to file
    with open(file_name, 'w') as f:
        f.write(contents)

# def write_object_to_file(file_name: str, obj):
#     # Save data to file
#     with open(file_name, 'w') as f:
#         f.write(obj.__str__())
#
# def read_object_from_file(file_name: str, output):
#     # Read data from file
#     with open(file_name, 'r') as f:
#         contents = f.read()
#         # Parse the contents
#         output.__str__(contents)
#
