---
title: "How Small Can a Text Classifier Be?"
description: "Fine-tuned encoders and decision models from 17M to 4B parameters: what each costs on a laptop, with labels and without."
date: 2026-11-16T10:00:00+01:00
tags: ["AI", "NLP", "Classification", "Benchmark"]
showTableOfContents: true
series: ["Classifying Text Locally"]
series_order: 2
---

{{< lead >}}
Fine-tuned encoders and decision models, from 17M to 4B parameters: what each costs on a laptop, with labels and without.
{{< /lead >}}

In [the previous post](/do-you-need-an-llm/), a fine-tuned encoder with 150M parameters beat prompting a 4B LLM on two tasks out of three, a hundred times faster. But it needed labels. Without any, the best answer was a decision model, and it had 4B parameters. So how small can a text classifier be, with labels and without? The point isn't to find the lightest model, but the best one that fits your constraints. And sometimes, those constraints are tight: no labels, no GPU, or not much RAM to spare. So this post compares the models on what you pay:

- **To set up:** labels, and the time and memory to train. A decision model needs no labels from you; a fine-tuned encoder does.
- **To serve:** RAM and latency per text when the model predicts, and whether it needs a GPU.

Then, for each budget, the quality you can get.

Same three tasks: **CLINC150** (150 intents plus out-of-scope, the words give the answer away), **VAST** (stance toward a topic, the answer is in a relation), **DynaSent** (sentiment written to fool a model, the words lie). Same laptop: Apple M5, 24 GB of unified memory. Same code: [driquet/local-classification](https://github.com/driquet/local-classification), in `experiments/how-small`.

And the same warning: this is a weekend project (well, a few nights of runs). One laptop, three tasks, three seeds at most. It gives the gist, not a law.

This post is long: there is a lot to compare, and I'd rather show the evidence than ask you to trust a verdict. So the answer comes first, right below, then the models and [the main results side by side](#side-by-side). Each section after that measures one cost, and stands on its own: read the ones that match your constraints.

## TL;DR: So, how small?

Unless you work at one of the biggest tech companies, you can't serve the biggest models, and calling one through an API is often off the table: cost, privacy, or both. So it's a trade-off between what your Product team wants as high as possible, the macro-F1, and what your Ops team wants as low as possible: the machine, and the labels. Here is what I take away from three tasks on one laptop. (The models are introduced [right after](#the-contestants).)

**Take the cheap wins.** int8 on a CPU for the encoders, 4 bits for the LLMs: here, they cost at most a point of macro-F1, and save a lot of RAM.

**Then, do you have labels?**

- **No, or fewer than a few hundred per class:** take a decision model, and it no longer has to be an LLM. A 400M decision encoder, without a label from me, matched a fine-tuned 150M one. How many labels fine-tuning needed to catch up depended on the task: 50 to 100 per intent on CLINC, roughly a few hundred per class on sentiment (over 1,000 at 400M), thousands on stance.
- **Hundreds per class, or more:** fine-tune an encoder. Up to 150M, it beats the decision model of its size by a few points (at 400M, by under 2), and it stays just as fast however many classes you have.

**Then, the machine and the task:**

<div class="card-grid card-grid-2">
<div class="card card-blue">
<p class="card-kicker">Labels · CPU only</p>
<p class="card-title">A fine-tuned encoder, in int8</p>
<p>Even the smallest one beats TF-IDF everywhere, in milliseconds, on one CPU thread. Each size up scored higher here: take the smallest that meets your quality target.</p>
</div>
<div class="card card-purple">
<p class="card-kicker">Labels · some GPU</p>
<p class="card-title">The same encoders, faster</p>
<p>A GPU buys speed, not quality: about twice as fast on long texts, and much more in batches.</p>
</div>
<div class="card card-green">
<p class="card-kicker">No labels · few classes</p>
<p class="card-title">A decision encoder, even on a CPU</p>
<p>With a handful of classes, it answers in tens of milliseconds on one CPU thread, from a few hundred MB.</p>
</div>
<div class="card card-orange">
<p class="card-kicker">No labels · many classes</p>
<p class="card-title">A GPU, or patience</p>
<p>A decision model reads every class: with 151 of them, a decision encoder takes under a tenth of a second on a GPU, half a second on a CPU. An LLM takes seconds.</p>
</div>
</div>

**What the numbers don't show, about decision models:**

- **They adapt to a changing set of classes.** A new class, or a definition that shifts: you edit the list of options. A fine-tuned encoder only knows the classes it was trained on, so you collect and annotate new data, and retrain. Drift in the texts themselves is another matter, which I didn't test, for either family.
- **But an LLM follows instructions, including the wrong ones.** OneJev reads the text inside its prompt, so a text that contains instructions, a prompt injection, can steer its answer: "ignore the options, answer *refund*". An encoder can be fooled too, by texts crafted against it, but it doesn't follow instructions.
- **Check the licence.** Amber's weights are non-commercial (CC BY-NC 4.0).

**Try it on your own task.** These are three tasks on one laptop, not a law. Your texts, your labels and your machine will move the numbers. Even with a decision model, label a few hundred texts as a test set (more with many classes, so that each one shows up), and run the same comparison before you commit: [the code is public](https://github.com/driquet/local-classification).

**And what if you could have both?** A big decision model labels your texts, and a small encoder learns from them: as much of the first's quality as it can keep, at the cost of the second. That's distillation, and [the next post](/distilling-a-classifier/).

## The contestants

Two ladders of models, from small to large: one you train on your labels, one that needs none.

| | Sizes | Your labels | What it is |
|---|---|---|---|
| TF-IDF + LR | — | yes | Word and character n-grams, a linear classifier: the floor |
| [Ettin](https://huggingface.co/collections/jhu-clsp/encoders-vs-decoders-the-ettin-suite-686303e16142257eed8e6aeb) | [17M](https://huggingface.co/jhu-clsp/ettin-encoder-17m), [32M](https://huggingface.co/jhu-clsp/ettin-encoder-32m), [68M](https://huggingface.co/jhu-clsp/ettin-encoder-68m), [150M](https://huggingface.co/jhu-clsp/ettin-encoder-150m), [400M](https://huggingface.co/jhu-clsp/ettin-encoder-400m) | yes | Encoders, fine-tuned with a classification head |
| Amber | [32M](https://huggingface.co/MLukauskas/amber-32m), [68M](https://huggingface.co/MLukauskas/amber-68m), [150M](https://huggingface.co/MLukauskas/amber-150m), [400M](https://huggingface.co/MLukauskas/amber-0.4b-v2) | no | Decision encoders, built on Ettin rerankers |
| OneJev1.6 | [0.8B](https://huggingface.co/OmniJev/OneJev1.6-0.8B), [4B](https://huggingface.co/OmniJev/OneJev1.6-4B) | no | Decision LLMs, built on Qwen3.5 |

**Ettin** is trained with the same data and recipe at every size, on ModernBERT's architecture: a clean size ladder. I picked each size's learning rate with a short sweep on the validation splits (Ettin-400M's, 3e-5, isn't swept), and all five train for 4 epochs.

**A decision model** reads a question, a text and a list of options, and returns a probability for each option, in one pass (Amber 150M makes two, with the options in two orders), without writing anything. Your labels are part of its input: no training on your task, and a new label is one more option. Both families come from the [Decision Index](https://huggingface.co/spaces/multimodalart/jev-decision-index), a public benchmark of such models. Each Amber starts from the Ettin reranker of its size, an Ettin encoder already fine-tuned to score how well a passage answers a query, then trained by Amber's author on decision questions (about 1.5 million for the 150M): size for size, the two ladders share the architecture and the pretraining, not what comes after. OneJev1.6-4B is the first post's; it beat the prompted Qwen3.5-4B by 16 points on CLINC and 27 on VAST, so the plain LLM is out.

**Precision and device.** The encoders run on the GPU in fp32 and 16 bits (PyTorch, MPS), and on one CPU thread in fp32 (PyTorch) and int8 (ONNX Runtime, dynamic, per channel). OneJev runs on [llama.cpp](https://github.com/ggml-org/llama.cpp), what Ollama and LM Studio use, in 8 bits (Q8_0) and 4 bits (Q4_0), on the GPU and on four CPU threads, and in bf16 on Apple's [MLX](https://github.com/ml-explore/mlx).

## Side by side

The main results in three charts: quality, RAM and latency, on all three tasks: CLINC, the one with the most classes, VAST, the one with the longest texts, and DynaSent, the one with no exposure found. Each model is in its cheapest setup within [1 point](#first-does-precision-cost-quality) of its best precision: int8 on one CPU thread for the encoders, fine-tuned or not, and 4 bits on the GPU with llama.cpp for OneJev. One text at a time:

{{< chart >}}
type: 'bar',
data: (() => {
  const dark = document.documentElement.classList.contains('dark');
  // Decision models: diagonal hatch over a pale fill of the same color. Fine-tuned: solid.
  const hatch = (c) => { const k = document.createElement('canvas'); k.width = k.height = 8; const x = k.getContext('2d'); x.fillStyle = c + '40'; x.fillRect(0, 0, 8, 8); x.strokeStyle = c; x.lineWidth = 2; x.beginPath(); x.moveTo(0, 8); x.lineTo(8, 0); x.moveTo(-2, 2); x.lineTo(2, -2); x.moveTo(6, 10); x.lineTo(10, 6); x.stroke(); return x.createPattern(k, 'repeat'); };
  const solid = (label, data, light, dk) => ({ label, data, backgroundColor: dark ? dk : light });
  const dm = (label, data, light, dk) => ({ label, data, backgroundColor: hatch(dark ? dk : light), borderColor: dark ? dk : light, borderWidth: 1 });
  return {
    labels: ["CLINC", "VAST", "DynaSent"],
    datasets: [
      solid("TF-IDF + LR, ⚙️ CPU", [87.8, 32.9, 55.7], '#898781', '#898781'),
      solid("Ettin-32M, fine-tuned, int8, ⚙️ CPU", [90.7, 68.3, 65.9], '#b8860b', '#d4a72c'),
      solid("Ettin-150M, fine-tuned, int8, ⚙️ CPU", [92.8, 76.1, 72.6], '#2a78d6', '#3987e5'),
      solid("Ettin-400M, fine-tuned, int8, ⚙️ CPU", [93.4, 79.0, 77.4], '#c2408c', '#e06bb0'),
      dm("Amber 32M, int8, ⚙️ CPU", [85.5, 65.5, 61.8], '#b8860b', '#d4a72c'),
      dm("Amber 150M, int8, ⚙️ CPU", [90.5, 75.3, 68.0], '#2a78d6', '#3987e5'),
      dm("Amber 400M, int8, ⚙️ CPU", [93.3, 78.2, 75.0], '#c2408c', '#e06bb0'),
      dm("OneJev1.6-0.8B, 4-bit, ⚡ GPU", [91.4, 74.2, 62.7], '#eb6834', '#d95926'),
      dm("OneJev1.6-4B, 4-bit, ⚡ GPU", [95.6, 80.1, 73.4], '#a8431c', '#f2905f')
    ]
  };
})(),
options: {
  aspectRatio: 1.8,
  plugins: {
    title: { display: true, text: 'Quality: macro-F1 on the test set, higher is better', color: '#898781', font: { size: 14, weight: 'bold' }, padding: { top: 28, bottom: 12 } },
    legend: { position: 'bottom', labels: { color: '#898781', usePointStyle: true, boxWidth: 8, boxHeight: 8, padding: 12 } },
    tooltip: { callbacks: { label: (c) => c.dataset.label + ': ' + c.parsed.y.toFixed(1) } }
  },
  scales: {
    x: { ticks: { color: '#898781' }, grid: { display: false } },
    y: { title: { display: true, text: "macro-F1 on the test set", color: '#898781' }, min: 0, max: 100, ticks: { color: '#898781' }, grid: { color: document.documentElement.classList.contains('dark') ? 'rgba(148, 163, 184, 0.2)' : '#e1e0d9' } }
  }
}
{{< /chart >}}

{{< chart >}}
type: 'bar',
data: (() => {
  const dark = document.documentElement.classList.contains('dark');
  const hatch = (c) => { const k = document.createElement('canvas'); k.width = k.height = 8; const x = k.getContext('2d'); x.fillStyle = c + '40'; x.fillRect(0, 0, 8, 8); x.strokeStyle = c; x.lineWidth = 2; x.beginPath(); x.moveTo(0, 8); x.lineTo(8, 0); x.moveTo(-2, 2); x.lineTo(2, -2); x.moveTo(6, 10); x.lineTo(10, 6); x.stroke(); return x.createPattern(k, 'repeat'); };
  const solid = (label, data, light, dk) => ({ label, data, backgroundColor: dark ? dk : light });
  const dm = (label, data, light, dk) => ({ label, data, backgroundColor: hatch(dark ? dk : light), borderColor: dark ? dk : light, borderWidth: 1 });
  return {
    labels: ["CLINC", "VAST", "DynaSent"],
    datasets: [
      solid("TF-IDF + LR, ⚙️ CPU", [0.29, 0.16, 0.15], '#898781', '#898781'),
      solid("Ettin-32M, fine-tuned, int8, ⚙️ CPU", [0.145, 0.157, 0.14], '#b8860b', '#d4a72c'),
      solid("Ettin-150M, fine-tuned, int8, ⚙️ CPU", [0.300, 0.326, 0.30], '#2a78d6', '#3987e5'),
      solid("Ettin-400M, fine-tuned, int8, ⚙️ CPU", [0.725, 0.752, 0.73], '#c2408c', '#e06bb0'),
      dm("Amber 32M, int8, ⚙️ CPU", [0.216, 0.175, 0.16], '#b8860b', '#d4a72c'),
      dm("Amber 150M, int8, ⚙️ CPU", [0.426, 0.351, 0.32], '#2a78d6', '#3987e5'),
      dm("Amber 400M, int8, ⚙️ CPU", [0.877, 0.772, 0.74], '#c2408c', '#e06bb0'),
      dm("OneJev1.6-0.8B, 4-bit, ⚡ GPU", [1.31, 1.30, 1.29], '#eb6834', '#d95926'),
      dm("OneJev1.6-4B, 4-bit, ⚡ GPU", [4.00, 3.98, 3.97], '#a8431c', '#f2905f')
    ]
  };
})(),
options: {
  aspectRatio: 1.8,
  plugins: {
    title: { display: true, text: 'RAM: peak of the process, lower is better', color: '#898781', font: { size: 14, weight: 'bold' }, padding: { top: 28, bottom: 12 } },
    legend: { display: false }, // same colors as the first chart's legend
    tooltip: { callbacks: { label: (c) => c.dataset.label + ': ' + c.parsed.y.toLocaleString('en-US') + ' GB' } }
  },
  scales: {
    x: { ticks: { color: '#898781' }, grid: { display: false } },
    y: { type: 'logarithmic', title: { display: true, text: "GB (log scale)", color: '#898781' }, min: 0.01, max: 30, ticks: { color: '#898781', callback: (v) => [0.01, 0.1, 1, 10].includes(v) ? v.toLocaleString('en-US') : '' }, grid: { color: document.documentElement.classList.contains('dark') ? 'rgba(148, 163, 184, 0.2)' : '#e1e0d9' } }
  }
}
{{< /chart >}}

{{< chart >}}
type: 'bar',
data: (() => {
  const dark = document.documentElement.classList.contains('dark');
  const hatch = (c) => { const k = document.createElement('canvas'); k.width = k.height = 8; const x = k.getContext('2d'); x.fillStyle = c + '40'; x.fillRect(0, 0, 8, 8); x.strokeStyle = c; x.lineWidth = 2; x.beginPath(); x.moveTo(0, 8); x.lineTo(8, 0); x.moveTo(-2, 2); x.lineTo(2, -2); x.moveTo(6, 10); x.lineTo(10, 6); x.stroke(); return x.createPattern(k, 'repeat'); };
  const solid = (label, data, light, dk) => ({ label, data, backgroundColor: dark ? dk : light });
  const dm = (label, data, light, dk) => ({ label, data, backgroundColor: hatch(dark ? dk : light), borderColor: dark ? dk : light, borderWidth: 1 });
  return {
    labels: ["CLINC", "VAST", "DynaSent"],
    datasets: [
      solid("TF-IDF + LR, ⚙️ CPU", [0.37, 0.66, 0.39], '#898781', '#898781'),
      solid("Ettin-32M, fine-tuned, int8, ⚙️ CPU", [0.9, 8.5, 1.5], '#b8860b', '#d4a72c'),
      solid("Ettin-150M, fine-tuned, int8, ⚙️ CPU", [4.0, 39.5, 6.6], '#2a78d6', '#3987e5'),
      solid("Ettin-400M, fine-tuned, int8, ⚙️ CPU", [9.0, 83.5, 15.0], '#c2408c', '#e06bb0'),
      dm("Amber 32M, int8, ⚙️ CPU", [52.5, 10.0, 2.6], '#b8860b', '#d4a72c'),
      dm("Amber 150M, int8, ⚙️ CPU", [483, 92, 23.7], '#2a78d6', '#3987e5'),
      dm("Amber 400M, int8, ⚙️ CPU", [487, 99, 26.3], '#c2408c', '#e06bb0'),
      dm("OneJev1.6-0.8B, 4-bit, ⚡ GPU", [439, 50, 29.5], '#eb6834', '#d95926'),
      dm("OneJev1.6-4B, 4-bit, ⚡ GPU", [2041, 237, 127], '#a8431c', '#f2905f')
    ]
  };
})(),
options: {
  aspectRatio: 1.8,
  plugins: {
    title: { display: true, text: 'Latency: median per text, lower is better', color: '#898781', font: { size: 14, weight: 'bold' }, padding: { top: 28, bottom: 12 } },
    legend: { display: false }, // same colors as the first chart's legend
    tooltip: { callbacks: { label: (c) => c.dataset.label + ': ' + c.parsed.y.toLocaleString('en-US') + ' ms' } }
  },
  scales: {
    x: { ticks: { color: '#898781' }, grid: { display: false } },
    y: { type: 'logarithmic', title: { display: true, text: "median latency per text (ms, log scale)", color: '#898781' }, min: 0.1, max: 3000, ticks: { color: '#898781', callback: (v) => [0.1, 1, 10, 100, 1000, 10000].includes(v) ? v.toLocaleString('en-US') : '' }, grid: { color: document.documentElement.classList.contains('dark') ? 'rgba(148, 163, 184, 0.2)' : '#e1e0d9' } }
  }
}
{{< /chart >}}

<p class="caption">Solid bars: fine-tuned on the full training set. Hatched bars: decision models, no labels. Same color, same size. The CPU runs on one thread. RAM is the peak of the process. OneJev: quality, latency and RAM from the same llama.cpp runs, on the full test sets.</p>

**Three orders of magnitude, for a few points.** With CLINC's 151 labels, a fine-tuned int8 encoder answers in 1 to 9 ms; a decision encoder of the same size, in 50 ms to half a second; OneJev1.6-4B, in 2 seconds and 4 GB. For that, OneJev1.6-4B gains about 3 points over the fine-tuned Ettin-150M on CLINC and 4 on VAST. With three classes, the gap narrows. On VAST, from 150M, Amber answers in 0.1 s on one CPU thread, at the quality of the fine-tuned Ettin of its size, without a label. On DynaSent's short sentences, Amber 400M answers in 26 ms, ahead of the fine-tuned Ettin-150M (75.0 vs. 72.6), but behind the fine-tuned Ettin-400M (77.4), which answers in 15 ms.

The whole trade-off on CLINC, the task with the most labels: quality against latency, with the RAM as the size of the bubbles, each model in the same setup as above. One color per family:

{{< chart >}}
type: 'bubble',
data: (() => {
  const dark = document.documentElement.classList.contains('dark');
  const set = (label, points, light, dk) => ({ label, data: points.map(([x, y, ram, how, name, side]) => ({ x, y, r: 3 + 4 * Math.sqrt(ram), ram, how, name, side })), backgroundColor: dark ? dk : light, borderColor: dark ? dk : light });
  return {
    datasets: [
      set('TF-IDF + LR', [[0.37, 87.8, 0.29, 'CPU', 'TF-IDF', 'left']], '#898781', '#898781'),
      set('Ettin, fine-tuned, int8 on the CPU', [[0.47, 89.5, 0.12, '17M', '17M'], [0.92, 90.7, 0.14, '32M', '32M'], [2.29, 91.6, 0.19, '68M', '68M'], [4.03, 92.8, 0.30, '150M', '150M'], [8.97, 93.4, 0.73, '400M', '400M']], '#2a78d6', '#3987e5'),
      set('Amber, no labels, int8 on the CPU', [[52.5, 85.5, 0.22, '32M', '32M'], [133, 89.2, 0.31, '68M', '68M', 'left'], [483, 90.5, 0.43, '150M', '150M'], [487, 93.3, 0.88, '400M', '400M']], '#1baf7a', '#199e70'),
      set('OneJev1.6, no labels, 4 bits on the GPU', [[439, 91.4, 1.31, '0.8B', '0.8B', 'left'], [2041, 95.6, 4.00, '4B', '4B', 'left']], '#eb6834', '#d95926')
    ]
  };
})(),
plugins: [{
  id: 'pointNames',
  afterDatasetsDraw: (chart) => {
    const { ctx } = chart;
    chart.data.datasets.forEach((ds, i) => {
      if (!chart.isDatasetVisible(i)) return;
      chart.getDatasetMeta(i).data.forEach((pt, j) => {
        const { name, side } = ds.data[j];
        if (!name) return;
        const gap = (pt.options.radius || 5) + 5;
        ctx.save();
        ctx.fillStyle = '#898781'; ctx.font = '12px sans-serif'; ctx.textBaseline = 'middle';
        ctx.textAlign = side === 'left' ? 'right' : 'left';
        ctx.fillText(name, side === 'left' ? pt.x - gap : pt.x + gap, pt.y);
        ctx.restore();
      });
    });
  }
}],
options: {
  aspectRatio: 1.3,
  plugins: {
    legend: { position: 'bottom', labels: { color: '#898781', usePointStyle: true, boxWidth: 8, boxHeight: 8, padding: 16 } },
    tooltip: { callbacks: { label: (c) => c.dataset.label + ' (' + c.raw.how + '): ' + c.raw.y + ' macro-F1, ' + c.raw.x + ' ms, ' + c.raw.ram + ' GB of RAM' } }
  },
  scales: {
    x: {
      type: 'logarithmic', min: 0.1, max: 10000,
      title: { display: true, text: 'latency per text, p50 (log scale)', color: '#898781' },
      ticks: { color: '#898781', maxRotation: 0, callback: (v) => ({0.1: '0.1 ms', 1: '1 ms', 10: '10 ms', 100: '100 ms', 1000: '1 s', 10000: '10 s'})[v] ?? '' },
      grid: { color: document.documentElement.classList.contains('dark') ? 'rgba(148, 163, 184, 0.2)' : '#e1e0d9' }
    },
    y: {
      min: 80, max: 100,
      title: { display: true, text: 'macro-F1 on the full CLINC task', color: '#898781' },
      ticks: { color: '#898781', stepSize: 5 },
      grid: { color: document.documentElement.classList.contains('dark') ? 'rgba(148, 163, 184, 0.2)' : '#e1e0d9' }
    }
  }
}
{{< /chart >}}

The fine-tuned ladder sits on the left, 230 to 4,300 times faster than OneJev1.6-4B. The decision encoders pay for reading 151 labels: half a second on one CPU thread at 150M and 400M, or 61 to 70 ms on a GPU.

## What it costs to set up

Before a model can classify anything, what does it take? Three measures:

- **Labels:** how many labeled examples per class it trains on, from none to the full training set.
- **RAM:** the peak physical footprint of the training process, loading included, what Activity Monitor shows.
- **Time:** how long training takes on this laptop.

And what the cost buys: **macro-F1** on the official test sets, as in the first post.

### With your labels: fine-tuning

TF-IDF and the five Ettin models learn from labeled examples. The two charts below show what training on the full training sets buys and costs on each task: the macro-F1 on the test set, then the peak RAM during training.

{{< chart >}}
type: 'bar',
data: (() => {
  const dark = document.documentElement.classList.contains('dark');
  return {
    labels: ['CLINC', 'VAST', 'DynaSent'],
    datasets: [
      { label: 'TF-IDF + LR', data: [87.8, 32.9, 55.7], backgroundColor: dark ? '#898781' : '#898781' },
      { label: 'Ettin-17M', data: [89.3, 64.8, 62.4], backgroundColor: dark ? '#a77fe0' : '#7c4dcc' },
      { label: 'Ettin-32M', data: [90.3, 68.5, 65.4], backgroundColor: dark ? '#d4a72c' : '#b8860b' },
      { label: 'Ettin-68M', data: [91.7, 72.1, 67.6], backgroundColor: dark ? '#199e70' : '#1baf7a' },
      { label: 'Ettin-150M', data: [93.0, 75.5, 72.7], backgroundColor: dark ? '#3987e5' : '#2a78d6' },
      { label: 'Ettin-400M', data: [93.5, 79.1, 76.7], backgroundColor: dark ? '#e06bb0' : '#c2408c' }
    ]
  };
})(),
options: {
  aspectRatio: 1.8,
  plugins: { legend: { position: 'bottom', labels: { color: '#898781', usePointStyle: true, boxWidth: 8, boxHeight: 8, padding: 12 } } },
  scales: {
    x: { ticks: { color: '#898781' }, grid: { display: false } },
    y: { min: 0, max: 100, title: { display: true, text: 'macro-F1 on the test set', color: '#898781' }, ticks: { color: '#898781', stepSize: 20 }, grid: { color: document.documentElement.classList.contains('dark') ? 'rgba(148, 163, 184, 0.2)' : '#e1e0d9' } }
  }
}
{{< /chart >}}

<p class="caption">Macro-F1 on the test sets, after training on the full training sets. Ettin: mean of three seeds, one for Ettin-400M. On DynaSent's 720 test sentences, a model's 95% bootstrap interval spans about ±3.3 points: a point or two apart is a tie.</p>

{{< chart >}}
type: 'bar',
data: (() => {
  const dark = document.documentElement.classList.contains('dark');
  return {
    labels: ['CLINC', 'VAST', 'DynaSent'],
    datasets: [
      { label: 'TF-IDF + LR', data: [3.37, 0.93, 0.38], backgroundColor: dark ? '#898781' : '#898781' },
      { label: 'Ettin-17M', data: [1.95, 6.04, 2.18], backgroundColor: dark ? '#a77fe0' : '#7c4dcc' },
      { label: 'Ettin-32M', data: [2.06, 8.0, 3.3], backgroundColor: dark ? '#d4a72c' : '#b8860b' },
      { label: 'Ettin-68M', data: [3.36, 14.47, 4.72], backgroundColor: dark ? '#199e70' : '#1baf7a' },
      { label: 'Ettin-150M', data: [6.04, 20.61, 8.27], backgroundColor: dark ? '#3987e5' : '#2a78d6' },
      { label: 'Ettin-400M, gradient checkpointing', data: [9.48, 14.55, 10.23], backgroundColor: dark ? '#e06bb0' : '#c2408c' }
    ]
  };
})(),
plugins: [{
  id: 'laptopLines',
  afterDatasetsDraw: (chart) => {
    const { ctx, chartArea: a, scales: { y } } = chart;
    [[8, '8 GB laptop'], [16, '16 GB laptop'], [24, '24 GB, this laptop']].forEach(([v, text]) => {
      const py = y.getPixelForValue(v);
      ctx.save(); ctx.strokeStyle = '#898781'; ctx.lineWidth = 1; ctx.setLineDash([2, 4]);
      ctx.beginPath(); ctx.moveTo(a.left, py); ctx.lineTo(a.right, py); ctx.stroke();
      ctx.fillStyle = '#898781'; ctx.font = '12px sans-serif'; ctx.textAlign = 'right'; ctx.textBaseline = 'bottom';
      ctx.fillText(text, a.right - 6, py - 3); ctx.restore();
    });
  }
}],
options: {
  aspectRatio: 1.8,
  plugins: { legend: { position: 'bottom', labels: { color: '#898781', usePointStyle: true, boxWidth: 8, boxHeight: 8, padding: 12 } } },
  scales: {
    x: { ticks: { color: '#898781' }, grid: { display: false } },
    y: { min: 0, max: 28, title: { display: true, text: 'peak RAM during training, GB', color: '#898781' }, ticks: { color: '#898781', stepSize: 4 }, grid: { color: document.documentElement.classList.contains('dark') ? 'rgba(148, 163, 184, 0.2)' : '#e1e0d9' } }
  }
}
{{< /chart >}}

<p class="caption">Peak RAM of training on the full training sets, in GB, loading included. Ettin: mean of three seeds, one for Ettin-400M. Dotted lines: common laptop sizes.</p>

**The smallest encoder already beats TF-IDF everywhere.** Ettin-17M is 1.5 points ahead on intents (89.3 vs. 87.8), where the words give the answer away, and 6.7 on sentiment (62.4 vs. 55.7). On stance, it's 31.9 points ahead (64.8 vs. 32.9): even at 17M parameters, it reads the comment and the topic together, where my bag of n-grams, over the two pasted together, has no feature that ties one to the other.

**Why 21 GB for 150M parameters?** Because of VAST's long texts: the same model peaks at 6 GB on CLINC. Training keeps every layer's activations for the backward pass, and they grow with the tokens in a batch: 16 texts, padded to the longest, and a VAST comment has a median of 123 tokens, up to 270, against 11 for a CLINC request. Yet one step on the 16 longest comments needs 8.3 GB on the GPU: the rest is most likely PyTorch's allocator, which keeps the memory of earlier batches, of other shapes, for reuse.

**Ettin-400M doesn't fit, unless it recomputes.** Trained like the others, it passed 25 GB and sent the laptop into swap. With gradient checkpointing, PyTorch keeps only some of the activations, and recomputes the others during the backward pass. It changes nothing to the result: the gradients and the updates are the same, computed twice. The cost is time: on the 16 longest VAST comments, Ettin-150M needs 4.1 GB instead of 8.3, and 1.96 s per step instead of 1.49, 30% more. For Ettin-400M, one step on those 16 comments needs 8.1 GB. The whole training still peaks higher, 9.5 GB on CLINC and 14.6 on VAST: the allocator again. On VAST, its cache kept growing, about 1 GB of swap every 15 minutes, until I had it emptied every 50 steps and capped (`torch.mps.empty_cache()` and `PYTORCH_MPS_HIGH_WATERMARK_RATIO`): no slower, and the same updates.

**So why not always?** For the time, and because it has a floor: it only shrinks the activations, not the weights, their gradients and the optimizer's state, about 16 bytes per parameter in fp32 (2.4 GB at 150M, 6.4 GB at 400M). Above that floor, it's what lets a smaller machine fine-tune a bigger model, as do smaller batches with gradient accumulation, or shorter texts. Ettin 17M to 150M fit without it, so they train without it.

**Time.** Training takes from 3 minutes (Ettin-17M on CLINC) to 81 minutes (Ettin-150M on VAST). Ettin-400M takes about an hour on CLINC and DynaSent, and 4 hours 20 minutes on VAST. TF-IDF needs 16 seconds at most.

<div class="card card-grey">
<p class="card-kicker">Takeaway</p>
<p>On full training sets, bigger is better, steadily: each step up gains 0.5 to 5 points, on every task. Even 17M parameters is enough to read a relation, which is where TF-IDF fails. The catch is the RAM to train: with long texts, Ettin-68M and 150M need 14 to 21 GB, and Ettin-400M only fits with gradient checkpointing, which costs time, not quality.</p>
</div>

### With no labels: decision models

Labels are often the most expensive part: collecting the texts, then annotating them, one by one. A decision model skips that. Someone else trained it, once, on many tasks, and your labels are a list of options in its input. Here is each one, with the fine-tuned Ettin of the same size next to it:

<table class="grouped">
<thead><tr><th></th><th colspan="2">CLINC</th><th colspan="2">VAST</th><th colspan="2">DynaSent</th></tr>
<tr><th>Size</th><th>Fine-tuned</th><th>Decision model</th><th>Fine-tuned</th><th>Decision model</th><th>Fine-tuned</th><th>Decision model</th></tr></thead>
<tbody>
<tr><td>32M</td><td><span class="f1 f1-ref">90.3</span></td><td><span class="f1 f1-c">85.3</span></td><td><span class="f1 f1-ref">68.5</span></td><td><span class="f1 f1-b">65.5</span></td><td><span class="f1 f1-ref">65.4</span></td><td><span class="f1 f1-c">61.8</span></td></tr>
<tr><td>68M</td><td><span class="f1 f1-ref">91.7</span></td><td><span class="f1 f1-b">89.3</span></td><td><span class="f1 f1-ref">72.1</span></td><td><span class="f1 f1-b">69.3</span></td><td><span class="f1 f1-ref">67.6</span></td><td><span class="f1 f1-c">63.6</span></td></tr>
<tr><td>150M</td><td><span class="f1 f1-ref">93.0</span></td><td><span class="f1 f1-b">90.4</span></td><td><span class="f1 f1-ref">75.5</span></td><td><span class="f1 f1-a">75.4</span></td><td><span class="f1 f1-ref">72.7</span></td><td><span class="f1 f1-c">67.7</span></td></tr>
<tr><td>400M</td><td><span class="f1 f1-ref">93.5</span></td><td><span class="f1 f1-a">93.4</span></td><td><span class="f1 f1-ref">79.1</span></td><td><span class="f1 f1-a">78.3</span></td><td><span class="f1 f1-ref">76.7</span></td><td><span class="f1 f1-b">74.9</span></td></tr>
</tbody>
<tbody>
<tr><td>OneJev1.6-0.8B</td><td>—</td><td>92.4</td><td>—</td><td>74.5</td><td>—</td><td>63.2</td></tr>
<tr><td>OneJev1.6-4B</td><td>—</td><td>95.7</td><td>—</td><td>80.6</td><td>—</td><td>73.7</td></tr>
</tbody>
</table>

<p class="caption">Macro-F1 on the test sets. Fine-tuned: Ettin of that size on the full training set, mean of three seeds (one for 400M). Decision model, no labels: Amber of that size, or OneJev, in bf16. Each Amber is colored by its gap to the fine-tuned Ettin of its size, in <span class="f1 f1-ref">grey</span>: <span class="f1 f1-a">within 1 point</span> <span class="f1 f1-b">1 to 3 behind</span> <span class="f1 f1-c">3 to 6</span> <span class="f1 f1-d">over 6</span>.</p>

**At the same size, fine-tuning wins, by up to 5 points.** The gap is 2.4 to 5 points on CLINC and 3.6 to 5 on DynaSent, up to 150M. On VAST, it closes at 150M (75.5 vs. 75.4). At 400M, it narrows on CLINC and DynaSent (0.1 and 1.8 points), and reopens a little on VAST (0.8).

**A 400M encoder with no labels matches a fine-tuned 150M one.** Amber 400M gets 93.4, 78.3 and 74.9, against 93.0, 75.5 and 72.7 for Ettin-150M with its full training sets.

**And it beats an LLM twice its size.** Amber 400M is ahead of OneJev1.6-0.8B on all three tasks, by 1 to 12 points, and level with OneJev1.6-4B on DynaSent (74.9 vs. 73.7, within the noise). The 4B keeps the lead on CLINC and VAST (95.7 and 80.6).

**"No labels" needs a footnote.** No labels from you, but these models were trained on many public datasets. Amber's card lists CLINC150's training split among its sources (the Decision Index allows training splits, never test rows), and I can't rule out VAST's. OneJev doesn't publish its training data. DynaSent isn't in the Decision Index, and I found no sign that either family trained on it, though with OneJev's data private, I can't rule it out. It is the closest I have to your own task. Here is the gap to the fine-tuned Ettin of the same size, from the table above:

<table class="grouped">
<thead><tr><th>Size</th><th>CLINC</th><th>VAST</th><th>DynaSent</th></tr></thead>
<tbody>
<tr><td>32M</td><td><span class="f1 f1-c">5.0</span></td><td><span class="f1 f1-b">3.0</span></td><td><span class="f1 f1-c">3.6</span></td></tr>
<tr><td>68M</td><td><span class="f1 f1-b">2.4</span></td><td><span class="f1 f1-b">2.8</span></td><td><span class="f1 f1-c">4.0</span></td></tr>
<tr><td>150M</td><td><span class="f1 f1-b">2.6</span></td><td><span class="f1 f1-a">0.1</span></td><td><span class="f1 f1-c">5.0</span></td></tr>
<tr><td>400M</td><td><span class="f1 f1-a">0.1</span></td><td><span class="f1 f1-a">0.8</span></td><td><span class="f1 f1-b">1.8</span></td></tr>
</tbody>
</table>

<p class="caption">Points of macro-F1 between Amber, no labels, and the fine-tuned Ettin of its size: fine-tuned minus Amber. Colored as in the table above: <span class="f1 f1-a">within 1 point</span> <span class="f1 f1-b">1 to 3 behind</span> <span class="f1 f1-c">3 to 6</span> <span class="f1 f1-d">over 6</span>.</p>

On DynaSent, where I found no exposure, a decision encoder lands 2 to 5 points below fine-tuning. Up to 150M, that gap grows with size on DynaSent (3.6 to 5.0 points), where it shrinks on CLINC and VAST; at 400M, it falls to 1.8, so the trend stops at the top of the ladder. OneJev1.6-4B is 2.3 points ahead of Amber 400M on CLINC and VAST, and level with it on DynaSent (1.2 behind). With 720 test sentences, a few points is within the noise, so read it as a hint, not a measure: for a task of your own, the DynaSent column is a better guide than the CLINC one, but your task isn't DynaSent either.

<div class="card card-grey">
<p class="card-kicker">Takeaway</p>
<p>Without a single label from you, a decision encoder gets within 5 points of the fine-tuned encoder of its size, and Amber 400M matches a fine-tuned Ettin-150M. You no longer need a 4B LLM to classify without labels.</p>
</div>

### How many labels until fine-tuning wins?

Fine-tuning wins with the full training set: about 100 examples per intent on CLINC, about 4,400 per class on DynaSent. And with fewer? Here is DynaSent, the one with no exposure found, with the training set cut from 10 examples per class to the full set. The solid lines are the fine-tuned Ettins; the dotted lines, the Amber of the same size, with no labels:

{{< chart >}}
type: 'line',
data: (() => {
  const dark = document.documentElement.classList.contains('dark');
  const xs = [10, 25, 50, 100, 333, 1000, 4355];
  const line = (label, data, light, dk) => ({ label, data: data.map((y, i) => ({ x: xs[i], y })), borderColor: dark ? dk : light, backgroundColor: dark ? dk : light, borderWidth: 2, pointRadius: 5, pointHoverRadius: 7 });
  return {
    datasets: [
      line('Ettin-400M', [42.1, 48.5, 54.6, 59.2, 71.3, 74.3, 76.7], '#c2408c', '#e06bb0'),
      line('Ettin-150M', [42.9, 49.5, 55.5, 58.1, 67.9, 69.4, 72.7], '#2a78d6', '#3987e5'),
      line('Ettin-68M', [41.1, 46.2, 50.3, 56.6, 63.5, 65.6, 67.6], '#1baf7a', '#199e70'),
      line('Ettin-32M', [41.6, 45.8, 50.4, 54.8, 59.3, 64.1, 65.4], '#b8860b', '#d4a72c')
    ]
  };
})(),
plugins: [{
  id: 'amberLines',
  afterDatasetsDraw: (chart) => {
    const { ctx, chartArea: a, scales: { y } } = chart;
    const dark = document.documentElement.classList.contains('dark');
    [['Amber 400M, no labels', 74.9, '#c2408c', '#e06bb0', 'above'], ['Amber 150M, no labels', 67.7, '#2a78d6', '#3987e5', 'above'],
     ['Amber 68M, no labels', 63.6, '#1baf7a', '#199e70', 'above'], ['Amber 32M, no labels', 61.8, '#b8860b', '#d4a72c', 'below']].forEach(([text, v, light, dk, pos]) => {
      const py = y.getPixelForValue(v), color = dark ? dk : light;
      ctx.save();
      ctx.strokeStyle = color; ctx.lineWidth = 1.5; ctx.setLineDash([2, 4]);
      ctx.beginPath(); ctx.moveTo(a.left, py); ctx.lineTo(a.right, py); ctx.stroke();
      ctx.fillStyle = color; ctx.font = '12px sans-serif'; ctx.textAlign = 'left';
      ctx.textBaseline = pos === 'above' ? 'bottom' : 'top';
      ctx.fillText(text, a.left + 8, pos === 'above' ? py - 3 : py + 3);
      ctx.restore();
    });
  }
}],
options: {
  aspectRatio: 1.3,
  plugins: {
    legend: { position: 'bottom', labels: { color: '#898781', usePointStyle: true, boxWidth: 8, boxHeight: 8, padding: 16 } },
    tooltip: { callbacks: { label: (c) => c.dataset.label + ', fine-tuned: ' + c.parsed.y + ' macro-F1' } }
  },
  scales: {
    x: {
      type: 'logarithmic', min: 8, max: 5500,
      title: { display: true, text: 'labeled examples per class (DynaSent, log scale)', color: '#898781' },
      afterBuildTicks: (axis) => { axis.ticks = [10, 25, 50, 100, 333, 1000, 4355].map((value) => ({ value })); },
      ticks: { color: '#898781', maxRotation: 0, callback: (v) => v === 4355 ? 'all (4,355)' : v.toLocaleString('en-US') },
      grid: { display: false }
    },
    y: {
      min: 35, max: 80,
      title: { display: true, text: 'macro-F1 on the test set', color: '#898781' },
      ticks: { color: '#898781', stepSize: 5 },
      grid: { color: document.documentElement.classList.contains('dark') ? 'rgba(148, 163, 184, 0.2)' : '#e1e0d9' }
    }
  }
}
{{< /chart >}}

<p class="caption">Macro-F1 on DynaSent's test set. Fine-tuned: mean of three seeds up to 100 examples per class, one seed beyond. Same color, same size.</p>

**With my recipe, fine-tuning needs roughly a few hundred labels per class to catch the decision model of its size.** At 333 per class, Ettin-150M and Ettin-68M tie the Amber of their size (67.9 vs. 67.7, 63.5 vs. 63.6), Ettin-32M needs between 333 and 1,000, and Ettin-400M more than 1,000 (74.3 vs. 74.9 at 1,000). With 100 per class or fewer, every fine-tuned encoder is at least 7 points behind. Beyond 100 per class, each point is one seed, on a test set with a ±3.3 point interval: the crossovers are rough.

**The other two tasks move the crossover.** On CLINC, 50 to 100 examples per intent are enough (Ettin-150M gets 89.7 at 50 and 93.0 with the full set, against 90.4 for Amber 150M), but Amber has seen CLINC's training split. On VAST, fine-tuning needs the full set, about 4,500 per class, to pass Amber at 32M and 68M, and only ties it at 150M: with 1,000 per class, it is still 3 to 6 points behind.

<div class="card card-grey">
<p class="card-kicker">Takeaway</p>
<p>With no labels, or fewer than a few hundred per class, take a decision model: here, fine-tuning didn't catch it, except on CLINC, which Amber had seen. With more, fine-tune, for up to 5 points more at the same size. On stance, fine-tuning needed thousands per class.</p>
</div>

## What it costs to serve

Once a model is ready, what does it cost every time it classifies a text? Two measures:

- **[Peak RAM](#peak-ram):** the peak physical footprint of the process, loading included, what Activity Monitor shows.
- **[Latency](#latency):** the median time per text, the model already loaded. In batches, texts per second.

Other costs are left out. Storage, the weights on disk, from tens of MB to a few GB: RAM runs out long before the disk does. Power, what each prediction costs in energy, on a laptop's battery or a server's bill. And load time, how long a fresh process takes before its first answer, which matters when a service scales to zero or restarts often.

OneJev's latency and RAM come from llama.cpp, on the first 200 test texts of each task (on CLINC, they cover only 7 intents, but every prompt lists all 151). MLX was up to 1.8 times faster on the GPU, but took up to 10 times more RAM (18 GB for the 4B on VAST), and its CPU code for quantized weights is unusable: 29 minutes per sentence for the 4B in 8 bits. The encoders' numbers come from the first 1,000 test texts, or the full test sets.

For the sake of brevity, I only report the numbers that show each effect; the full benchmark is in the [repository](https://github.com/driquet/local-classification).

### First, does precision cost quality?

Precision is the one variable that could change the answers, so before what it saves, what it costs. One model of each kind at each of its precisions:

<table class="grouped">
<thead><tr><th></th><th>CLINC</th><th>VAST</th><th>DynaSent</th></tr></thead>
<tbody>
<tr><td>Ettin-150M, fp32, GPU</td><td><span class="f1 f1-ref">92.9</span></td><td><span class="f1 f1-ref">75.9</span></td><td><span class="f1 f1-ref">72.6</span></td></tr>
<tr><td>Ettin-150M, fp16, GPU</td><td><span class="f1 f1-a">92.9</span></td><td><span class="f1 f1-a">75.9</span></td><td><span class="f1 f1-a">72.6</span></td></tr>
<tr><td>Ettin-150M, int8, CPU</td><td><span class="f1 f1-a">92.8</span></td><td><span class="f1 f1-a">76.1</span></td><td><span class="f1 f1-a">72.6</span></td></tr>
</tbody>
<tbody>
<tr><td>Amber 150M, fp32, GPU</td><td><span class="f1 f1-ref">90.4</span></td><td><span class="f1 f1-ref">75.3</span></td><td><span class="f1 f1-ref">67.5</span></td></tr>
<tr><td>Amber 150M, bf16, GPU</td><td><span class="f1 f1-a">90.4</span></td><td><span class="f1 f1-a">75.4</span></td><td><span class="f1 f1-a">67.7</span></td></tr>
<tr><td>Amber 150M, int8, CPU</td><td><span class="f1 f1-a">90.5</span></td><td><span class="f1 f1-a">75.3</span></td><td><span class="f1 f1-a">68.0</span></td></tr>
</tbody>
<tbody>
<tr><td>OneJev1.6-0.8B, bf16</td><td><span class="f1 f1-ref">92.4</span></td><td><span class="f1 f1-ref">74.5</span></td><td><span class="f1 f1-ref">63.2</span></td></tr>
<tr><td>OneJev1.6-0.8B, 8-bit</td><td><span class="f1 f1-a">92.4</span></td><td><span class="f1 f1-a">74.5</span></td><td><span class="f1 f1-a">63.7</span></td></tr>
<tr><td>OneJev1.6-0.8B, 4-bit</td><td><span class="f1 f1-a">91.4</span></td><td><span class="f1 f1-a">74.2</span></td><td><span class="f1 f1-a">62.7</span></td></tr>
</tbody>
<tbody>
<tr><td>OneJev1.6-4B, bf16</td><td><span class="f1 f1-ref">95.7</span></td><td><span class="f1 f1-ref">80.6</span></td><td><span class="f1 f1-ref">73.7</span></td></tr>
<tr><td>OneJev1.6-4B, 8-bit</td><td><span class="f1 f1-a">95.8</span></td><td><span class="f1 f1-a">80.6</span></td><td><span class="f1 f1-a">74.0</span></td></tr>
<tr><td>OneJev1.6-4B, 4-bit</td><td><span class="f1 f1-a">95.6</span></td><td><span class="f1 f1-a">80.1</span></td><td><span class="f1 f1-a">73.4</span></td></tr>
</tbody>
</table>

<p class="caption">Macro-F1 on the test sets. OneJev: bf16 and 8 bits on MLX, 4 bits on llama.cpp (Q4_0); llama.cpp's 8 bits give the same answer as MLX's on 98.5 to 100% of the first 200 test texts (7 intents, on CLINC). Each value is colored by its drop against the first row of its block, in <span class="f1 f1-ref">grey</span>: <span class="f1 f1-a">up to 2 points</span> <span class="f1 f1-b">2 to 6</span> <span class="f1 f1-c">6 to 15</span> <span class="f1 f1-d">over 15</span>.</p>

<div class="card card-grey">
<p class="card-kicker">Takeaway</p>
<p>Fewer bits cost little here: at most 1 point, for OneJev1.6-0.8B in 4 bits on CLINC. So the rest of this section only asks what they save.</p>
</div>

### Peak RAM

Three things move the peak RAM: the device, the precision and the batch size. The length of the text barely does. The number of labels only does for the decision encoders, whose input holds every option.

#### Device and precision, on CLINC

One text at a time. The encoders first:

<table class="grouped">
<thead><tr><th></th><th colspan="2">⚙️ CPU</th><th colspan="2">⚡ GPU, process</th><th colspan="2">⚡ GPU, tensors</th></tr>
<tr><th></th><th>fp32</th><th>int8</th><th>fp32</th><th>16-bit</th><th>fp32</th><th>16-bit</th></tr></thead>
<tbody>
<tr><td>Ettin-17M</td><td><span class="f1 f1-ref">0.43</span></td><td><span class="f1 f1-a">0.12</span></td><td><span class="f1 f1-ref">1.43</span></td><td><span class="f1 f1-c">1.45</span></td><td><span class="f1 f1-ref">0.06</span></td><td><span class="f1 f1-b">0.03</span></td></tr>
<tr><td>Ettin-32M</td><td><span class="f1 f1-ref">0.49</span></td><td><span class="f1 f1-a">0.14</span></td><td><span class="f1 f1-ref">1.43</span></td><td><span class="f1 f1-c">1.46</span></td><td><span class="f1 f1-ref">0.12</span></td><td><span class="f1 f1-b">0.06</span></td></tr>
<tr><td>Ettin-68M</td><td><span class="f1 f1-ref">0.63</span></td><td><span class="f1 f1-a">0.19</span></td><td><span class="f1 f1-ref">1.44</span></td><td><span class="f1 f1-c">1.46</span></td><td><span class="f1 f1-ref">0.26</span></td><td><span class="f1 f1-b">0.13</span></td></tr>
<tr><td>Ettin-150M</td><td><span class="f1 f1-ref">0.95</span></td><td><span class="f1 f1-a">0.30</span></td><td><span class="f1 f1-ref">1.42</span></td><td><span class="f1 f1-c">1.46</span></td><td><span class="f1 f1-ref">0.56</span></td><td><span class="f1 f1-b">0.28</span></td></tr>
<tr><td>Ettin-400M</td><td><span class="f1 f1-ref">1.87</span></td><td><span class="f1 f1-a">0.73</span></td><td><span class="f1 f1-ref">2.43</span></td><td><span class="f1 f1-b">1.44</span></td><td><span class="f1 f1-ref">1.48</span></td><td><span class="f1 f1-b">0.74</span></td></tr>
</tbody>
<tbody>
<tr><td>Amber 32M</td><td><span class="f1 f1-ref">0.81</span></td><td><span class="f1 f1-a">0.22</span></td><td><span class="f1 f1-ref">1.85</span></td><td><span class="f1 f1-c">1.91</span></td><td><span class="f1 f1-ref">0.12</span></td><td><span class="f1 f1-b">0.06</span></td></tr>
<tr><td>Amber 68M</td><td><span class="f1 f1-ref">1.05</span></td><td><span class="f1 f1-a">0.31</span></td><td><span class="f1 f1-ref">2.10</span></td><td><span class="f1 f1-c">2.15</span></td><td><span class="f1 f1-ref">0.26</span></td><td><span class="f1 f1-b">0.13</span></td></tr>
<tr><td>Amber 150M</td><td><span class="f1 f1-ref">1.56</span></td><td><span class="f1 f1-a">0.43</span></td><td><span class="f1 f1-ref">2.55</span></td><td><span class="f1 f1-c">2.62</span></td><td><span class="f1 f1-ref">0.56</span></td><td><span class="f1 f1-b">0.28</span></td></tr>
<tr><td>Amber 400M</td><td><span class="f1 f1-ref">2.90</span></td><td><span class="f1 f1-a">0.88</span></td><td><span class="f1 f1-ref">3.60</span></td><td><span class="f1 f1-c">3.33</span></td><td><span class="f1 f1-ref">1.49</span></td><td><span class="f1 f1-b">0.74</span></td></tr>
</tbody>
<tbody>
<tr><td>TF-IDF + LR</td><td><span class="f1 f1-ref">0.29</span></td><td>—</td><td>—</td><td>—</td><td>—</td><td>—</td></tr>
</tbody>
</table>

<p class="caption">Peak RAM of the encoders on CLINC, in GB. "Process" is the whole process, what the system counts; "tensors" is what the model's tensors actually hold. 16-bit is fp16 for Ettin, bf16 for Amber. The CPU runs on one thread. Each value is colored by its ratio to fp32 on the same hardware, in <span class="f1 f1-ref">grey</span>: <span class="f1 f1-a">under 0.4×</span> <span class="f1 f1-b">0.4 to 0.75×</span> <span class="f1 f1-c">0.75 to 1.25×</span> <span class="f1 f1-d">over 1.25×</span>.</p>

On a CPU, int8 divides an encoder's RAM by three: up to 68M, a fine-tuned Ettin takes less than TF-IDF. On the GPU, PyTorch reserves memory in large blocks, so any encoder up to 150M costs about 1.4 GB, and 16 bits only halve the tensors. Amber takes more than the Ettin of its size because its input holds all 151 options: with DynaSent's three, Amber 150M in int8 needs 0.32 GB, not 0.43.

Then the LLMs, on llama.cpp:

<table class="grouped">
<thead><tr><th></th><th colspan="2">⚙️ CPU</th><th colspan="2">⚡ GPU</th></tr>
<tr><th></th><th>8-bit</th><th>4-bit</th><th>8-bit</th><th>4-bit</th></tr></thead>
<tbody>
<tr><td>OneJev1.6-0.8B</td><td><span class="f1 f1-ref">1.74</span></td><td><span class="f1 f1-c">1.33</span></td><td><span class="f1 f1-ref">1.72</span></td><td><span class="f1 f1-c">1.31</span></td></tr>
<tr><td>OneJev1.6-4B</td><td><span class="f1 f1-ref">6.13</span></td><td><span class="f1 f1-b">4.03</span></td><td><span class="f1 f1-ref">6.10</span></td><td><span class="f1 f1-b">3.99</span></td></tr>
</tbody>
</table>

<p class="caption">Peak RAM of the LLMs on CLINC, in GB, on the first 200 test texts. The CPU runs on four threads. Each value is colored by its ratio to 8 bits on the same hardware, in <span class="f1 f1-ref">grey</span>: <span class="f1 f1-a">under 0.4×</span> <span class="f1 f1-b">0.4 to 0.75×</span> <span class="f1 f1-c">0.75 to 1.25×</span> <span class="f1 f1-d">over 1.25×</span>.</p>

llama.cpp allocates everything up front: the same peak on both devices, whatever the task. 4 bits save 2 GB on the 4B, 0.4 GB on the 0.8B.

**Batches** of long texts cost RAM on a CPU: attention scores stay in fp32, so batches of 128 VAST comments add 3.9 GB to the int8 Ettin-150M's peak, against 0.9 GB on the GPU. Short texts batch freely.

<div class="card card-grey">
<p class="card-kicker">Takeaway</p>
<p>An int8 encoder on a CPU is the lightest, fine-tuned or not. On a GPU, any encoder pays a fixed overhead. An LLM needs gigabytes, whatever the device.</p>
</div>

### Latency

One variable at a time. Everything else stays at its default: one text at a time, fp32 on the GPU for the encoders, 8 bits on the GPU with llama.cpp for OneJev, and the CPU for TF-IDF.

#### Device

What does a GPU buy? The same model on the same texts, on the GPU and then on the CPU: how much slower each model gets without a GPU. On VAST, whose long comments give the computing its full weight:

<table class="grouped">
<thead><tr><th></th><th>⚡ GPU</th><th>⚙️ CPU</th><th>Slower by</th></tr></thead>
<tbody>
<tr><td>Ettin-17M</td><td><span class="f1 f1-ref">2.8</span></td><td><span class="f1 f1-c">3.0</span></td><td>1.1×</td></tr>
<tr><td>Ettin-32M</td><td><span class="f1 f1-ref">4.1</span></td><td><span class="f1 f1-d">6.5</span></td><td>1.6×</td></tr>
<tr><td>Ettin-68M</td><td><span class="f1 f1-ref">8.3</span></td><td><span class="f1 f1-d">18.2</span></td><td>2.2×</td></tr>
<tr><td>Ettin-150M</td><td><span class="f1 f1-ref">15.2</span></td><td><span class="f1 f1-d">37.4</span></td><td>2.5×</td></tr>
<tr><td>Ettin-400M</td><td><span class="f1 f1-ref">38.0</span></td><td><span class="f1 f1-d">93.7</span></td><td>2.5×</td></tr>
</tbody>
<tbody>
<tr><td>Amber 32M</td><td><span class="f1 f1-ref">4.5</span></td><td><span class="f1 f1-d">7.8</span></td><td>1.7×</td></tr>
<tr><td>Amber 68M</td><td><span class="f1 f1-ref">9.3</span></td><td><span class="f1 f1-d">21.9</span></td><td>2.4×</td></tr>
<tr><td>Amber 150M</td><td><span class="f1 f1-ref">29.8</span></td><td><span class="f1 f1-d">80.1</span></td><td>2.7×</td></tr>
<tr><td>Amber 400M</td><td><span class="f1 f1-ref">43.8</span></td><td><span class="f1 f1-d">112</span></td><td>2.6×</td></tr>
</tbody>
<tbody>
<tr><td>OneJev1.6-0.8B</td><td><span class="f1 f1-ref">48</span></td><td><span class="f1 f1-d">307</span></td><td>6.4×</td></tr>
<tr><td>OneJev1.6-4B</td><td><span class="f1 f1-ref">237</span></td><td><span class="f1 f1-d">1,768</span></td><td>7.5×</td></tr>
</tbody>
<tbody>
<tr><td>TF-IDF + LR</td><td>—</td><td>0.66</td><td>—</td></tr>
</tbody>
</table>

<p class="caption">Median latency per text on VAST, in ms. Encoders: the full test set on the GPU, its first 1,000 texts on the CPU. OneJev: the first 200. The CPU runs on one thread, four for OneJev. Each value is colored by its ratio to the GPU, in <span class="f1 f1-ref">grey</span>: <span class="f1 f1-a">under 0.6×</span> <span class="f1 f1-b">0.6 to 0.9×</span> <span class="f1 f1-c">0.9 to 1.1×</span> <span class="f1 f1-d">over 1.1×</span>.</p>

**On long texts, the GPU wins from 32M up, and halves the latency from 68M.** Each call seems to cost about 2 ms, whatever the model (I didn't profile it), so a model has to be big enough for the GPU's speed to pay that back. Ettin-17M isn't: 3.0 ms on the CPU, 2.8 on the GPU. On CLINC's shorter texts, the CPU even stays ahead up to 32M (1.0 ms against 2.1 for Ettin-17M). More threads don't help a single text: on four, Ettin-150M takes 35.4 ms, against 37.4 on one.

**With three options, a decision encoder costs about what a fine-tuned one does.** Amber 32M and 68M take about 10% longer than the Ettin of their size on the GPU. Amber 150M takes almost twice as long: it reads each request twice, with the options in two orders, and averages. The LLMs run on a CPU too, with llama.cpp: OneJev1.6-0.8B answers a DynaSent sentence in 0.16 s on four threads, the 4B in 0.9 s.

**Long texts cost 1.3 to 2 times more.** On the test sets, DynaSent's sentences have a median of 17 tokens, VAST's comments 122 (123 in training), both with three labels. Seven times more tokens make Ettin-17M 1.3 times slower on the GPU (2.1 to 2.8 ms), Ettin-150M 1.9 times (7.8 to 15.2) and OneJev1.6-4B 1.9 times (123 to 237): the small model mostly pays the cost of the call, the big ones the computing.

<div class="card card-grey">
<p class="card-kicker">Takeaway</p>
<p>On long texts in fp32, a GPU is faster from about 30M parameters, 2.2 to 2.7 times for the larger encoders. Below that, one CPU thread keeps up, and on short texts, an int8 encoder on a CPU can beat the GPU (4.0 vs. 7.6 ms for Ettin-150M on CLINC). An LLM runs on a CPU, 6.4 to 7.5 times slower than on the GPU.</p>
</div>

#### Labels

Why would the number of labels change the latency? A fine-tuned encoder reads the text once, and its last layer gives a score to every label at once: one more label is one more row in that layer. A decision model reads the labels: every option is part of its input. Amber reads the text and all the options in one sequence. OneJev lists them in its prompt, each behind a letter, and reads the probability of each letter. So more labels mean a longer input.

DynaSent's sentences and CLINC's requests are both short (medians of 17 and 11 tokens). What differs is the number of labels, 3 against 151:

<table class="grouped">
<thead><tr><th></th><th colspan="2">⚡ GPU</th><th colspan="2">⚙️ CPU</th></tr>
<tr><th></th><th>3 labels</th><th>151 labels</th><th>3 labels</th><th>151 labels</th></tr></thead>
<tbody>
<tr><td>Ettin-150M, fine-tuned</td><td><span class="f1 f1-ref">7.8</span></td><td><span class="f1 f1-a">7.6</span></td><td><span class="f1 f1-ref">6.6</span></td><td><span class="f1 f1-a">4.0</span></td></tr>
</tbody>
<tbody>
<tr><td>Amber 32M</td><td><span class="f1 f1-ref">3.2</span></td><td><span class="f1 f1-b">8.1</span></td><td><span class="f1 f1-ref">2.6</span></td><td><span class="f1 f1-d">53</span></td></tr>
<tr><td>Amber 68M</td><td><span class="f1 f1-ref">5.4</span></td><td><span class="f1 f1-b">17.9</span></td><td><span class="f1 f1-ref">6.6</span></td><td><span class="f1 f1-d">133</span></td></tr>
<tr><td>Amber 150M</td><td><span class="f1 f1-ref">10.4</span></td><td><span class="f1 f1-c">60.8</span></td><td><span class="f1 f1-ref">23.7</span></td><td><span class="f1 f1-d">483</span></td></tr>
<tr><td>Amber 400M</td><td><span class="f1 f1-ref">14.8</span></td><td><span class="f1 f1-c">69.9</span></td><td><span class="f1 f1-ref">26.3</span></td><td><span class="f1 f1-d">487</span></td></tr>
</tbody>
<tbody>
<tr><td>OneJev1.6-0.8B</td><td><span class="f1 f1-ref">29</span></td><td><span class="f1 f1-d">454</span></td><td><span class="f1 f1-ref">158</span></td><td><span class="f1 f1-d">3,091</span></td></tr>
<tr><td>OneJev1.6-4B</td><td><span class="f1 f1-ref">123</span></td><td><span class="f1 f1-d">2,147</span></td><td><span class="f1 f1-ref">921</span></td><td><span class="f1 f1-d">15,396</span></td></tr>
</tbody>
</table>

<p class="caption">Median latency per text, in ms, on DynaSent (3 labels) and CLINC (151). GPU: fp32 for Ettin, bf16 for Amber, 8 bits for OneJev. CPU: int8 on one thread for the encoders, 8 bits on four threads for OneJev. Each value is colored by its ratio to 3 labels, in <span class="f1 f1-ref">grey</span>: <span class="f1 f1-a">up to 1.25×</span> <span class="f1 f1-b">1.25 to 4×</span> <span class="f1 f1-c">4 to 10×</span> <span class="f1 f1-d">over 10×</span>.</p>

**A fine-tuned encoder doesn't care; a decision model reads every label.** From 3 to 151 labels, Amber gets 2.5 to 6 times slower on the GPU, and OneJev 15 to 18 times. On a CPU, every decision model gets 17 to 20 times slower: Amber 150M goes from 24 ms to half a second. In the first post, on MLX, OneJev1.6-4B grew by about 9 ms per intent, from 148 ms at 10 intents to 1.35 s on the full task, while Ettin-150M stayed at 7.7 ms.

<div class="card card-grey">
<p class="card-kicker">Takeaway</p>
<p>A fine-tuned encoder's latency doesn't depend on the number of labels. A decision model's does: with 151 labels, Amber 150M is 8 times slower than the fine-tuned Ettin-150M on a GPU, and 120 times on a CPU.</p>
</div>

#### Precision

Each kind of model at each of its precisions, on short and long texts:

<table class="grouped">
<thead><tr><th></th><th>DynaSent</th><th>VAST</th></tr></thead>
<tbody>
<tr><td>Ettin-17M, ⚡ GPU, fp32 → fp16</td><td><span class="f1 f1-ref">2.1</span> → <span class="f1 f1-d">2.4</span></td><td><span class="f1 f1-ref">2.8</span> → <span class="f1 f1-c">3.0</span></td></tr>
<tr><td>Ettin-150M, ⚡ GPU, fp32 → fp16</td><td><span class="f1 f1-ref">7.8</span> → <span class="f1 f1-c">7.6</span></td><td><span class="f1 f1-ref">15.2</span> → <span class="f1 f1-b">12.0</span></td></tr>
<tr><td>Ettin-17M, ⚙️ CPU, fp32 → int8</td><td><span class="f1 f1-ref">1.1</span> → <span class="f1 f1-b">0.7</span></td><td><span class="f1 f1-ref">3.0</span> → <span class="f1 f1-d">4.1</span></td></tr>
<tr><td>Ettin-150M, ⚙️ CPU, fp32 → int8</td><td><span class="f1 f1-ref">14.7</span> → <span class="f1 f1-a">6.6</span></td><td><span class="f1 f1-ref">37.4</span> → <span class="f1 f1-c">39.5</span></td></tr>
</tbody>
<tbody>
<tr><td>Amber 150M, ⚡ GPU, fp32 → bf16</td><td><span class="f1 f1-ref">11.3</span> → <span class="f1 f1-c">10.4</span></td><td><span class="f1 f1-ref">29.8</span> → <span class="f1 f1-b">21.0</span></td></tr>
<tr><td>Amber 400M, ⚡ GPU, fp32 → bf16</td><td><span class="f1 f1-ref">19.7</span> → <span class="f1 f1-b">14.8</span></td><td><span class="f1 f1-ref">43.8</span> → <span class="f1 f1-a">24.8</span></td></tr>
<tr><td>Amber 150M, ⚙️ CPU, fp32 → int8</td><td><span class="f1 f1-ref">26.4</span> → <span class="f1 f1-b">23.7</span></td><td><span class="f1 f1-ref">80.1</span> → <span class="f1 f1-d">92.2</span></td></tr>
<tr><td>Amber 400M, ⚙️ CPU, fp32 → int8</td><td><span class="f1 f1-ref">52.7</span> → <span class="f1 f1-a">26.3</span></td><td><span class="f1 f1-ref">112</span> → <span class="f1 f1-b">98.5</span></td></tr>
</tbody>
<tbody>
<tr><td>OneJev1.6-4B, ⚡ GPU, 8 → 4 bits</td><td><span class="f1 f1-ref">123</span> → <span class="f1 f1-c">123</span></td><td><span class="f1 f1-ref">237</span> → <span class="f1 f1-c">236</span></td></tr>
<tr><td>OneJev1.6-4B, ⚙️ CPU, 8 → 4 bits</td><td><span class="f1 f1-ref">921</span> → <span class="f1 f1-c">854</span></td><td><span class="f1 f1-ref">1,768</span> → <span class="f1 f1-c">1,652</span></td></tr>
</tbody>
</table>

<p class="caption">Median latency per text, in ms. Each value is colored by its ratio to the highest precision of the same model, in <span class="f1 f1-ref">grey</span>: <span class="f1 f1-a">under 0.6×</span> <span class="f1 f1-b">0.6 to 0.9×</span> <span class="f1 f1-c">0.9 to 1.1×</span> <span class="f1 f1-d">over 1.1×</span>.</p>

**16 bits on a GPU help long inputs; int8 on a CPU, short ones.** fp16 makes the small encoders up to 13% slower, but Ettin-150M faster on VAST (12.0 ms against 15.2), and Amber, whose inputs are longer, up to 1.8 times faster. int8 makes a fine-tuned Ettin 1.4 to 2.2 times faster on DynaSent, and slower on VAST: 6% for Ettin-150M, 37% for Ettin-17M. Mind that int8 also changes the runtime, from PyTorch to ONNX Runtime: these rows compare two setups, not the precision alone. For the LLMs, 4 bits are at most 7% faster than 8.

**This one surprised me:** I expected fewer bits to mean faster predictions. My guess, not profiled: they mostly shrink what is read from memory, and memory is rarely the bottleneck here: the small encoders mostly pay the fixed cost of each call, the LLMs read their prompt in one pass without generating, and int8 leaves attention, which dominates long inputs, in fp32.

<div class="card card-grey">
<p class="card-kicker">Takeaway</p>
<p>Here, fewer bits saved memory more than time. Two exceptions: int8 on a CPU, up to twice as fast on short inputs, and 16 bits on a GPU, up to twice as fast on long ones.</p>
</div>

#### Batching

A backlog (a day of tickets, a whole dataset) can go in batches, and then what counts is how many texts per second. I measured it on the fine-tuned Ettin-17M and Ettin-150M, in fp16 on the GPU and int8 on one CPU thread, in batches of 8 to 128 texts sorted by length.

**The GPU gains 10 to 14 times on short texts.** On CLINC, Ettin-150M goes from 145 to 1,501 texts per second, and Ettin-17M from 449 to 6,127. One text at a time, the GPU spends most of its time on the cost of each call, and a batch pays that once. Long texts gain less, 1.8 to 5 times on VAST: computing dominates them.

**The CPU gains little:** 1.4 to 1.6 times on short texts, nothing on long ones. A batch saves it the cost of each call, which is small, not the computing.

I didn't batch TF-IDF, already under a millisecond per text, or the decision models.

<div class="card card-grey">
<p class="card-kicker">Takeaway</p>
<p>For a backlog, batch on a GPU. A million short texts take Ettin-150M 11 minutes on the GPU, against 54 in int8 on one CPU thread.</p>
</div>

## Caveats

- **One laptop.** An Apple M5, with fast unified memory and a fast CPU. A cloud vCPU may well be slower: benchmark your target hardware. And PyTorch on the MPS GPU is not CUDA.
- **Seeds.** Three seeds for the full sets of Ettin 17M to 150M; one for Ettin-400M, for each serving variant and for the decision models. On DynaSent, a model's 95% bootstrap interval is about ±3.3 points.
- **Ettin-400M.** Its learning rate (3e-5) isn't swept. It trains with gradient checkpointing, and on VAST with PyTorch's GPU cache emptied every 50 steps and capped.
- **"No labels" isn't "never seen".** Amber trained on CLINC150's training split, among many datasets, and OneJev's training data isn't public. And each Amber starts from an Ettin reranker, not the plain Ettin. Amber's weights are under a non-commercial licence (CC BY-NC 4.0).
- **One quantization method each.** Dynamic int8 with ONNX Runtime for the encoders, llama.cpp's Q8_0 and Q4_0 for the LLMs (and MLX's, for one comparison). Static int8, 4-bit encoders or other runtimes could change both the latency and the quality.

## What's next

- **Distillation.** A decision model labels the training set, a small encoder learns from it: no labels from you, and the serving cost of a fine-tuned encoder. That's [the next post](/distilling-a-classifier/).
- **A decision encoder, plus a few labels?** Amber needs none, and fine-tuning needs hundreds. Fine-tuning Amber itself on 10 to 100 labels per class could beat both.
- **Fine-tune or optimize the prompt?** Same tasks: plain vs. GEPA-optimized prompt, base vs. LoRA weights.
- **Few labels, a frozen sentence encoder?** A ready-made embedding model with a logistic regression on top, trained in seconds, or SetFit, which first fine-tunes it on pairs of examples.

## Related reading

- [Seq vs Seq: An Open Suite of Paired Encoders and Decoders](https://arxiv.org/abs/2507.11412), by Orion Weller et al. (2025). The Ettin paper: encoders and decoders from 17M to 1B parameters, trained the same way, which is what makes Ettin a clean size ladder.
- [Smarter, Better, Faster, Longer: A Modern Bidirectional Encoder for Fast, Memory Efficient, and Long Context Finetuning and Inference](https://arxiv.org/abs/2412.13663), by Benjamin Warner et al. (2024). ModernBERT, whose architecture Ettin reuses.
- [An Evaluation Dataset for Intent Classification and Out-of-Scope Prediction](https://arxiv.org/abs/1909.02027), by Stefan Larson et al. (2019). CLINC150: 150 intents and out-of-scope requests.
- [Zero-Shot Stance Detection: A Dataset and Model using Generalized Topic Representations](https://arxiv.org/abs/2010.03640), by Emily Allaway and Kathleen McKeown (2020). VAST: stance toward thousands of topics, many seen only at test time.
- [DynaSent: A Dynamic Benchmark for Sentiment Analysis](https://arxiv.org/abs/2012.15349), by Christopher Potts et al. (2021). Sentences written by people to fool a sentiment model.
- The model cards of [Amber 400M](https://huggingface.co/MLukauskas/amber-0.4b-v2) and [OneJev1.6-4B](https://huggingface.co/OmniJev/OneJev1.6-4B): how each was trained, and on what.
- [Decision Index](https://huggingface.co/spaces/multimodalart/jev-decision-index). The public leaderboard of decision models, where Amber and OneJev come from: 42 benchmarks, CLINC150 and VAST among them.
