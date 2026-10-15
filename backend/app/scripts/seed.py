from app.services.data_collection import generate_sample_data


if __name__ == "__main__":
    df = generate_sample_data()
    print(f"Generated demo dataset with {len(df)} rows.")
