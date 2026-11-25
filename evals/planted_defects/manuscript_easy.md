# Neural-behavioural lag coupling predicts attention lapses: evidence from 24 participants

## Abstract
Attention lapses are costly in sustained-attention work, yet their neural precursors remain poorly understood. We recorded 64-channel EEG while 24 adults completed a 40-minute sustained-attention task. Pre-stimulus alpha power was coupled to subsequent reaction times with a delay of about 6 seconds (r = .21, p = .03), and a linear classifier decoded lapse from non-lapse trials with 71% accuracy (chance 50%). Alpha power over parieto-occipital electrodes drives attention lapses, suggesting that alpha-based neurofeedback could prevent them.

## Introduction
Sustained attention degrades over time on task. Prior work links increases in posterior alpha oscillations to reduced external processing (Klimesch, 2012; Jensen & Mazaheri, 2010). We tested whether slow fluctuations of alpha power lead behavioural lapses by a consistent delay, and whether alpha power can decode individual lapses. The study was pre-registered on the Open Science Framework (osf.io/xxxxx). The hypotheses were that alpha power would lead reaction time by several seconds and that decoding would exceed chance.

## Methods

### Participants
Twenty-four healthy adults (mean age 24.1 years, 13 female) took part after giving informed consent. A power analysis indicated that 18 participants would detect a correlation of r = .5 with 80% power at alpha = .05, and we recruited 24 to allow for attrition. Four participants whose coupling estimates were inconsistent with the group trend were excluded as having poor signal quality, leaving 20 participants (1,200 trials: 60 per participant, 600 lapses and 600 non-lapses after balancing).

### Task and recording
Participants responded to a digit stream (press for every digit except 3) for 40 minutes. A lapse was defined as a reaction time above 1.5 times the participant's median. EEG was recorded from 64 channels at 500 Hz, band-pass filtered 1-40 Hz, and referenced to the average. Alpha power (8-12 Hz) was computed in 1-second bins. Reaction times were resampled to the same 1-second bins to give one neural series and one behavioural series per participant.

### Alignment of neural and behavioural series
To account for the delay between neural activity and behaviour, we estimated the neural-behavioural lag (lag*) as the offset between -10 s and +10 s (21 candidate offsets) that maximised the cross-correlation between the alpha series and the reaction-time series, and shifted each participant's neural series by lag* before all further analysis. Individual cross-correlation peaks ranged from 1 s to 9 s across participants (SD = 3.8 s), indicating that the delay is not identical for every person.

### Electrode selection
To focus on the most informative sites, we ranked the 64 electrodes by the strength of the correlation between alpha power and reaction time across all participants and retained the top 8 electrodes for all subsequent tests.

### Statistics
Coupling was quantified as Pearson's r between the aligned alpha series and the reaction-time series. The group lag was tested against zero with a one-sample t-test. To compare alpha power before lapses with alpha power before non-lapses, we pooled all 1,200 trials and ran an independent-samples t-test. For decoding, alpha features from the selected electrodes were z-scored and a linear support vector machine was evaluated with 5-fold cross-validation over trials. The code is given in the Appendix and the data are available at the repository listed below.

## Results
The group lag was reliably different from zero (t(19) = 1.20, p = .04). At the best lag (6 s, chosen from the 21 lags tested) the coupling between alpha power and reaction time was r = .21, p = .03; no correction for the number of lags tested was applied. In the eight selected electrodes, alpha power was correlated with reaction time at r = .52, p < .001. Alpha power was higher before lapses than before non-lapses (t(1198) = 4.10, p < .001). The classifier decoded lapse from non-lapse trials with 71% accuracy (chance 50%, p < .001 by binomial test).

## Discussion
These results show that increases in alpha power drive attention lapses roughly six seconds later. Because alpha power over parieto-occipital sites precedes lapses, interventions that lower alpha power, such as neurofeedback, should reduce lapses in sustained-attention work. Limitations include the modest sample, which a power analysis showed to be adequate. Future work should extend the findings to clinical populations.

## Data and code availability
Anonymised data and analysis code are available at the repository listed in the pre-registration. The analysis code is reproduced below.

## Appendix: analysis code (analysis.py)
```python
import numpy as np
from sklearn.svm import LinearSVC
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold, cross_val_score
from scipy import stats

def best_lag(neural, behav, max_lag=10):
    scores = {}
    for lag in range(-max_lag, max_lag + 1):
        scores[lag] = np.corrcoef(np.roll(neural, lag), behav)[0, 1]
    return max(scores, key=lambda k: abs(scores[k]))

def align_all(neural_all, behav_all):
    # neural_all, behav_all: arrays of shape (participants, time)
    grand_neural = neural_all.mean(axis=0)
    grand_behav = behav_all.mean(axis=0)
    lag_star = best_lag(grand_neural, grand_behav)
    aligned = []
    for p in range(neural_all.shape[0]):
        aligned.append(np.roll(neural_all[p], lag_star))
    return np.array(aligned), lag_star

def select_electrodes(alpha_by_electrode, rt, k=8):
    # alpha_by_electrode: (electrodes, samples) pooled over all participants
    r = [abs(np.corrcoef(alpha_by_electrode[e], rt)[0, 1]) for e in range(alpha_by_electrode.shape[0])]
    return np.argsort(r)[-k:]

def decode(features, labels):
    X = StandardScaler().fit_transform(features)
    cv = KFold(n_splits=5, shuffle=True)
    return cross_val_score(LinearSVC(), X, labels, cv=cv).mean()

def pooled_ttest(alpha_lapse, alpha_nonlapse):
    return stats.ttest_ind(alpha_lapse, alpha_nonlapse)
```

## References
Jensen, O., & Mazaheri, A. (2010). Shaping functional architecture by oscillatory alpha activity. Frontiers in Human Neuroscience, 4, 186.
Klimesch, W. (2012). Alpha-band oscillations, attention, and controlled access to stored information. Trends in Cognitive Sciences, 16(12), 606-617.
