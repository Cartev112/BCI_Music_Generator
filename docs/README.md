# BCI Music Generation System - Planning Document

## 1. Project Goal

To develop a Brain-Computer Interface (BCI) system that:
1.  Acquires EEG signals using a Ganglion board (4 channels).
2.  Processes these signals in near real-time.
3.  Classifies user mental states, specifically focusing on detecting periods of active mental imagery versus baseline/rest states.
4.  Uses the classified states to modulate simple parameters of a generative music algorithm (to be implemented in a later phase).

## 2. Hardware

*   **EEG Device:** OpenBCI Ganglion Board
*   **Electrodes:** 4 channels.
*   **Proposed Placement (Refined Recommendation):**
    *   **Primary:** O1, O2 (Occipital Lobe): Critical for capturing visual imagery correlates (Alpha band modulation).
    *   **Secondary Option 1 (Recommended):** P3, P4 (Parietal Lobe): Involved in spatial/attentional networks, generally less EOG artifact contamination than frontal sites.
    *   **Secondary Option 2:** Fp1, Fp2 (Frontal Lobe): May capture 'effort' but highly susceptible to eye artifacts. Requires careful artifact management.
    *   **Reference/Ground:** Mastoids (A1/A2) or earlobes.

## 3. Software Stack (Potential)

*   **Language:** Python
*   **Core Libraries:**
    *   `BrainFlow`: For interfacing with the Ganglion board and acquiring data.
    *   `NumPy`: For numerical operations.
    *   `SciPy`: For scientific computing, including signal processing functions (filtering).
    *   `MNE-Python`: Comprehensive EEG analysis toolkit (filtering, artifact handling, epoching, feature extraction, visualization).
    *   `Scikit-learn`: For machine learning (SVM, cross-validation, performance metrics).
*   **Real-time:**
    *   Python's built-in `threading` or `multiprocessing`.
    *   Possibly LabStreamingLayer (LSL) if using separate acquisition/processing components.
*   **Music Generation (Later):** `python-osc` (for sending control signals), a DAW (like Ableton Live, Reaper) or a dedicated music environment (Max/MSP, Pure Data, SuperCollider), or a Python music library (`Mingus`, `Music21` - though potentially less suitable for real-time generative audio).

## 4. Data Acquisition Strategy

*   **Task Paradigm:** Cued Mental Imagery vs. Rest.
    *   **Imagery Task:** Ask the user to perform a specific, consistent mental imagery task (e.g., vividly visualizing a rotating cube, imagining a specific familiar face, recalling a detailed memory). Consistency is key.
    *   **Rest Task:** Ask the user to relax, keep eyes open or closed (be consistent), and avoid specific mental tasks (e.g., count backwards from 10 slowly).
    *   **Trial Structure:** Block design (e.g., 10s Rest, 10s Imagery, repeated N times) with clear visual or auditory cues.
*   **Data Recording:**
    *   Use BrainFlow or OpenBCI GUI (with LSL) to stream and record data.
    *   Save data in a standard format (e.g., BrainFlow's default, CSV, or convert to FIF using MNE).
    *   Crucial: Record event markers/timestamps precisely indicating the start/end of each task condition (Rest/Imagery).
*   **Initial Goal:** Collect a robust dataset from a single user for initial model development and feasibility testing. Aim for **at least 30-50 clean trials per class (Rest and Imagery)**. Assuming ~10s per trial, this equates to roughly 10-15 minutes of core task data, suggesting a ~20-30 minute recording session.

## 5. Signal Processing Pipeline (Offline First)

1.  **Loading Data:** Load recorded sessions.
2.  **Filtering:**
    *   **Band-pass:** ~1 Hz to 40 Hz (or higher, e.g., 50Hz) to remove DC drift and high-frequency noise.
    *   **Notch:** 50 Hz or 60 Hz (depending on local power line frequency) to remove electrical interference.
3.  **Referencing:** Re-reference data if necessary (e.g., to average reference or linked mastoids if recorded).
4.  **Artifact Handling (Challenging with 4 channels):**
    *   **Visual Inspection:** Identify and potentially reject segments with gross muscle artifacts (EMG) or signal loss.
    *   **Filtering:** Aggressive low-pass filtering might reduce EMG, but also valuable gamma activity.
    *   **EOG:** Frontal channels (Fp1, Fp2) will be heavily contaminated by eye blinks/movements. Independent Component Analysis (ICA) is standard but often requires more channels. Simpler methods like regression based on EOG channels (if available) or simply rejecting trials with large EOG artifacts might be necessary.
    *   *Initial Strategy:* Focus on clean data collection protocols, visual rejection, and robust filtering.
5.  **Epoching:** Segment the continuous data into epochs (time windows) corresponding to the task conditions (e.g., 2-8 seconds within each Imagery/Rest block, avoiding transition periods).
6.  **Feature Extraction:** Calculate features for each epoch that might differentiate the states.
    *   **Power Spectral Density (PSD):** Calculate power in different frequency bands (e.g., Delta (1-4Hz), Theta (4-8Hz), Alpha (8-13Hz), Beta (13-30Hz), Low Gamma (30-50Hz)) for each channel. Occipital alpha power (decrease during visual imagery) is a classic target.
    *   **Band Power Ratios:** e.g., Alpha/Beta ratio.
    *   **Time-domain features:** Mean, variance, Hjorth parameters (Activity, Mobility, Complexity).
    *   *Note:* Common Spatial Patterns (CSP) is effective for motor imagery but requires more channels and distinct spatial patterns, likely less suitable here.

## 6. Machine Learning (Offline First)

1.  **Feature Matrix:** Create a matrix where rows are epochs and columns are the extracted features.
2.  **Labels:** Assign a label (e.g., 0 for Rest, 1 for Imagery) to each epoch.
3.  **Model Selection:**
    *   **Primary Candidates:**
        *   **Linear Discriminant Analysis (LDA):** Fast, simple, often effective BCI baseline. Good starting point.
        *   **Support Vector Machine (SVM):** Test both Linear and RBF kernels. RBF can capture non-linearities. Good performance common in BCI.
    *   **Others (Later):** Logistic Regression, Simple Neural Networks (MLP).
4.  **Training & Validation:**
    *   **Split:** Divide data into training and testing sets (e.g., 80%/20%). Ensure chronological split or use cross-validation that respects trial structure (e.g., Leave-One-Session-Out or K-Fold on trials).
    *   **Cross-Validation:** Use K-Fold cross-validation on the training set to tune hyperparameters (e.g., SVM's C and gamma parameters).
    *   **Scaling:** Standardize features (e.g., zero mean, unit variance) before training.
5.  **Evaluation Metrics:**
    *   **Accuracy:** Overall correctness (use with caution if classes are imbalanced).
    *   **Precision, Recall, F1-Score:** Better for understanding performance per class.
    *   **ROC AUC:** Evaluates discriminability across different thresholds.
    *   **Confusion Matrix:** Visualize correct/incorrect classifications per class.

## 7. Real-Time System Outline

1.  **Data Acquisition:** Continuously acquire small chunks of data via BrainFlow.
2.  **Buffering:** Store incoming data in a rolling buffer.
3.  **Processing:** Apply the *same* signal processing steps (filtering, etc.) as offline, adapted for real-time chunks.
4.  **Feature Extraction:** Calculate features on the latest processed window.
5.  **Classification:** Feed extracted features into the *pre-trained* model to get a prediction (Imagery/Rest).
6.  **Decision Smoothing:** Apply a smoothing logic (e.g., require N consecutive predictions of the same class, or use a moving average of probabilities) to avoid overly rapid switching.
7.  **Output:** Trigger music parameter changes based on the smoothed classification output (e.g., send OSC messages).

## 8. Challenges & Mitigation Strategies

*   **Low SNR:** Maximize signal quality via proper skin prep, electrode contact, minimizing external noise.
*   **Artifacts:** Strict instructions to user (minimize blinking/movement during trials), visual inspection/rejection, potentially adaptive filtering (use with care).
*   **Low Spatial Resolution:** Focus on features known to be less spatially specific or prominent at chosen locations (e.g., Occipital Alpha, Frontal Theta/Beta). Feature engineering becomes critical.
*   **Imagery Consistency/Detection:** The biggest challenge. Start with *very distinct* states (intense imagery vs. deep relaxation). User training and feedback are essential. Ensure the chosen imagery task reliably modulates EEG (e.g., visual imagery affecting Occipital Alpha).
*   **Variability (Inter/Intra-subject):** Models trained on one user/session may not generalize well. Requires calibration/re-training. Adaptive algorithms could be explored later.
*   **Real-time Constraints:** Optimize processing pipeline. Feature selection to use only the most informative *and* computationally cheap features. Test processing time per window.

## 9. Brainstorming: Enhancing Accuracy, Feasibility, Functionality

*   **Accuracy:**
    *   **Better Features:** Explore phase-based features, connectivity measures (coherence, phase-locking value between channels - might be noisy), non-linear features.
    *   **Feature Selection:** Use techniques (e.g., Recursive Feature Elimination, Mutual Information) to select the most discriminative subset of features, especially if initial performance is low.
    *   **Advanced Artifact Rejection:** If possible, explore algorithms robust to few channels, or focus heavily on data cleaning.
    *   **Ensemble Methods:** Combine predictions from multiple models (e.g., SVM + LDA).
    *   **Refined Task Design:** Experiment with different types of mental imagery known to have clearer EEG correlates.
*   **Feasibility:**
    *   **Simplify Initial Goal:** Classify 'Cognitive Load/Effort' vs. 'Rest' instead of specific imagery first. This might be more robust.
    *   **User Training:** Provide feedback to the user during training sessions to help them learn to produce more distinct brain states.
    *   **Robust Baseline:** Ensure the 'Rest' state is well-defined and consistently achievable.
    *   **Offline First:** Thoroughly validate the pipeline offline before attempting real-time. Start with LDA and SVM.
*   **Functionality:**
    *   **Calibration Phase:** Include a short calibration session before each use to adapt the classifier.
    *   **Confidence Threshold:** Only trigger music changes when the classifier's confidence is high.
    *   **Continuous Control:** Instead of binary classification, map a feature (e.g., Alpha power) or classifier probability directly to a music parameter for smoother modulation.
    *   **Feedback:** Provide clear feedback to the user about their detected state (visual or simple auditory cue) to help them control the system.
    *   **Adaptive Learning:** (Advanced) Allow the system to slowly adapt over time based on ongoing performance or user feedback.

## 10. Development Phases

1.  **Phase 1: Setup & Data Collection:** Hardware setup, software install, implement data acquisition script with event markers, collect initial labeled dataset (Imagery vs. Rest).
2.  **Phase 2: Offline Analysis & Modeling:** Implement signal processing pipeline, feature extraction, train and evaluate initial classifiers (SVM, LDA). Assess feasibility based on offline accuracy.
3.  **Phase 3: Real-time Prototype (Classification Only):** Implement real-time data acquisition and processing loop, apply pre-trained model, output classifications (e.g., print to console).
4.  **Phase 4: Basic Music Integration:** Choose a simple music modulation strategy (e.g., OSC messages controlling volume/filter cutoff in a DAW/synth), link real-time classifier output to music control.
5.  **Phase 5: Refinement & Testing:** Improve pipeline, retrain models, enhance music mapping, conduct user testing and gather feedback.

---
*This document provides a starting point and will evolve as the project progresses.*
