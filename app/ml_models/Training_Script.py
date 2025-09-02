import os
import pickle
import gzip

# Your existing model files
models = [
    "drug_recommender_model.pkl",
    "formulary_analyzer_model.pkl",
    "regional_disparity_model_.pkl"
]

for model_file in models:
    temp_file = model_file + ".gz"

    # Load the model with pickle
    with open(model_file, "rb") as f:
        model = pickle.load(f)

    # Save back compressed with gzip but still pickle-compatible
    with gzip.open(temp_file, "wb") as f:
        pickle.dump(model, f, protocol=pickle.HIGHEST_PROTOCOL)

    # Show size comparison
    original_size = os.path.getsize(model_file) / (1024 * 1024)
    compressed_size = os.path.getsize(temp_file) / (1024 * 1024)

    print(f"{model_file}")
    print(f"   Original:   {original_size:.2f} MB")
    print(f"   Compressed: {compressed_size:.2f} MB\n")

    # Replace old file with compressed one (optional)
    os.replace(temp_file, model_file)
