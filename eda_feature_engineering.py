# AI Enabled Visa Status Prediction and Processing Time Estimator
# Milestone 2: Exploratory Data Analysis & Feature Engineering

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Set style for plots
sns.set_style("whitegrid")

# 1. Load the cleaned dataset and convert date columns to datetime
df = pd.read_csv('processed_visa.csv')

# Convert date columns to datetime
date_cols = ['application_date', 'biometrics_date', 'decision_date']
for col in date_cols:
    df[col] = pd.to_datetime(df[col], errors='coerce')

# 2. Display dataset shape, info, and summary statistics for processing_days
print("Dataset Shape:", df.shape)
print("\nDataset Info:")
print(df.info())
print("\nSummary Statistics for processing_days:")
print(df['processing_days'].describe())

# 3. Visualizations

# Distribution of processing_days (histogram with KDE)
plt.figure(figsize=(10, 6))
sns.histplot(df['processing_days'], kde=True, bins=50)
plt.title('Distribution of Processing Days')
plt.xlabel('Processing Days')
plt.ylabel('Frequency')
plt.savefig('processing_days_distribution.png')
plt.show()

# Boxplot for processing_days (outlier detection)
plt.figure(figsize=(8, 6))
sns.boxplot(x=df['processing_days'])
plt.title('Boxplot of Processing Days')
plt.xlabel('Processing Days')
plt.show()

# Reverse one-hot encoding for visa_type
visa_type_cols = [col for col in df.columns if col.startswith('visa_type_')]
df['visa_type'] = df[visa_type_cols].idxmax(axis=1).str.replace('visa_type_', '')

# Processing_days vs visa_type (boxplot)
plt.figure(figsize=(12, 6))
sns.boxplot(x='visa_type', y='processing_days', data=df)
plt.title('Processing Days by Visa Type')
plt.xlabel('Visa Type')
plt.ylabel('Processing Days')
plt.xticks(rotation=45)
plt.savefig('processing_days_by_visa_type.png')
plt.show()

# Reverse one-hot encoding for applicant_country
applicant_country_cols = [col for col in df.columns if col.startswith('applicant_country_')]
df['applicant_country'] = df[applicant_country_cols].idxmax(axis=1).str.replace('applicant_country_', '')

# Processing_days vs applicant_country (top 10 countries)
top_countries = df['applicant_country'].value_counts().head(10).index
df_top_countries = df[df['applicant_country'].isin(top_countries)]
plt.figure(figsize=(12, 6))
sns.boxplot(x='applicant_country', y='processing_days', data=df_top_countries)
plt.title('Processing Days by Top 10 Applicant Countries')
plt.xlabel('Applicant Country')
plt.ylabel('Processing Days')
plt.xticks(rotation=45)
plt.savefig('processing_days_by_applicant_country.png')
plt.show()

# Seasonal trend of processing_days using application month
df['application_month'] = df['application_date'].dt.month
monthly_avg = df.groupby('application_month')['processing_days'].mean().reset_index()
plt.figure(figsize=(10, 6))
sns.lineplot(x='application_month', y='processing_days', data=monthly_avg, marker='o')
plt.title('Average Processing Days by Application Month')
plt.xlabel('Application Month')
plt.ylabel('Average Processing Days')
plt.xticks(range(1, 13))
plt.savefig('average_processing_days_by_month.png')
plt.show()

# Application volume per processing_center
plt.figure(figsize=(12, 6))
sns.countplot(x='processing_center', data=df, order=df['processing_center'].value_counts().index)
plt.title('Application Volume per Processing Center')
plt.xlabel('Processing Center')
plt.ylabel('Number of Applications')
plt.xticks(rotation=45)
plt.savefig('application_volume_by_processing_center.png')
plt.show()

# 4. Identify correlations between numeric features and processing_days
numeric_cols = df.select_dtypes(include=['number']).columns
correlations = df[numeric_cols].corr()['processing_days'].sort_values(ascending=False)
print("\nCorrelations with processing_days:")
print(correlations)

# Correlation matrix for processing_days and application_month
corr_matrix = df[["processing_days", "application_month"]].corr()
print("\nCorrelation Matrix:")
print(corr_matrix)

# Heatmap of correlation
plt.figure(figsize=(6, 4))
sns.heatmap(corr_matrix, annot=True, cmap="coolwarm")
plt.title("Correlation Heatmap")
plt.show()

# Scatterplot of processing_days vs application_month
plt.figure(figsize=(8, 6))
sns.scatterplot(x="application_month", y="processing_days", data=df)
plt.title("Processing Days vs Application Month")
plt.xlabel("Application Month")
plt.ylabel("Processing Days")
plt.show()

# 5. Engineer new features

# application_month (already added above)
# FEATURE 2: Seasonal Index (Peak vs Off-Peak)
def get_seasonal_index(month):
    if month in [6, 7, 8]:  # Assuming summer months are peak
        return 'Peak'
    else:
        return 'Off-Peak'

df['seasonal_index'] = df['application_month'].apply(get_seasonal_index)

# country_avg_processing
country_avg = df.groupby('applicant_country')['processing_days'].mean()
df['country_avg_processing'] = df['applicant_country'].map(country_avg)

# FEATURE 4: Visa-Type Average Processing Time (Aggregated Feature)
visa_type_avg = df.groupby('visa_type')['processing_days'].mean()
df['visa_type_avg_processing'] = df['visa_type'].map(visa_type_avg)

# 6. Save the final feature-engineered dataset
df.to_csv('visa_eda_features.csv', index=False)
print("\nFeature-engineered dataset saved as 'visa_eda_features.csv'")
