import pandas as pd
from dateutil import parser

# Function to extract keyword
def simplify_traveler_type(text):
    if pd.isna(text):
        return None
    text = text.lower()
    if "partner" in text:
        return "Couple"
    elif "family" in text:
        return "Family"
    elif "group" in text:
        return "Group"
    else:
        return "Solo"

# --- Load CSV files ---
df_booking = pd.read_csv("booking_reviews_Boulan.csv")
df_expedia = pd.read_csv("expedia_reviews_Boulan.csv")
df_tripadvisor = pd.read_csv("tripadvisor_reviews_Boulan.csv")

# --- Standardize column names ---
for df in [df_booking, df_expedia, df_tripadvisor]:
    df.columns = df.columns.str.strip().str.lower()

# --- Add source column ---
df_booking["source"] = "Booking"
df_expedia["source"] = "Expedia"
df_tripadvisor["source"] = "Tripadvisor"

# Format total reviews field
for df in [df_booking]:
    df['total_reviews'] = df['total_reviews'].str.replace(' reviews', '').astype(int)

for df in [df_expedia]:
    df['total_reviews'] = df['total_reviews'].str.replace(',', '').str.replace(' verified reviews', '').astype(int)

# Strip text for traveler_type for Expedia
for df in [df_expedia]:
    df['traveler_type'] = df['traveler_type'].apply(simplify_traveler_type)

# --- Rename for consistency ---
for df in [df_booking, df_expedia, df_tripadvisor]:
    df.rename(columns={"traveler_name": "name", "review_text": "text"}, inplace=True)

# --- Robust date parsing ---
for df in [df_booking, df_expedia, df_tripadvisor]:
    df["review_date"] = df["review_date"].apply(lambda x: parser.parse(x) if pd.notna(x) else pd.NaT)
    df["review_date"] = pd.to_datetime(df["review_date"], errors="coerce")

# --- Convert numeric fields ---
for df in [df_booking, df_expedia, df_tripadvisor]:
    df["review_rating"] = pd.to_numeric(df["review_rating"], errors="coerce")
    df["length_of_stay"] = pd.to_numeric(df.get("length_of_stay"), errors="coerce")

# --- Clean text ---
for df in [df_booking, df_expedia, df_tripadvisor]:
    df["text"] = df["text"].astype(str).str.strip()

# --- Drop exact duplicates within each source ---
def deduplicate(df, label):
    before = len(df)
    df.drop_duplicates(subset=["text", "review_date", "review_rating"], inplace=True)
    removed = before - len(df)
    print(f"Duplicates removed in {label}: {removed}")
    return df

df_booking = deduplicate(df_booking, "Booking")
df_expedia = deduplicate(df_expedia, "Expedia")
df_tripadvisor = deduplicate(df_tripadvisor, "TripAdvisor")

# --- Drop rows with missing ratings ---
for df in [df_booking, df_expedia, df_tripadvisor]:
    df.dropna(subset=["review_rating"], inplace=True)

# --- Combine datasets ---
df_all = pd.concat([df_booking, df_expedia, df_tripadvisor], ignore_index=True)

# --- Final deduplication: prioritize Booking > Expedia > TripAdvisor ---
combined_before = len(df_all)
source_priority = {"booking": 3, "expedia": 2, "tripadvisor": 1}
df_all["source_rank"] = df_all["source"].map(source_priority)
df_all = df_all.sort_values(by="source_rank", ascending=False)
df_all.drop_duplicates(subset=["text", "name", "review_date"], inplace=True)
combined_dupes_removed = combined_before - len(df_all)
df_all.drop(columns=["source_rank"], inplace=True)

# --- Filter reviews: 2014 onward ---
df_all = df_all[df_all["review_date"] >= pd.to_datetime("2014-01-01")]

# --- Normalize traveler_type labels ---
df_all["traveler_type"] = df_all["traveler_type"].replace({
    "Solo traveler": "Solo",
    "Couples": "Couple"
})

# Fill empty values for Traveler Type
df_all.fillna({'traveler_type': 'Unknown'}, inplace=True)

# Fill empty values for Lenght of Stay
df_all.fillna({'length_of_stay': '0'}, inplace=True)

# Drop review_title and date_visited columns
df_all.drop(columns=["review_title", "date_visited"], inplace=True)


# --- Save to CSV ---
df_all.to_csv("cleaned_reviews.csv", index=False)

# --- Summary ---
print("\nCleaning complete.")
print(f"Final cleaned review count (2014+): {len(df_all)}")
print("\nDataset shape:", df_all.shape)
print("Columns:", df_all.columns.tolist())
print("\nMissing values per column:\n", df_all.isna().sum())
