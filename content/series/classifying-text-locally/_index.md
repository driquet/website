---
title: "Classifying Text Locally"
description: "A series on classifying text without calling an LLM API: when you need one, how small a model can be, and how to train it without labels."
---

Calling an LLM API is the default answer to "classify this text". This series asks when that default is wrong. Each post runs the same kind of benchmark on public datasets and answers one practical question:

1. Do you need an LLM at all, or does a small local model do the job?
2. How small can that model get before accuracy breaks?
3. With no labels, can an LLM teacher label the data for a small student?
4. Do a few human labels on top of the teacher's labels help?

Read them in order, or jump to the question you have.
