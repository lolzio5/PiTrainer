import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV
import pickle
import matplotlib.pyplot as plt
import ast
import re
import json

df = pd.read_csv('backend/lat_pulldowns.csv', header=None)

grouped = df.groupby(0).agg(lambda x: list(x)).reset_index()


array_columns = ['rep_nb','time_stamp', 'accel_x', 'accel_y', 'accel_z', 'vel_x', 'vel_y', 'vel_z', 'pos_x', 'pos_y', 'pos_z', 'mag_x', 'mag_y', 'mag_z']

# # Open the file and read the lines
# with open("backend/seated_cable_rows.csv", "r") as file:
#     lines = file.readlines()

# # Manually process rows
# data = []
# for line in lines[1:]:
#     # Strip newline and split by commas using the regular expression
#     parts = re.split(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', line.strip())
#     data.append(parts)

# Convert to DataFrame
df = pd.DataFrame(grouped)
df.columns = array_columns

print(df)
# for column in df.columns:
#     # Apply ast.literal_eval only to columns that contain list-like strings
#     df[column] = df[column].apply(lambda x:ast.literal_eval(x))
#     df[column] = df[column].apply(lambda x:ast.literal_eval(x) if type(x) == str else x)

labels = [78, 78, 56, 90, 98, 78, 79, 67, 89, 89, 89, 90, 89, 89, 67, 89, 98, 78, 79, 88, 65, 77, 76, 78, 78, 64, 46, 57, 87, 87, 54, 34,
54, 34, 32, 76, 57, 89, 79, 76, 78, 98, 87, 78, 76, 57, 87, 68, 78, 87, 75]
df['quality_score'] = labels

# Convert list columns to statistical features
def extract_features(series):
    return pd.Series({
        'mean': np.mean(series),
        'std': np.std(series),
        'median': np.median(series),
        'min': np.min(series),
        'max': np.max(series),
        'iqr': np.percentile(series, 75) - np.percentile(series, 25),
        'skew': pd.Series(series).skew(),
        'kurtosis': pd.Series(series).kurtosis()
    })


# Process sensor columns
sensor_columns = ['accel_x', 'accel_y', 'accel_z', 
                 'vel_x', 'vel_y', 'vel_z',
                 'pos_x', 'pos_y', 'pos_z',
                 'mag_x', 'mag_y', 'mag_z']

# Create new DataFrame with extracted features
feature_df = pd.DataFrame()
for col in sensor_columns:
    feature_df = pd.concat([feature_df, df[col].apply(extract_features).add_prefix(f"{col}_")], axis=1)

# Add target
feature_df['quality_score'] = df['quality_score']

# Split data
# Preprocessing
X = feature_df.drop('quality_score', axis=1)
y = feature_df['quality_score']


# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

param_grid = {
    'n_estimators': [50, 100, 200, 300],
    'max_depth': [3, 5, 7, 10, 15, 20],
    'learning_rate': [0.01, 0.05, 0.1, 0.2],
}

# from sklearn.model_selection import RandomizedSearchCV

# random_search = GridSearchCV(
#     XGBRegressor(random_state=42, verbose=1),
#     param_grid=param_grid,
#     cv=2,  # More cross-validation folds
#     scoring='neg_mean_squared_error',
#     verbose=1
# )
# random_search.fit(X_train, y_train)



#best_tree = random_search.best_estimator_

# with open("backend/lat_pulldowns.pkl", "wb") as file:
#     pickle.dump(best_tree, file)

with open("backend/lat_pulldowns.pkl", "rb") as file:
    best_tree = pickle.load(file)

# print(type(X_test))
# print(X_test)
# Evaluate
def evaluate_model(best_tree, X_test, y_test):
    y_pred = best_tree.predict(X_test)
    print(f"MAE: {mean_absolute_error(y_test, y_pred):.2f}")
    print(f"MSE: {mean_squared_error(y_test, y_pred):.2f}")
    print(f"R²: {r2_score(y_test, y_pred):.2f}")
    
print("Test Set Performance:")
evaluate_model(best_tree, X_test, y_test)

# Feature Importance
feature_importance = pd.Series(best_tree.feature_importances_, index=X.columns)
plt.figure(figsize=(10, 6))
feature_importance.sort_values().plot(kind='barh')
plt.title('Feature Importance')
plt.show()