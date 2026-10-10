---
title: "Tau-Eval: A Unified Evaluation Framework for Useful and Private Text Anonymization"
date: 2025-10-15T08:00:00+01:00
tags: ["Publication", "Privacy-Utility Trade-off", "Anonymization"]
---

We are incredibly proud to announce the publication of our latest work, **TAU-EVAL: A Unified Evaluation Framework for Useful and Private Text Anonymization**, which has been accepted to the **Demo Track** of the prestigious **EMNLP** conference!

I am personally very proud of **Gabriel Loiseau**, the lead author, for publishing this foundational work in the Demo Track of an A* conference like EMNLP. This acceptance recognizes the immediate practical value and contribution of the TAU-EVAL framework to the field.

Gabriel will be presenting the framework at EMNLP in November.

**TL;DR: Bridging the Privacy-Utility Gap in Text Anonymization**

Text anonymization inherently involves a complex trade-off between privacy protection and the preservation of information utility, which existing research struggles to quantify using only generic, surface-level metrics. To address this, we introduce **TAU-EVAL** (Text Anonymization Utilities Evaluation), an **open-source Python framework** designed to systematically evaluate both privacy preservation and **task-aware utility loss** in anonymization systems.

The modular framework supports comprehensive evaluation workflows across two privacy objectives (like PII redaction and authorship obfuscation) and eight downstream tasks, spanning domains like healthcare and social science. Our experiments confirm that achieving a clear privacy-utility trade-off is complex, demonstrating that while Large Language Models are effective anonymizers, their high privacy gains often come at a pronounced cost to text utility, especially in socially critical tasks.

**Why it matters**

Every anonymization paper reports privacy and utility, but each one measures them differently, usually with generic metrics that say little about whether the anonymized text still works for what you need it for. That makes methods impossible to compare. Tau-Eval gives the field a common yardstick: plug in an anonymization method, pick the privacy objective and the downstream tasks you care about, and get comparable numbers. Its first finding is a useful warning: LLM-based anonymizers protect privacy well, but that protection can cost a lot of utility on exactly the tasks where text quality matters most.

> :uk: **TAU-EVAL: A Unified Evaluation Framework for Useful and Private Text Anonymization**. [Gabriel Loiseau](https://gabrielloiseau.github.io/), Damien Sileo, **Damien Riquet**, Maxime Meyer, Marc Tommasi. Accepted to the Conference on Empirical Methods in Natural Language Processing (EMNLP) Demo Track.

Links:

- [{{< icon "graduation-cap" >}} Paper](https://arxiv.org/abs/2506.05979)

