#!/usr/bin/env python3
"""
CNN Training for Heart Rhythm Classification
Author: Antigravity AI
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras import layers, models, callbacks
from sklearn.metrics import classification_report, confusion_matrix

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models'))
RESULTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'results'))

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

def build_model(input_shape=(1000, 1), num_classes=3):
    model = models.Sequential([
        # Conv1D(32, 7) + BN + ReLU + MaxPooling1D
        layers.Input(shape=input_shape),
        layers.Conv1D(filters=32, kernel_size=7, padding='same'),
        layers.BatchNormalization(),
        layers.ReLU(),
        layers.MaxPooling1D(pool_size=2),
        
        # Conv1D(64, 5) + BN + ReLU + MaxPooling1D
        layers.Conv1D(filters=64, kernel_size=5, padding='same'),
        layers.BatchNormalization(),
        layers.ReLU(),
        layers.MaxPooling1D(pool_size=2),
        
        # Conv1D(128, 3) + BN + ReLU
        layers.Conv1D(filters=128, kernel_size=3, padding='same'),
        layers.BatchNormalization(),
        layers.ReLU(),
        
        # GlobalAveragePooling1D
        layers.GlobalAveragePooling1D(),
        
        # Dense(64) + Dropout(0.3)
        layers.Dense(64),
        layers.Dropout(0.3),
        
        # Dense(3, activation='softmax')
        layers.Dense(num_classes, activation='softmax')
    ])
    return model

def main():
    # Load dataset
    print("Loading prepared dataset from /data...")
    X_path = os.path.join(DATA_DIR, 'X.npy')
    y_path = os.path.join(DATA_DIR, 'y.npy')
    
    if not os.path.exists(X_path) or not os.path.exists(y_path):
        raise FileNotFoundError("Dataset files not found. Please run dataset_preparation.py first.")
        
    X = np.load(X_path)
    y = np.load(y_path)
    
    print(f"Loaded X shape: {X.shape}, y shape: {y.shape}")
    
    # Shuffle and split into train and validation sets
    indices = np.arange(len(X))
    np.random.seed(42)
    np.random.shuffle(indices)
    X = X[indices]
    y = y[indices]
    
    # 80/20 train/val split
    split_idx = int(0.8 * len(X))
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_train, y_val = y[:split_idx], y[split_idx:]
    
    print(f"Training set: X_train={X_train.shape}, y_train={y_train.shape}")
    print(f"Validation set: X_val={X_val.shape}, y_val={y_val.shape}")
    
    # Class mapping
    class_names = ["Bradycardia", "Normal", "Tachycardia"]
    
    # Build Model
    model = build_model()
    model.summary()
    
    # Compile
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    
    # Callbacks
    early_stopping = callbacks.EarlyStopping(
        monitor='val_loss',
        patience=10,
        restore_best_weights=True,
        verbose=1
    )
    
    reduce_lr = callbacks.ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=4,
        min_lr=1e-6,
        verbose=1
    )
    
    # We will save the best model weights dynamically or at the end
    print("Starting training...")
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=40,
        batch_size=32,
        callbacks=[early_stopping, reduce_lr],
        verbose=1
    )
    
    # Save best model versions
    model_keras_path = os.path.join(MODELS_DIR, 'cnn_model.keras')
    model_h5_path = os.path.join(MODELS_DIR, 'cnn_model.h5')
    
    model.save(model_keras_path)
    model.save(model_h5_path)
    print(f"Model saved to: {model_keras_path} and {model_h5_path}")
    
    # 1. Plot Accuracy
    plt.figure(figsize=(8, 5))
    plt.plot(history.history['accuracy'], label='Train Accuracy', color='#3498db', lw=2)
    plt.plot(history.history['val_accuracy'], label='Val Accuracy', color='#e74c3c', lw=2)
    plt.title('CNN Model Accuracy', fontsize=14, fontweight='bold')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, 'accuracy_plot.png'), dpi=300)
    plt.close()
    
    # 2. Plot Loss
    plt.figure(figsize=(8, 5))
    plt.plot(history.history['loss'], label='Train Loss', color='#3498db', lw=2)
    plt.plot(history.history['val_loss'], label='Val Loss', color='#e74c3c', lw=2)
    plt.title('CNN Model Loss', fontsize=14, fontweight='bold')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, 'loss_plot.png'), dpi=300)
    plt.close()
    
    # Evaluate model
    y_pred_probs = model.predict(X_val)
    y_pred = np.argmax(y_pred_probs, axis=1)
    
    # 3. Generate and print classification report
    report = classification_report(y_val, y_pred, target_names=class_names)
    print("\nClassification Report:\n")
    print(report)
    
    with open(os.path.join(RESULTS_DIR, 'classification_report.txt'), 'w') as f:
        f.write(report)
        
    # 4. Confusion Matrix
    cm = confusion_matrix(y_val, y_pred)
    print("\nConfusion Matrix:\n", cm)
    
    plt.figure(figsize=(6, 5))
    plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    plt.title('Confusion Matrix', fontsize=14, fontweight='bold')
    plt.colorbar()
    tick_marks = np.arange(len(class_names))
    plt.xticks(tick_marks, class_names, rotation=45)
    plt.yticks(tick_marks, class_names)
    
    # Print values on confusion matrix
    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(j, i, format(cm[i, j], 'd'),
                     ha="center", va="center",
                     color="white" if cm[i, j] > thresh else "black")
                     
    plt.ylabel('True label')
    plt.xlabel('Predicted label')
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, 'confusion_matrix.png'), dpi=300)
    plt.close()
    
    print("Evaluation reports and plots saved in results/ folder.")

if __name__ == "__main__":
    main()
