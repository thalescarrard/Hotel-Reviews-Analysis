import pandas as pd
from dateutil import parser

# --- Load CSV files ---
df_booking = pd.read_csv("booking_reviews_Boulan.csv")
df_expedia = pd.read_csv("expedia_reviews_Boulan.csv")

# --- Standardize column names ---
df_booking.columns = df_booking.columns.str.strip().str.lower()
df_expedia.columns = df_expedia.columns.str.strip().str.lower()

# Apply robust parsing using dateutil for both datasets
df_booking["review_date"] = df_booking["review_date"].apply(
    lambda x: parser.parse(x) if pd.notna(x) else pd.NaT
)

df_expedia["review_date"] = df_expedia["review_date"].apply(
    lambda x: parser.parse(x) if pd.notna(x) else pd.NaT
)

# --- Rename for consistency ---
df_booking.rename(columns={"traveler_name": "name", "review_text": "text"}, inplace=True)
df_expedia.rename(columns={"traveler_name": "name", "review_text": "text"}, inplace=True)

# --- Convert datatypes ---
df_booking["review_rating"] = pd.to_numeric(df_booking["review_rating"], errors="coerce")
df_expedia["review_rating"] = pd.to_numeric(df_expedia["review_rating"], errors="coerce")

df_booking["review_date"] = pd.to_datetime(df_booking["review_date"], errors="coerce")
df_expedia["review_date"] = pd.to_datetime(df_expedia["review_date"], errors="coerce")

df_booking["length_of_stay"] = pd.to_numeric(df_booking["length_of_stay"], errors="coerce")
df_expedia["length_of_stay"] = pd.to_numeric(df_expedia["length_of_stay"], errors="coerce")

# --- Clean text ---
df_booking["text"] = df_booking["text"].astype(str).str.strip()
df_expedia["text"] = df_expedia["text"].astype(str).str.strip()

# --- Drop exact duplicates within source ---
booking_before = len(df_booking)
df_booking.drop_duplicates(subset=["text", "review_date", "review_rating"], inplace=True)
booking_dupes_removed = booking_before - len(df_booking)

expedia_before = len(df_expedia)
df_expedia.drop_duplicates(subset=["text", "review_date", "review_rating"], inplace=True)
expedia_dupes_removed = expedia_before - len(df_expedia)

# --- Drop entries missing ratings ---
df_booking.dropna(subset=["review_rating"], inplace=True)
df_expedia.dropna(subset=["review_rating"], inplace=True)

# --- Combine datasets ---
df_all = pd.concat([df_booking, df_expedia], ignore_index=True)
df_all['review_date'] = pd.to_datetime(df_all['review_date'], errors='coerce')

# --- Prioritize Booking if duplicate appears in both ---
combined_before = len(df_all)
df_all = df_all.sort_values(by="source", ascending=False)
df_all = df_all.drop_duplicates(subset=["text", "name", "review_date"])
combined_dupes_removed = combined_before - len(df_all)

# Filter to keep only reviews with dates in 2020 or later
df = df_all[df_all['review_date'] >= pd.to_datetime('2020-01-01')]

# --- Save cleaned output ---
df_all.to_csv("cleaned_reviews.csv", index=False)

# --- Summary printout ---
print("Cleaning complete.")
print(f"Booking reviews loaded: {booking_before}")
print(f"Expedia reviews loaded: {expedia_before}")
print(f"Duplicates removed in Booking: {booking_dupes_removed}")
print(f"Duplicates removed in Expedia: {expedia_dupes_removed}")
print(f"Total combined reviews before final deduplication: {combined_before}")
print(f"Final duplicates removed across both sources: {combined_dupes_removed}")
print(f"Dropped reviews before 2020, final cleaned review count: {len(df_all)}")

# --- Quick Overview ---
print("\nDataset shape:", df_all.shape)
print("Columns:", df_all.columns.tolist())
print("\nMissing values per column:\n", df_all.isna().sum())
