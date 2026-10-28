from grid.cell_extractor import extract_cells


image_path = "test_data/testimage.png"

output_directory = "test_data/extracted_cells"


print("Extracting rainfall cells...")
print(f"Image: {image_path}")


cells = extract_cells(
    image_path=image_path,
    output_directory=output_directory
)


print()
print("Extraction complete.")
print(f"Cells extracted: {len(cells)}")


print()
print("First 5 cells:")

for cell in cells[:5]:
    print(
        f"{cell['month']} "
        f"day {cell['day']:02d} → "
        f"{cell['path']}"
    )


print()
print("Last 5 cells:")

for cell in cells[-5:]:
    print(
        f"{cell['month']} "
        f"day {cell['day']:02d} → "
        f"{cell['path']}"
    )