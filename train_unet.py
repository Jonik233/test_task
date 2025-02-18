import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Setting log level to remove extra warnings

import tensorflow as tf
from utils import Config
from data import DataUtils
from dotenv import load_dotenv
import segmentation_models as sm

load_dotenv()

# Loading data dirs
IMG_DIR = os.getenv("UNET_IMG_DIR")
CSV_DIR = os.getenv("UNET_CSV_DIR")
CONFIG_DIR = os.getenv("UNET_CONFIG_DIR")

# Loading configuration
config = Config(CONFIG_DIR).load()

### Hyperparameters ###
LR = config["learning_rate"]
EPOCHS = config["epochs"]
NUM_CLASSES = config["num_classes"]
BATCH_SIZE = config["batch_size"]
BACKBONE = config["backbone"]
ACTIVATION = config["activation"]
preprocessing_fn = DataUtils.get_preprocessing_fn(BACKBONE)

ds = DataUtils.load_data(IMG_DIR, CSV_DIR) # Loading data
train_ds, val_ds = DataUtils.split_data(ds, 0.8) # Splitting data

# Preparing datasets
train_ds = DataUtils.prepare_ds(train_ds, BATCH_SIZE, preprocessing_fn, masks=True)
val_ds = DataUtils.prepare_ds(val_ds, BATCH_SIZE, preprocessing_fn, masks=True)

# Loaing model
model = sm.Unet(BACKBONE, classes=NUM_CLASSES, activation=ACTIVATION)

# Model compilation
optimizer = tf.keras.optimizers.Adam(LR)
dice_loss = sm.losses.DiceLoss()
metrics = sm.metrics.FScore(threshold=0.5)
model.compile(optimizer, dice_loss, metrics)

# Setting callbacks
callbacks = [
    tf.keras.callbacks.ModelCheckpoint(config["weights_path"], save_weights_only=True, save_best_only=True, mode='min'),
    tf.keras.callbacks.ReduceLROnPlateau(patience=3),
    tf.keras.callbacks.TensorBoard(log_dir=config["logs_path"], histogram_freq=1)
]

# Training
history = model.fit(
    train_ds,
    steps_per_epoch=len(train_ds),
    epochs=EPOCHS,
    callbacks=callbacks, 
    validation_data=val_ds, 
    validation_steps=len(val_ds)
)