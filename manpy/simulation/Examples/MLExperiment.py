from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import accuracy_score

def SGD_clf(df):
    x = df.drop(["Result"], axis=1)
    y = df["Result"]
    trainX, testX, trainY, testY = train_test_split(x, y, test_size = 0.2)

    scaler = StandardScaler().fit(trainX)
    trainX = scaler.transform(trainX)
    testX = scaler.transform(testX)

    clf = SGDClassifier("log")
    clf.fit(trainX, trainY)
    y_pred = clf.predict(testX)

    return accuracy_score(testY, y_pred)
