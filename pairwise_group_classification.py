#!/usr/bin/env python
"""Code from the paper "A signature-based machine
learning model for bipolar disorder and borderline
personality disorder".

Classifies participants according to the clinical
group they were linked with at the beginning
of the study.
"""

from __future__ import print_function
import random
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import roc_auc_score, accuracy_score

from esig import tosig

import psychiatry
from logger import Logger


__author__ = "Imanol Perez Arribas"
__credits__ = ["Imanol Perez Arribas", "Guy M. Goodwin", "John R. Geddes",
                "Terry Lyons", "Kate E. A. Saunders"]
__version__ = "1.0.1"
__maintainer__ = "Imanol Perez Arribas"
__email__ = "imanol.perez@maths.ox.ac.uk"


def _findMin(p, A):
    """Given a point p and a list of points A, returns the point
    in A closest to p.

    Parameters
    ----------
    p : array
        Point on the plane.
    A : list
        List of points on the plane.

    Returns
    -------
    tuple
        Point in A closest to p in the Euclidean metric.

    """

    m=(-1, (0,0))
    for p0 in A:
            dist = np.linalg.norm(p0-np.array(p))
            if m[0]==-1 or m[0]>dist:
                    m = (dist, p0)
    
    return tuple(m[1])

def test(collection, reg, threshold, order=2):
    """Tests the model against an out-of-sample set.

    Parameters
    ----------
    collection : list
        The out-of-sample set.
    reg : RandomForestRegressor
        Trained random forest.
    threshold : array
        List of 3 points on the plane.
    order : int, optional
        Order of the signature.
        Default is 2.

    Returns
    -------
    float
        Accuracy of the predictions.

    """

    # x will contain the input of the model, while
    # y will contain the output.
    x=[]
    y=[]

    for X in collection:
            x.append(list(tosig.stream2sig(np.array(X.data), order)))

            y.append(threshold[X.diagnosis])

    predicted_raw = reg.predict(x)
    predicted = np.array([_findMin(prediction, threshold) for prediction in predicted_raw])
    
    # Convert predictions and true values to labels
    predicted_labels = [threshold.tolist().index(val.tolist()) for val in predicted]
    y_labels = [threshold.tolist().index(val.tolist()) for val in y]

    acc = accuracy_score(y_labels, predicted_labels)
    roc = roc_auc_score(y_labels, predicted_labels)

    return acc, roc


def fit(collection, threshold, order=2):
    """Fits the model using the training set.

    Parameters
    ----------
    collection : list
        Training set.
    threshold : array
        List of 3 points on the plane.
    order : int, optional
        Order of the signature.
        Default is 2.

    Returns
    -------
    RandomForestRegressor
        Trained model.

    """

    # x will contain the input of the model, while
    # y will contain the output.
    x=[]
    y=[]

    for participant in collection:
        # The input will be the signature of the stream of
        # the participant.
        x.append(tosig.stream2sig(np.array(participant.data), order))

        # The output, on the other hand, will be the point
        # on the plane corresponding to the clinical group
        # of the participant.
        y.append(threshold[participant.diagnosis])

    # We train the model using Random Forest.
    reg = RandomForestRegressor(n_estimators=100, oob_score=True)
    reg.fit(x, y)

    return reg

if __name__ == "__main__":
    # Each clinical group is associated with a point on the
    # plane. These points were found using cross-valiation.

    random.seed(83042)
    np.random.seed(83042)

    threshold=np.array([[1, 0],
                        [0, 1],
                        [-1/np.sqrt(2), -1/np.sqrt(2)]])



    diagnosis = ("healthy", "bipolar", "borderline")
    accuracy_results = pd.DataFrame(index=diagnosis, columns=diagnosis)
    auc_results = pd.DataFrame(index=diagnosis, columns=diagnosis)


    logger = Logger("pairwise_group_classification")

    for i, group1 in enumerate(diagnosis):
        for group2 in diagnosis[i + 1:]:
            
            groups = (group1, group2)
            
            # The training and out-of-sample sets are built
            logger.log("Loading {} and {}...".format(group1, group2))
            ts, os = psychiatry.buildData(20, "../data", training=0.7,
                                        groups=groups)
            logger.log("Done.\n")

            # We fit data
            logger.log("Training the model...")
            reg = fit(ts, order=2, threshold=threshold)
            logger.log("Done.\n")

            # We check the performance of the algorithm with out of sample data
            logger.log("Testing the model...")
            accuracy, auc = test(os, reg, order=2, threshold=threshold)
            logger.log("Done.")

            # We save the accuracy in the results table.
            accuracy_results.loc[group1][group2] = accuracy
            auc_results.loc[group1][group2] = auc


    logger.log("###########")
    logger.log("  Results  ")
    logger.log("###########")

    logger.log("Accuracy:")
    logger.log(accuracy_results.to_string())
    logger.log("AUC:")
    logger.log(auc_results.to_string())
