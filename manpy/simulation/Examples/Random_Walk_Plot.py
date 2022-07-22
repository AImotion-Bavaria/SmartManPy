import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_excel(r"C:\Users\User\PycharmProjects\ManPyExperiments\manpy\simulation\Examples\Random_Walk.xls")
df = list(df.loc[df['entity_id'] == "--"]["message"])
for i in df:
    df[df.index(i)] = float(i)

plt.plot(df)
plt.title("Random_Walk")
plt.show()
