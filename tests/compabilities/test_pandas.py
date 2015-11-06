import pandas as pd
from sklearn import datasets, preprocessing, metrics
from sklearn.cross_validation import train_test_split
from neupy import algorithms, layers

from base import BaseTestCase


class PandasCompatibilityTestCase(BaseTestCase):
    def test_pandas_for_bp(self):
        dataset = datasets.load_diabetes()
        target = dataset.target.reshape(-1, 1)

        input_scaler = preprocessing.MinMaxScaler()
        target_scaler = preprocessing.MinMaxScaler()

        n_features = dataset.data.shape[1]
        input_columns = ['column_' + str(i) for i in range(n_features)]

        pandas_data = pd.DataFrame(dataset.data, columns=input_columns)
        pandas_data['target'] = target_scaler.fit_transform(target)
        pandas_data[input_columns] = input_scaler.fit_transform(
            pandas_data[input_columns]
        )

        x_train, x_test, y_train, y_test = train_test_split(
            pandas_data[input_columns],
            pandas_data['target'],
            train_size=0.85
        )

        bpnet = algorithms.Backpropagation(
            connection=[
                layers.Sigmoid(10),
                layers.Sigmoid(40),
                layers.Output(1),
            ],
            use_bias=True,
            show_epoch=100
        )

        bpnet.train(x_train, y_train, epochs=1000)
        y_predict = bpnet.predict(x_test)

        error = metrics.mean_absolute_error(
            target_scaler.inverse_transform(y_test),
            target_scaler.inverse_transform(y_predict).round()
        )
        self.assertAlmostEqual(51.2239, error, places=4)
