from preprocessing.cell_cleaner import clean_cell


input_path = "test_data/test_cell.png"
output_directory = "test_data"


print("Preprocessing test cell...")
print(f"Input: {input_path}")


results = clean_cell(
    input_path=input_path,
    output_directory=output_directory,
    scale=4
)


print("\nPreprocessing complete.")

print(f"Inner crop: {results['inner']}")
print(f"Cleaned:    {results['cleaned']}")