# -*- coding: utf-8 -*-
"""Untitled13.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Ilpm50aFfu0S2sV8Q71iDqGU3uxVXji9
"""

pip install pyspark

import os
import numpy as np
import pandas as pd
from pyspark.sql.types import *
from pyspark.ml import Pipeline
from pyspark.sql import functions as f
from pyspark.sql.functions import udf, StringType
from pyspark.sql import SparkSession, functions as F
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from pyspark.ml.classification import MultilayerPerceptronClassifier
from pyspark.ml.feature import OneHotEncoder, VectorAssembler,StringIndexer
#Building session now
spark =SparkSession.builder.appName('deep_learning_with_spark').getOrCreate()

from google.colab import files


uploaded = files.upload()

#Reading the file now
data = spark.read.csv('dl_data.csv', header=True,
inferSchema=True)
data.show()

data.dtypes

from pyspark.sql.functions import col

# Rename the 'Orders_Normalized' column to 'label'
data = data.withColumnRenamed("Orders_Normalized", "label")

# Verify the column name change
data.printSchema()

#3) Applying MPC
train, validation, test = data.randomSplit([0.7, 0.2, 0.1], 1234)
#4) Building the pipeline
categorical_columns = [item[0] for item in data.dtypes if item[1].startswith('string')]
numeric_columns = [item[0] for item in data.dtypes if item[1].startswith('double')]
indexers = [StringIndexer(inputCol=column, outputCol='{0}_index'.format(
column)) for column in categorical_columns]
#Now we will building string indexer to further create the feature set from our data
featuresCreator = VectorAssembler(inputCols=[indexer.getOutputCol() for indexer in indexers] +
numeric_columns, outputCol="features")
#Configure the classifier
layers = [len(featuresCreator.getInputCols()), 4, 2, 2]
classifier = MultilayerPerceptronClassifier(labelCol='label', featuresCol='features', maxIter=100,
layers=layers, blockSize=128, seed=1234)
#Now are pipeline is configured so we can further move to fitting and prediction
#5) Fit and get output from pipeline
pipeline = Pipeline(stages=indexers + [featuresCreator, classifier])
model = pipeline.fit(train)
# let's checkout the results
train_output_df = model.transform(train)
validation_output_df = model.transform(validation)
test_output_df = model.transform(test)

#6) Evaluate using different metrics
from pyspark.ml.evaluation import MulticlassClassificationEvaluator

train_predictionAndLabels = train_output_df.select("prediction", "label")
validation_predictionAndLabels = validation_output_df.select("prediction", "label")
test_predictionAndLabels = test_output_df.select("prediction", "label")
metrics = ['weightedPrecision', 'weightedRecall', 'accuracy']

for metric in metrics:
    evaluator = MulticlassClassificationEvaluator(metricName=metric)
    print('Train ' + metric + ' = ' + str(evaluator.evaluate(train_predictionAndLabels)))
    print('Validation ' + metric + ' = ' + str(evaluator.evaluate(validation_predictionAndLabels)))
    print('Test ' + metric + ' = ' + str(evaluator.evaluate(test_predictionAndLabels)))

#7) Plots and visualizations
import matplotlib.pyplot as plt
import numpy as np
import itertools

def plot_confusion_matrix(cm, classes, normalize=False, title='Confusion matrix', cmap=plt.cm.Blues):
    """
    This function prints and plots the confusion matrix.
    Normalization can be applied by setting `normalize=True`.
    """
    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        print("Normalized confusion matrix")
    else:
        print('Confusion matrix, without normalization')
    print(cm)

    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)
    plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=45)
    plt.yticks(tick_marks, classes)
    fmt = '.2f' if normalize else 'd'
    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, format(cm[i, j], fmt), horizontalalignment="center", color="white" if cm[i, j] > thresh else "black")

    plt.tight_layout()
    plt.ylabel('True label')
    plt.xlabel('Predicted label')

# Get Class labels
class_temp = test_predictionAndLabels.select("label").groupBy("label").count().sort('count', ascending=False).toPandas()
class_labels = class_temp['label'].tolist()

# Calculate confusion matrix
from sklearn.metrics import confusion_matrix

y_true = test_predictionAndLabels.select("label").toPandas()
y_pred = test_predictionAndLabels.select("prediction").toPandas()
cnf_matrix = confusion_matrix(y_true, y_pred, labels=class_labels)

# Plotting Results
plt.figure()
plot_confusion_matrix(cnf_matrix, classes=class_labels, title='Confusion matrix, without normalization')
plt.show()

"""
Q:What have you learned today?
A: How to check the data types, and rename the
column Applying MPC and Building the pipeline
Overall, I learned how to use a pipeline in Apache Spark and how to perform data preprocessing by indexing categorical columns
Furthermore, I learned how to create a feature vector, and train the classifier using the pipeline, and generates predictions on different datasets.
2. Put results of steps 6 and 7. Explain what you have got there.
A Step 6 :
Train weightedPrecision = 0.9694729151327164: This indicates that, on the training dataset,
the model achieved a weighted precision of approximately 0.969.
Weighted precision means that the precision of each class and their respective proportions in the dataset.

Validation weightedPrecision = 0.9691785841956515: This shows the weighted precision on the validation dataset,
 which is around 0.969. which means the model maintains a similar level of precision
  when applied to unseen data during the validation stage.

Test weightedPrecision = 0.9659545221451951: This represents the weighted precision on the test dataset,
which is approximately 0.966.
The model performs slightly lower in precision compared to the training and validation datasets.

Train weightedRecall = 0.9690713633094225: This indicates the weighted recall on the training dataset,
 which is approximately 0.969.
Weighted recall considers the recall of each class and their respective proportions in the dataset.

Validation weightedRecall = 0.9687627603103308: This represents the weighted recall on the validation dataset,
 around 0.969. It implies that the model maintains a similar level of recall when
  applied to unseen data during the validation stage.

Test weightedRecall = 0.9654515778019587: This shows the weighted recall on the test dataset,
 which is approximately 0.965.The model performs slightly lower in recall compared to the training and validation datasets
 , but it still demonstrates a reasonably high recall.

Train accuracy = 0.9690713633094225: This indicates the accuracy on the training dataset,
which is approximately 0.969. Accuracy represents the overall correctness of the model's predictions.

Validation accuracy = 0.9687627603103307: This represents the accuracy on the validation dataset, around 0.969.
It suggests that the model maintains a similar level of accuracy when applied to unseen data during the validation stage.

Test accuracy = 0.9654515778019587: This shows the accuracy on the test dataset, which is approximately 0.965.
The model performs slightly lower in accuracy compared to the training and validation datasets,
 but it still demonstrates a reasonably high accuracy.

Step 7

The resulting plot provides a visual representation of the performance of a classification model by showing the distribution
of predicted labels compared to the true labels.It helps in analyzing the model's accuracy and identifying any patterns or misclassifications.
the code also calculates the confusion matrix using the confusion_matrix function from scikit-learn.
The true labels (y_true) and predicted labels (y_pred) are extracted from the DataFrame and
converted to pandas DataFrames. The confusion matrix is calculated based on the class labels.







"""