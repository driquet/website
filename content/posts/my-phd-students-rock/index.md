---
title: "My PhD Students Rock: Three New Publications"
date: 2026-06-30T08:00:00+02:00
tags: ["publication", "privacy-utility trade-off", "anonymization", "intent-detection", "phishing"]
---

It's been a remarkable few months, and I couldn't be prouder of my PhD students. Their hard work has paid off with **three new publications** spanning text anonymization, privacy evaluation, and intent detection in digital communications. Huge congratulations to **Gabriel Loiseau** and **Senaid Popovic**: this one is for you. 🎉

Below is a short summary of each paper, with links to read more.

## DIDECO: Detecting Intent in Digital Communications

Led by **Senaid Popovic**, DIDECO is the **first annotated dataset** built specifically to detect both *explicit* and *implicit* intents in digital communications. It tackles a real cybersecurity gap with a taxonomy, grounded in Speech Act Theory and persuasion psychology, that separates explicit communicative goals (*what* is requested) from implicit persuasion mechanisms (*how* compliance is engineered), covering 20 intent categories. The team annotated 220 LLM-generated spear-phishing emails with a multi-label protocol and six trained annotators, producing 2,162 intent annotations. The analysis shows that sophisticated attacks layer multiple intents, combining explicit goals with implicit persuasion, paving the way for intent-aware detection of social engineering.

> :uk: **DIDECO: An Annotated Dataset for Intent Detection in Digital Communications**. Senaid Popovic, **Damien Riquet**, Maxime Meyer, Fabien Lauer, Yannick Parmentier. The 15th biennial Language Resources and Evaluation Conference (LREC 2026). [\[link\]](https://hal.science/hal-05616045)

## Adaptive Text Anonymization

Anonymizing text is highly context-sensitive: the right privacy/utility balance shifts with the domain, the privacy objective, and the downstream task. Led by **Gabriel Loiseau**, this work introduces a framework for **task-specific prompt optimization** that automatically builds anonymization instructions for language models, adapting to different privacy goals, domains, and usage patterns. Across five datasets, it consistently achieves a better privacy/utility trade-off than existing baselines while staying computationally efficient on open-source models, and it even discovers novel anonymization strategies along the privacy/utility frontier.

> :uk: **Adaptive Text Anonymization: Learning Privacy-Utility Trade-offs via Prompt Optimization**. [Gabriel Loiseau](https://gabrielloiseau.github.io/), Damien Sileo, **Damien Riquet**, Maxime Meyer, Marc Tommasi. Findings of the Association for Computational Linguistics: ACL 2026. [\[link\]](https://aclanthology.org/2026.findings-acl.401/)

## Distilling Human-Aligned Privacy Sensitivity Assessment

Also led by **Gabriel Loiseau**, this paper distills the privacy-assessment capabilities of Mistral Large 3 (675B) into compact encoder models of roughly 150M parameters. Using a large-scale dataset of privacy-annotated texts spanning 10 diverse domains, the resulting classifiers keep strong agreement with human annotations while dramatically cutting compute, and double as an evaluation metric for de-identification systems.

> :uk: **Distilling Human-Aligned Privacy Sensitivity Assessment from Large Language Models**. [Gabriel Loiseau](https://gabrielloiseau.github.io/), Damien Sileo, **Damien Riquet**, Maxime Meyer, Marc Tommasi. Joint Workshop on Legal and Ethical Issues in Human Language Technologies (LEGAL2026) and Computational Approaches to Language Data Pseudonymization, Anonymization, De-identification, and Data Privacy (CALD-pseudo 2026). [\[link\]](https://arxiv.org/abs/2603.29497)
