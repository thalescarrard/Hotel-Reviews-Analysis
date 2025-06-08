import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load cleaned review data
df = pd.read_csv("cleaned_reviews.csv")

# Convert review_date to datetime, coerce errors to NaT
df['review_date'] = pd.to_datetime(df['review_date'], errors='coerce')

# Keep only reviews from 2020 or later
df = df[df['review_date'] >= pd.to_datetime('2020-01-01')]

# Distribution of review ratings
plt.figure(figsize=(8, 5))
sns.histplot(df["review_rating"].dropna(), bins=20, kde=True, color="skyblue")
plt.title("Distribution of Review Ratings")
plt.xlabel("Rating")
plt.ylabel("Frequency")
plt.tight_layout()
plt.show()

# Number of reviews per source
plt.figure(figsize=(6, 4))
sns.countplot(data=df, x="source", palette="Set2")
plt.title("Number of Reviews per Source")
plt.ylabel("Count")
plt.tight_layout()
plt.show()

# Rating distribution by source
plt.figure(figsize=(8, 5))
sns.boxplot(data=df, x="source", y="review_rating", palette="Set3")
plt.title("Rating Distribution by Source")
plt.tight_layout()
plt.show()

# Average rating over time (monthly)
if 'review_date' in df.columns:
    # Ensure datetime index
    df.set_index('review_date', inplace=True)
    avg_rating_monthly = df['review_rating'].resample('M').mean()
    plt.figure(figsize=(10, 4))
    avg_rating_monthly.plot(marker='o')
    plt.title("Average Rating Over Time")
    plt.ylabel("Average Rating")
    plt.xlabel("Month")
    plt.tight_layout()
    plt.show()
