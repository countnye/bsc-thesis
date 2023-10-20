from tensorflow import keras
import keras_tuner as kt
import keras.backend as K
from keras.constraints import max_norm
from keras_uncertainty.layers import DropConnectDense, DropConnectConv2D, StochasticDropout
from keras_uncertainty.utils import numpy_entropy

# need these for ShallowConvNet
def square(x):
    return K.square(x)

def log(x):
    return K.log(K.clip(x, min_value = 1e-7, max_value = 10000))   

def uncertainty(probs):
  return numpy_entropy(probs, axis=-1)

def uncertainty(probs):
  return numpy_entropy(probs, axis=-1)


def build_dropout_model(hp):
      C = 22          # Number of electrodes
      T = 1125        # Time samples of network input

      k_1 = 40        # K is number of convolutional kernels. SUBJECT TO HYPERPARAM TUNING
      f_1 = 25        # F is kernel size SUBJECT TO HYPERPARAM TUNING

      k_2 = 40
      f_2 = C

      f_p = (1, 75)   # Fp is pooling size
      s_p = (1, 15)   # Sp is pool stride

      Nc = 4          # Number of classes
      drop_rates = hp.Choice('drop_rates', [0.1, 0.2, 0.3, 0.4, 0.5, 0.6])

      model = keras.models.Sequential()
      model.add(keras.layers.Conv2D(f_1,  k_1, padding = 'SAME',
                                  activation="linear",
                                  input_shape = (C, T, 1),
                                  kernel_constraint = max_norm(2)))
      model.add(keras.layers.Conv2D(f_2,  k_2, padding = 'SAME',
                                  input_shape = (1, C, T),
                                  activation="linear",
                                  kernel_constraint = max_norm(2)))
      model.add(keras.layers.BatchNormalization(momentum=0.9, epsilon=0.00001))
      model.add(keras.layers.Activation(square))
      model.add(keras.layers.AveragePooling2D(pool_size= f_p, strides= s_p))
      model.add(keras.layers.Activation(log))
      model.add(StochasticDropout(drop_rates))
      model.add(keras.layers.Flatten())
      model.add(keras.layers.Dense(Nc, activation='softmax', kernel_constraint = max_norm(0.5)))

      optimizer = keras.optimizers.Adam(learning_rate=1e-4)
      model.compile(loss="categorical_crossentropy",
                    optimizer=optimizer, metrics=["accuracy"])
      return model

def build_dropconnect_model(hp):
      C = 22          # Number of electrodes
      T = 1125        # Time samples of network input

      k_1 = 40        # K is number of convolutional kernels. SUBJECT TO HYPERPARAM TUNING
      f_1 = 25        # F is kernel size SUBJECT TO HYPERPARAM TUNING

      k_2 = 40
      f_2 = C

      f_p = (1, 75)   # Fp is pooling size
      s_p = (1, 15)   # Sp is pool stride

      Nc = 4          # Number of classes
      drop_rates = hp.Choice('drop_rates', [0.1, 0.2, 0.3, 0.4, 0.5, 0.6])

      model = keras.models.Sequential()
      model.add(keras.layers.Conv2D(f_1,  k_1, padding = 'SAME',
                                  activation="linear",
                                  input_shape = (C, T, 1),
                                  kernel_constraint = max_norm(2)))
      model.add(keras.layers.Conv2D(f_2,  k_2, padding = 'SAME',
                                  input_shape = (1, C, T),
                                  activation="linear",
                                  kernel_constraint = max_norm(2)))
      model.add(keras.layers.BatchNormalization(momentum=0.9, epsilon=0.00001))
      model.add(keras.layers.Activation(square))
      model.add(keras.layers.AveragePooling2D(pool_size= f_p, strides= s_p))
      model.add(keras.layers.Activation(log))
      model.add(DropConnectDense(22, drop_rates))
      model.add(keras.layers.Flatten())
      model.add(keras.layers.Dense(Nc, activation='softmax', kernel_constraint = max_norm(0.5)))

      optimizer = keras.optimizers.Adam(learning_rate=1e-4)
      model.compile(loss="categorical_crossentropy",
                    optimizer=optimizer, metrics=["accuracy"])
      return model

def tune_model(x_train, x_val, y_train, y_val, method, callbacks):
    methods = {'mcdropout': build_dropout_model, 'mcdropconnect': build_dropconnect_model}
    tuner = kt.GridSearch(hypermodel=methods[method],
                          objective='val_loss',
                          max_trials=100,
                          executions_per_trial=1,
                          overwrite=True,
                          directory=f'{method}/tuning')
    tuner.search(x_train, y_train, epochs=100, validation_data=(x_val, y_val),
                 callbacks=callbacks)
    return tuner

    
def create_model(drop_rates, method):
    C = 22          # Number of electrodes
    T = 1125        # Time samples of network input

    k_1 = 40        # K is number of convolutional kernels. SUBJECT TO HYPERPARAM TUNING
    f_1 = 25        # F is kernel size SUBJECT TO HYPERPARAM TUNING

    k_2 = 40
    f_2 = C

    f_p = (1, 75)   # Fp is pooling size
    s_p = (1, 15)   # Sp is pool stride

    Nc = 4          # Number of classes

    model = keras.models.Sequential()
    model.add(keras.layers.Conv2D(f_1,  k_1, padding = 'SAME',
                                activation="linear",
                                input_shape = (C, T, 1),
                                kernel_constraint = max_norm(2)))
    model.add(keras.layers.Conv2D(f_2,  k_2, padding = 'SAME',
                                input_shape = (1, C, T),
                                activation="linear",
                                kernel_constraint = max_norm(2)))
    model.add(keras.layers.BatchNormalization(momentum=0.9, epsilon=0.00001))
    model.add(keras.layers.Activation(square))
    model.add(keras.layers.AveragePooling2D(pool_size= f_p, strides= s_p))
    model.add(keras.layers.Activation(log))
    if method == 'mcdropconnect':
        model.add(DropConnectDense(22, drop_rates))
    elif method == 'mcdropout':
        model.add(StochasticDropout(drop_rates))
    else:
        model.add(keras.layers.Dropout(drop_rates))
    model.add(keras.layers.Flatten())
    model.add(keras.layers.Dense(Nc, activation='softmax', kernel_constraint = max_norm(0.5)))

    optimizer = keras.optimizers.Adam(learning_rate=1e-4)
    model.compile(loss="categorical_crossentropy",
                  optimizer=optimizer, metrics=["accuracy"])
    return model

