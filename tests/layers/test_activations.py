import math

import six
import numpy as np
import tensorflow as tf

from neupy.utils import asfloat
from neupy.exceptions import (
    LayerConnectionError,
    WeightInitializationError,
)
from neupy import layers, algorithms, init

from base import BaseTestCase
from helpers import simple_classification


class ActivationLayerMainTestCase(BaseTestCase):
    def test_linear_layer_withuot_bias(self):
        input_layer = layers.Input(10)
        output_layer = layers.Linear(2, weight=0.1, bias=None)
        network = layers.join(input_layer, output_layer)

        input_value = asfloat(np.ones((1, 10)))
        actual_output = self.eval(network.output(input_value))
        expected_output = np.ones((1, 2))

        np.testing.assert_array_almost_equal(expected_output, actual_output)

    def test_exception(self):
        with self.assertRaises(TypeError):
            layers.Linear(2, weight=None)

    def test_repr_without_size(self):
        layer = layers.Sigmoid()
        self.assertEqual("Sigmoid(name='sigmoid-1')", str(layer))

    def test_repr_with_size(self):
        layer1 = layers.Sigmoid(13)
        self.assertEqual(
            str(layer1),
            (
                "Sigmoid(13, weight=HeNormal(gain=1.0), "
                "bias=Constant(0), name='sigmoid-1')"
            )
        )

    def test_variables(self):
        network = layers.join(
            layers.Input(2),
            layers.Sigmoid(3, name='sigmoid'),
        )
        self.assertDictEqual(network.layer('sigmoid').variables, {})

        network.outputs
        variables = network.layer('sigmoid').variables
        self.assertSequenceEqual(
            sorted(variables.keys()),
            ['bias', 'weight'])

        self.assertShapesEqual(variables['bias'].shape, (3,))
        self.assertShapesEqual(variables['weight'].shape, (2, 3))

    def test_failed_propagation_for_multiple_inputs(self):
        inputs = layers.parallel(
            layers.Input(1),
            layers.Input(2),
        )
        if six.PY3:
            expected_message = "2 positional arguments but 3 were given."
        else:
            expected_message = (
                "get_output_shape\(\) takes exactly 2 arguments \(3 given\)"
            )
        with self.assertRaisesRegexp(TypeError, expected_message):
            layers.join(inputs, layers.Relu(3, name='relu'))

    def test_fail_rejoining_to_new_input(self):
        network = layers.join(
            layers.Input(10),
            layers.Relu(5, name='relu'),
        )
        network.create_variables()

        error_message = "Cannot connect layer `in` to layer `relu`"
        with self.assertRaisesRegexp(LayerConnectionError, error_message):
            layers.join(layers.Input(7, name='in'), network.layer('relu'))

    def test_invalid_input_shape(self):
        error_message = (
            "Input shape expected to have 2 "
            "dimensions, got 3 instead. Shape: \(\?, 10, 3\)"
        )
        with self.assertRaisesRegexp(LayerConnectionError, error_message):
            layers.join(
                layers.Input((10, 3)),
                layers.Linear(10),
            )

    def test_unknwown_feature_during_weight_init(self):
        network = layers.join(
            layers.Input(None),
            layers.Linear(10, name='linear'),
        )

        message = (
            "Cannot create variables for the layer `linear`, "
            "because number of input features is unknown. "
            "Input shape: \(\?, \?\)"
        )
        with self.assertRaisesRegexp(WeightInitializationError, message):
            network.create_variables()

        with self.assertRaisesRegexp(WeightInitializationError, message):
            network.outputs

    def test_invalid_weight_shape(self):
        network = layers.join(
            layers.Input(5),
            layers.Linear(4, weight=np.ones((3, 3))),
        )
        with self.assertRaisesRegexp(ValueError, "Cannot create variable"):
            network.create_variables()

        variable = tf.Variable(np.ones((3, 3)), dtype=tf.float32)
        network = layers.join(
            layers.Input(5),
            layers.Linear(4, weight=variable),
        )
        with self.assertRaisesRegexp(ValueError, "Cannot create variable"):
            network.create_variables()


class ActivationLayersTestCase(BaseTestCase):
    def test_activation_layers_without_size(self):
        X = np.array([1, 2, -1, 10])
        expected_output = np.array([1, 2, 0, 10])

        layer = layers.Relu()

        actual_output = self.eval(layer.output(X))
        np.testing.assert_array_equal(actual_output, expected_output)

    def test_hard_sigmoid_layer(self):
        layer = layers.HardSigmoid(6)

        input_value = asfloat(np.array([[-3, -2, -1, 0, 1, 2]]))
        expected = np.array([[0, 0.1, 0.3, 0.5, 0.7, 0.9]])

        output = self.eval(layer.activation_function(input_value))
        np.testing.assert_array_almost_equal(output, expected)

    def test_linear_layer(self):
        layer = layers.Linear(1)
        self.assertEqual(layer.activation_function(1), 1)

    def test_tanh_layer(self):
        layer1 = layers.Tanh(1)
        self.assertGreater(1, self.eval(layer1.activation_function(1.)))

    def test_leaky_relu(self):
        X = asfloat(np.array([[10, 1, 0.1, 0, -0.1, -1]]).T)
        expected_output = asfloat(np.array([[10, 1, 0.1, 0, -0.001, -0.01]]).T)
        layer = layers.LeakyRelu(1)

        actual_output = self.eval(layer.activation_function(X))
        np.testing.assert_array_almost_equal(
            expected_output, actual_output)

    def test_softplus_layer(self):
        layer = layers.Softplus(1)
        self.assertAlmostEqual(
            math.log(2),
            self.eval(layer.activation_function(0.)))

    def test_elu_layer(self):
        test_input = asfloat(np.array([[10, 1, 0.1, 0, -1]]).T)
        expected_output = np.array([
            [10, 1, 0.1, 0, -0.6321205588285577]]).T

        layer = layers.Elu()
        actual_output = self.eval(layer.activation_function(test_input))

        np.testing.assert_array_almost_equal(
            expected_output, actual_output)


class SigmoidTestCase(BaseTestCase):
    def test_sigmoid_layer(self):
        layer1 = layers.Sigmoid(1)
        self.assertGreater(1, self.eval(layer1.activation_function(1.)))

    def test_sigmoid_semantic_segmentation(self):
        network = layers.join(
            layers.Input((10, 10, 1)),
            layers.Sigmoid(),
        )

        input = 10 * np.random.random((2, 10, 10, 1)) - 5
        actual_output = self.eval(network.output(input))

        self.assertTrue(np.all(actual_output >= 0))
        self.assertTrue(np.all(actual_output <= 1))


class SoftmaxTestCase(BaseTestCase):
    def test_softmax_layer(self):
        test_input = asfloat(np.array([[0.5, 0.5, 0.1]]))
        softmax_layer = layers.Softmax(3)
        correct_result = np.array([[0.37448695, 0.37448695, 0.25102611]])
        np.testing.assert_array_almost_equal(
            correct_result,
            self.eval(softmax_layer.activation_function(test_input)))

    def test_softmax_semantic_segmentation(self):
        network = layers.join(
            layers.Input((10, 10, 6)),
            layers.Softmax(),
        )

        input = np.random.random((2, 10, 10, 6))
        actual_output = self.eval(network.output(input))

        np.testing.assert_array_almost_equal(
            actual_output.sum(axis=-1),
            np.ones((2, 10, 10)))


class ReluTestCase(BaseTestCase):
    def test_relu_activation(self):
        layer = layers.Relu()
        self.assertEqual(0, self.eval(layer.activation_function(-10)))
        self.assertEqual(0, self.eval(layer.activation_function(0)))
        self.assertEqual(10, self.eval(layer.activation_function(10)))

        layer = layers.Relu(alpha=0.1)
        self.assertAlmostEqual(-1, self.eval(layer.activation_function(-10)))
        self.assertAlmostEqual(-0.2, self.eval(layer.activation_function(-2)))

    def test_relu(self):
        # Test alpha parameter
        X = asfloat(np.array([[10, 1, 0.1, 0, -0.1, -1]]).T)
        expected_output = asfloat(np.array([[10, 1, 0.1, 0, -0.01, -0.1]]).T)
        layer = layers.Relu(1, alpha=0.1)

        actual_output = self.eval(layer.activation_function(X))
        np.testing.assert_array_almost_equal(
            expected_output, actual_output)

    def test_repr_without_size(self):
        self.assertEqual("Relu(alpha=0, name='relu-1')", str(layers.Relu()))

    def test_repr_with_size(self):
        self.assertEqual(
            str(layers.Relu(10)),
            (
                "Relu(10, alpha=0, weight=HeNormal(gain=2), "
                "bias=Constant(0), name='relu-1')"
            )
        )


class PReluTestCase(BaseTestCase):
    def test_invalid_alpha_axes_parameter(self):
        network = layers.join(
            layers.PRelu(10, alpha_axes=2),
            layers.Relu(),
        )
        with self.assertRaises(LayerConnectionError):
            # cannot specify 2-axis, because we only
            # have 0 and 1 axes (2D input)
            layers.join(layers.Input(10), network)

        with self.assertRaises(ValueError):
            # 0-axis is not allowed
            layers.PRelu(10, alpha_axes=0)

    def test_prelu_alpha_init_random_params(self):
        prelu_layer = layers.PRelu(10, alpha=init.XavierNormal())
        prelu_layer.create_variables((None, 5))

        alpha = self.eval(prelu_layer.alpha)
        self.assertEqual(10, np.unique(alpha).size)

    def test_prelu_alpha_init_constant_value(self):
        prelu_layer = layers.PRelu(10, alpha=0.25)
        prelu_layer.create_variables((None, 5))

        alpha = self.eval(prelu_layer.alpha)
        self.assertEqual(alpha.shape, (10,))
        np.testing.assert_array_almost_equal(alpha, np.ones(10) * 0.25)

    def test_prelu_layer_param_conv(self):
        network = layers.join(
            layers.Input((10, 10, 3)),
            layers.Convolution((3, 3, 5)),
            layers.PRelu(alpha=0.25, alpha_axes=(1, 3), name='prelu'),
        )
        network.create_variables()

        alpha = self.eval(network.layer('prelu').alpha)
        expected_alpha = np.ones((8, 5)) * 0.25

        self.assertEqual(alpha.shape, (8, 5))
        np.testing.assert_array_almost_equal(alpha, expected_alpha)

    def test_prelu_output_by_dense_input(self):
        prelu_layer = layers.PRelu(alpha=0.25)
        prelu_layer.create_variables((None, 1))

        X = np.array([[10, 1, 0.1, 0, -0.1, -1]]).T
        expected_output = np.array([[10, 1, 0.1, 0, -0.025, -0.25]]).T
        actual_output = self.eval(prelu_layer.activation_function(X))

        np.testing.assert_array_almost_equal(expected_output, actual_output)

    def test_prelu_output_by_spatial_input(self):
        network = layers.join(
            layers.Input((10, 10, 3)),
            layers.Convolution((3, 3, 5)),
            layers.PRelu(alpha=0.25, alpha_axes=(1, 3)),
        )

        X = asfloat(np.random.random((1, 10, 10, 3)))
        actual_output = self.eval(network.output(X))
        self.assertEqual(actual_output.shape, (1, 8, 8, 5))

    def test_prelu_param_updates(self):
        x_train, _, y_train, _ = simple_classification()
        prelu_layer1 = layers.PRelu(20, alpha=0.25)
        prelu_layer2 = layers.PRelu(1, alpha=0.25)

        gdnet = algorithms.GradientDescent(
            [
                layers.Input(10),
                prelu_layer1,
                prelu_layer2,
            ],
            batch_size=None,
        )

        prelu1_alpha_before_training = self.eval(prelu_layer1.alpha)
        prelu2_alpha_before_training = self.eval(prelu_layer2.alpha)

        gdnet.train(x_train, y_train, epochs=10)

        prelu1_alpha_after_training = self.eval(prelu_layer1.alpha)
        prelu2_alpha_after_training = self.eval(prelu_layer2.alpha)

        self.assertTrue(all(np.not_equal(
            prelu1_alpha_before_training,
            prelu1_alpha_after_training,
        )))
        self.assertTrue(all(np.not_equal(
            prelu2_alpha_before_training,
            prelu2_alpha_after_training,
        )))

    def test_repr_without_size(self):
        self.assertEqual(
            "PRelu(alpha_axes=(-1,), alpha=Constant(0.25), name='p-relu-1')",
            str(layers.PRelu()))

    def test_repr_with_size(self):
        self.assertEqual(
            str(layers.PRelu(10)),
            (
                "PRelu(10, alpha_axes=(-1,), alpha=Constant(0.25), "
                "weight=HeNormal(gain=2), bias=Constant(0), "
                "name='p-relu-1')"
            )
        )

    def test_prelu_variables(self):
        network = layers.join(
            layers.Input(2),
            layers.PRelu(3, name='prelu'),
        )
        self.assertDictEqual(network.layer('prelu').variables, {})

        network.create_variables()
        variables = network.layer('prelu').variables
        self.assertSequenceEqual(
            sorted(variables.keys()),
            ['alpha', 'bias', 'weight'])

        self.assertShapesEqual(variables['bias'].shape, (3,))
        self.assertShapesEqual(variables['weight'].shape, (2, 3))
        self.assertShapesEqual(variables['alpha'].shape, (3,))
