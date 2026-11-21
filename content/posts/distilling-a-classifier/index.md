---
title: "No Labels? Borrow Them: Distilling a Classifier Locally"
date: 2026-11-21T10:00:00+01:00
tags: ["AI", "Classification", "Encoders", "Distillation", "Benchmark"]
showTableOfContents: true
series: ["Classifying Text Locally"]
series_order: 3
---

<!-- ALL RUNS DONE (night 5, 2026-11-20/21). Real: every teacher's numbers (labeling on 2026-11-19 via OpenRouter's Decisions API, OneJev1.6-4B on the laptop), OneJev1.6-4B's students (seeds 0 and 1), Decider 27B and Mammoth 27B students hard and soft (seeds 0-2), Ettin-150M on gold labels (seeds 0-2), TF-IDF on gold and on every teacher's labels (seed 0). Part 1: /do-you-need-an-llm/. Part 2: /how-small-can-a-classifier-be/.
  Setup: arXiv papers first submitted March to October 2026 (librarian-bots/arxiv-metadata-snapshot), 8 CS primary categories, train pool 1,000/class (gold set aside), validation 125/class (silver), test 250/class (gold).
  Teachers: Base Labs Joey 1 (2B), Elephant 1 (9B), Mammoth 1 (27B); Perplexity Decider Flash v1.2 (4B), Decider v1.2 (27B); OneJev1.6-4B (bf16, local). Dropped: Amber 32M/150M/400M (teachers 38.2/39.2/47.5, soft students 41.1/39.4/48.3), OneJev1.6-9B (8-bit, teacher 72.9, soft student 72.1, hard 71.5).
  Night 5 (2026-11-20/21): Decider hard seed 2, gold seeds 1-2, Mammoth soft seeds 1-2, Mammoth hard seeds 0-2, TF-IDF on Elephant and Decider Flash labels. -->

{{< lead >}}
Rent a teacher for a few cents, keep a 150M student. How much of the teacher survives, and what does it cost?
{{< /lead >}}

<style>#TableOfContents ul ul, #TableOfContentsMobile ul ul { display: none !important; }</style>

In [the previous post](/how-small-can-a-classifier-be/), the two ladders (decision models and fine-tuned encoders) left a gap in the middle. A decision model needs no labels, but it is slow: on CLINC, OneJev1.6-4B took two seconds per text. A fine-tuned Ettin answers CLINC's short queries in 1 to 9 ms, but needs hundreds of labels per class. You may not have them, and you may be weighing it up: spend hours annotating data, or just use a decision model?

Distillation promises both. Let a decision model (the **teacher**) label your texts once. Then fine-tune a small encoder (the **student**) on its answers, as if they were real labels. No labels from you, and the serving cost of a fine-tuned encoder. And since the teacher runs only once, it can be big and rented, a few cents away behind an API. The catch: the student learns from a teacher that makes mistakes. So how much of the teacher survives the trip, and what do its mistakes become?

Two words for the rest of the post. A **gold label** is the real answer, given by a person: here, it is only used to grade. A **silver label** is the teacher's answer: free, plentiful, and sometimes wrong. The student only ever sees silver.

<figure class="svg-figure">
<svg viewBox="0 0 600 500" role="img" aria-label="A large teacher model labels unlabeled papers once; its silver labels go through a funnel into a small student model, which serves every prediction and is graded on gold labels.">
  <defs>
    <marker id="df-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker>
    <linearGradient id="df-funnel" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7c4dcc" stop-opacity="0.28"/><stop offset="1" stop-color="#2a78d6" stop-opacity="0.35"/></linearGradient>
    <g id="df-paper"><path d="M0,0 h20 l8,8 v28 h-28 z" fill="currentColor" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.6" stroke-width="1.5"/><path d="M5,13 h17 M5,19 h17 M5,25 h12" stroke="currentColor" stroke-opacity="0.45" stroke-width="1.5"/></g>
    <g id="df-tag"><path d="M0,4 l4,-4 h16 v12 h-16 z" fill="#b9bec7" stroke="#8a909a" stroke-width="1"/><circle cx="5" cy="6" r="1.6" fill="#6b7079"/></g>
  </defs>
  <g fill="currentColor" font-family="inherit" text-anchor="middle">
    <!-- unlabeled papers -->
    <use href="#df-paper" x="190" y="8"/><use href="#df-paper" x="235" y="8"/><use href="#df-paper" x="280" y="8"/><use href="#df-paper" x="325" y="8"/><use href="#df-paper" x="370" y="8"/>
    <text x="300" y="66" font-size="15" opacity="0.8">Papers, no labels</text>
    <line x1="300" y1="74" x2="300" y2="100" stroke="currentColor" stroke-width="1.5" marker-end="url(#df-arrow)"/>
    <!-- teacher -->
    <rect x="70" y="104" width="460" height="74" rx="14" fill="#7c4dcc" fill-opacity="0.22" stroke="#9a6fe3" stroke-width="2"/>
    <text x="300" y="135" font-size="18" font-weight="700">Teacher: a decision model, 2B to 27B</text>
    <text x="300" y="160" font-size="14" opacity="0.8">labels each paper once · rented, or on the laptop</text>
    <line x1="300" y1="178" x2="300" y2="202" stroke="currentColor" stroke-width="1.5" marker-end="url(#df-arrow)"/>
    <!-- silver-tagged papers -->
    <use href="#df-paper" x="190" y="208"/><use href="#df-tag" x="206" y="230"/>
    <use href="#df-paper" x="235" y="208"/><use href="#df-tag" x="251" y="230"/>
    <use href="#df-paper" x="280" y="208"/><use href="#df-tag" x="296" y="230"/>
    <use href="#df-paper" x="325" y="208"/><use href="#df-tag" x="341" y="230"/>
    <use href="#df-paper" x="370" y="208"/><use href="#df-tag" x="386" y="230"/>
    <text x="485" y="232" font-size="14" opacity="0.8">silver labels</text>
    <text x="485" y="250" font-size="14" opacity="0.8">+ probabilities</text>
    <!-- funnel -->
    <path d="M70,262 H530 L380,372 V392 H220 V372 Z" fill="url(#df-funnel)" stroke="currentColor" stroke-opacity="0.35" stroke-width="1.5"/>
    <text x="300" y="296" font-size="16" font-weight="700">Distillation</text>
    <text x="300" y="320" font-size="14" opacity="0.85">fine-tune on the teacher's answers</text>
    <text x="300" y="343" font-size="14" opacity="0.85">27B → 150M parameters</text>
    <line x1="300" y1="392" x2="300" y2="410" stroke="currentColor" stroke-width="1.5" marker-end="url(#df-arrow)"/>
    <!-- student -->
    <rect x="205" y="414" width="190" height="66" rx="12" fill="#2a78d6" fill-opacity="0.25" stroke="#3987e5" stroke-width="2"/>
    <text x="300" y="442" font-size="16" font-weight="700">Student: Ettin-150M</text>
    <text x="300" y="465" font-size="13" opacity="0.85">32 ms · on the laptop's GPU</text>
    <!-- serving and grading -->
    <text x="105" y="442" font-size="14" opacity="0.8">serves every</text>
    <text x="105" y="460" font-size="14" opacity="0.8">prediction</text>
    <line x1="395" y1="447" x2="440" y2="447" stroke="currentColor" stroke-width="1.5" marker-end="url(#df-arrow)"/>
    <rect x="446" y="420" width="128" height="54" rx="10" fill="#d4a72c" fill-opacity="0.22" stroke="#d4a72c" stroke-width="2"/>
    <text x="510" y="443" font-size="14" font-weight="700">graded on</text>
    <text x="510" y="461" font-size="14" font-weight="700">gold labels</text>
  </g>
</svg>
</figure>
<p class="caption">The teacher is slow but runs once. The student is fast, and is the one you serve. Gold labels are only used to grade, at the very end.</p>

Four questions:

1. **How close does the student get?** To its teacher, and to the same encoder trained on real labels.
2. **Hard or soft labels?** Does the student learn more from the teacher's full probabilities than from its top answer?
3. **Does a better teacher make a better student?** From 2B to 27B, in two families of decision models. And can the student beat its teacher?
4. **What does it cost?** Renting a teacher once and training, against serving the teacher forever.

The students train on the same laptop (Apple M5, 24 GB of unified memory), with the same code: [driquet/local-classification](https://github.com/driquet/local-classification), in `experiments/distillation`. Same warning: a weekend project, one task, three seeds where the numbers are close and one elsewhere. It gives the gist, not a law.

<div class="card card-green">
<p class="card-kicker">TL;DR · in a hurry?</p>
<p>Without a single label, the student scores within a point of its teacher, mistakes included. So the best teacher makes the best student: here Decider 27B, which labeled 9,000 papers for 8 cents. Its student answers in 32 ms on the laptop's GPU, with no API, but stays 5 points below the same encoder trained on real labels.</p>
<p class="card-title"><a href="#so-should-you-distill">Jump to the answer →</a></p>
</div>

## A new task: which field is this paper from?

The first two posts used CLINC, VAST and DynaSent: classic datasets, the kind decision models are trained on ([tasksource](https://huggingface.co/datasets/tasksource/tasksource-jev-typed-decisions) alone gathers about 750). A teacher that has already seen the gold labels would make distillation look better than it is. So I wanted a task the teachers are unlikely to have trained on.

**arXiv papers from 2026.** Every paper on [arXiv](https://arxiv.org/) has a primary category, picked by its authors when they submit it. The task: read the title and abstract, and guess the category. I kept eight computer science categories, and only papers first submitted between March and October 2026, from the [arXiv metadata snapshot](https://huggingface.co/datasets/librarian-bots/arxiv-metadata-snapshot).

The teachers themselves came out later, so in theory they could have seen these papers. I consider the risk low. Their base model, Qwen3.5 for all but one, came out at the end of February, before the first of these papers. Their fine-tuning is about decisions in general, not this year's arXiv. The one teacher on a newer base, Decider 27B on Qwen3.8 (August 2026), could have seen the papers from March to July. Yet it scores level with Mammoth 27B on Qwen3.5: a teacher that had read the answers would stand out. Its mistakes don't look like recall either: it files papers by their method, where the authors file them by their field (more on that below).

| Category | Name given to the teachers | Example (title) |
|---|---|---|
| cs.CL | Computation and Language (NLP) | *"Tracing Pharmacological Knowledge In Large Language Models"* |
| cs.CV | Computer Vision | *"NanoGS: Training-Free Gaussian Splat Simplification"* |
| cs.LG | Machine Learning | *"Large Spikes in Stochastic Gradient Descent: A Large-Deviations View"* |
| cs.CR | Cryptography and Security | *"Unclonable Encryption in the Haar Random Oracle Model"* |
| cs.RO | Robotics | *"Multifingered force-aware control for humanoid robots"* |
| cs.SE | Software Engineering | *"Coverage-Guided Multi-Agent Harness Generation for Java Library Fuzzing"* |
| cs.HC | Human-Computer Interaction | *"Understanding the Effects of Interaction on Emotional Experiences in VR"* |
| cs.IR | Information Retrieval | *"Negative Sampling Techniques in Information Retrieval: A Survey"* |

Easy to explain, easy for a bag of words with labels, and harder for a model without them.

{{< alert "circle-info" >}}
**The gold labels are the authors' choice, not a ground truth.** A paper about training vision models can be cs.CV or cs.LG, depending on who wrote it, and half of these papers are also cross-listed in another category. So the task is noisy: part of any model's errors, and of the gap to the gold encoder, comes from the labels, not from the models.
{{< /alert >}}

### Gold labels, only for grading

1,000 papers per category form the **training pool** (8,000 papers). Their gold labels are set aside before the teacher sees anything. The **validation** set (125 per category) is labeled by the teacher too: no gold label touches training. The **test set** (250 per category, 2,000 papers) keeps its gold labels, and is only read at the very end.

<figure class="svg-figure">
<svg viewBox="0 0 600 370" role="img" aria-label="arXiv papers split into a training pool and a validation set, labeled by the teacher, and a test set with gold labels. The student learns from the teacher's silver labels; both are graded on the test set.">
  <defs>
    <marker id="sp-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker>
  </defs>
  <g fill="currentColor" font-family="inherit" text-anchor="middle">
    <!-- dataset -->
    <rect x="185" y="6" width="230" height="52" rx="12" fill="currentColor" fill-opacity="0.07" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.5"/>
    <text x="300" y="29" font-size="16" font-weight="700">arXiv, 2026</text>
    <text x="300" y="48" font-size="13" opacity="0.8">8 CS categories</text>
    <path d="M250,58 L110,94" stroke="currentColor" stroke-width="1.5" fill="none" marker-end="url(#sp-arrow)"/>
    <line x1="300" y1="58" x2="300" y2="94" stroke="currentColor" stroke-width="1.5" marker-end="url(#sp-arrow)"/>
    <path d="M350,58 L490,94" stroke="currentColor" stroke-width="1.5" fill="none" marker-end="url(#sp-arrow)"/>
    <!-- splits -->
    <rect x="20" y="98" width="180" height="72" rx="12" fill="currentColor" fill-opacity="0.07" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.5"/>
    <text x="110" y="122" font-size="15" font-weight="700">Training pool</text>
    <text x="110" y="141" font-size="13" opacity="0.8">8,000 papers</text>
    <text x="110" y="159" font-size="13" opacity="0.8">gold labels set aside</text>
    <rect x="215" y="98" width="170" height="72" rx="12" fill="currentColor" fill-opacity="0.07" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.5"/>
    <text x="300" y="122" font-size="15" font-weight="700">Validation</text>
    <text x="300" y="141" font-size="13" opacity="0.8">1,000 papers</text>
    <text x="300" y="159" font-size="13" opacity="0.8">gold labels set aside</text>
    <rect x="400" y="98" width="180" height="72" rx="12" fill="#d4a72c" fill-opacity="0.22" stroke="#d4a72c" stroke-width="2"/>
    <text x="490" y="122" font-size="15" font-weight="700">Test set</text>
    <text x="490" y="141" font-size="13" opacity="0.85">2,000 papers</text>
    <text x="490" y="159" font-size="13" opacity="0.85">gold labels, untouched</text>
    <line x1="110" y1="170" x2="110" y2="204" stroke="currentColor" stroke-width="1.5" marker-end="url(#sp-arrow)"/>
    <line x1="300" y1="170" x2="300" y2="204" stroke="currentColor" stroke-width="1.5" marker-end="url(#sp-arrow)"/>
    <!-- teacher -->
    <rect x="20" y="208" width="365" height="56" rx="12" fill="#7c4dcc" fill-opacity="0.22" stroke="#9a6fe3" stroke-width="2"/>
    <text x="202" y="232" font-size="15" font-weight="700">Teacher</text>
    <text x="202" y="251" font-size="13" opacity="0.85">labels both: silver labels + probabilities</text>
    <line x1="202" y1="264" x2="202" y2="298" stroke="currentColor" stroke-width="1.5" marker-end="url(#sp-arrow)"/>
    <!-- student -->
    <rect x="92" y="302" width="220" height="60" rx="12" fill="#2a78d6" fill-opacity="0.25" stroke="#3987e5" stroke-width="2"/>
    <text x="202" y="327" font-size="15" font-weight="700">Student: Ettin-150M</text>
    <text x="202" y="347" font-size="13" opacity="0.85">trained on silver labels</text>
    <!-- grading -->
    <path d="M385,236 H470 V174" stroke="#d4a72c" stroke-width="1.8" fill="none" stroke-dasharray="5 4" marker-end="url(#sp-arrow)"/>
    <path d="M312,332 H515 V174" stroke="#d4a72c" stroke-width="1.8" fill="none" stroke-dasharray="5 4" marker-end="url(#sp-arrow)"/>
    <text x="530" y="262" font-size="13" text-anchor="start" opacity="0.85">both</text>
    <text x="530" y="279" font-size="13" text-anchor="start" opacity="0.85">graded</text>
    <text x="530" y="296" font-size="13" text-anchor="start" opacity="0.85">at the end</text>
  </g>
</svg>
</figure>

The gold labels of the training pool have two uses only: training the ceiling (the same encoder on real labels), and measuring how often the teacher is wrong on the data the student learns from.

## The contestants

<div class="card-grid card-grid-2">
<div class="card card-purple">
<p class="card-kicker">Teachers · no labels</p>
<p class="card-title">Base Labs Joey · Elephant · Mammoth<br>Perplexity Decider Flash · Decider<br>OneJev1.6-4B</p>
<p>Decision models from 2B to 27B, among them OneJev1.6-4B from <a href="/do-you-need-an-llm/#the-contestants">part 1</a>. They label the training pool.</p>
</div>
<div class="card card-blue">
<p class="card-kicker">Student · the teacher's labels</p>
<p class="card-title">Ettin-150M</p>
<p>Fine-tuned on a teacher's answers, on the laptop. One student per teacher.</p>
</div>
<div class="card card-green">
<p class="card-kicker">Ceiling · gold labels</p>
<p class="card-title">Ettin-150M</p>
<p>The same encoder, fine-tuned on the real labels: what labeling by hand would buy.</p>
</div>
<div class="card card-grey">
<p class="card-kicker">Floor · both</p>
<p class="card-title">TF-IDF + logistic regression</p>
<p>On the gold labels, and on the teachers' labels: does the student need to be an encoder?</p>
</div>
</div>

### Two families, rented

**Why rent the teachers?** The teacher runs only once, so it doesn't have to live on the laptop. And renting is simpler (one API for every model), much faster than running them locally, and cheap: $0.86 for every label in this post. Besides, the 27B teachers are too big to serve on the laptop.

[OpenRouter](https://openrouter.ai/docs/guides/features/decisions) serves decision models behind one API: you send a text, a question and the options, and get back a probability per option. Nothing is generated. Each provider runs its model with its own prompt template, in its own best setup, which is exactly what I want from a teacher. I picked the two families that come in several sizes and rank high on the [Decision Index](https://huggingface.co/spaces/multimodalart/jev-decision-index), the public leaderboard of decision models:

| Teacher | Maker | Size | Base | Decision Index | Price, per M input tokens |
|---|---|---|---|---|---|
| Joey 1 | Base Labs (Baseten) | 2B | Qwen3.5-2B | 35.9 | $0.010 |
| Elephant 1 | Base Labs (Baseten) | 9B | Qwen3.5-9B | 60.3 | $0.035 |
| Mammoth 1 | Base Labs (Baseten) | 27B | Qwen3.5-27B | 68.4 | $0.100 |
| Decider Flash v1.2 | Perplexity | 4B | Qwen3.5-4B | 54.3 | $0.010 |
| Decider v1.2 | Perplexity | 27B | Qwen3.8-27B | 68.0 | $0.020 |
| OneJev1.6-4B | OmniJev | 4B | Qwen3.5-4B | 48.9 | on the laptop |

<p class="caption">Decision Index 0.4.1 (November 2026), full score. A paper with its question and options is about 430 tokens with Perplexity's prompt template, 445 with Base Labs'.</p>

OneJev1.6-4B stays as the local option: the teacher you can run when your texts can't leave the machine.

**The teachers** all get the same prompt: the question *"Which arXiv category is this paper's primary one?"*, the title and abstract, and the eight names above as options A to H (the Decision Index layout). Each returns a probability per option. Their top answer is the **hard label**; the full distribution is the **soft label**. For example, here is what OneJev1.6-4B says about *"Compact convolutional neural networks for AI-based drone detection system"*, filed by its authors under cs.LG:

{{< chart >}}
type: 'bar',
data: {
  labels: ['cs.CV', 'cs.LG', 'cs.RO', 'cs.CR', 'cs.SE', 'cs.CL', 'cs.HC', 'cs.IR'],
  datasets: [{
    label: 'Probability',
    data: [0.45, 0.41, 0.09, 0.03, 0.01, 0.00, 0.00, 0.00],
    backgroundColor: [
      document.documentElement.classList.contains('dark') ? '#a77fe0' : '#7c4dcc',
      '#d4a72c', '#898781', '#898781', '#898781', '#898781', '#898781', '#898781'
    ],
    borderWidth: 0, borderRadius: 3
  }]
},
options: {
  indexAxis: 'y',
  aspectRatio: 2.2,
  plugins: {
    legend: { display: false },
    tooltip: { callbacks: { label: (c) => 'Probability: ' + c.parsed.x } }
  },
  scales: {
    x: {
      min: 0, max: 0.5,
      title: { display: true, text: "teacher's probability", color: '#898781' },
      ticks: { color: '#898781', stepSize: 0.1 },
      grid: { color: document.documentElement.classList.contains('dark') ? '#2c2c2a' : '#e1e0d9' }
    },
    y: { ticks: { color: '#898781' }, grid: { display: false } }
  }
}
{{< /chart >}}

<p class="caption">One paper, as the teacher sees it. The hard label is its top answer, <span style="color:#9a6fe3;font-weight:700">cs.CV</span>: wrong. The soft label keeps the whole distribution, and the gold answer, <span style="color:#d4a72c;font-weight:700">cs.LG</span>, is a close second. On this paper, the student trained on these soft labels answers cs.LG.</p>

**The student** is the Ettin-150M of part 2, with its hyperparameters (learning rate 5e-5, 4 epochs, texts cut at 512 tokens). Only the targets change. No checkpoint selection: the student is the one at the end of training. The validation set only tracks the loss during training.

## How I measured

- **Quality:** macro-F1 on the 2,000 gold test papers, so every category counts the same, with a 95% bootstrap interval (about ±2 points). Where results are close, I ran two or three seeds and report the mean; elsewhere, one seed: it's a weekend project. Seeds move a student by up to 1.3 points, so a gap under a point between two single-seed students means nothing. Two models graded on the same test papers can be compared more finely than ±2, but I only lean on gaps that hold across seeds.
- **Agreement:** how often the student gives the same answer as its teacher, right or wrong.
- **Hard labels:** cross-entropy on the teacher's top answer.
- **Soft labels:** KL divergence to the teacher's probabilities, softened with a temperature of 2 ([Hinton et al., 2015](https://arxiv.org/abs/1503.02531)).
- **Cost:** labeling time and price for the pool and validation (9,000 papers), training time, median latency per paper at batch size 1, peak RAM while predicting.

## How close does the student get?

Macro-F1 on the gold test set, for each teacher and for its student (soft labels). The dotted lines: the same encoder trained on the 8,000 gold labels, and TF-IDF trained on them.

{{< chart >}}
type: 'bar',
data: {
  labels: ['Decider Flash 4B', 'OneJev1.6-4B', 'Elephant 9B', 'Mammoth 27B', 'Decider 27B'],
  datasets: [
    {
      label: 'Teacher, no labels',
      data: [72.4, 75.1, 76.5, 79.3, 79.8],
      backgroundColor: '#898781',
      borderWidth: 0, borderRadius: 3
    },
    {
      label: 'Student: Ettin-150M on its labels',
      data: [71.8, 74.6, 77.3, 78.9, 79.4],
      backgroundColor: document.documentElement.classList.contains('dark') ? '#3987e5' : '#2a78d6',
      borderWidth: 0, borderRadius: 3
    }
  ]
},
plugins: [{
  id: 'refLines',
  afterDatasetsDraw: (chart) => {
    const { ctx, chartArea: a, scales: { y } } = chart;
    [['Ettin-150M on gold labels: 84.7', 84.7, '#2e9e6b', 'bottom', -3], ['TF-IDF on gold labels: 83.9', 83.9, '#b8a03a', 'top', 3]].forEach(([text, v, color, baseline, dy]) => {
      const py = y.getPixelForValue(v);
      ctx.save();
      ctx.strokeStyle = color; ctx.lineWidth = 1.5; ctx.setLineDash([2, 4]);
      ctx.beginPath(); ctx.moveTo(a.left, py); ctx.lineTo(a.right, py); ctx.stroke();
      ctx.fillStyle = color; ctx.font = '12px sans-serif'; ctx.textAlign = 'left'; ctx.textBaseline = baseline;
      ctx.fillText(text, a.left + 4, py + dy);
      ctx.restore();
    });
  }
}],
options: {
  aspectRatio: 1.3,
  plugins: {
    legend: { position: 'bottom', labels: { color: '#898781' } },
    tooltip: { callbacks: { label: (c) => c.dataset.label + ': ' + c.parsed.y } }
  },
  scales: {
    x: { ticks: { color: '#898781', maxRotation: 0, autoSkip: false }, grid: { display: false } },
    y: {
      min: 60, max: 90,
      title: { display: true, text: 'macro-F1 on the gold test set', color: '#898781' },
      ticks: { color: '#898781', stepSize: 5 },
      grid: { color: document.documentElement.classList.contains('dark') ? '#2c2c2a' : '#e1e0d9' }
    }
  }
}
{{< /chart >}}

<p class="caption">Means over seeds where I ran several. Joey 1 (48.7) is left out: too weak to be worth a student, see below.</p>

**Every student lands on its teacher.** 79.4 against 79.8 for Decider 27B, 78.9 against 79.3 for Mammoth 27B, 77.3 against 76.5 for Elephant 9B: five teachers, and no student more than 0.8 points away, either way. Within the noise. The student never sees a gold label, and it ends up as right as the model that taught it, within the noise. Never clearly better, never clearly worse.

**The gold labels are 5 points away.** The best students (79.4 and 78.9) stay below Ettin trained on real labels (84.7). And TF-IDF trained on those same real labels gets 83.9: on arXiv, the words give the answer away, as on CLINC in [part 1](/do-you-need-an-llm/#does-the-number-of-classes-matter-clinc150). A bag of words is enough, if its labels are right. The bottleneck is the teacher, not the student.

**With the teacher's labels, the encoder does earn its keep.** On every teacher's labels, TF-IDF trails the Ettin student trained on the same labels: by 3.0 points on Decider's (76.4), 3.2 on Mammoth's (75.7), 3.3 on OneJev's (71.3), 4.6 on Elephant's (72.7) and on Decider Flash's (67.2). On gold labels the two are level; on silver ones, the encoder copes better with the noise.

**Where it goes wrong: cs.IR, cs.CR, cs.CL and cs.LG.** Per category, for the best teacher:

| Category | Decider 27B | Its student | Ettin-150M, gold |
|---|---|---|---|
| cs.CL | <span class="f1 f1-d">67</span> | <span class="f1 f1-d">69</span> | <span class="f1 f1-ref">76</span> |
| cs.CV | <span class="f1 f1-a">85</span> | <span class="f1 f1-a">85</span> | <span class="f1 f1-ref">86</span> |
| cs.LG | <span class="f1 f1-c">69</span> | <span class="f1 f1-d">67</span> | <span class="f1 f1-ref">75</span> |
| cs.CR | <span class="f1 f1-d">79</span> | <span class="f1 f1-d">80</span> | <span class="f1 f1-ref">87</span> |
| cs.RO | <span class="f1 f1-a">92</span> | <span class="f1 f1-a">91</span> | <span class="f1 f1-ref">91</span> |
| cs.SE | <span class="f1 f1-c">83</span> | <span class="f1 f1-c">83</span> | <span class="f1 f1-ref">87</span> |
| cs.HC | <span class="f1 f1-b">85</span> | <span class="f1 f1-c">84</span> | <span class="f1 f1-ref">88</span> |
| cs.IR | <span class="f1 f1-d">77</span> | <span class="f1 f1-d">77</span> | <span class="f1 f1-ref">88</span> |
| **Macro-F1** | <span class="f1 f1-c">**79.8**</span> | <span class="f1 f1-c">**79.4**</span> | <span class="f1 f1-ref">**84.7**</span> |

<p class="caption">F1 per category on the gold test set. Teacher and student are colored by their gap to the encoder trained on gold labels, in <span class="f1 f1-ref">grey</span>: <span class="f1 f1-a">within 1 point</span> <span class="f1 f1-b">1 to 3 behind</span> <span class="f1 f1-c">3 to 6</span> <span class="f1 f1-d">over 6</span>.</p>

The teacher files papers by their method, the authors by their field. Of the 250 retrieval papers, Decider 27B puts 58 under NLP and 24 under Machine Learning; of the 250 security papers, 35 under Machine Learning and 23 under NLP. A recommender built on an LLM is about an LLM: reasonable, but not what the authors chose. cs.CL and cs.LG pay the other side: the misfiled papers land there, which lowers their precision. The bigger teachers make this mistake less often: OneJev1.6-4B put 54 security papers under Machine Learning and 41 under NLP, and Mammoth 27B only 18 and 9 (F1 88 on cs.CR, level with the gold encoder). Where the name of the category leaves little doubt (Robotics, Computer Vision, HCI), the teacher is within about 3 points of the gold encoder. The student keeps the same profile, category by category.

### Does the student copy its teacher's mistakes?

On the test set, Decider 27B is wrong on 418 papers. What does its student (seed 0) answer on those?

<div class="card-grid">
<div class="card card-orange">
<p class="card-kicker">Same mistake</p>
<p class="card-big">67%</p>
<p>The student copies the teacher's wrong answer.</p>
</div>
<div class="card card-green">
<p class="card-kicker">Fixed</p>
<p class="card-big">27%</p>
<p>The student gives the gold label.</p>
</div>
<div class="card card-grey">
<p class="card-kicker">Another mistake</p>
<p class="card-big">6%</p>
<p>Wrong too, but differently.</p>
</div>
</div>

Most mistakes carry over, and they are the systematic ones: retrieval and security papers filed by their method. The student fixes 112 of the teacher's mistakes, and makes 111 new ones on papers the teacher got right: the two cancel out. The better the teacher, the more of its mistakes the student fixes (27% for Decider 27B, 18% for Decider Flash), but the new mistakes keep pace. Overall, the student agrees with its teacher on 87.5% of the test papers (88 to 90% for the other pairs). It learns the teacher's idea of the categories, bias included.

<div class="card card-grey">
<p class="card-kicker">Takeaway</p>
<p>Without a single label, the student matches its teacher, mistakes included: the teacher sets the ceiling.</p>
</div>

## Hard or soft labels?

The same students, trained on the teacher's top answer (hard) or on its probabilities (soft), for the local teacher and the two 27B rented ones:

{{< chart >}}
type: 'bar',
data: {
  labels: ['OneJev1.6-4B', 'Mammoth 27B', 'Decider 27B'],
  datasets: [
    {
      label: 'Hard labels (top answer)',
      data: [73.0, 77.9, 79.5],
      backgroundColor: document.documentElement.classList.contains('dark') ? '#2c5a8a' : '#9cc3ee',
      borderWidth: 0, borderRadius: 3
    },
    {
      label: 'Soft labels (probabilities)',
      data: [74.6, 78.9, 79.4],
      backgroundColor: document.documentElement.classList.contains('dark') ? '#3987e5' : '#2a78d6',
      borderWidth: 0, borderRadius: 3
    }
  ]
},
plugins: [{
  id: 'deltas',
  afterDatasetsDraw: (chart) => {
    const { ctx } = chart, hard = chart.getDatasetMeta(0).data, soft = chart.getDatasetMeta(1).data;
    [['soft +1.6', '#1baf7a'], ['soft +1.0', '#1baf7a'], ['level', '#898781']].forEach(([text, color], i) => {
      ctx.save();
      ctx.fillStyle = color; ctx.font = 'bold 13px sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'bottom';
      ctx.fillText(text, (hard[i].x + soft[i].x) / 2, Math.min(hard[i].y, soft[i].y) - 8);
      ctx.restore();
    });
  }
}],
options: {
  aspectRatio: 1.3,
  plugins: {
    legend: { position: 'bottom', labels: { color: '#898781' } },
    tooltip: { callbacks: { label: (c) => c.dataset.label + ': ' + c.parsed.y } }
  },
  scales: {
    x: { ticks: { color: '#898781', maxRotation: 0, autoSkip: false }, grid: { display: false } },
    y: {
      min: 60, max: 90,
      title: { display: true, text: 'student macro-F1 on the gold test set', color: '#898781' },
      ticks: { color: '#898781', stepSize: 5 },
      grid: { color: document.documentElement.classList.contains('dark') ? '#2c2c2a' : '#e1e0d9' }
    }
  }
}
{{< /chart >}}

<p class="caption">Means over seeds where I ran several.</p>

**Soft labels help two teachers out of three.** With OneJev1.6-4B, soft beats hard by 1.6 points (74.6 against 73.0), on both seeds. With Mammoth 27B, by 1.0 (78.9 against 77.9), and every soft seed beats every hard one (78.3 to 79.6 against 77.5 to 78.2). With Decider 27B, the two are level: 79.4 soft, 79.5 hard, and the seeds overlap (soft: 78.9 to 79.9; hard: 79.1 to 80.3).

**And it's not about how confident the teacher is.** I expected a hesitant teacher to put more in its probabilities. OneJev1.6-4B's top answer gets 0.66 on average, Decider 27B's 0.73, Mammoth 27B's 0.80: the most confident teacher is the one where soft labels help, and the one in the middle is where they don't. Three teachers is too few to tell what makes the difference.

Soft labels cost nothing more: the teacher returns the probabilities anyway, and training takes the same time. If your teacher gives probabilities, use them.

<div class="card card-grey">
<p class="card-kicker">Takeaway</p>
<p>Keep the teacher's probabilities: they cost nothing and never hurt.</p>
</div>

## Does a better teacher make a better student?

Each dot is one teacher and its student. Left to right: how good the teacher is. Bottom to top: how good its student is. On the dashed line, the student scores exactly like its teacher.

{{< chart >}}
type: 'scatter',
data: {
  datasets: [
    {
      label: 'Base Labs teachers',
      data: [{x: 76.5, y: 77.3, name: 'Elephant 9B'}, {x: 79.3, y: 78.9, name: 'Mammoth 27B'}],
      backgroundColor: document.documentElement.classList.contains('dark') ? '#f0924a' : '#d9772b',
      pointRadius: 7, pointHoverRadius: 9, side: 'left'
    },
    {
      label: 'Perplexity teachers',
      data: [{x: 72.4, y: 71.8, name: 'Decider Flash 4B'}, {x: 79.8, y: 79.4, name: 'Decider 27B'}],
      backgroundColor: document.documentElement.classList.contains('dark') ? '#3cc2b2' : '#2a9d8f',
      pointRadius: 7, pointHoverRadius: 9, side: 'right'
    },
    {
      label: 'OneJev1.6-4B, on the laptop',
      data: [{x: 75.1, y: 74.6, name: 'OneJev1.6-4B'}],
      backgroundColor: document.documentElement.classList.contains('dark') ? '#a77fe0' : '#7c4dcc',
      pointRadius: 7, pointHoverRadius: 9, side: 'right'
    },
    {
      label: 'Student = teacher',
      data: [{x: 70, y: 70}, {x: 82, y: 82}],
      showLine: true,
      borderColor: '#898781', borderDash: [4, 4], borderWidth: 1.5,
      pointRadius: 0, pointHoverRadius: 0
    }
  ]
},
plugins: [{
  id: 'pointLabels',
  afterDatasetsDraw: (chart) => {
    const { ctx, chartArea: a, scales: { x, y } } = chart;
    chart.data.datasets.slice(0, 3).forEach((ds) => {
      ds.data.forEach((p) => {
        const px = x.getPixelForValue(p.x), py = y.getPixelForValue(p.y), left = ds.side === 'left';
        ctx.save();
        ctx.fillStyle = ds.backgroundColor; ctx.font = 'bold 12px sans-serif'; ctx.textBaseline = 'middle';
        ctx.textAlign = left ? 'right' : 'left';
        ctx.fillText(p.name, px + (left ? -12 : 12), py);
        ctx.restore();
      });
    });
    ctx.save();
    ctx.fillStyle = '#898781'; ctx.font = 'italic 12px sans-serif';
    ctx.textAlign = 'left'; ctx.textBaseline = 'top';
    ctx.fillText('↖ student beats its teacher', a.left + 8, a.top + 8);
    ctx.textAlign = 'right'; ctx.textBaseline = 'bottom';
    ctx.fillText('teacher beats its student ↘', a.right - 8, a.bottom - 8);
    ctx.restore();
  }
}],
options: {
  aspectRatio: 1.2,
  plugins: {
    legend: { position: 'bottom', labels: { color: '#898781', usePointStyle: true } },
    tooltip: { filter: (c) => c.datasetIndex < 3, callbacks: { label: (c) => c.raw.name + ': teacher ' + c.raw.x + ', its student ' + c.raw.y } }
  },
  scales: {
    x: {
      min: 70, max: 82,
      title: { display: true, text: "the teacher's score (macro-F1) →", color: '#898781' },
      ticks: { color: '#898781', stepSize: 2 },
      grid: { color: document.documentElement.classList.contains('dark') ? '#2c2c2a' : '#e1e0d9' }
    },
    y: {
      min: 70, max: 82,
      title: { display: true, text: "its student's score (macro-F1) →", color: '#898781' },
      ticks: { color: '#898781', stepSize: 2 },
      grid: { color: document.documentElement.classList.contains('dark') ? '#2c2c2a' : '#e1e0d9' }
    }
  }
}
{{< /chart >}}

<p class="caption">One dot per teacher, labeled with the teacher's name; its height is the score of the Ettin-150M student trained on its soft labels. Means over seeds where I ran several.</p>

**Yes, point for point.** Every dot sits on the line: a 7.4-point gap between teachers (Decider Flash to Decider) becomes a 7.6-point gap between students. Pick the best teacher you can afford to run once.

**Bigger helps, less and less.** Within a family, the teachers line up by size:

| Family | 2B | 4B | 9B | 27B |
|---|---|---|---|---|
| Base Labs | Joey: 48.7 | | Elephant: 76.5 | Mammoth: 79.3 |
| Perplexity | | Decider Flash: 72.4 | | Decider: 79.8 |

<p class="caption">Teacher macro-F1 on the gold test set.</p>

The big step is from 2B to 9B: Joey 1 files half the papers under Machine Learning, and a teacher this weak isn't worth a student. From 9B to 27B, the Decision Index gains 8 points; arXiv only 2.8. The two 27B teachers end up level (79.3 and 79.8, within the noise), still 5 points under the gold encoder. What's left is mostly about the authors' conventions, which no teacher can read off an abstract.

**The leaderboard doesn't pick the teacher for you.** OneJev1.6-4B (48.9) has the lowest Decision Index score of the teachers, after Joey, and it beats Decider Flash (54.3) by 2.7 points here. The index averages dozens of tasks; yours is one. A pilot on 100 papers per split, for 2 cents across all five rented teachers, got the order right except for two teachers 1.4 points apart. Run one before you pick.

**Silver labels, measured.** On the training pool, the teachers' top answer matches the gold label 72% (Decider Flash), 74% (OneJev1.6-4B), 75% (Elephant) and 78% of the time (Mammoth and Decider). Even with the best teacher, more than a fifth of the labels are wrong, and the student learns them as they are.

<div class="card card-grey">
<p class="card-kicker">Takeaway</p>
<p>Spend your money on the teacher, once, after a pilot on your own data.</p>
</div>

## What does it cost?

On the arXiv task. Labeling is the training pool plus validation (9,000 papers): through the API for the rented teachers, one request at a time, and in bf16 with MLX on the GPU for OneJev1.6-4B. Serving is on the laptop's GPU: fp32 with PyTorch (MPS) for the encoders, Q4_0 with llama.cpp for OneJev. TF-IDF runs on one CPU thread, and the rented teachers through the API. Serving on a CPU, with int8 encoders, was [part 2](/how-small-can-a-classifier-be/#what-it-costs-to-serve)'s topic.

<div class="table-tight">
<table class="grouped">
<thead><tr><th></th><th>Your labels</th><th>F1</th><th>Labeling, once</th><th>Training</th><th>Latency</th><th>RAM</th><th>Per million papers</th></tr></thead>
<tbody class="rows-purple">
<tr><td>Decider 27B, via the API</td><td>0</td><td>79.8</td><td>none</td><td>none</td><td>316 ms</td><td>none</td><td>$8.60</td></tr>
<tr><td>Mammoth 27B, via the API</td><td>0</td><td>79.3</td><td>none</td><td>none</td><td>268 ms</td><td>none</td><td>$44.50</td></tr>
<tr><td>OneJev1.6-4B, on the laptop</td><td>0</td><td>75.1</td><td>none</td><td>none</td><td>456 ms</td><td>4.1 GB</td><td>GPU time</td></tr>
</tbody>
<tbody class="rows-blue">
<tr><td><strong>Student of Decider 27B</strong></td><td><strong>0</strong></td><td><strong>79.4</strong></td><td><strong>60 min, $0.08</strong></td><td>1.3 h</td><td><strong>32 ms</strong></td><td>1.7 GB</td><td>GPU time</td></tr>
<tr><td>Student of OneJev1.6-4B</td><td>0</td><td>74.6</td><td>49 min</td><td>1.3 h</td><td>32 ms</td><td>1.7 GB</td><td>GPU time</td></tr>
</tbody>
<tbody class="rows-green">
<tr><td>Ettin-150M, gold labels</td><td>8,000</td><td>84.7</td><td>65 to 130 h by hand</td><td>1.3 h</td><td>32 ms</td><td>1.7 GB</td><td>GPU time</td></tr>
<tr><td>TF-IDF, gold labels</td><td>8,000</td><td>83.9</td><td>65 to 130 h by hand</td><td>33 s</td><td>1.1 ms</td><td>0.5 GB</td><td>one CPU thread</td></tr>
</tbody>
</table>

</div>

<p class="caption"><span class="row-key row-key-purple">teachers</span> <span class="row-key row-key-blue">students</span> <span class="row-key row-key-green">gold labels</span>. F1 on the 2,000 test papers. Latency: median per paper at batch size 1, as served; through the API, it includes the round trip from the laptop. Labeling the five rented teachers, test sets included, cost $0.86. Labeling by hand is an estimate: 30 seconds to a minute per abstract, for someone who knows the field.</p>

**The money is not the point.** Labeling 9,000 papers with the best teacher costs 8 cents, and serving it costs $8.60 per million papers: a student won't pay for itself in dollars. Mammoth, at the same quality, costs five times more, which the leaderboard won't tell you either.

**The point is everything else.** The student answers in 32 ms on the laptop's GPU, ten times faster than the API. No network, no rate limit, no API key, and no provider who can change or retire the model under you. Your texts leave the machine once, to be labeled, and never again. And if they can't leave it at all, OneJev1.6-4B labels them locally, in under an hour, for 4.8 points less.

**What the gold labels would buy.** 5.3 points over the best student, and they make the student itself optional: TF-IDF on the same labels trains in 33 seconds and answers in a millisecond. But 8,000 labels by hand are 65 to 130 hours, two to three weeks of full-time work, against an hour of API calls; [part 1](/do-you-need-an-llm/#how-many-labels-does-the-encoder-need) suggests a few hundred per class would already get close on a task where the words give the answer away. That's for a later post.

## So, should you distill?

Back to the starting point: you have a classification task, but no gold labels. You can call a decision model on every text, or train a small model on its answers. Or label the data yourself. Here is how I would decide, with the numbers from arXiv:

<figure class="svg-figure">
<svg viewBox="0 0 600 650" role="img" aria-label="Decision tree. First pick a teacher: if your texts can leave the machine, rent several big decision models; if not, host the biggest you can; either way, keep the best one on 100 hand-labeled texts. If it isn't good enough, mix gold and silver labels (the next post) or label everything by hand. If serving it is fine, call it. If not, distill it, unless every point is crucial: then mix gold and silver labels.">
  <defs>
    <marker id="dt-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker>
  </defs>
  <g fill="currentColor" font-family="inherit" text-anchor="middle">
    <!-- picking the teacher -->
    <rect x="140" y="10" width="300" height="50" rx="25" fill="currentColor" fill-opacity="0.07" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.5"/>
    <text x="290" y="40" font-size="15" font-weight="700">Can your texts leave the machine?</text>
    <path d="M290,60 V76 H150 V96" stroke="currentColor" stroke-width="1.5" fill="none" marker-end="url(#dt-arrow)"/>
    <path d="M290,76 H430 V96" stroke="currentColor" stroke-width="1.5" fill="none" marker-end="url(#dt-arrow)"/>
    <text x="162" y="92" font-size="13" text-anchor="start" opacity="0.85">no</text>
    <text x="442" y="92" font-size="13" text-anchor="start" opacity="0.85">yes</text>
    <rect x="20" y="100" width="260" height="74" rx="12" fill="#7c4dcc" fill-opacity="0.15" stroke="#9a6fe3" stroke-width="1.5"/>
    <text x="150" y="122" font-size="14" font-weight="700">Host the biggest you can</text>
    <text x="150" y="141" font-size="12" opacity="0.85">keep the best on 100 hand-labeled texts</text>
    <text x="150" y="160" font-size="12" opacity="0.85">here: OneJev1.6-4B, F1 75.1</text>
    <rect x="300" y="100" width="260" height="74" rx="12" fill="#7c4dcc" fill-opacity="0.15" stroke="#9a6fe3" stroke-width="1.5"/>
    <text x="430" y="122" font-size="14" font-weight="700">Rent several big ones</text>
    <text x="430" y="141" font-size="12" opacity="0.85">keep the best on 100 hand-labeled texts</text>
    <text x="430" y="160" font-size="12" opacity="0.85">here: Decider 27B, F1 79.8 (2¢ pilot)</text>
    <path d="M150,174 V194 H430" stroke="currentColor" stroke-width="1.5" fill="none"/>
    <line x1="430" y1="174" x2="430" y2="216" stroke="currentColor" stroke-width="1.5" marker-end="url(#dt-arrow)"/>
    <!-- questions, right column -->
    <rect x="280" y="220" width="300" height="56" rx="28" fill="currentColor" fill-opacity="0.07" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.5"/>
    <text x="430" y="244" font-size="15" font-weight="700">Is the best teacher good enough?</text>
    <text x="430" y="264" font-size="12" opacity="0.8">on your 100 hand-labeled texts</text>
    <rect x="280" y="330" width="300" height="56" rx="28" fill="currentColor" fill-opacity="0.07" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.5"/>
    <text x="430" y="354" font-size="15" font-weight="700">Is serving the teacher a problem?</text>
    <text x="430" y="374" font-size="12" opacity="0.8">speed · CPU only · API dependency</text>
    <rect x="280" y="440" width="300" height="56" rx="28" fill="currentColor" fill-opacity="0.07" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.5"/>
    <text x="430" y="464" font-size="15" font-weight="700">Is every point crucial?</text>
    <text x="430" y="484" font-size="12" opacity="0.8">the student stays 5 points below gold</text>
    <!-- yes, down -->
    <line x1="430" y1="276" x2="430" y2="326" stroke="currentColor" stroke-width="1.5" marker-end="url(#dt-arrow)"/>
    <text x="442" y="306" font-size="13" text-anchor="start" opacity="0.85">yes</text>
    <line x1="430" y1="386" x2="430" y2="436" stroke="currentColor" stroke-width="1.5" marker-end="url(#dt-arrow)"/>
    <text x="442" y="416" font-size="13" text-anchor="start" opacity="0.85">yes</text>
    <line x1="430" y1="496" x2="430" y2="536" stroke="currentColor" stroke-width="1.5" marker-end="url(#dt-arrow)"/>
    <text x="442" y="521" font-size="13" text-anchor="start" opacity="0.85">yes</text>
    <!-- no -->
    <path d="M580,248 H592 V590 H544" stroke="currentColor" stroke-width="1.5" fill="none" marker-end="url(#dt-arrow)"/>
    <text x="588" y="240" font-size="13" opacity="0.85">no</text>
    <line x1="280" y1="358" x2="246" y2="358" stroke="currentColor" stroke-width="1.5" marker-end="url(#dt-arrow)"/>
    <text x="263" y="351" font-size="13" opacity="0.85">no</text>
    <line x1="280" y1="468" x2="246" y2="468" stroke="currentColor" stroke-width="1.5" marker-end="url(#dt-arrow)"/>
    <text x="263" y="461" font-size="13" opacity="0.85">no</text>
    <!-- leaf: call the teacher -->
    <rect x="20" y="316" width="220" height="84" rx="12" fill="#7c4dcc" fill-opacity="0.22" stroke="#9a6fe3" stroke-width="2"/>
    <text x="130" y="338" font-size="15" font-weight="700">Call the teacher</text>
    <text x="130" y="358" font-size="12" opacity="0.85">rented: F1 79.8 · 316 ms</text>
    <text x="130" y="375" font-size="12" opacity="0.85">local: F1 75.1 · 456 ms</text>
    <text x="130" y="392" font-size="12" opacity="0.85">nothing to train</text>
    <!-- leaf: distill -->
    <rect x="20" y="426" width="220" height="84" rx="12" fill="#2a78d6" fill-opacity="0.28" stroke="#3987e5" stroke-width="2.5"/>
    <text x="130" y="448" font-size="15" font-weight="700">Distill</text>
    <text x="130" y="468" font-size="12" opacity="0.85">rented teacher: F1 79.4</text>
    <text x="130" y="485" font-size="12" opacity="0.85">local teacher: F1 74.6</text>
    <text x="130" y="502" font-size="12" opacity="0.85">32 ms on the GPU, no API</text>
    <!-- leaf: next post -->
    <rect x="300" y="540" width="240" height="100" rx="12" fill="#d4a72c" fill-opacity="0.15" stroke="#d4a72c" stroke-width="2" stroke-dasharray="6 4"/>
    <text x="420" y="564" font-size="15" font-weight="700">Mix gold and silver</text>
    <text x="420" y="584" font-size="12" opacity="0.85">distill, then add a few gold labels</text>
    <text x="420" y="603" font-size="12" font-weight="700" fill="#d4a72c">the next post</text>
    <text x="420" y="627" font-size="11" opacity="0.7">or label all by hand: F1 84.7, 65 to 130 h</text>
  </g>
</svg>
</figure>
<p class="caption">Numbers from this post: macro-F1 on the arXiv test set, latency per paper as served.</p>

Two steps cost a little time but save a lot. The pilot: label 100 of your texts by hand, about an hour, and grade the candidate teachers on them (2 cents for all five here). And whichever branch you take, check a few hundred of the teacher's labels by hand: what it gets wrong every time, the student will too.

## This is also what we did in the paper

<div class="card card-purple">
<p class="card-kicker">The paper</p>
<p class="card-title"><a href="https://arxiv.org/abs/2603.29497">Distilling Human-Aligned Privacy Sensitivity Assessment from Large Language Models</a></p>
<p>Gabriel Loiseau, Damien Sileo, <u>Damien Riquet</u>, Maxime Meyer, Marc Tommasi (LEGAL / CALD-pseudo workshop, 2026). Models, code and data on <a href="https://github.com/gabrielloiseau/privacy-distillation">GitHub</a>.</p>
</div>

Same recipe, bigger scale, on another question: **how private is a text?**, from 1 (*harmless*) to 5 (*extremely private*), on the scale of [Meisenbacher et al. (2025)](https://arxiv.org/abs/2508.12158). Their study showed that a large LLM agrees with people on this about as well as people agree with each other. But sending private texts to an API to ask how private they are defeats the purpose: the evaluator has to be small, and local. So [Mistral Large 3](https://mistral.ai/news/mistral-3) (675B) rated 200,000 user-written texts, Ettin students learned its ratings, and 250 texts rated by 677 people served as gold, with agreement measured by Krippendorff's α (1: perfect, 0: chance).

| Model | Parameters | Agreement with the average human rating (α) |
|---|---|---|
| Mistral-7B, prompted | 7B | 0.563 |
| **Mistral Large 3, the teacher** | 675B | **0.716** |
| Ettin-17M, its student | 17M | 0.708 |
| **Ettin-150M, its student** | 150M | **0.737** |

<p class="caption">On the 250 texts rated by people, from the paper's Table 5.</p>

**There, the student beat its teacher**, with 4,500 times fewer parameters. We read it as denoising: an LLM's answers vary from one prompt to the next, and 200,000 of them smooth out into one stable decision boundary. That didn't happen here: the teachers' mistakes on arXiv are systematic, not scattered, and 8,000 examples are not 200,000. The warning holds at both scales: the student inherits the teacher's biases, which is why both measure against people.

## Caveats

- **One task.** arXiv categories are a task where the words give the answer away. On a task where the answer is in a relation, like VAST, the teacher's mistakes may be harder to average out.
- **Gold labels are the authors' choice.** cs.LG vs. cs.CV is a matter of opinion, and part of the gap to the ceiling is in the labels, not in the models.
- **Contamination.** The teachers came out after these papers, and an arXiv page shows the primary category right next to the abstract: a base model trained on a later crawl could have read both. The risk is low, not zero. Decider 27B is built on Qwen3.8, released in August 2026: papers from March to July could be in its training data. It still scores level with Mammoth 27B, on Qwen3.5.
- **Rented teachers move.** The API models are named by version (Decider v1.2), but the provider runs them, and can update or retire them. The labels are saved with the code; the teachers may not be there in a year.
- **One student size, one temperature.** Ettin-150M only, soft labels at a temperature of 2, no tuning, no checkpoint selection.

## What's next

- **A few gold labels on top?** Fine-tune the student, or a small teacher, on 10 to 100 gold labels per class after distillation.
- **Fine-tune or optimize the prompt?** Plain vs. GEPA-optimized prompt, base vs. LoRA weights.

## Related reading

- [Distilling the Knowledge in a Neural Network](https://arxiv.org/abs/1503.02531), by Geoffrey Hinton, Oriol Vinyals and Jeff Dean (2015). Soft labels and temperature: where the idea of learning from the teacher's probabilities comes from.
- [Want To Reduce Labeling Cost? GPT-3 Can Help](https://aclanthology.org/2021.findings-emnlp.354/), by Shuohang Wang et al. (Findings of EMNLP 2021). An LLM labels, a small model learns: the same recipe, with GPT-3 as the teacher.
- [Distilling Step-by-Step!](https://arxiv.org/abs/2305.02301), by Cheng-Yu Hsieh et al. (Findings of ACL 2023). Small students beating much larger teachers, with fewer labels.