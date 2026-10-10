---
title: "TAROT: Task-Oriented Authorship Obfuscation Using Policy Optimization Methods"
date: 2025-03-21T09:02:08+01:00
tags: ["Publication", "Authorship Attribution", "Anonymization"]
---

I'm proud to announce that our latest article **TAROT: Task-Oriented Authorship Obfuscation Using Policy Optimization Methods** has been accepted at PrivateNLP 2025 (Sixth Workshop on Privacy in Natural Language Processing, Colocated with NAACL 2025).

*TL;DR*: The paper introduces **TAROT**, an unsupervised method for **authorship obfuscation** that balances **privacy and utility** in text rewriting. While strong obfuscation techniques protect identity but harm text quality, weaker ones maintain utility but risk de-anonymization. TAROT uses **policy optimization** to fine-tune small language models, regenerating text to obscure authorship while preserving usefulness for downstream tasks. Experiments show it effectively reduces attacker accuracy while maintaining utility. The code and models are publicly available.

**Why it matters**

Anonymizing a text is not only about removing names. Writing style alone (vocabulary, syntax, punctuation habits) is often enough to tell who wrote it. The usual obfuscation methods sit at one of two extremes: rewrite so aggressively that the text becomes useless, or rewrite so lightly that an attacker still recognizes the author. TAROT takes a different angle: it rewrites the whole text with a small language model trained by policy optimization, rewarded both for fooling an authorship attacker and for keeping the text useful for its downstream task. Because the method is unsupervised and the models are small, it is practical to run on real data, and the code and models are public.

> :uk: **TAROT: Task-Oriented Authorship Obfuscation Using Policy Optimization Methods**. [Gabriel Loiseau](https://gabrielloiseau.github.io/), Damien Sileo, **Damien Riquet**, Maxime Meyer, Marc Tommasi. Sixth Workshop on Privacy in Natural Language Processing (PrivateNLP 2025).

Links:

- [{{< icon "graduation-cap" >}} Paper](https://doi.org/10.48550/arXiv.2407.21630)

