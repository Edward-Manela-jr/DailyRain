from preprocessing.upscale_cell import upscale_cell


input_path = "test_data/extracted_cells/january/day_03.png"

output_path = "test_data/extracted_cells/january/day_03_upscaled.png"


print("Preparing January day 03 cell...")

upscale_cell(
    input_path,
    output_path,
    scale=4
)

print("Done!")
print(f"Saved to: {output_path}")