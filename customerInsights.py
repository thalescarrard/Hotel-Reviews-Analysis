# Customer Experience Insights

import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from textblob import TextBlob
import seaborn as sns
from deep_translator import GoogleTranslator
from tqdm import tqdm
import spacy
from collections import Counter
from collections import defaultdict


# Load the cleaned data
df = pd.read_csv("cleaned_reviews.csv")

# Drop missing or non-string entries in review text
df = df[df['text'].notna() & df['text'].apply(lambda x: isinstance(x, str))]

# Translate reviews if not already in English
def translate_to_english(text):
    try:
        if pd.notnull(text) and len(text.strip()) > 5:
            return GoogleTranslator(source='auto', target='en').translate(text)
    except:
        return text  # fallback if translation fails

# Only translate if 'translated_text' column doesn't already exist
if 'translated_text' not in df.columns:
    tqdm.pandas()
    df['translated_text'] = df['text'].progress_apply(translate_to_english)

# Optional: Save progress with translations
df.to_csv("translated_reviews.csv", index=False)

# Drop null values 
valid_texts = df['translated_text'].dropna().astype(str)

# Sentiment Analysis using TextBlob
df['sentiment'] = valid_texts.apply(lambda x: TextBlob(x).sentiment.polarity)
df['sentiment_category'] = pd.cut(df['sentiment'], bins=[-1, -0.1, 0.1, 1], labels=['Negative', 'Neutral', 'Positive'])
plt.figure(figsize=(6, 4))
sns.countplot(data=df, x='sentiment_category', palette='coolwarm')
plt.title("Sentiment Distribution")
plt.tight_layout()
plt.show()

# Keep only negative reviews
negative_reviews = df[df['sentiment'] < 0.1]
negative_texts = negative_reviews['translated_text'].dropna().astype(str)

# Filter out missing traveler types and sentiments
filtered_df = df[df['traveler_type'].notna() & df['sentiment'].notna()]

# Sentiment by Traveler Type
avg_sentiment = filtered_df.groupby('traveler_type')['sentiment'].mean().reset_index()

plt.figure(figsize=(8, 5))
sns.barplot(data=avg_sentiment.sort_values(by="sentiment", ascending=False), x='traveler_type', y='sentiment', palette='coolwarm')
plt.title("Average Sentiment by Traveler Type")
plt.ylabel("Average Sentiment")
plt.xlabel("Traveler Type")
plt.tight_layout()
plt.show()

# Frequent Bigrams or Trigrams
# Using already cleaned/translations: valid_texts
bigram_vectorizer = CountVectorizer(ngram_range=(2, 3), stop_words='english', max_features=20)
X2 = bigram_vectorizer.fit_transform(valid_texts)
bigram_freq = pd.DataFrame({
    "bigram": bigram_vectorizer.get_feature_names_out(),
    "count": X2.toarray().sum(axis=0)
})

plt.figure(figsize=(10, 6))
sns.barplot(data=bigram_freq.sort_values(by="count", ascending=False), x="count", y="bigram", palette="magma")
plt.title("Top 20 Most Frequent Phrases in Reviews")
plt.tight_layout()
plt.show()

# Named Entity Recognition with spaCy
# Load English model
nlp = spacy.load("en_core_web_sm")

# Apply only to valid (translated) texts
texts_sample = valid_texts[:1200]  # limit to 1000 for speed

# Extract entities
all_entities = []
for doc in nlp.pipe(texts_sample, disable=["parser", "tagger"]):
    all_entities.extend([(ent.text, ent.label_) for ent in doc.ents])

# Count and sort entities
entity_df = pd.DataFrame(all_entities, columns=["Entity", "Label"])
top_entities = entity_df.groupby("Label")["Entity"].apply(lambda x: Counter(x).most_common(5))

# Organize entities by type
entities_by_type = {}
for ent, label in all_entities:
    if label not in entities_by_type:
        entities_by_type[label] = []
    entities_by_type[label].append(ent)

# Sentiment by Entity
# Optional: filter reviews with text only
valid_df = df[df['translated_text'].notna() & df['translated_text'].apply(lambda x: isinstance(x, str))]

# Initialize storage
entity_sentiments = defaultdict(list)

# Loop through reviews and extract entities with sentiment
for text in valid_df['translated_text']:
    doc = nlp(text)
    polarity = TextBlob(text).sentiment.polarity
    for ent in doc.ents:
        if ent.label_ in {"ORG", "PERSON"}:
            key = (ent.text.lower(), ent.label_)
            entity_sentiments[key].append(polarity)

# Build sentiment DataFrame
avg_entity_sentiment = pd.DataFrame([
    {
        "entity": ent_text,
        "label": label,
        "avg_sentiment": sum(pols)/len(pols),
        "count": len(pols)
    }
    for (ent_text, label), pols in entity_sentiments.items()
    if len(pols) >= 2
])

# Top 10 entities with lowest sentiment
top_negative = avg_entity_sentiment.sort_values(by="avg_sentiment").head(10)
plt.figure(figsize=(10, 6))
sns.barplot(data=top_negative, x="avg_sentiment", y="entity", hue="label", dodge=False, palette="coolwarm")
plt.title("Lowest Average Sentiment (ORG & PERSON)")
plt.xlabel("Average Sentiment")
plt.ylabel("Entity")
plt.tight_layout()
plt.show()

# Top 10 entities with highest sentiment
top_positive = avg_entity_sentiment.sort_values(by="avg_sentiment", ascending=False).head(10)
plt.figure(figsize=(10, 6))
sns.barplot(data=top_positive, x="avg_sentiment", y="entity", hue="label", dodge=False, palette="crest")
plt.title("Highest Average Sentiment (ORG & PERSON)")
plt.xlabel("Average Sentiment")
plt.ylabel("Entity")
plt.tight_layout()
plt.show()

# Generate Word Cloud
## text_combined = " ".join(df['translated_text'].dropna().astype(str))
text_combined = " ".join(negative_reviews['translated_text'].dropna().astype(str))
wordcloud = WordCloud(width=1000, height=500, background_color='white').generate(text_combined)
plt.figure(figsize=(12, 6))
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis('off')
plt.title("Most Common Words in Reviews")
plt.tight_layout()
plt.show()