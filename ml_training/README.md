# ML Training - Tajweed Analysis Model

This directory contains the machine learning training pipeline for the AI Tajweed Analysis feature.

## 📓 Training Notebook

**File**: `tajweed_wav2vec2_tpu_training.ipynb`

Complete Kaggle TPU notebook for training a Tajweed rule classifier using fine-tuned Wav2Vec2.

### Architecture

- **Base Model**: `facebook/wav2vec2-xls-r-300m` (pre-trained multilingual speech model)
- **Fine-tuning**: Freeze all layers except last 4 transformer blocks
- **Custom Head**:
  - Conv1D (256 → 128 filters)
  - Bidirectional LSTM (128 units)
  - GlobalAveragePooling1D
  - Dense (6 classes, softmax)

### Classes (6 Tajweed Rules)

0. **Correct** - No Tajweed violation
1. **Al-Madd** - Vowel elongation (المد)
2. **Ghunnah** - Nasalization (الغنة)
3. **Ikhfāʾ** - Concealment (الإخفاء)
4. **Idghām** - Assimilation (الإدغام)
5. **Qalqalah** - Echoing (القلقلة)

### Training Specifications

| Parameter | Value |
|-----------|-------|
| **Platform** | Kaggle TPU v5e-8 |
| **Batch Size** | 32 |
| **Epochs** | 8-12 (with early stopping) |
| **Optimizer** | AdamW (lr=2e-5, weight_decay=0.01) |
| **Mixed Precision** | bfloat16 |
| **XLA Compilation** | Enabled |
| **Label Smoothing** | 0.1 |
| **Target Accuracy** | 93-95% |
| **Target Runtime** | 10-15 minutes |

### Data Augmentation

- **Noise Injection**: Gaussian noise (σ=0.005)
- **Time Stretching**: Speed variation (0.9x - 1.1x)
- **SpecAugment**: Applied via Wav2Vec2FeatureExtractor
- **Augmentation Rate**: 50% of training samples
- **Expected Dataset Size**: ~1500 → ~3000 samples (with augmentation)

### Features

1. **TPU Optimization**
   - `tf.distribute.TPUStrategy`
   - Efficient data prefetching
   - XLA graph compilation
   - Mixed precision (bfloat16)

2. **Production-Ready Export**
   - Keras `.keras` format (SavedModel)
   - TFLite with FP16 quantization
   - Target latency: <100ms for real-time feedback

3. **Comprehensive Evaluation**
   - Test set accuracy
   - Confusion matrix
   - Classification report per class
   - Inference speed benchmarks

## 🚀 Usage on Kaggle

### 1. Setup Kaggle Notebook

1. Create new notebook on Kaggle
2. Enable **TPU v5e-8** accelerator (Settings → Accelerator)
3. Upload QDAT dataset to Kaggle Datasets

### 2. Dataset Structure

```
/kaggle/input/qdat/al-maidah-109/
├── correct/
│   ├── audio_001.wav
│   ├── audio_002.wav
│   └── ...
├── madd/
├── ghunnah/
├── ikhfa/
├── idgham/
└── qalqalah/
```

**Requirements**:
- Audio format: WAV (16kHz mono)
- Duration: 5-10 seconds per sample
- Minimum: ~250 samples per class (~1500 total)

### 3. Run Training

```python
# Copy notebook content into Kaggle
# Click "Run All" or execute cells sequentially
# Training will take ~10-15 minutes on TPU
```

### 4. Download Trained Model

After training completes, download from `/kaggle/working/`:
- `tajweed_model.keras` - Full Keras model
- `tajweed_model.tflite` - TFLite for production
- `model_metadata.json` - Training metadata
- `training_history.png` - Training curves
- `confusion_matrix.png` - Performance visualization

## 📦 Integration with Backend

### 1. Copy Models

```bash
# From Kaggle downloads to Flask backend
cp tajweed_model.keras backend-flask/models/
cp tajweed_model.tflite backend-flask/models/
cp model_metadata.json backend-flask/models/
```

### 2. Update Configuration

Edit `backend-flask/.env`:
```bash
MODEL_PATH=./models/tajweed_model.keras
# Or for TFLite:
# MODEL_PATH=./models/tajweed_model.tflite
```

### 3. Verify Integration

```python
# Test model loading
from ml.implementations.model_loader import ModelLoader

loader = ModelLoader(model_path='models/tajweed_model.keras')
model = loader.get_model()
print(f"Model loaded: {model.summary()}")
```

## 🔧 Customization

### Change Target Verse

To train on different Quran verses, update dataset path in notebook:
```python
base_path = '/kaggle/input/qdat/surah-name-ayah-number'
```

### Adjust Hyperparameters

Modify `CONFIG` dict in notebook:
```python
CONFIG = {
    'batch_size': 32,      # Increase for faster training
    'epochs': 12,          # More epochs = better accuracy
    'learning_rate': 2e-5, # Lower for fine-tuning
    # ...
}
```

### Add More Classes

1. Update `num_classes` in CONFIG
2. Add folders in dataset structure
3. Update `class_names` list
4. Backend will automatically handle new classes

## 📊 Expected Performance

| Metric | Target | Typical |
|--------|--------|---------|
| **Test Accuracy** | 93-95% | ~94% |
| **Training Time** | 10-15 min | ~12 min |
| **TFLite Latency** | <100ms | ~50-80ms |
| **Model Size (TFLite)** | <50 MB | ~35-45 MB |

## 🐛 Troubleshooting

### TPU Not Detected
```python
# Check TPU availability
import tensorflow as tf
print(tf.config.list_physical_devices('TPU'))

# If empty, ensure TPU is enabled in notebook settings
```

### Out of Memory
- Reduce `batch_size` from 32 to 16
- Reduce `max_duration` from 10 to 5 seconds
- Use fewer augmentation techniques

### Low Accuracy
- Increase `epochs` (12-15)
- Add more training data
- Reduce `label_smoothing` to 0.05
- Unfreeze more Wav2Vec2 layers (change `freeze_layers` to -6)

### Slow Inference
- Ensure TFLite quantization is enabled
- Use GPU/TPU for batch inference
- Reduce audio `max_length`
- Consider model pruning/distillation

## 📚 References

- **Wav2Vec2 XLS-R**: [Hugging Face Model Card](https://huggingface.co/facebook/wav2vec2-xls-r-300m)
- **QDAT Dataset**: Quranic Data for Arabic Text & Audio
- **TFLite Optimization**: [TensorFlow Lite Guide](https://www.tensorflow.org/lite/performance/best_practices)
- **TPU Training**: [Kaggle TPU Documentation](https://www.kaggle.com/docs/tpu)

## 📝 Notes

- Model uses raw waveform input (no manual MFCC extraction needed)
- Wav2Vec2FeatureExtractor handles all preprocessing
- Real-time inference requires <100ms latency for smooth UX
- TFLite conversion includes FP16 quantization for 2x size reduction
- Training on CPU/GPU is possible but will take ~2-3 hours

## ✅ Checklist

Before deploying to production:

- [ ] Train on full QDAT dataset (not just Al-Ma'idah 109)
- [ ] Achieve >93% test accuracy
- [ ] Verify TFLite latency <100ms on target device
- [ ] Test with diverse Qari voices
- [ ] Validate real-time WebSocket streaming
- [ ] Load test API endpoints (100+ concurrent requests)
- [ ] Document model version and training date
- [ ] Set up model monitoring in production
