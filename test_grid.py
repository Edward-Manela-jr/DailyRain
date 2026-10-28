from grid.grid_detector import detect_grid


image_path = "test_data/testimage.png"


horizontal, vertical = detect_grid(image_path)


print("GRID DETECTION RESULTS")
print("=" * 40)

print(f"Horizontal boundaries: {len(horizontal)}")
print(horizontal)

print()

print(f"Vertical boundaries: {len(vertical)}")
print(vertical)