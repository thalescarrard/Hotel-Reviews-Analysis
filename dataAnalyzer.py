import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load cleaned review data
df = pd.read_csv("cleaned_reviews.csv")

# Convert review_date to datetime, coerce errors to NaT
df['review_date'] = pd.to_datetime(df['review_date'], errors='coerce')

# Keep only reviews from 2014 or later
df = df[df['review_date'] >= pd.to_datetime('2014-01-01')]

# Number of reviews per source
plt.figure(figsize=(6, 4))
sns.countplot(data=df, x="source", palette="Set2")
plt.title("Number of Reviews per Source")
plt.ylabel("Count")
plt.tight_layout()
plt.show()

# Distribution of review ratings
plt.figure(figsize=(8, 5))
sns.histplot(df["review_rating"].dropna(), bins=20, kde=True, color="skyblue")
plt.title("Distribution of Review Ratings")
plt.xlabel("Rating")
plt.ylabel("Frequency")
plt.tight_layout()
plt.show()

# Average rating per year
df['year'] = df['review_date'].dt.year
avg_rating_yearly = df.groupby('year')['review_rating'].mean()

plt.figure(figsize=(8, 5))
sns.lineplot(x='year', y='review_rating', data=df, ci=95, marker='o', color='coral')
plt.title("Average Rating by Year with Trend Line")
plt.ylabel("Average Rating")
plt.xlabel("Year")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# Number of reviews per year
review_counts_yearly = df.groupby('year')['review_rating'].count()

plt.figure(figsize=(8, 4))
review_counts_yearly.plot(kind='bar', color='teal')
plt.title("Number of Reviews by Year")
plt.ylabel("Review Count")
plt.xlabel("Year")
plt.tight_layout()
plt.show()
# Reset index to make review_date a column again
df.reset_index(inplace=True)

# Reviews by Traveler Type
plt.figure(figsize=(8, 4))
sns.countplot(data=df, x='traveler_type', palette='pastel', order=df['traveler_type'].value_counts().index)
plt.title("Number of Reviews by Traveler Type")
plt.ylabel("Count")
plt.xlabel("Traveler Type")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# Average rating per traveler type (excluding missing traveler_type)
df_filtered = df[df['traveler_type'].notna()]
avg_rating_traveler = df_filtered.groupby('traveler_type')['review_rating'].mean().sort_values(ascending=False)

# Plot average rating per traveler type
plt.figure(figsize=(8, 5))
sns.barplot(x=avg_rating_traveler.index, y=avg_rating_traveler.values, palette="viridis")
plt.title("Average Review Rating by Traveler Type")
plt.xlabel("Traveler Type")
plt.ylabel("Average Rating")
plt.ylim(0, 10)  # assuming ratings are out of 10
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# Avg Rating by Length of Stay
plt.figure(figsize=(8, 5))
sns.boxplot(data=df[df['length_of_stay'].notna()], x='length_of_stay', y='review_rating', palette='Blues')
plt.title("Review Rating by Length of Stay")
plt.xlabel("Length of Stay (days)")
plt.ylabel("Rating")
plt.tight_layout()
plt.show()
