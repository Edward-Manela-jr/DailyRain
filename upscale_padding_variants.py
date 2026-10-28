from preprocessing.upscale_cell import upscale_cell
import os

INPUT_DIR = "test_data/padding_variants"
OUTPUT_DIR = "test_data/padding_variants_upscaled"

os.makedirs(OUTPUT_DIR, exist_ok=True)

files = sorted(
    f for f in os.listdir(INPUT_DIR)
    if f.endswith(".png")
)

for filename in files:

    input_path = os.path.join(INPUT_DIR, filename)
    output_path = os.path.join(OUTPUT_DIR, filename)

    upscale_cell(
        input_path,
        output_path,
        scale=4
    )

    print(f"Upscaled: {filename}")

print()
print(f"Total: {len(files)} images")
print("Done.")
