import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeRegressor, plot_tree
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV
import pickle
import matplotlib.pyplot as plt
import ast

array_columns = ['accel_x', 'accel_y', 'accel_z', 'vel_x', 'vel_y', 'vel_z', 'pos_x', 'pos_y', 'pos_z', 'mag_x', 'mag_y', 'mag_z']

df = pd.read_csv("seated_cable_rows.csv", 
                 converters={col: ast.literal_eval for col in array_columns})
labels = [
    93, 78, 87, 78, 84, 85, 78, 89, 67, 89,
    78, 56, 78, 89, 56, 57, 65, 78, 87, 78,
    79, 78, 67, 65, 73, 86, 68, 68, 76, 54,
    36, 78, 68, 64, 89, 87, 67, 67, 77, 68,
    90, 87, 69, 87, 84, 84, 81, 59, 75, 76
]
df['quality_score'] = labels

# Preprocessing
X = df.drop('quality_score', axis=1)
y = df['quality_score']

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

param_grid = {
    'max_depth': [3, 5, 7, None],
    'min_samples_split': [2, 5, 10, 20],
    'min_samples_leaf': [1, 2, 5, 10]
}

grid_search = GridSearchCV(DecisionTreeRegressor(random_state=42),
                          param_grid,
                          cv=5,
                          scoring='neg_mean_squared_error')
grid_search.fit(X_train, y_train)

best_tree = grid_search.best_estimator_

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

pickle.dump(best_tree, "seated_cable_rows.pkl")