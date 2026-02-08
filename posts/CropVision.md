# CropVision - AI-Powered Plant Disease Detection

## Introduction

India is a country with a majority of the population relying heavily on the agricultural sector. Tomato is the most common vegetable used across India. The three most important antioxidants namely vitamin E, vitamin C and beta-carotene are present in tomatoes. They are also rich in potassium, a very important mineral for good health. Tomato crop cultivation area in India spans around 350,000 hectares approximately and the production quantities roughly sum up to 5,300,000 tons, making India the third largest tomato producer in the world. The sensitivity of crops coupled with climatic conditions have made diseases common in the tomato crop during all the stages of its growth. Disease-affected plants constitute 10–30% of the total crop loss. Identification of such diseases in the plant is very important in preventing heavy losses in yield as well as the quantity of the agricultural product. Monitoring the plant diseases manually is difficult due to its complex nature and is a time-consuming process.

There is a need to reduce the manual effort while making accurate predictions and ensuring that farmers’ lives are hassle-free. Visually observable patterns are difficult to decipher at a single glance, leading to inaccurate assumptions regarding disease. Farmers usually rely on common disease prevention mechanisms without expert advice, sometimes leading to over-dosage or under-dosage of pesticides, which can damage crops. This motivates the proposed methodology to accurately detect and classify diseases in the tomato crop.



## Motivation

India relies heavily on agriculture. Disease-affected tomato plants constitute 10–30% of crop loss. Identifying these diseases is important to prevent heavy losses and ensure farmers’ lives are easier. Reducing manual effort while improving accuracy motivates this work.



## Aim

The proposed methodology aims to accurately detect and classify diseases in tomato crops to prevent crop damage from incorrect pesticide usage.



## Objectives

The objective is to design a system that accurately detects and classifies diseases in tomato crops using modern computational techniques, reducing manual supervision.



## Scope

The proposed system aims to achieve 94–95% accuracy, showing the feasibility of neural networks even under unfavourable conditions. The model can serve as a decision tool for farmers to identify tomato crop diseases.



# Literature Survey

## Background History

Plant leaf disease detection is a major research area, employing image processing and deep learning for accurate classification. Manual monitoring is tedious; thus, automation is desired. Recent technologies, especially during pandemic scenarios, have helped reduce human intervention. Deep learning techniques like Faster-RCNN with ResNet-34 have been used for tomato plant disease localization and categorization.



## Related Work

- Le et al. introduced a classification method using morphological pre-processing and the k-FLBPCM approach with SVM training achieving 98.63% accuracy, though performance decreases for distorted images.
- Directional Local Quinary Patterns (DLQP) is another framework for feature extraction followed by SVM training.

**Journal References:**

| Sr. | Journal Name & Year | Author(s) | Title |
|-|--|--|-|
| 1  | Int. Conf. on IoT & Intelligence System Analysis [IEEE] 2018 | Sachin D Khirade | Identification of plant disease is key to preventing yield and product loss |
| 2  | Int. Conf. for Convergence in Technology (EEE) 2018 | M. Malathi, K. Aruli | Survey on plant leaf disease detection using image processing |
| 3  | Int. Research Journal of Eng. & Tech [IEEE] 2018 | Y. Sanjana, Ashwanath Sivasamy | Images captured by mobile phones presented to expert group for opinion |



## Limitations of Existing System

- Accuracy drops on test images differing from training set (from 99% to 31.4%).
- High-quality leaf images required.
- Public datasets necessary.
- Noisy data can affect classification.
- Segmentation requires training/testing.
- Leaf color variations due to environment.
- Variety of diseases complicates detection.



## Summary & Discussion

Tomato crops are commercially important. Early disease detection is crucial. A variation of LeNet CNN can detect tomato leaf diseases with 94–95% accuracy. Confusion matrix and ROC curves can help visualize classification results for different classes.



# Proposed Work

## Proposed Concept

The methodology has three steps: data acquisition, pre-processing, and classification. Images from the Plant Village dataset are resized and fed into a CNN (LeNet variant). Filters, pooling, dropout, flatten, and dense layers are used to extract and classify features. Training uses batch size 32 and image size 128×128.

### Proposed Concept:



1. The proposed methodology consists of three major steps: data acquisition, pre-processing and classification. The images used for the implementation of the proposed methodology were acquired from a publicly available dataset called Plant Village, as mentioned earlier. 

2. The images were re-sized to a standard size before feeding it into the classification model. The final step is the classification of the input images with the use of a slight variation of the deep learning convolutional neural network (CNN) standard model called the LeNet which consists of the convolutional, activation, pooling and fully connected layers.

3. The total image classes are divided into training and testing dataset.


4. We are creating Filter blocks to extract features using Conv2D layer, Max Pooling 2D, Dropout, Flatten, and then stacking them together and at the end-use Dense Layer for output.

5. To build the training model, training and validation batches are generated with the dataset image size 128x128 and batch size as 32 to speed up the training process with Max pooling layer & that 2D array from feature maps will be passed to flattened layer  as input in flattened layer that 2D array will convert it into single continuous linear vector as an input for the understanding of dense layer.

6. Here, we proposed a tomato leaf disease prediction system that used convolutional neural network architecture with fully connected layers in order to extract the features then classify the extracted features based classifier. 



## System Architecture / Design

- CNN converts unstructured image inputs to classification labels.
- Convolutional layers extract features; filter sizes fixed at 5×5, increasing in depth.
- Three blocks of convolution, activation, and max pooling layers followed by fully connected layers with softmax activation.
- Feature extraction is handled by convolutional/pooling layers, classification by fully connected layers, non-linearity by activation layers.

![CropVision](Pictures/PRJ_CropVision_Architecture.jpg)

Convolutional neural networks (CNN) can be used for the creation of a computational model that works on the unstructured image inputs and converts them to corresponding classification output labels. They belong to the category of multi-layer neural networks which can be trained to learn the required features for classification purposes.



Convolutional layer applies convolution operation for extraction of features. With the increase in depth, the complexity of the extracted features increases. The size of the filter is fixed to 5 × 5 whereas number of filters is increased progressively as we move from one block to another. The number of filters is 20 in the first convolutional block while it is increased to 50 in the second and 80 in the third. This increase in the number of filters is necessary to compensate for the reduction in the size of the feature maps caused by the use of pooling layers in each of the blocks.



Each block consists of a convolutional, activation and a max pooling layer. Three such blocks followed by fully connected layers and softmax activation are used in this architecture. Convolutional and pooling layers are used for feature extraction whereas the fully connected layers are used for classification. Activation layers are used for introducing non-linearity into the network.





## Working of Proposed System: Flowchart


![CropVision](Pictures/PRJ_CropViosion_WorkFlow.jpg)

# Advantages & Disadvantages

## Advantages

- Automates plant disease identification using CNN.
- CNN locates disease areas without manual intervention.
- Higher performance compared to shallow networks.
- Achieves 93–94% accuracy on test set.

## Disadvantages

- Early disease detection and fine-grained identification remain challenging.
- False detection due to similar background.
- Mobile real-time computing speed is limited.
- High-quality images required.
- Leaf color variation due to environment affects accuracy.



# Conclusion & Future Scope

## Conclusion

CNN outperforms KNN in detecting tomato leaf diseases based on accuracy, precision, recall, and F1-score metrics.

## Future Scope

- Extend study to entire Plant Village dataset.
- Use LIME and other XAI techniques for interpretability.
- Develop real-time mobile application for disease detection.
- Incorporate environmental conditions, soil type, and volatile organic compounds data for enhanced detection and trustworthiness.



# References

1. Jihen Amara, Bassem Bouaziz, Alsayed Algergawy, et al. “A Deep Learning-based Approach for Banana Leaf Diseases Classification.” BTW (Workshops), 2017, pp. 79–88.  
2. Hui-Ling Chen et al. “Support vector machine based diagnostic system for breast cancer using swarm intelligence.” Journal of Medical Systems 36.4 (2012), pp. 2505–2519.  
3. S. D. Khirade and A. B. Patil. “Plant Disease Detection Using Image Processing.” 2015 Int. Conf. on Computing Communication Control and Automation. Feb. 2015, pp. 768–771. DOI: 10...
