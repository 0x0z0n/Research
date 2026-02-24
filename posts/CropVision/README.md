# CropVision-AI-Powered-Plant-Disease-Detection
CropVision uses deep learning (CNNs) to automatically detect and classify plant diseases from images, achieving 93%+ accuracy. It reduces reliance on expert knowledge, helps monitor crop health, minimize losses, and supports sustainable agriculture.


## Objectives
- Automate detection and classification of tomato leaf diseases.
- Reduce manual effort in plant disease monitoring.
- Provide a reliable tool for farmers and agricultural researchers.
- Improve prediction accuracy using deep learning and pre-trained models.

---

## Literature Survey
- Early approaches relied on image processing and manual feature extraction.
- Machine learning techniques such as SVM, DLQP, and k-FLBPCM have been applied for classification.
- CNN-based approaches, especially **Faster-RCNN with ResNet-34**, enhance localization and classification accuracy.
- Challenges include varying leaf sizes, lighting, noise, and similarity between healthy and diseased areas.

---

## Proposed System
1. **Data Acquisition**: Images collected from PlantVillage dataset.
2. **Preprocessing**: Images resized and normalized for uniform input.
3. **Feature Extraction & Classification**: CNN (LeNet variant) with convolutional, pooling, dropout, and fully connected layers to extract features and classify diseases.

### Architecture
- Convolutional layers extract hierarchical features.
- Max pooling reduces spatial dimensions.
- Fully connected layers and softmax activation perform classification.
- Pre-trained weights enhance accuracy.

### Working
- Input images resized to 128×128.
- CNN extracts features via Conv2D, MaxPooling2D, and Dropout.
- Flattened feature maps feed into dense layers for classification.
- Output provides predicted disease class.

---

## Advantages
- Eliminates reliance on manual feature extraction.
- CNN automatically identifies disease areas.
- Pre-trained weights improve accuracy.
- Achieves ~94% accuracy.

## Disadvantages
- Fine-grained early disease detection remains challenging.
- Background similarities may reduce accuracy.
- High-quality images required.
- Real-time mobile implementation is computationally intensive.

---

## Conclusion & Future Scope
- **Conclusion**: CNN outperforms KNN in tomato leaf disease detection.
- **Future Scope**: Expand to multiple plant types, use larger datasets, integrate explainable AI (XAI) techniques, and develop real-time mobile applications.

---

## References
1. Jihen Amara, Bassem Bouaziz, Alsayed Algergawy, et al. *A Deep Learning-based Approach for Banana Leaf Diseases Classification*, BTW Workshops, 2017.  
2. Hui-Ling Chen et al. *Support Vector Machine Based Diagnostic System for Breast Cancer Using Swarm Intelligence*, Journal of Medical Systems, 36(4), 2012.  
3. S.D. Khirade and A.B. Patil. *Plant Disease Detection Using Image Processing*, 2015 International Conference on Computing Communication Control and Automation, 2015.

