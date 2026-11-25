S1 CRITICAL code: align_all applies lags[p - 1] (previous participant's lag; participant 0 gets the last) -> cross-participant lag misalignment. Text says each participant's own lag.
S2 code vs text: trial_features uses stim_bins + 1 (the bin AFTER onset) but text says pre-stimulus bin (stim_bins - 1) -> post-stimulus activity enters the classifier.
S3 code vs text: text says leave-one-participant-out; code uses KFold(n_splits=n_participants, shuffle=True) over pooled trials -> same participant in train and test.
S4 code vs text: StandardScaler().fit_transform on ALL features before CV; text says z-scored within training participants only.
S5 numeric: r(18)=.38, p=.03 (recomputed p ~ .10); also df 18 does not match 22 participants (should be 20).
Deliberately clean (not defects): impedance exclusion pre-specified; power analysis consistent; permutation-corrected lags; careful causal wording; pre-registration and DOI present.
