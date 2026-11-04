from pathlib import Path
import pandas as pd

data_path = Path(__file__).with_name("iris.data")

columns = [
    "sepal_length",
    "sepal_width",
    "petal_length",
    "petal_width",
    "class",
]

df = pd.read_csv(data_path, header=None, names=columns)

X = df.iloc[:, :-1]
y = df.iloc[:, [-1]]

# print(df.head())
# print(f"Dataset shape: {df.shape}")
# print("\nFeatures:")
# print(X)
# print("\nTargets:")
# print(y)


# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
#     print(df)

a = df.loc[:, "sepal_length"]
print(a)
