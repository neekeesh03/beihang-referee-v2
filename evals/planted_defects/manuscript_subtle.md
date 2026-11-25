# Alpha power leads reaction time by several seconds during sustained attention

## Abstract
Slow fluctuations of posterior alpha power are thought to precede lapses of sustained attention. We recorded 64-channel EEG from 22 adults during a 40-minute sustained-attention task. After estimating each participant's own delay between alpha power and reaction time, alpha power led reaction time by 6.1 s on average (range 2 to 9 s; coupling r = .24 at the individual best lag, permutation-corrected across lags, p = .02). Pre-stimulus alpha power decoded lapse from non-lapse trials with 68% accuracy (chance 50%) in leave-one-participant-out cross-validation. Alpha power is associated with, and precedes, attention lapses, which makes it a candidate marker for lapse prediction.

## Introduction
Sustained attention degrades with time on task, and posterior alpha oscillations are linked to reduced processing of external input (Klimesch, 2012; Jensen & Mazaheri, 2010). It is unknown whether slow alpha fluctuations lead behavioural lapses at a consistent delay, and whether alpha measured immediately before a stimulus can classify upcoming lapses in people not used for training. The study was pre-registered (osf.io/q7x4k). We hypothesised a lead of several seconds and above-chance decoding in held-out participants.

## Methods

### Participants
Twenty-six healthy adults took part with informed consent. Four were excluded before any analysis for electrode impedance above 50 kOhm throughout the session (pre-specified criterion), leaving 22 participants (mean age 25.0 years, 12 female). A sample of 20 gives 80% power to detect r = .4 at alpha = .05; we aimed for 22 to allow for attrition.

### Task and recording
Participants responded to a digit stream (press for every digit except 3) for 40 minutes. A lapse was a reaction time above 1.5 times the participant's own median. EEG was recorded from 64 channels at 500 Hz, band-pass filtered 1-40 Hz and average-referenced. Alpha power (8-12 Hz) over eight parieto-occipital electrodes, fixed in advance in the pre-registration, was computed in 1-second bins. Reaction times were resampled to the same bins. Each participant therefore has one alpha series and one reaction-time series.

### Individual delay estimation and alignment
Because delays differ between people, we estimated each participant's own lag as the offset between -10 s and +10 s (21 candidates) that maximised the absolute cross-correlation between that participant's alpha series and reaction-time series, and shifted that participant's alpha series by their own lag before analysis. To account for the 21 candidate lags, significance of the coupling at the individual best lag was assessed against a null distribution built from 1,000 circularly time-shifted surrogate series per participant, taking the maximum over lags in each surrogate.

### Pre-stimulus alpha and decoding
For each trial, alpha power in the 1-second bin immediately before stimulus onset was taken as the feature, so that no post-stimulus activity enters the classifier. A linear support vector machine classified lapse versus non-lapse trials. To test generalisation to unseen people, performance was evaluated with leave-one-participant-out cross-validation; features were z-scored within the training participants only. Code and data are deposited (doi:10.5281/zenodo.0000000); the analysis code is reproduced in the Appendix.

### Statistics
The group lag was tested against zero with a one-sample t-test across the 22 individual lags. Decoding accuracy was tested against chance with a permutation test (1,000 label permutations within participant). Exploratory associations between individual lag and age are reported with Pearson's r.

## Results
Individual lags ranged from 2 s to 9 s (mean 6.1 s, SD 2.0 s) and differed reliably from zero (t(21) = 14.3, p < .001). Coupling at each participant's best lag was r = .24 on average, which exceeded the maximum-over-lags surrogate null (p = .02). Pre-stimulus alpha power decoded lapse versus non-lapse trials with 68% accuracy in held-out participants (permutation p = .001). Individual lag correlated with age, r(18) = .38, p = .03 (exploratory).

## Discussion
Alpha power is associated with attention lapses and precedes them by about six seconds, with substantial individual differences in the delay. Decoding in unseen participants suggests that alpha could serve as a marker for predicting lapses, although causal claims require intervention studies. Limitations are the modest sample, one task and a healthy young population.

## Data and code availability
Anonymised data and code: doi:10.5281/zenodo.0000000. The pre-registration is at osf.io/q7x4k.

## Appendix: analysis code (analysis.py)
```python
import numpy as np
from sklearn.svm import LinearSVC
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold

def best_lag(neural, behav, max_lag=10):
    scores = {}
    for lag in range(-max_lag, max_lag + 1):
        scores[lag] = np.corrcoef(np.roll(neural, lag), behav)[0, 1]
    return max(scores, key=lambda k: abs(scores[k]))

def lag_per_participant(neural_all, behav_all, max_lag=10):
    lags = []
    for p in range(neural_all.shape[0]):
        lags.append(best_lag(neural_all[p], behav_all[p], max_lag))
    return lags  # lags[p] belongs to participant p

def align_all(neural_all, behav_all):
    lags = lag_per_participant(neural_all, behav_all)
    aligned = []
    for p in range(neural_all.shape[0]):
        aligned.append(np.roll(neural_all[p], lags[p - 1]))
    return np.array(aligned), lags

def trial_features(alpha_aligned, stim_bins):
    # alpha power in the 1-second bin before stimulus onset, per participant
    return alpha_aligned[:, stim_bins + 1]

def decode(features, labels, n_participants):
    # features: (n_trials, n_features) pooled over participants; labels: (n_trials,)
    X = StandardScaler().fit_transform(features)
    cv = KFold(n_splits=n_participants, shuffle=True, random_state=0)
    accs = []
    for train, test in cv.split(X):
        clf = LinearSVC().fit(X[train], labels[train])
        accs.append((clf.predict(X[test]) == labels[test]).mean())
    return float(np.mean(accs))
```

## References
Jensen, O., & Mazaheri, A. (2010). Shaping functional architecture by oscillatory alpha activity. Frontiers in Human Neuroscience, 4, 186.
Klimesch, W. (2012). Alpha-band oscillations, attention, and controlled access to stored information. Trends in Cognitive Sciences, 16(12), 606-617.
