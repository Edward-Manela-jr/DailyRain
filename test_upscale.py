from preprocessing.upscale_cell import upscale_cell


input_path = "test_data/extracted/jan_cell_6_5_original.png"

output_path = "test_data/extracted/jan_cell_6_5_upscaled.png"


print("Upscaling exact rainfall cell...")

upscale_cell(
    input_path,
    output_path,
    scale=4
)

print("Done!")
print(f"Saved to: {output_path}")