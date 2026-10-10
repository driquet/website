---
title: "WikiPhish: A Diverse Wikipedia-Based Dataset for Phishing Website Detection"
date: 2024-04-09T11:21:45+02:00
tags: ["Publication", "Phishing", "Dataset"]
---

Edit 09/2024: Added links.

I'm proud to announce that our latest article **WikiPhish: A Diverse Wikipedia-Based Dataset for Phishing Website Detection** has been accepted at CODASPY 2024 (ACM Conference on Data and Application Security and Privacy).

*TL;DR*: Phishing poses a persistent threat, demanding advanced detection systems. Supervised machine learning is widely employed to automate detection, reliant on extensive annotated data. The introduction of WikiPhish dataset, comprising 110,606 webpages (from Wikipedia, OpenPhish and PhishTank), addresses this need for diverse and robust data, enhancing phishing detection model development.

**Why it matters**

Most phishing datasets pair phishing pages with a narrow slice of legitimate pages, often popular homepages. A model trained on that learns to separate "phishing" from "big brand homepage", which is not the problem it faces in production. WikiPhish uses Wikipedia as the source of its legitimate pages, which covers a far more diverse range of topics and site types, alongside phishing pages from OpenPhish and PhishTank. The result is a dataset of 110,606 webpages that is harder to game with shortcuts, and that we made available so others can benchmark their detectors on something closer to the real web.

> :uk: **WikiPhish: A Diverse Wikipedia-Based Dataset for Phishing Website Detection**. [Gabriel Loiseau](https://gabrielloiseau.github.io/), Valentin Lefils, Maxime Meyer, **Damien Riquet**. ACM Conference on Data and Application Security and Privacy (CODASPY 2024).

Links:

- [{{< icon "graduation-cap" >}} Paper](https://dl.acm.org/doi/10.1145/3626232.3653283)
- [{{< icon "code" >}} Corpus](https://www.hornetsecurity.com/en/wikiphish/)

