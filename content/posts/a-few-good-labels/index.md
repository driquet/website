---
title: "A Few Good Labels: Mixing Silver and Gold"
description: "With an LLM teacher's labels in hand, how many human labels does it take to do better, and how should you mix the two?"
date: 2026-11-26T10:00:00+01:00
tags: ["AI", "LLM", "NLP", "Classification", "Benchmark"]
showTableOfContents: true
series: ["Classifying Text Locally"]
series_order: 4
---

{{< lead >}}
A teacher's labels for free, and half an hour of your own. How many gold labels does it take, and what should you do with them?
{{< /lead >}}

In [the previous post](/distilling-a-classifier/), a decision model labeled 8,000 arXiv papers, and a small encoder learned from its answers. Without a single label from me, the student landed level with its teacher: 79.4 against 79.8 for Decider 27B. But it stayed 5.3 points below the same encoder trained on the real labels (84.7), and it [copied 67% of its teacher's mistakes](/distilling-a-classifier/#does-the-student-copy-its-teachers-mistakes): the systematic ones, retrieval and security papers filed by their method.

So you have two kinds of labels, and neither is enough:

- **Silver labels**, from the teacher: as many as you want, for a few cents, with the teacher's mistakes in them.
- **Gold labels**, from you: right, but each one costs a minute of your time, and you don't have weeks.

This post is about the middle: an hour or a day of annotation, not a month. Promote some papers from silver to gold. Do they fix what the teacher gets wrong, or get lost in the crowd?

Three questions:

1. **How should you use them?** Swap them in for silver ones, weight them up in the loss, or train on them last.
2. **Which papers should you promote?** Random ones, or the ones the teacher is likely to get wrong.
3. **How does it compare to gold only?** With no silver at all, how many labels reach the silver student, and the ceiling?

The short answer: gold labels are worth a lot, but only if they come last. Forty of them, half an hour of work, in a second training on their own, close 85% of the gap to a fully labeled training set. Mixed into the silver ones, fifty times as many do less.

Same laptop (Apple M5, 24 GB of unified memory), same code: [driquet/local-classification](https://github.com/driquet/local-classification), in `experiments/silver-and-gold`. Same warning: a weekend project, one task, one teacher, three runs per point. It gives the gist, not a law.

<div class="card card-green">
<p class="card-kicker">TL;DR · in a hurry?</p>
<p class="card-title"><a href="#so-should-you-mix">Jump to the answer →</a></p>
<p>How many labels to annotate, which ones, and what to do with them.</p>
</div>

## Same task, a smaller student

Everything comes from [part 3](/distilling-a-classifier/#a-new-task-which-field-is-this-paper-from): the task (the primary arXiv category of a 2026 paper, among eight computer science ones, from its title and abstract), the splits, and the recipe. One thing changes: the student.

**Ettin-68M instead of 150M.** This post trains over a hundred students, and Ettin-150M takes 1.3 hours each on the 8,000 papers. Ettin-68M takes 38 minutes. It costs less than a point: 78.5 on silver labels (79.4 at 150M), 84.0 on gold ones (84.7). What I'm after is the difference between ways of mixing, not the best absolute score, so every reference is retrained at 68M.

<div class="card-grid card-grid-2">
<div class="card card-purple">
<p class="card-kicker">Silver · 8,000 labels</p>
<p class="card-title">Decider 27B</p>
<p>The best teacher of part 3, rented once. Its probabilities for every paper of the training pool, right 78% of the time.</p>
</div>
<div class="card card-orange">
<p class="card-kicker">Gold · 8 to 2,000 labels</p>
<p class="card-title">The authors' category</p>
<p>The real label of some papers of the pool: from six minutes of annotation to three days.</p>
</div>
<div class="card card-blue">
<p class="card-kicker">Student</p>
<p class="card-title">Ettin-68M</p>
<p>Fine-tuned on silver, gold, or both. Graded on the 2,000 gold test papers.</p>
</div>
<div class="card card-grey">
<p class="card-kicker">References</p>
<p class="card-title">Silver only · all gold</p>
<p>Ettin-68M on the teacher's labels (78.5), and on the 8,000 gold labels (84.0).</p>
</div>
</div>

**The gold labels are simulated.** I didn't annotate anything: the training pool has gold labels, set aside in part 3, and "annotating" a paper means revealing its label. So my annotator is perfect, and agrees with the authors every time. A real one wouldn't (see the caveats).

**The budgets:** 80, 200, 400, 800 and 2,000 papers, drawn at random from the pool: 1% to 25% of it, 10 to 250 per category on average. At about 45 seconds per abstract, a guess, that is from 1 hour to 25 hours of work. The draws are uniform, not balanced per category: an annotator doesn't know a paper's category before reading it. Within a draw, each budget contains the smaller ones.

### Three ways to mix, one without

A gold label always belongs to a paper that already has a silver one. What changes is what the student does with it:

<div class="card-grid card-grid-2">
<div class="card card-grey">
<p class="card-kicker">One training</p>
<p class="card-title">Same weight</p>
<p>The gold label replaces the silver one. The student trains once on the 8,000 papers, every paper counting the same.</p>
</div>
<div class="card card-grey">
<p class="card-kicker">One training</p>
<p class="card-title">Upweight</p>
<p>The same, but each gold paper counts 10 times in the loss.</p>
</div>
<div class="card card-blue">
<p class="card-kicker">Two trainings</p>
<p class="card-title">Two stages</p>
<p>The silver student, then fine-tuned again on the gold papers only.</p>
</div>
<div class="card card-orange">
<p class="card-kicker">No silver</p>
<p class="card-title">Gold only</p>
<p>Ettin-68M, and TF-IDF, trained on the gold papers and nothing else.</p>
</div>
</div>

A gold paper has a single answer, so it is a hard label; a silver one keeps the teacher's probabilities, softened at a temperature of 2, as in part 3. The first stage of two stages is the silver reference itself. The second stage uses a lower learning rate (1e-5) for 10 epochs, with no checkpoint selection: I didn't want to spend gold labels on a validation set.

### How I measured

- **Quality:** macro-F1 on the 2,000 gold test papers, as in part 3.
- **Draws and seeds:** three runs per point, each with its own draw of gold papers and its own seed, so the spread covers both. The references: three seeds each.
- **Mistakes:** on the test papers the teacher gets wrong, does the student copy the mistake, fix it, or make another one? And on the ones it gets right, does the student break them?
- **Cost:** hours of annotation, at 45 seconds per abstract; the compute runs at night.

## How should you use gold labels?

Three ways, from the simplest, with the same gold papers at each budget.

### Same weight: lost in the crowd

The simplest mix: promote some papers from silver to gold, and train once, every paper counting the same. Macro-F1 against the number of gold papers in the pool:

{{< chart >}}
type: 'scatter',
data: {
  datasets: [
    {
      label: 'Same weight: gold replaces silver',
      data: [{x: 80, y: 78.6}, {x: 200, y: 78.3}, {x: 400, y: 78.8}, {x: 800, y: 79.7}, {x: 2000, y: 81.3}, {x: 8000, y: 84.0}],
      showLine: true,
      borderColor: '#898781', backgroundColor: '#898781',
      borderWidth: 2, pointRadius: 5, pointHoverRadius: 7
    }
  ]
},
plugins: [{
  id: 'refLines',
  beforeDatasetsDraw: (chart) => {
    const { ctx, chartArea: a, scales: { y } } = chart;
    [['All gold, 8,000 labels: 84.0', 84.0, '#2e9e6b', 'bottom'], ['Teacher, Decider 27B: 79.8', 79.8, '#9a6fe3', 'bottom'], ['Silver only: 78.5', 78.5, '#898781', 'top']].forEach(([text, v, color, base]) => {
      const py = y.getPixelForValue(v);
      ctx.save();
      ctx.strokeStyle = color; ctx.lineWidth = 1.5; ctx.setLineDash([2, 4]);
      ctx.beginPath(); ctx.moveTo(a.left, py); ctx.lineTo(a.right, py); ctx.stroke();
      ctx.fillStyle = color; ctx.font = '12px sans-serif'; ctx.textAlign = 'left'; ctx.textBaseline = base;
      ctx.fillText(text, a.left + 4, base === 'bottom' ? py - 3 : py + 3);
      ctx.restore();
    });
  }
}],
options: {
  aspectRatio: 1.3,
  plugins: {
    legend: { position: 'bottom', labels: { color: '#898781', usePointStyle: true } },
    tooltip: { callbacks: { label: (c) => c.parsed.x.toLocaleString('en-US') + ' gold labels: ' + c.parsed.y + ' macro-F1' } }
  },
  scales: {
    x: {
      type: 'logarithmic', min: 60, max: 10000,
      title: { display: true, text: 'gold labels, out of 8,000 papers (log scale)', color: '#898781' },
      afterBuildTicks: (axis) => { axis.ticks = [80, 200, 400, 800, 2000, 8000].map((value) => ({ value })); },
      ticks: { color: '#898781', autoSkip: false, maxRotation: 0, callback: (v) => v.toLocaleString('en-US') },
      grid: { display: false }
    },
    y: {
      min: 77, max: 85,
      title: { display: true, text: 'macro-F1 on the gold test set', color: '#898781' },
      ticks: { color: '#898781', stepSize: 1 },
      grid: { color: document.documentElement.classList.contains('dark') ? 'rgba(148, 163, 184, 0.2)' : '#e1e0d9' }
    }
  }
}
{{< /chart >}}

<p class="caption">Mean of three runs per point; the three runs are never more than 1.1 points apart. At 8,000, every label is gold: the ceiling.</p>

**Below 800 labels, it's worthless.** A few hundred gold labels change nothing: the student stays level with silver only, below the teacher, which costs no annotation at all. Most of them only confirm the silver label they replace: the teacher is right 78% of the time.

**A real gain takes 2,000.** That's a quarter of the pool, 25 hours of annotation, for less than three points, still far from the ceiling.

### Upweight: louder, not better

If the gold labels are drowned out, make them louder. The same papers, the same single training, but each gold paper counts 10 times in the loss: at 800 papers, that's more than half of the loss.

{{< chart >}}
type: 'scatter',
data: {
  datasets: [
    {
      label: 'Same weight',
      data: [{x: 80, y: 78.6}, {x: 200, y: 78.3}, {x: 400, y: 78.8}, {x: 800, y: 79.7}, {x: 2000, y: 81.3}, {x: 8000, y: 84.0}],
      showLine: true,
      borderColor: '#898781', backgroundColor: '#898781',
      borderWidth: 2, pointRadius: 5, pointHoverRadius: 7
    },
    {
      label: 'Upweight (x10)',
      data: [{x: 80, y: 78.2}, {x: 200, y: 78.1}, {x: 400, y: 77.7}, {x: 800, y: 79.0}, {x: 2000, y: 81.5}, {x: 8000, y: 84.0}],
      showLine: true,
      borderColor: document.documentElement.classList.contains('dark') ? '#6f9fd8' : '#9cc3ee',
      backgroundColor: document.documentElement.classList.contains('dark') ? '#6f9fd8' : '#9cc3ee',
      borderWidth: 2, pointRadius: 5, pointHoverRadius: 7
    }
  ]
},
plugins: [{
  id: 'refLines',
  beforeDatasetsDraw: (chart) => {
    const { ctx, chartArea: a, scales: { y } } = chart;
    [['All gold, 8,000 labels: 84.0', 84.0, '#2e9e6b', 'bottom'], ['Teacher, Decider 27B: 79.8', 79.8, '#9a6fe3', 'bottom'], ['Silver only: 78.5', 78.5, '#898781', 'top']].forEach(([text, v, color, base]) => {
      const py = y.getPixelForValue(v);
      ctx.save();
      ctx.strokeStyle = color; ctx.lineWidth = 1.5; ctx.setLineDash([2, 4]);
      ctx.beginPath(); ctx.moveTo(a.left, py); ctx.lineTo(a.right, py); ctx.stroke();
      ctx.fillStyle = color; ctx.font = '12px sans-serif'; ctx.textAlign = 'left'; ctx.textBaseline = base;
      ctx.fillText(text, a.left + 4, base === 'bottom' ? py - 3 : py + 3);
      ctx.restore();
    });
  }
}],
options: {
  aspectRatio: 1.3,
  plugins: {
    legend: { position: 'bottom', labels: { color: '#898781', usePointStyle: true } },
    tooltip: { callbacks: { label: (c) => c.dataset.label + ', ' + c.parsed.x.toLocaleString('en-US') + ' gold labels: ' + c.parsed.y + ' macro-F1' } }
  },
  scales: {
    x: {
      type: 'logarithmic', min: 60, max: 10000,
      title: { display: true, text: 'gold labels, out of 8,000 papers (log scale)', color: '#898781' },
      afterBuildTicks: (axis) => { axis.ticks = [80, 200, 400, 800, 2000, 8000].map((value) => ({ value })); },
      ticks: { color: '#898781', autoSkip: false, maxRotation: 0, callback: (v) => v.toLocaleString('en-US') },
      grid: { display: false }
    },
    y: {
      min: 77, max: 85,
      title: { display: true, text: 'macro-F1 on the gold test set', color: '#898781' },
      ticks: { color: '#898781', stepSize: 1 },
      grid: { color: document.documentElement.classList.contains('dark') ? 'rgba(148, 163, 184, 0.2)' : '#e1e0d9' }
    }
  }
}
{{< /chart >}}

<p class="caption">Mean of three runs per point. At 8,000, every label is gold, so the weight changes nothing.</p>

**Upweighting doesn't help.** It's level with same weight at best (81.5 against 81.3 at 2,000, within noise), and below it most of the time, sometimes even below the silver student.

**It fixes more, and breaks more.** The upweighted student corrects more of the teacher's mistakes, but now gets wrong more of the papers the teacher had right, and the balance ends slightly worse. My guess: in a single training, the student hears two answers for similar papers, the teacher's and mine, and making mine ten times louder moves it on papers it should have left alone.

**Why 10?** A single weight, not tuned: a smaller one might well sit between the two curves. The goal was only to see whether making gold louder changes anything. It does: it moves the student, in both directions at once.

### Two stages: gold comes last

The other way to make gold count: don't mix at all. Train the student on silver, as in part 3, then fine-tune it on the gold papers alone.

<figure class="svg-figure">
<svg viewBox="0 0 600 500" role="img" aria-label="Two stages. Stage 1: the student is fine-tuned on the teacher's silver labels for the 8,000 papers, once. Stage 2: the silver student is fine-tuned again on a few gold papers only. The two-stage student is graded on gold labels.">
  <defs>
    <marker id="ts-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker>
    <g id="ts-paper"><path d="M0,0 h20 l8,8 v28 h-28 z" fill="currentColor" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.6" stroke-width="1.5"/><path d="M5,13 h17 M5,19 h17 M5,25 h12" stroke="currentColor" stroke-opacity="0.45" stroke-width="1.5"/></g>
    <g id="ts-silver"><path d="M0,4 l4,-4 h16 v12 h-16 z" fill="#b9bec7" stroke="#8a909a" stroke-width="1"/><circle cx="5" cy="6" r="1.6" fill="#6b7079"/></g>
    <g id="ts-gold"><path d="M0,4 l4,-4 h16 v12 h-16 z" fill="#e3b83c" stroke="#b8860b" stroke-width="1"/><circle cx="5" cy="6" r="1.6" fill="#8a6a10"/></g>
  </defs>
  <g fill="currentColor" font-family="inherit" text-anchor="middle">
    <!-- silver papers -->
    <use href="#ts-paper" x="190" y="8"/><use href="#ts-silver" x="206" y="30"/>
    <use href="#ts-paper" x="235" y="8"/><use href="#ts-silver" x="251" y="30"/>
    <use href="#ts-paper" x="280" y="8"/><use href="#ts-silver" x="296" y="30"/>
    <use href="#ts-paper" x="325" y="8"/><use href="#ts-silver" x="341" y="30"/>
    <use href="#ts-paper" x="370" y="8"/><use href="#ts-silver" x="386" y="30"/>
    <text x="300" y="66" font-size="15" opacity="0.8">8,000 papers, silver labels from the teacher</text>
    <line x1="300" y1="74" x2="300" y2="100" stroke="currentColor" stroke-width="1.5" marker-end="url(#ts-arrow)"/>
    <!-- stage 1 -->
    <rect x="70" y="104" width="460" height="70" rx="14" fill="currentColor" fill-opacity="0.07" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.5"/>
    <text x="300" y="133" font-size="17" font-weight="700">Stage 1: fine-tune on the silver labels</text>
    <text x="300" y="157" font-size="14" opacity="0.8">probabilities at T = 2 · 4 epochs · 38 minutes, once</text>
    <line x1="300" y1="174" x2="300" y2="198" stroke="currentColor" stroke-width="1.5" marker-end="url(#ts-arrow)"/>
    <!-- silver student -->
    <rect x="180" y="202" width="240" height="60" rx="12" fill="#2a78d6" fill-opacity="0.12" stroke="#3987e5" stroke-width="1.5"/>
    <text x="300" y="228" font-size="16" font-weight="700">Silver student: Ettin-68M</text>
    <text x="300" y="250" font-size="13" opacity="0.85">as in part 3 · 78.5 macro-F1</text>
    <line x1="300" y1="262" x2="300" y2="318" stroke="currentColor" stroke-width="1.5" marker-end="url(#ts-arrow)"/>
    <!-- gold papers -->
    <use href="#ts-paper" x="470" y="212"/><use href="#ts-gold" x="486" y="234"/>
    <use href="#ts-paper" x="510" y="212"/><use href="#ts-gold" x="526" y="234"/>
    <text x="508" y="270" font-size="13" opacity="0.85">8 to 2,000 papers,</text>
    <text x="508" y="287" font-size="13" opacity="0.85">gold labels</text>
    <line x1="508" y1="294" x2="508" y2="318" stroke="#d4a72c" stroke-width="1.8" marker-end="url(#ts-arrow)"/>
    <!-- stage 2 -->
    <rect x="70" y="322" width="490" height="70" rx="14" fill="#d4a72c" fill-opacity="0.18" stroke="#d4a72c" stroke-width="2"/>
    <text x="315" y="351" font-size="17" font-weight="700">Stage 2: fine-tune again, on the gold labels only</text>
    <text x="315" y="375" font-size="14" opacity="0.85">one answer per paper · 1e-5 · 10 epochs · seconds to minutes</text>
    <line x1="300" y1="392" x2="300" y2="416" stroke="currentColor" stroke-width="1.5" marker-end="url(#ts-arrow)"/>
    <!-- two-stage student -->
    <rect x="170" y="420" width="260" height="64" rx="12" fill="#2a78d6" fill-opacity="0.25" stroke="#3987e5" stroke-width="2"/>
    <text x="300" y="447" font-size="16" font-weight="700">Two-stage student</text>
    <text x="300" y="470" font-size="13" opacity="0.85">graded on the 2,000 gold test papers</text>
  </g>
</svg>
</figure>
<p class="caption">Stage 1 is the silver student itself, trained once. Only stage 2 sees the gold labels, and only it needs rerunning when you annotate more.</p>

Against the two ways of mixing in one training, and down to 8 gold labels:

{{< chart >}}
type: 'scatter',
data: {
  datasets: [
    {
      label: 'Same weight',
      data: [{x: 80, y: 78.6}, {x: 200, y: 78.3}, {x: 400, y: 78.8}, {x: 800, y: 79.7}, {x: 2000, y: 81.3}],
      showLine: true,
      borderColor: '#898781', backgroundColor: '#898781',
      borderWidth: 2, pointRadius: 5, pointHoverRadius: 7
    },
    {
      label: 'Upweight (x10)',
      data: [{x: 80, y: 78.2}, {x: 200, y: 78.1}, {x: 400, y: 77.7}, {x: 800, y: 79.0}, {x: 2000, y: 81.5}],
      showLine: true,
      borderColor: document.documentElement.classList.contains('dark') ? '#6f9fd8' : '#9cc3ee',
      backgroundColor: document.documentElement.classList.contains('dark') ? '#6f9fd8' : '#9cc3ee',
      borderWidth: 2, pointRadius: 5, pointHoverRadius: 7
    },
    {
      label: 'Two stages',
      data: [{x: 8, y: 79.5}, {x: 20, y: 82.4}, {x: 40, y: 83.2}, {x: 80, y: 83.0}, {x: 200, y: 83.8}, {x: 400, y: 83.3}, {x: 800, y: 83.6}, {x: 2000, y: 83.8}],
      showLine: true,
      borderColor: document.documentElement.classList.contains('dark') ? '#3987e5' : '#2a78d6',
      backgroundColor: document.documentElement.classList.contains('dark') ? '#3987e5' : '#2a78d6',
      borderWidth: 2, pointRadius: 5, pointHoverRadius: 7
    }
  ]
},
plugins: [{
  id: 'refLines',
  beforeDatasetsDraw: (chart) => {
    const { ctx, chartArea: a, scales: { y } } = chart;
    [['All gold, 8,000 labels: 84.0', 84.0, '#2e9e6b', 'bottom'], ['Teacher, Decider 27B: 79.8', 79.8, '#9a6fe3', 'bottom'], ['Silver only: 78.5', 78.5, '#898781', 'top']].forEach(([text, v, color, base]) => {
      const py = y.getPixelForValue(v);
      ctx.save();
      ctx.strokeStyle = color; ctx.lineWidth = 1.5; ctx.setLineDash([2, 4]);
      ctx.beginPath(); ctx.moveTo(a.left, py); ctx.lineTo(a.right, py); ctx.stroke();
      ctx.fillStyle = color; ctx.font = '12px sans-serif'; ctx.textAlign = 'left'; ctx.textBaseline = base;
      ctx.fillText(text, a.left + 4, base === 'bottom' ? py - 3 : py + 3);
      ctx.restore();
    });
  }
}],
options: {
  aspectRatio: 1.3,
  plugins: {
    legend: { position: 'bottom', labels: { color: '#898781', usePointStyle: true } },
    tooltip: { callbacks: { label: (c) => c.dataset.label + ', ' + c.parsed.x.toLocaleString('en-US') + ' gold labels: ' + c.parsed.y + ' macro-F1' } }
  },
  scales: {
    x: {
      type: 'logarithmic', min: 6, max: 3000,
      title: { display: true, text: 'gold labels, picked at random (log scale)', color: '#898781' },
      afterBuildTicks: (axis) => { axis.ticks = [8, 20, 40, 80, 200, 400, 800, 2000].map((value) => ({ value })); },
      ticks: { color: '#898781', autoSkip: false, maxRotation: 0, callback: (v) => v.toLocaleString('en-US') },
      grid: { display: false }
    },
    y: {
      min: 77, max: 85,
      title: { display: true, text: 'macro-F1 on the gold test set', color: '#898781' },
      ticks: { color: '#898781', stepSize: 1 },
      grid: { color: document.documentElement.classList.contains('dark') ? 'rgba(148, 163, 184, 0.2)' : '#e1e0d9' }
    }
  }
}
{{< /chart >}}

<p class="caption">Mean of three runs per point. Same gold papers at each budget: the three ways differ only in what the student does with them. Below 40 labels, the three two-stage runs spread over 3 to 5 points.</p>

**Two stages is in another league.** From 40 labels on, it's within a point of the student trained on all 8,000 gold labels. The same labels, mixed into one training, give nothing. My smallest budget, 80 labels, was already near the ceiling, so I couldn't tell how fast it got there: I added runs at 40, 20 and 8 labels to find out.

**And it plateaus early.** Past 40 labels, more annotation barely moves it: there's little room left below the ceiling.

### How few is enough?

**Forty labels, half an hour, close 85% of the gap** between silver only and all gold. Twenty close 70% of it, but the runs are far apart. Eight is a lottery: the three draws cover only four to six of the eight categories, and the runs land anywhere from below the silver student to three points above it.

**It's not the corrections.** The 20 papers of a draw hold two to five teacher mistakes. That's not enough to teach the student where the teacher goes wrong, paper by paper. What they change is how often the student answers each category. The test set has 250 papers per category:

| Category | Test set | Teacher | Silver only | Two stages, 20 | Two stages, 800 | All gold |
|---|---|---|---|---|---|---|
| cs.CL | <span class="f1 f1-ref">250</span> | <span class="f1 f1-d">375</span> | <span class="f1 f1-d">392</span> | <span class="f1 f1-d">377</span> | <span class="f1 f1-a">248</span> | <span class="f1 f1-a">250</span> |
| cs.LG | <span class="f1 f1-ref">250</span> | <span class="f1 f1-d">356</span> | <span class="f1 f1-d">366</span> | <span class="f1 f1-c">203</span> | <span class="f1 f1-a">255</span> | <span class="f1 f1-a">262</span> |
| cs.CV | <span class="f1 f1-ref">250</span> | <span class="f1 f1-c">276</span> | <span class="f1 f1-b">266</span> | <span class="f1 f1-a">254</span> | <span class="f1 f1-b">233</span> | <span class="f1 f1-a">256</span> |
| cs.RO | <span class="f1 f1-ref">250</span> | <span class="f1 f1-a">239</span> | <span class="f1 f1-b">230</span> | <span class="f1 f1-a">261</span> | <span class="f1 f1-a">260</span> | <span class="f1 f1-a">251</span> |
| cs.SE | <span class="f1 f1-ref">250</span> | <span class="f1 f1-c">208</span> | <span class="f1 f1-c">210</span> | <span class="f1 f1-a">255</span> | <span class="f1 f1-a">243</span> | <span class="f1 f1-a">253</span> |
| cs.HC | <span class="f1 f1-ref">250</span> | <span class="f1 f1-c">204</span> | <span class="f1 f1-c">198</span> | <span class="f1 f1-a">239</span> | <span class="f1 f1-a">260</span> | <span class="f1 f1-a">246</span> |
| cs.CR | <span class="f1 f1-ref">250</span> | <span class="f1 f1-d">181</span> | <span class="f1 f1-d">178</span> | <span class="f1 f1-c">204</span> | <span class="f1 f1-a">261</span> | <span class="f1 f1-a">245</span> |
| cs.IR | <span class="f1 f1-ref">250</span> | <span class="f1 f1-d">161</span> | <span class="f1 f1-d">159</span> | <span class="f1 f1-c">208</span> | <span class="f1 f1-a">240</span> | <span class="f1 f1-b">237</span> |

<p class="caption">Test papers predicted in each category, out of 2,000. Students: mean of three runs; "two stages, 800" is the version picked where the teachers disagree ([below](#which-papers-should-you-promote)). Each count is colored by its gap to the true count, in <span class="f1 f1-ref">grey</span>: <span class="f1 f1-a">within 12 (5%)</span> <span class="f1 f1-b">13 to 25</span> <span class="f1 f1-c">26 to 62</span> <span class="f1 f1-d">over 62 (25%)</span>, too many or too few.</p>

The teacher answers cs.CL and cs.LG nearly 1.5 times too often, and cs.IR and cs.CR about a third too rarely: [the systematic mistakes of part 3](/distilling-a-classifier/#does-the-student-copy-its-teachers-mistakes), retrieval and security papers filed by their method. The silver student copies those proportions, and even amplifies them a little. Twenty gold papers are enough to pull most categories toward 250 (cs.LG even overshoots), but not cs.CL. With 800, every category is within 17 papers of its true count.

**Does it forget?** Ten epochs on a few hundred papers, with nothing from the teacher, could wash out what the silver labels taught. It doesn't: on the test papers the teacher gets right, the silver student gets 8.9% wrong; after the second stage on 800 random gold papers, 9.2%; the student trained on all gold labels, 9.4%.

**It's also the cheapest to redo.** The first stage is the silver student, trained once (38 minutes). The second takes 6 seconds with 8 labels, a minute with 80, 10 minutes with 800. Annotate 200 more papers next week, and you rerun only that second stage; the two other ways retrain on the 8,000 papers every time.

<div class="card card-grey">
<p class="card-kicker">Takeaway</p>
<p>Don't swap your labels into the silver set, and don't make them louder: in one training, a few hundred barely count. Train on silver first, then on gold alone: 40 gold labels, half an hour of work, get within a point of a fully labeled training set.</p>
</div>

## Which papers should you promote?

So far, the gold papers were drawn at random. But 78% of the teacher's labels are right: on most papers, an annotation only confirms what the student already learned. Can I pick the papers where it matters, without looking at their gold label?

Two cheap signals, both already computed in part 3:

- **The teacher is unsure.** A decision model doesn't just answer: it gives a probability for each category, the same ones the silver labels keep. When its two best answers are close, it hesitates.
- **Two teachers disagree.** Decider 27B and Mammoth 27B, from two families and at the same quality, give different answers.

Each strategy draws 800 papers from its 16% most suspicious ones: the disagreements, or the least confident answers.

### Do the signals find the teacher's mistakes?

A check first, with no training: the pool has gold labels, so I can count how many picked papers would correct the teacher. At random, one in five. Picked by either signal, one in two.

But both signals share a blind spot. Most of the teacher's mistakes are made by the second teacher too, with the same wrong answer, and with confidence. Neither signal sees those, and they are the systematic ones of part 3: retrieval papers, above all.

### Do they help the student?

The two-stage students, at 800 labels:

| 800 gold papers picked... | Two stages |
|---|---|
| At random | 83.6 |
| Where the teacher is unsure | 84.5 |
| Where two teachers disagree | 84.6 |
| *All gold, 8,000 labels* | *84.0* |

<p class="caption">Macro-F1 on the gold test set, mean of three runs.</p>

Picking is worth a point, and that point closes the gap: 800 hard papers on top of the teacher's labels do as well as 8,000 gold ones. The blind spot doesn't seem to matter. My guess is that any gold labels already fix most of the category proportions ([above](#how-few-is-enough)), retrieval included, and that the picked ones add the hard cases on top. Mixed into one training instead, the same papers barely help, and upweighted, they hurt.

One warning: picked papers are the hard ones, by construction. They make good corrections for a student that already knows the task, and a bad test set. Keep a random one to measure your model.

### Do they fix the teacher's mistakes?

The question I care about most. In part 3, the student copied the teacher's systematic mistakes. Gold labels are the only place where it can learn that the teacher is wrong.

On the test set, Decider 27B is wrong on 418 papers. What do the students answer on those?

{{< chart >}}
type: 'bar',
data: {
  labels: ['Silver only', 'Same weight, 800 random', 'Upweight, 800 random', 'Two stages, 800 disagree', 'All gold'],
  datasets: [
    {
      label: 'Same mistake as the teacher',
      data: [65, 58, 51, 32, 32],
      backgroundColor: document.documentElement.classList.contains('dark') ? '#d95926' : '#eb6834',
      borderWidth: 0
    },
    {
      label: 'Another mistake',
      data: [8, 8, 11, 9, 9],
      backgroundColor: '#898781',
      borderWidth: 0
    },
    {
      label: 'Fixed',
      data: [27, 34, 38, 59, 59],
      backgroundColor: '#2e9e6b',
      borderWidth: 0
    }
  ]
},
options: {
  indexAxis: 'y',
  aspectRatio: 2.0,
  plugins: {
    legend: { position: 'bottom', labels: { color: '#898781' } },
    tooltip: { callbacks: { label: (c) => c.dataset.label + ': ' + c.parsed.x + '%' } }
  },
  scales: {
    x: {
      stacked: true, min: 0, max: 100,
      title: { display: true, text: "% of the teacher's 418 mistakes on the test set", color: '#898781' },
      ticks: { color: '#898781', stepSize: 20 },
      grid: { color: document.documentElement.classList.contains('dark') ? 'rgba(148, 163, 184, 0.2)' : '#e1e0d9' }
    },
    y: { stacked: true, ticks: { color: '#898781' }, grid: { display: false } }
  }
}
{{< /chart >}}

<p class="caption">Ettin-68M students, mean of three runs each.</p>

**The silver student copies 65% of the teacher's mistakes**, as in part 3 (67% at 150M). Mixed in at the same weight, 800 gold labels bring it down to 58%.

**Two stages copies no more than a student that never saw the teacher.** The student trained on all gold labels never saw Decider 27B, yet it makes the same mistake on 32% of these papers: they are ambiguous enough that, even with the true labels, a student picks the teacher's answer. Two stages lands on the same 32%: whatever it had copied from the teacher, it unlearned. Overall, fixed mistakes minus broken right answers, the two-stage student gets 109 more test papers right than the teacher; the silver student, 29 fewer.

**Where the points come from.** Per category:

| Category | Silver only | Two stages, 800 disagree | Ettin-68M, all gold |
|---|---|---|---|
| cs.CL | <span class="f1 f1-d">67</span> | <span class="f1 f1-a">76</span> (+9) | <span class="f1 f1-ref">75</span> |
| cs.CV | <span class="f1 f1-a">84</span> | <span class="f1 f1-a">84</span> (0) | <span class="f1 f1-ref">85</span> |
| cs.LG | <span class="f1 f1-d">67</span> | <span class="f1 f1-a">75</span> (+8) | <span class="f1 f1-ref">74</span> |
| cs.CR | <span class="f1 f1-d">78</span> | <span class="f1 f1-a">88</span> (+10) | <span class="f1 f1-ref">87</span> |
| cs.RO | <span class="f1 f1-a">90</span> | <span class="f1 f1-a">89</span> (−1) | <span class="f1 f1-ref">90</span> |
| cs.SE | <span class="f1 f1-c">83</span> | <span class="f1 f1-a">88</span> (+5) | <span class="f1 f1-ref">88</span> |
| cs.HC | <span class="f1 f1-c">83</span> | <span class="f1 f1-a">88</span> (+5) | <span class="f1 f1-ref">87</span> |
| cs.IR | <span class="f1 f1-d">76</span> | <span class="f1 f1-a">87</span> (+11) | <span class="f1 f1-ref">86</span> |
| **Macro-F1** | <span class="f1 f1-c">**78.5**</span> | <span class="f1 f1-a">**84.6**</span> (**+6.1**) | <span class="f1 f1-ref">**84.0**</span> |

<p class="caption">F1 per category on the gold test set, mean of three runs. Each value is colored by its gap to the encoder trained on all gold labels, in <span class="f1 f1-ref">grey</span>: <span class="f1 f1-a">within 1 point</span> <span class="f1 f1-b">1 to 3 behind</span> <span class="f1 f1-c">3 to 6</span> <span class="f1 f1-d">over 6</span>.</p>

The teacher's systematic mistakes gain the most: cs.IR +11, cs.CR +10. So do the two categories it answers too often, cs.CL (+9) and cs.LG (+8): every retrieval or security paper filed there was also a false positive for them. After the second stage, every category is within a point of the fully labeled student.

<div class="card card-grey">
<p class="card-kicker">Takeaway</p>
<p>If you annotate for a day, annotate where the teacher hesitates, or where a second teacher disagrees, and use those labels in a second stage: one annotation out of two corrects a label, and the student reaches the fully labeled one.</p>
</div>

## How does it compare to gold only?

The other side of the question: forget the teacher. How many gold labels does the same student need, on its own, to catch up?

{{< chart >}}
type: 'scatter',
data: {
  datasets: [
    {
      label: 'Silver + gold, two stages',
      data: [{x: 8, y: 79.5}, {x: 20, y: 82.4}, {x: 40, y: 83.2}, {x: 80, y: 83.0}, {x: 200, y: 83.8}, {x: 400, y: 83.3}, {x: 800, y: 83.6}, {x: 2000, y: 83.8}],
      showLine: true,
      borderColor: document.documentElement.classList.contains('dark') ? '#3987e5' : '#2a78d6',
      backgroundColor: document.documentElement.classList.contains('dark') ? '#3987e5' : '#2a78d6',
      borderWidth: 2, pointRadius: 5, pointHoverRadius: 7
    },
    {
      label: 'Gold only: Ettin-68M',
      data: [{x: 80, y: 51.7}, {x: 200, y: 68.2}, {x: 400, y: 75.6}, {x: 800, y: 78.1}, {x: 2000, y: 82.2}, {x: 8000, y: 84.0}],
      showLine: true,
      borderColor: document.documentElement.classList.contains('dark') ? '#d4a72c' : '#b8860b',
      backgroundColor: document.documentElement.classList.contains('dark') ? '#d4a72c' : '#b8860b',
      borderWidth: 2, pointRadius: 5, pointHoverRadius: 7
    },
    {
      label: 'Gold only: TF-IDF',
      data: [{x: 80, y: 28.0}, {x: 200, y: 48.8}, {x: 400, y: 71.9}, {x: 800, y: 77.6}, {x: 2000, y: 81.2}, {x: 8000, y: 83.9}],
      showLine: true,
      borderColor: '#898781', backgroundColor: '#898781', borderDash: [5, 4],
      borderWidth: 2, pointRadius: 5, pointHoverRadius: 7
    }
  ]
},
plugins: [{
  id: 'refLines',
  beforeDatasetsDraw: (chart) => {
    const { ctx, chartArea: a, scales: { y } } = chart;
    [['Ettin-68M on 8,000 gold labels: 84.0', 84.0, '#2e9e6b', 'bottom'], ['Silver only: 78.5', 78.5, '#898781', 'top']].forEach(([text, v, color, base]) => {
      const py = y.getPixelForValue(v);
      ctx.save();
      ctx.strokeStyle = color; ctx.lineWidth = 1.5; ctx.setLineDash([2, 4]);
      ctx.beginPath(); ctx.moveTo(a.left, py); ctx.lineTo(a.right, py); ctx.stroke();
      ctx.fillStyle = color; ctx.font = '12px sans-serif'; ctx.textAlign = 'left'; ctx.textBaseline = base;
      ctx.fillText(text, a.left + 4, base === 'bottom' ? py - 3 : py + 3);
      ctx.restore();
    });
  }
}],
options: {
  aspectRatio: 1.3,
  plugins: {
    legend: { position: 'bottom', labels: { color: '#898781', usePointStyle: true } },
    tooltip: { callbacks: { label: (c) => c.dataset.label + ', ' + c.parsed.x.toLocaleString('en-US') + ' gold labels: ' + c.parsed.y + ' macro-F1' } }
  },
  scales: {
    x: {
      type: 'logarithmic', min: 6, max: 10000,
      title: { display: true, text: 'gold labels, picked at random (log scale)', color: '#898781' },
      afterBuildTicks: (axis) => { axis.ticks = [8, 20, 80, 200, 800, 2000, 8000].map((value) => ({ value })); },
      ticks: { color: '#898781', autoSkip: false, maxRotation: 0, callback: (v) => v.toLocaleString('en-US') },
      grid: { display: false }
    },
    y: {
      min: 25, max: 90,
      title: { display: true, text: 'macro-F1 on the gold test set', color: '#898781' },
      ticks: { color: '#898781', stepSize: 10 },
      grid: { color: document.documentElement.classList.contains('dark') ? 'rgba(148, 163, 184, 0.2)' : '#e1e0d9' }
    }
  }
}
{{< /chart >}}

<p class="caption">Mean of three runs per point. TF-IDF on 8,000 gold labels is part 3's (83.9).</p>

It takes about a thousand gold labels, twelve hours of annotation, for the student alone to match the silver student. That's what the teacher's labels are worth, for a night of compute and a few cents.

Below that, gold alone collapses: ten papers per category aren't enough to learn the task. The silver labels teach the student the task; the gold ones correct it. Gold alone runs out of examples, silver alone runs out of truth.

Above it, two stages still wins: 40 gold labels on top of the teacher beat 2,000 on their own. Mixed badly, though, silver costs points: 2,000 gold labels swapped into the silver set do worse than the same 2,000 alone. The teacher's mistakes pull the student back more than its examples help.

TF-IDF follows the same curve: far behind the encoder with a few hundred labels, close to it from 800 on, and it trains in seconds.

### What does it cost?

Everything on the same scale: my time. Annotation at 45 seconds per abstract; the compute runs while I sleep.

| Training set | Gold labels | Annotation | Macro-F1 |
|---|---|---|---|
| Silver only | 0 | none | 78.5 |
| **Silver + gold, random, two stages** | **40** | **30 min** | **83.2** |
| Silver + gold, random, two stages | 800 | 10 h | 83.6 |
| **Silver + gold, teachers disagree, two stages** | **800** | **10 h** | **84.6** |
| Silver + gold, random, same weight | 2,000 | 25 h | 81.3 |
| Gold only, Ettin-68M | 2,000 | 25 h | 82.2 |
| Gold only, Ettin-68M | 8,000 | 100 h | 84.0 |

<p class="caption">Mean of three runs per row. Annotation time from the 45-second guess.</p>

Half an hour of annotation, in a second stage, gets 85% of the way from the silver student to the fully labeled one. A day of picked papers gets the rest: level with 100 hours of annotation.

And these costs are only the tip of the iceberg. One thing went unsaid so far: every score in this post comes from a test set with gold labels. To see a one-point difference, I graded every student on 2,000 gold papers. Mine came free, from the authors' categories; annotating them myself would have taken about 25 hours, fifty times the half hour of the 40 training labels. Training labels are cheap; knowing that they worked is not.

## So, should you mix?

Back to the starting point: a teacher labeled your texts, and a small student learned from its answers. The student matches its teacher, but copies its systematic mistakes, and stays about 5 points below a student trained on real labels. You have a few hours to annotate, not weeks. Should you mix your labels with the teacher's?

Not in one training. Here's what worked for me:

1. **Distill first.** Let the best teacher you can rent label your texts, and train the student on them, as in [part 3](/distilling-a-classifier/). It costs a night, and nothing of your time.
2. **Annotate a few dozen texts, at random.** Forty, half an hour: enough to correct the teacher's habits, starting with how often it answers each category. Below 20, it's a lottery.
3. **Fine-tune the student again, on those labels only.** A low learning rate, a few epochs, a minute of training. Don't swap them into the silver set, and don't upweight them: in one training, they barely count.
4. **Have a day? Pick where to annotate.** Where the teacher hesitates, or where a second teacher, from another family, disagrees. 800 of those reach a fully labeled student.
5. **Keep a random gold test set.** Not the papers you picked: they are the hard ones. It's the biggest annotation bill of the lot.

That's one task, though, and an easy one: on arXiv, the words give the answer away, since the field is in the vocabulary. With a few dozen labels, the student mostly learns how often to answer each category. If your task hinges on implicit meaning (irony, tone, what a text implies rather than says), a few dozen labels will likely buy less. Check on your own random gold test set before trusting these numbers.

And when not to bother:

- **You have no time at all:** the silver student of part 3 is already level with its teacher. Still, six minutes of annotation are worth a try.
- **You have weeks:** annotate everything. But 200 gold labels on top of the teacher got within 0.2 points of 8,000, and with gold alone you need about a thousand just to reach the silver student.

## Caveats

- **Simulated annotation.** My gold labels are the authors' choice, revealed from the pool, and the test set is graded on the same choice. A real annotator would sometimes disagree with the authors, as the teacher does, and would gain less.
- **Annotation time is an estimate.** 45 seconds per abstract is a guess. The papers picked by the teachers are the hard ones, and probably take longer to annotate than random ones.
- **Balanced classes.** The pool and the test set have the same number of papers per category, so a few random gold labels show the student the true proportions, and much of the gain at small budgets comes from that. On a task where the teacher's proportions are already right, a few dozen labels would buy less.
- **A smaller student.** Ettin-68M, not part 3's 150M, to fit over a hundred trainings in three nights. Absolute scores are 0.7 to 0.9 points lower; the comparisons between mixes are what this post is about.
- **One task, one teacher.** arXiv categories are a task where the words give the answer away, and Decider 27B is a confident teacher. The second stage's recipe (learning rate, epochs) and the weight of 10 aren't tuned.
- **Picking only at 800.** I compared strategies at a single budget. Whether picking helps with 40 labels is open.
- **No checkpoint selection in the second stage.** It runs a fixed 10 epochs, and I keep the last one. Picking the best epoch would need a gold validation set, which means more labels: with 40, setting 10 aside is a quarter of the budget. The second-stage scores may be slightly below what it can reach.

## What's next

- **Fine-tune the teacher instead?** The same few dozen gold labels could go into the teacher's prompt, as examples, or into its weights: a better teacher, then a better student.
- **Few labels, a frozen sentence encoder?** An embedding model with a logistic regression on top, or SetFit: the other way to use a few hundred labels, with no teacher at all.
- **When the classes change.** A new category appears: edit the teacher's list of options, relabel, distill again? Or annotate a few examples, and run a second stage?

## Related reading

- [Learning from Noisy Labels with Deep Neural Networks: A Survey](https://arxiv.org/abs/2007.08199), by Hwanjun Song et al. (2020). What a model does with wrong labels, and the usual ways to limit the damage, a small clean set among them.
- [Snorkel: Rapid Training Data Creation with Weak Supervision](https://arxiv.org/abs/1711.10160), by Alexander Ratner et al. (VLDB 2017). Many cheap, noisy labelers instead of one annotator: where "silver labels" got serious.
- [Query by Committee](https://dl.acm.org/doi/10.1145/130385.130417), by H. Sebastian Seung, Manfred Opper and Haim Sompolinsky (COLT 1992). Annotating where several models disagree is an old idea.
- [Want To Reduce Labeling Cost? GPT-3 Can Help](https://aclanthology.org/2021.findings-emnlp.354/), by Shuohang Wang et al. (Findings of EMNLP 2021). An LLM labels most of the data, people label the examples it is least sure of.
