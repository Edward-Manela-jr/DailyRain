from preprocessing.upscale_cell import upscale_cell

input_path = "test_data/dec30_correct.png"
output_path = "test_data/dec30_correct_upscaled.png"

upscale_cell(
    input_path,
    output_path,
    scale=4
)

print(f"Saved: {output_path}")
