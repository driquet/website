---
title: "Do You Need an LLM for That? Classifying Text Locally"
date: 2026-11-01T10:00:00+01:00
tags: ["AI", "LLM", "Classification", "Benchmark"]
showTableOfContents: true
---

<!-- Results: run of 2026-10-30/31 (experiments/do-you-need-an-llm/results/results.csv, 129 runs), Decision Index 0.4.1 (data of 2026-10-29). Part 2: /how-small-can-a-classifier-be/. -->

{{< lead >}}
Three tasks, four approaches, one laptop. Counting labels tells you less than you think; reading the task tells you more.
{{< /lead >}}

One of the things that keeps me up at night is a simple question: what is the best way to classify text on my own machine? And, now that LLMs are everywhere, do I even need one? More generally: what should I do when the environment is constrained, with little RAM, no GPU, or a tight latency budget?

The reflex in 2026 is to paste the label list into a prompt and ask an LLM. It works, sort of, and you never have to train anything. But text classification is an old problem. A bag of words and a logistic regression have been doing it for twenty years, and small fine-tuned encoders like BERT have been doing it very well for the last eight. They are cheaper, faster, and they fit in a few hundred megabytes. So before reaching for a 4-billion-parameter model, it's worth checking what it actually buys you.

Four questions:

1. **Does the number of classes change the answer?** (CLINC150, from 10 to 150 intents) Listing 10 labels in a prompt is easy; listing 150 is not. Does prompting fall apart as labels are added, and do trained models care?
2. **Or is it the kind of task?** (VAST, then DynaSent) Some tasks are given away by their words, others are not. Which approach survives when they are not?
3. **How many labels does a trained model need?** To beat a prompt that needs none, on each of the three tasks.
4. **What does each approach cost?** Not only quality: labeled data, training time, latency, and RAM once deployed.

One rule: everything runs on my laptop (Apple M5, 24 GB of unified memory). All the code is on GitHub: [driquet/local-classification](https://github.com/driquet/local-classification).

A word of warning: this is a personal weekend project, so I kept it to the minimum. One seed, one prompt, no tuning: that's not how a paper would do it, but it's enough to get the gist. I'm also the kind of person who needs to tweak and hack things to understand how they work, and I'm convinced every insight in this post is already covered somewhere in the literature (a few pointers at the end). This is me finding it out by hand.

<div class="card card-green">
<p class="card-kicker">TL;DR · in a hurry?</p>
<p class="card-title"><a href="#so-do-you-need-an-llm">Jump to the answer →</a></p>
<p>What I would use, depending on your labels, your constraints and your task, with a decision tree.</p>
</div>

## The contestants

One per approach, from the oldest trick in the book to an LLM trained to make decisions:

<div class="card-grid card-grid-2">
<div class="card card-grey">
<p class="card-kicker">Classic · labels</p>
<p class="card-title">TF-IDF + logistic regression</p>
<p>Bag of words, linear model. No GPU, trains in seconds.</p>
</div>
<div class="card card-blue">
<p class="card-kicker">Encoder · labels</p>
<p class="card-title">Ettin-150M</p>
<p>A small transformer, fine-tuned with a classification head.</p>
</div>
<div class="card card-orange">
<p class="card-kicker">Prompt · no or few labels</p>
<p class="card-title">Qwen3.5-4B, zero-shot and few-shot</p>
<p>A prompt listing the labels, with or without a few examples per class.</p>
</div>
<div class="card card-purple">
<p class="card-kicker">Decision model · no labels</p>
<p class="card-title">OneJev1.6-4B</p>
<p>The same Qwen3.5-4B, trained by its authors to pick among options.</p>
</div>
</div>

**TF-IDF + logistic regression.** Each text becomes a sparse vector of word and character n-gram weights, and a linear classifier does the rest. This is the floor: anything more expensive has to beat it to earn its keep.

**[Ettin-150M](https://huggingface.co/jhu-clsp/ettin-encoder-150m)**, fine-tuned. Ettin is a family of encoders from 17M to 1B parameters trained with the same data and recipe; 150M is the classic BERT-base size. 3 epochs, batch size 16, learning rate 5e-5, gradients clipped at 1.0, and at least 200 steps, so that tiny training sets still get enough updates to move the classification head ([Mosbach et al., 2021](https://arxiv.org/abs/2006.04884)). This is the textbook answer when you have labels. (Which size to pick will be addressed in a future post.)

**[Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B)**, prompted, in BF16 with [MLX](https://github.com/ml-explore/mlx), thinking off. I don't use a quantized version, so that quantization can't affect the F1 scores. The price is paid in RAM and disk (and a bit in latency), as the cost section shows. Instead of generating text and parsing it, I read the probability the model gives to each label, so the answer is always a valid label. Two prompts:

- **Zero-shot:** the prompt lists the labels and asks for one. No labeled data at all.
- **Few-shot:** the same prompt plus labeled examples from the training set, drawn at random: one per class when there are many classes, five when there are few. Every text gets the same examples, placed first, so the model reads them once and keeps them in its cache.

**[OneJev1.6-4B](https://huggingface.co/OmniJev/OneJev1.6-4B)**, an open decision model released in October 2026, built on the same Qwen3.5-4B. Its authors fine-tuned it to read a text and a list of options and return a probability for each, in one forward pass. I run it with the same MLX pipeline and the Decision Index's wording, and my runs match the index's scores within a tenth of a point (95.7 vs. 95.8 on CLINC, 80.6 vs. 80.7 on VAST). No training on my side, and no few-shot (its format has no slot for examples).

OneJev reports its scores on the [Decision Index](https://huggingface.co/spaces/multimodalart/jev-decision-index), a community leaderboard of over 240 "decision models" that try to reproduce Jev, TypeSafe's decision model. The index has two of my three tasks, CLINC with out-of-scope and VAST, and I score them exactly as it does. It gives me two reference points, drawn as dotted lines on the charts:

| Decision Index 0.4.1 | CLINC150 + out-of-scope | VAST |
|---|---|---|
| Jev | 90.3 | 73.7 |
| Best entrant | 97.6 (mammoth-1, baselabs, 27B) | 84.2 (Jeffan-31b, tattrongvu, 31B) |

## How I measured

- **Splits:** all three tasks use their official train and test splits.
- **Quality:** macro-F1 on the test set, so every class counts the same, as on the Decision Index.
- **Cost:** labeled examples used, training time, median latency per text at batch size 1, peak memory while predicting. All on the laptop, other GPU-heavy apps closed: TF-IDF on the CPU, Ettin on the GPU (PyTorch MPS), the 4B models on the GPU with MLX.
- **One seed:** each full training run and each few-shot draw happens once. Learning curves average three draws of the training examples up to 100 per class. Two numbers within a point are a tie, and on DynaSent, whose test set has only 720 sentences, within three.

## Does the number of classes matter? CLINC150

[CLINC150](https://github.com/clinc/oos-eval) is an intent classification dataset: short requests to a voice assistant, each filed under one of **150 intents** spread over 10 domains (banking, travel, kitchen, work, and so on), plus an *out-of-scope* class for requests that match none of them.

| Request | Intent |
|---|---|
| *"how do i put in a pto request for the first to the ninth"* | `pto_request` |
| *"can you explain to me what type of vacation days i have still"* | `pto_balance` |
| *"have i used half of my days off yet"* | `pto_used` |
| *"wake me up at noon tomorrow"* | `alarm` |
| *"what size wipers does this car take"* | out-of-scope |

Every intent has exactly 100 training and 30 test examples, which lets me cut the task down without changing anything else: I keep 10, 25, 50 or 100 intents and drop the others, and end with the full task, 150 intents plus out-of-scope. Which 10 intents you draw matters (ten banking intents is harder than ten from different domains), so at 10 and 25 I draw three sets and report the average.

For the prompts, intent names are made readable (`pto_request` becomes "pto request"), and few-shot gets one random example per intent: 151 on the full task, about 3,000 tokens. An intent keeps the same example in every slice, so the curve isn't also a curve of different draws.

Macro-F1 on CLINC as intents are added. The last point is the full task, with the out-of-scope class. The two dotted lines are the Decision Index scores for Jev and the best entrant. The index has no slices, so compare them with the last point only:

{{< chart >}}
type: 'line',
data: {
  labels: ['10', '25', '50', '100', '150 + OOS'],
  datasets: [
    {
      label: 'OneJev1.6-4B',
      data: [99.6, 98.9, 98.1, 97.9, 95.7],
      borderColor: document.documentElement.classList.contains('dark') ? '#a77fe0' : '#7c4dcc',
      backgroundColor: document.documentElement.classList.contains('dark') ? '#a77fe0' : '#7c4dcc',
      borderWidth: 2, pointRadius: 5, pointHoverRadius: 7
    },
    {
      label: 'Ettin-150M',
      data: [98.8, 98.9, 97.8, 97.3, 93.2],
      borderColor: document.documentElement.classList.contains('dark') ? '#3987e5' : '#2a78d6',
      backgroundColor: document.documentElement.classList.contains('dark') ? '#3987e5' : '#2a78d6',
      borderWidth: 2, pointRadius: 5, pointHoverRadius: 7
    },
    {
      label: 'TF-IDF + LR',
      data: [99.2, 98.6, 95.4, 93.8, 87.8],
      borderColor: '#898781',
      backgroundColor: '#898781',
      borderDash: [6, 4],
      borderWidth: 2, pointRadius: 5, pointHoverRadius: 7
    },
    {
      label: 'Qwen3.5-4B, few-shot',
      data: [97.6, 95.7, 92.3, 89.7, 79.0],
      borderColor: document.documentElement.classList.contains('dark') ? '#f2905f' : '#a8431c',
      backgroundColor: document.documentElement.classList.contains('dark') ? '#f2905f' : '#a8431c',
      borderWidth: 2, pointRadius: 5, pointHoverRadius: 7
    },
    {
      label: 'Qwen3.5-4B, zero-shot',
      data: [95.5, 94.5, 89.7, 87.2, 79.7],
      borderColor: document.documentElement.classList.contains('dark') ? '#d95926' : '#eb6834',
      backgroundColor: document.documentElement.classList.contains('dark') ? '#d95926' : '#eb6834',
      borderWidth: 2, pointRadius: 5, pointHoverRadius: 7
    },
    {
      label: 'Best entrant (index)',
      data: [97.6, 97.6, 97.6, 97.6, 97.6],
      borderColor: '#2e9e6b',
      backgroundColor: '#2e9e6b',
      borderDash: [2, 4],
      borderWidth: 1.5, pointRadius: 0, pointHoverRadius: 0
    },
    {
      label: 'Jev (index)',
      data: [90.3, 90.3, 90.3, 90.3, 90.3],
      borderColor: '#b8a03a',
      backgroundColor: '#b8a03a',
      borderDash: [2, 4],
      borderWidth: 1.5, pointRadius: 0, pointHoverRadius: 0
    }
  ]
},
options: {
  aspectRatio: 1.3,
  plugins: {
    legend: { position: 'bottom', labels: { color: '#898781', usePointStyle: true } },
    tooltip: { callbacks: { label: (c) => c.dataset.label + ': ' + c.parsed.y + ' macro-F1' } }
  },
  scales: {
    x: {
      title: { display: true, text: 'number of intents', color: '#898781' },
      ticks: { color: '#898781' }, grid: { display: false }
    },
    y: {
      min: 75, max: 100,
      title: { display: true, text: 'macro-F1 on the test set', color: '#898781' },
      ticks: { color: '#898781', stepSize: 5 },
      grid: { color: document.documentElement.classList.contains('dark') ? '#2c2c2a' : '#e1e0d9' }
    }
  }
}
{{< /chart >}}

**More classes hurt the prompt, much less the encoder.** With 10 intents, zero-shot Qwen gets 95.5 without any training example. At 100 intents it has lost 8.3 points, and it ends at 79.7 on the full task. Ettin-150M only loses 1.5 points from 10 to 100 intents. I see two reasons. The label list in the prompt gets longer (from about 30 to 470 tokens). And more intents means more neighbors that are hard to separate, like `pto_request`, `pto_balance` and `pto_used`. The choice of intents matters too: at 10 intents, zero-shot Qwen goes from 92.9 to 99.3 depending on the draw.

**One random example per intent helps, but not on the full task.** Few-shot Qwen is one to three points above zero-shot up to 100 intents: seeing one "pto balance" request helps to tell it from "pto used". On the full task, the gain is gone (79.0 vs. 79.7, a tie). I think one random out-of-scope example can't explain what "none of the above" means, and 151 examples (about 3,000 tokens) bury the label list. In any case, both prompts stay below TF-IDF at every size.

**The decision model holds, like the encoder.** OneJev1.6-4B is the same Qwen, trained to pick among options. It starts at 99.6, loses 1.7 points up to 100 intents, and ties the best trained model on every slice. On the full task it is ahead (95.7), and I gave it no labels. So the problem is not the LLM itself, it's the generic prompt. One reservation: OneJev has seen some CLINC150 training examples (see the caveats).

**TF-IDF is better than its reputation.** Up to 25 intents it matches the encoder. From 50 intents it falls behind, because more intents share the same words. Intents are mostly about words: "time off" means PTO.

The out-of-scope class is where the full task gets hard. F1 on that class alone: 92.5 for OneJev, 78.1 for Ettin, 76.7 for zero-shot Qwen, 72.1 for few-shot Qwen and TF-IDF.

<div class="card card-grey">
<p class="card-kicker">Takeaway</p>
<p>More classes hurt a generic prompt, not a trained model or a decision model. But on CLINC, the words give the intent away. What happens when they don't?</p>
</div>

## Or is it the kind of task? VAST

[VAST](https://github.com/emilyallaway/zero-shot-stance) is a stance detection dataset: given a New York Times comment and a topic, is the comment **for**, **against**, or **neutral** about that topic?

| Comment | Topic | Stance |
|---|---|---|
| *"Just wish them both well and give them a fair chance. Princess Diana's verve and spirit made her a superstar, and she used her celebrity to do real good in the world. I hope this will happen with William and Kate as well."* | princess diana | for |
| *(same comment as above)* | employer's first impression | neutral |
| *"A person who cares more about their furniture than they do about their cat shouldn't have a pet in the first place."* | animal cruelty | against |

Only three readable labels. But most test topics never appear in training, and the stance is not in the words, it's in how the comment relates to the topic: the first two rows are the same comment. That makes VAST the counterpoint to CLINC: few classes, hard task.

Few-shot gets five random examples per stance, 15 in total. By the logic of CLINC, three classes should be easy. Macro-F1 on the test set, with the same dotted lines as on the CLINC chart:

{{< chart >}}
type: 'bar',
data: {
  labels: ['TF-IDF', 'Qwen zero-shot', 'Qwen few-shot', 'Ettin', 'OneJev'],
  datasets: [
    {
      label: 'Macro-F1',
      data: [32.9, 54.0, 52.1, 75.8, 80.6],
      backgroundColor: [
        '#898781',
        document.documentElement.classList.contains('dark') ? '#d95926' : '#eb6834',
        document.documentElement.classList.contains('dark') ? '#f2905f' : '#a8431c',
        document.documentElement.classList.contains('dark') ? '#3987e5' : '#2a78d6',
        document.documentElement.classList.contains('dark') ? '#a77fe0' : '#7c4dcc'
      ],
      borderWidth: 0,
      borderRadius: 3
    }
  ]
},
plugins: [{
  id: 'indexLines',
  afterDatasetsDraw: (chart) => {
    const { ctx, chartArea: a, scales: { y } } = chart;
    [['Best entrant (index): 84.2', 84.2, '#2e9e6b'], ['Jev (index): 73.7', 73.7, '#b8a03a']].forEach(([text, v, color]) => {
      const py = y.getPixelForValue(v);
      ctx.save();
      ctx.strokeStyle = color; ctx.lineWidth = 1.5; ctx.setLineDash([2, 4]);
      ctx.beginPath(); ctx.moveTo(a.left, py); ctx.lineTo(a.right, py); ctx.stroke();
      ctx.fillStyle = color; ctx.font = '12px sans-serif'; ctx.textAlign = 'left'; ctx.textBaseline = 'bottom';
      ctx.fillText(text, a.left + 4, py - 3);
      ctx.restore();
    });
  }
}],
options: {
  aspectRatio: 1.3,
  plugins: {
    legend: { display: false },
    tooltip: { callbacks: { label: (c) => c.dataset.label + ': ' + c.parsed.y + (c.datasetIndex === 0 ? ' (' + ['13,477 labels', '0 labels', '15 labels', '13,477 labels', '0 labels'][c.dataIndex] + ')' : '') } }
  },
  scales: {
    x: {
      ticks: { color: '#898781', maxRotation: 0, autoSkip: false }, grid: { display: false }
    },
    y: {
      min: 0, max: 100,
      title: { display: true, text: 'macro-F1 on the VAST test set', color: '#898781' },
      ticks: { color: '#898781', stepSize: 20 },
      grid: { color: document.documentElement.classList.contains('dark') ? '#2c2c2a' : '#e1e0d9' }
    }
  }
}
{{< /chart >}}

**TF-IDF is at chance**, and almost never predicts "neutral". A bag of words sees which words are there, not if the comment talks about the topic.

**The encoder reads the pair.** After one hour of fine-tuning on the full training set, Ettin-150M gets 75.8, above Jev. "Neutral" even becomes its easiest class (88): once you compare comment and topic, an unrelated comment is easy to spot. The hard part is "for" vs. "against" on a topic never seen in training (68 and 72).

**Prompting is in between, and random examples don't help.** Zero-shot Qwen does read the topic (47 on "neutral") but is 22 points behind the encoder. With fifteen random examples, "neutral" improves (55), but "for" and "against" lose as much, and the total drops two points. None of the examples is about the test topic. OneJev is above everything (80.6), with no labels from me.

Latency is higher than on CLINC, as comments are longer: 15.6 ms per text for Ettin, 166 ms for OneJev, 195 ms for zero-shot Qwen.

<div class="card card-grey">
<p class="card-kicker">Takeaway</p>
<p>Three classes are not enough to make a task easy. When the answer is in the relation between comment and topic, the prompt is far behind, and the encoder needs to be trained on it. And what if the words are there, but lie?</p>
</div>

## When the words lie: DynaSent

[DynaSent](https://github.com/cgpotts/dynasent) is a sentiment dataset: is a sentence about a restaurant or a shop **positive**, **negative**, or **neutral**? Easy, except for how it was built. In its second round, which I use, crowdworkers wrote sentences meant to fool a fine-tuned sentiment model (RoBERTa); about one in five did, and the dataset keeps every attempt, validated by five other workers:

| Sentence | Sentiment |
|---|---|
| *"I would never not recommend this place."* | positive |
| *"You would have to be a terrible person to have a bad time here."* | positive |
| *"Every variation has been so good at being bad."* | negative |
| *"They gratefully charge 5% more and do an amazing NOTHING extra."* | negative |
| *"I have learned how to avoid the smokes"* | neutral |

The words are all there, they just point the wrong way. That's the third case: not words that give the answer away (CLINC), not an answer hidden in a relation (VAST), but words that lie.

Few-shot gets 15 examples here too. The Decision Index has no DynaSent, so there are no dotted lines on the chart, and for OneJev I worded the request like the index's VAST one. Macro-F1 on the test set:

{{< chart >}}
type: 'bar',
data: {
  labels: ['TF-IDF', 'Qwen zero-shot', 'Qwen few-shot', 'Ettin', 'OneJev'],
  datasets: [
    {
      label: 'Macro-F1',
      data: [55.7, 75.7, 74.3, 73.0, 73.7],
      backgroundColor: [
        '#898781',
        document.documentElement.classList.contains('dark') ? '#d95926' : '#eb6834',
        document.documentElement.classList.contains('dark') ? '#f2905f' : '#a8431c',
        document.documentElement.classList.contains('dark') ? '#3987e5' : '#2a78d6',
        document.documentElement.classList.contains('dark') ? '#a77fe0' : '#7c4dcc'
      ],
      borderWidth: 0,
      borderRadius: 3
    }
  ]
},
options: {
  aspectRatio: 1.3,
  plugins: {
    legend: { display: false, position: 'bottom', labels: { color: '#898781', usePointStyle: true, filter: (item) => item.text !== 'Macro-F1' } },
    tooltip: { callbacks: { label: (c) => c.dataset.label + ': ' + c.parsed.y + (c.datasetIndex === 0 ? ' (' + ['13,065 labels', '0 labels', '15 labels', '13,065 labels', '0 labels'][c.dataIndex] + ')' : '') } }
  },
  scales: {
    x: {
      ticks: { color: '#898781', maxRotation: 0, autoSkip: false }, grid: { display: false }
    },
    y: {
      min: 0, max: 100,
      title: { display: true, text: 'macro-F1 on the DynaSent test set', color: '#898781' },
      ticks: { color: '#898781', stepSize: 20 },
      grid: { color: document.documentElement.classList.contains('dark') ? '#2c2c2a' : '#e1e0d9' }
    }
  }
}
{{< /chart >}}

**TF-IDF picks up some signal, but not enough.** Sentiment words still help a bag of words. But it can't read "never not recommend" or "so good at being bad", and it ends 17 to 20 points behind the others.

**The four others are tied.** They are within 2.7 points, and on this test set three points is noise. Zero-shot Qwen, with no labels and a two-line prompt, does as well as an encoder trained on all 13,065 sentences. OneJev loses the lead it had on CLINC and VAST, and only ties a plain prompt (note that I wrote its request for this task, not the index). My first guess was that sentences written to fool RoBERTa also fool Ettin, but only one in five fooled RoBERTa, so I'm not sure.

<div class="card card-grey">
<p class="card-kicker">Takeaway</p>
<p>When the words mislead, a two-line prompt does as well as an encoder trained on 13,000 sentences. So how many labels does the encoder need to beat the prompt?</p>
</div>

## How many labels does the encoder need?

The prompts need no labels. The encoder does, but how many? The next chart shows how far Ettin-150M is from zero-shot Qwen as it gets more training examples per class. Zero-shot is the better of the two prompts on all three tasks, so above zero, the encoder beats both. Up to 100 per class, each point is the mean of three draws. The last point is the full training set (100 per intent on CLINC, about 4,400 per class on VAST and DynaSent):

{{< chart >}}
type: 'scatter',
data: {
  datasets: [
    {
      label: 'CLINC150 + OOS',
      data: [{x: 10, y: -12.3}, {x: 25, y: 5.5}, {x: 50, y: 10.1}, {x: 100, y: 13.4}],
      showLine: true,
      borderColor: '#1f9e89', backgroundColor: '#1f9e89',
      borderWidth: 2, pointRadius: 5, pointHoverRadius: 7
    },
    {
      label: 'VAST',
      data: [{x: 10, y: -21.3}, {x: 25, y: -18.8}, {x: 50, y: -16.4}, {x: 100, y: -7.7}, {x: 333, y: 7.5}, {x: 1000, y: 14.3}, {x: 4492, y: 21.8}],
      showLine: true,
      borderColor: '#c2417a', backgroundColor: '#c2417a',
      borderWidth: 2, pointRadius: 5, pointHoverRadius: 7
    },
    {
      label: 'DynaSent',
      data: [{x: 10, y: -33.0}, {x: 25, y: -27.5}, {x: 50, y: -20.1}, {x: 100, y: -17.8}, {x: 333, y: -8.5}, {x: 1000, y: -5.7}, {x: 4355, y: -2.7}],
      showLine: true,
      borderColor: '#5b6b8c', backgroundColor: '#5b6b8c',
      borderWidth: 2, pointRadius: 5, pointHoverRadius: 7
    }
  ]
},
plugins: [{
  id: 'zeroShotLine',
  beforeDatasetsDraw: (chart) => {
    const { ctx, chartArea: a, scales: { y } } = chart;
    const color = document.documentElement.classList.contains('dark') ? '#d95926' : '#eb6834';
    const py = y.getPixelForValue(0);
    ctx.save();
    ctx.strokeStyle = color; ctx.lineWidth = 1.5; ctx.setLineDash([2, 4]);
    ctx.beginPath(); ctx.moveTo(a.left, py); ctx.lineTo(a.right, py); ctx.stroke();
    ctx.fillStyle = color; ctx.font = '12px sans-serif'; ctx.textAlign = 'right'; ctx.textBaseline = 'bottom';
    ctx.fillText('Zero-shot Qwen (0 labels)', a.right - 4, py - 3);
    ctx.restore();
  }
}],
options: {
  aspectRatio: 1.3,
  plugins: {
    legend: { position: 'bottom', labels: { color: '#898781', usePointStyle: true } },
    tooltip: { callbacks: { label: (c) => c.dataset.label + ', ' + c.parsed.x + ' per class: ' + (c.parsed.y > 0 ? '+' : '') + c.parsed.y + ' points' } }
  },
  scales: {
    x: {
      type: 'logarithmic', min: 8, max: 6000,
      title: { display: true, text: 'training examples per class (log scale)', color: '#898781' },
      afterBuildTicks: (axis) => { axis.ticks = [10, 25, 50, 100, 333, 1000, 4400].map((v) => ({ value: v })); },
      ticks: { color: '#898781', autoSkip: false, maxRotation: 0, callback: (v) => (v === 4400 ? 'all (~4.4k)' : v) },
      grid: { display: false }
    },
    y: {
      min: -40, max: 30,
      title: { display: true, text: 'Ettin-150M minus zero-shot Qwen (macro-F1 points)', color: '#898781' },
      ticks: { color: '#898781', stepSize: 10 },
      grid: { color: document.documentElement.classList.contains('dark') ? '#2c2c2a' : '#e1e0d9' }
    }
  }
}
{{< /chart >}}

On CLINC, 25 examples per intent are enough to beat both prompts. On VAST, the encoder needs 333 per class (about 1,000 examples). On DynaSent, it never gets above them, even with all the labels. Intents need a few examples, stance on unseen topics needs thousands, and with misleading words, all the labels only bring a tie.

<div class="card card-grey">
<p class="card-kicker">Takeaway</p>
<p>The answer to "do you need an LLM?" depends less on how many classes you have than on <strong>whether the words give the answer away</strong>.</p>
</div>

## What does each approach cost?

On the full CLINC task (150 intents + out-of-scope), quality against latency. The size of each bubble is the peak RAM while predicting:

{{< chart >}}
type: 'bubble',
data: {
  datasets: [
    {
      label: 'TF-IDF + LR',
      data: [{x: 0.371, y: 87.8, r: 3.7, ram: 0.51}],
      backgroundColor: '#898781',
      borderColor: '#898781'
    },
    {
      label: 'Ettin-150M',
      data: [{x: 7.64, y: 93.2, r: 6.3, ram: 1.45}],
      backgroundColor: document.documentElement.classList.contains('dark') ? '#3987e5' : '#2a78d6',
      borderColor: document.documentElement.classList.contains('dark') ? '#3987e5' : '#2a78d6'
    },
    {
      label: 'Qwen3.5-4B, zero-shot',
      data: [{x: 1078.6, y: 79.7, r: 21.8, ram: 17.57}],
      backgroundColor: document.documentElement.classList.contains('dark') ? '#d95926' : '#eb6834',
      borderColor: document.documentElement.classList.contains('dark') ? '#d95926' : '#eb6834'
    },
    {
      label: 'Qwen3.5-4B, few-shot',
      data: [{x: 1669.1, y: 79.0, r: 21.9, ram: 17.81}],
      backgroundColor: document.documentElement.classList.contains('dark') ? '#f2905f' : '#a8431c',
      borderColor: document.documentElement.classList.contains('dark') ? '#f2905f' : '#a8431c'
    },
    {
      label: 'OneJev1.6-4B',
      data: [{x: 1348.1, y: 95.7, r: 21.9, ram: 17.67}],
      backgroundColor: document.documentElement.classList.contains('dark') ? '#a77fe0' : '#7c4dcc',
      borderColor: document.documentElement.classList.contains('dark') ? '#a77fe0' : '#7c4dcc'
    }
  ]
},
options: {
  aspectRatio: 1.3,
  plugins: {
    legend: { position: 'bottom', labels: { color: '#898781', usePointStyle: true } },
    tooltip: { callbacks: { label: (c) => c.dataset.label + ': ' + c.raw.y + ' macro-F1, ' + c.raw.x + ' ms, ' + c.raw.ram + ' GB of RAM' } }
  },
  scales: {
    x: {
      type: 'logarithmic', min: 0.1, max: 10000,
      title: { display: true, text: 'latency per text, p50 (log scale)', color: '#898781' },
      ticks: { color: '#898781', maxRotation: 0, callback: (v) => ({0.1: '0.1 ms', 1: '1 ms', 10: '10 ms', 100: '100 ms', 1000: '1 s', 10000: '10 s'})[v] ?? '' },
      grid: { color: document.documentElement.classList.contains('dark') ? '#2c2c2a' : '#e1e0d9' }
    },
    y: {
      min: 75, max: 100,
      title: { display: true, text: 'macro-F1 on the full CLINC task', color: '#898781' },
      ticks: { color: '#898781', stepSize: 5 },
      grid: { color: document.documentElement.classList.contains('dark') ? '#2c2c2a' : '#e1e0d9' }
    }
  }
}
{{< /chart >}}

The same numbers in a table (F1 is macro-F1, latency is the median per text, RAM is the peak while predicting):

| Approach | F1 | Labels | Training | Latency | RAM | Disk |
|---|---|---|---|---|---|---|
| TF-IDF | 87.8 | 15,250 | 16 s | 0.37 ms | 0.5 GB | 79 MB |
| Ettin | 93.2 | 15,250 | 16 min | 7.6 ms | 1.5 GB | 575 MB |
| Qwen zero-shot | 79.7 | 0 | none | 1.1 s | 17.6 GB | 8.7 GB |
| Qwen few-shot | 79.0 | 151 | none | 1.7 s | 17.8 GB | 8.7 GB |
| OneJev | 95.7 | 0 | none | 1.3 s | 17.7 GB | 8.5 GB |

And latency against the number of labels, from 3 (DynaSent) to 151 (full CLINC). At 10 and 25 intents, it's the mean of three draws:

{{< chart >}}
type: 'scatter',
data: {
  datasets: [
    {
      label: 'OneJev1.6-4B',
      data: [{x: 3, y: 102.3}, {x: 10, y: 148.1}, {x: 25, y: 237.3}, {x: 50, y: 487.7}, {x: 100, y: 820.9}, {x: 151, y: 1348.1}],
      showLine: true,
      borderColor: document.documentElement.classList.contains('dark') ? '#a77fe0' : '#7c4dcc',
      backgroundColor: document.documentElement.classList.contains('dark') ? '#a77fe0' : '#7c4dcc',
      borderWidth: 2, pointRadius: 4, pointHoverRadius: 6
    },
    {
      label: 'Qwen3.5-4B, few-shot',
      data: [{x: 3, y: 149.5}, {x: 10, y: 177.3}, {x: 25, y: 274.5}, {x: 50, y: 554.6}, {x: 100, y: 1044.6}, {x: 151, y: 1669.1}],
      showLine: true,
      borderColor: document.documentElement.classList.contains('dark') ? '#f2905f' : '#a8431c',
      backgroundColor: document.documentElement.classList.contains('dark') ? '#f2905f' : '#a8431c',
      borderWidth: 2, pointRadius: 4, pointHoverRadius: 6
    },
    {
      label: 'Qwen3.5-4B, zero-shot',
      data: [{x: 3, y: 148.3}, {x: 10, y: 175.9}, {x: 25, y: 258.4}, {x: 50, y: 475.2}, {x: 100, y: 782.9}, {x: 151, y: 1078.6}],
      showLine: true,
      borderColor: document.documentElement.classList.contains('dark') ? '#d95926' : '#eb6834',
      backgroundColor: document.documentElement.classList.contains('dark') ? '#d95926' : '#eb6834',
      borderWidth: 2, pointRadius: 4, pointHoverRadius: 6
    },
    {
      label: 'Ettin-150M',
      data: [{x: 3, y: 7.69}, {x: 10, y: 7.6}, {x: 25, y: 7.67}, {x: 50, y: 7.69}, {x: 100, y: 7.73}, {x: 151, y: 7.64}],
      showLine: true,
      borderColor: document.documentElement.classList.contains('dark') ? '#3987e5' : '#2a78d6',
      backgroundColor: document.documentElement.classList.contains('dark') ? '#3987e5' : '#2a78d6',
      borderWidth: 2, pointRadius: 4, pointHoverRadius: 6
    },
    {
      label: 'TF-IDF + LR',
      data: [{x: 3, y: 0.362}, {x: 10, y: 0.362}, {x: 25, y: 0.362}, {x: 50, y: 0.361}, {x: 100, y: 0.367}, {x: 151, y: 0.371}],
      showLine: true,
      borderDash: [6, 4],
      borderColor: '#898781',
      backgroundColor: '#898781',
      borderWidth: 2, pointRadius: 4, pointHoverRadius: 6
    }
  ]
},
options: {
  aspectRatio: 1.3,
  plugins: {
    legend: { position: 'bottom', labels: { color: '#898781', usePointStyle: true } },
    tooltip: { callbacks: { label: (c) => c.dataset.label + ', ' + c.parsed.x + ' labels: ' + c.parsed.y + ' ms' } }
  },
  scales: {
    x: {
      type: 'logarithmic', min: 2.5, max: 180,
      title: { display: true, text: 'number of labels (log scale)', color: '#898781' },
      afterBuildTicks: (axis) => { axis.ticks = [3, 10, 25, 50, 100, 151].map((v) => ({ value: v })); },
      ticks: { color: '#898781', autoSkip: false, maxRotation: 0, callback: (v) => v },
      grid: { display: false }
    },
    y: {
      type: 'logarithmic', min: 0.1, max: 3000,
      title: { display: true, text: 'latency per text, p50 (log scale)', color: '#898781' },
      ticks: { color: '#898781', callback: (v) => ({0.1: '0.1 ms', 1: '1 ms', 10: '10 ms', 100: '100 ms', 1000: '1 s', 10000: '10 s'})[v] ?? '' },
      grid: { color: document.documentElement.classList.contains('dark') ? '#2c2c2a' : '#e1e0d9' }
    }
  }
}
{{< /chart >}}

- **The LLM pays for the label list on every prediction.** At 151 labels, it takes 1.1 to 1.7 s per text, against 7.6 ms for the encoder. Zero-shot Qwen goes from 175 ms at 10 intents to 780 ms at 100. Few-shot is 55% slower on the full task: the examples are cached, but each label is scored against a 3,000-token prompt instead of 500. OneJev puts the options after the text, so they can't be cached. With three labels, all three models answer in 100 to 150 ms.
- **RAM is the real cost, at least the way I ran them.** TF-IDF needs half a gigabyte, the encoder 1.5 GB. The 4B models peak around 18 GB on the full task (10 to 11 GB with three labels). That rules out most small servers, but quantization and a cheaper scoring would help (see the caveats).
- **The LLM only saves labeling.** It's a real saving: 15,250 labels is days of work. How many you really need depends on the task, as the learning curves show.

<div class="card card-grey">
<p class="card-kicker">Takeaway</p>
<p>Prompting saves labels, nothing else. On the full CLINC task, the encoder is more than 100 times faster and needs 12 times less RAM.</p>
</div>

## So, do you need an LLM?

Well, it depends! Three tasks on one laptop are three data points, not a law. Your task, your labels and your hardware will change these numbers. So my best advice is to run the same kind of benchmark on your own data. A few hundred labeled examples for testing and an afternoon are enough to compare TF-IDF, a fine-tuned encoder and a prompt. It will tell you more than any rule of thumb, including this one. TF-IDF also tells you what kind of task you have. Close to the others: the words give the answer away. Near chance: the answer is in a relation. Above chance but far behind: the words may be misleading. With that said, here is how I would start:

{{< mermaid >}}
flowchart TD
  A(["Do you have<br/>labeled data?"])
  A -->|"No"| B(["Tight latency or<br/>deployment constraints?"])
  A -->|"Yes"| C(["Tight latency or<br/>deployment constraints?"])
  B -->|"No"| P1["Decision model<br/>or LLM prompt"]
  B -->|"Yes"| D["Label with a large LLM,<br/>distill into TF-IDF<br/>or an encoder"]
  C -->|"Yes"| S["TF-IDF or a<br/>fine-tuned encoder"]
  C -->|"No"| T(["What does<br/>the task look like?"])
  T -->|"Words give<br/>it away"| TF["TF-IDF, or an<br/>encoder for a few<br/>more points"]
  T -->|"Answer in<br/>a relation"| E["Encoder with thousands<br/>of labels, decision<br/>model with fewer"]
  T -->|"Words<br/>mislead"| P2["Encoder or LLM prompt:<br/>a tie, the encoder<br/>is cheaper to run"]
{{< /mermaid >}}

- **No labels, no hard constraints:** use something already trained. Try a decision model if one fits your task and your hardware: OneJev1.6-4B beat everything I trained on CLINC and VAST. But on DynaSent, the only task neither in its training data nor on the index, a plain zero-shot prompt did as well, so try both. A generic prompt gets worse with more classes, and a few random examples won't fix it: they helped on small intent sets, but on none of the full tasks.
- **No labels, but tight constraints:** a 4B model is out, so you need labels from somewhere. The practical way is to let a larger LLM label a few thousand of your texts, then train a small model on them (a teacher and a student, or distillation). I didn't test it, and the student will copy the teacher's mistakes. But the learning curves give an idea of how much to label: a few dozen per class for intents, thousands for stance.
- **Tight latency or deployment constraints:** there are not many options. TF-IDF answers in under a millisecond on a CPU, with half a gigabyte. A ~150M encoder needs 7.6 ms (on the laptop's GPU, more on a CPU) and 1.5 GB. The 4B models need 1 to 2 s and 18 GB.
- **No hard constraints:** it depends on the task.
  - *The words give the answer away* (intents, topics): start with TF-IDF, it's a strong baseline up to a few dozen classes. A ~150M encoder adds 5.4 points on the full CLINC task.
  - *The answer is in a relation* (stance): an encoder, but only with thousands of labels. With the full VAST training set, Ettin-150M beats Jev and both prompts, in 16 ms per text instead of 195. OneJev is still better (80.6 vs. 75.8), but ten times slower. With only a few hundred labels, use a decision model.
  - *The words mislead* (sarcasm, negation, irony): either one. On DynaSent, 13,000 labels only gave the encoder a tie with a two-line prompt. If you have the labels, the encoder is cheaper to run. If not, use a prompt.

## Caveats

As I said at the start, this is a weekend project. It was never meant to be paper-ready. Still, here are the limits I know of:

- **Contamination.** All three datasets have been public for years, and Qwen has likely seen them during pretraining. OneJev's training data even includes 206 CLINC150 training examples (and BANKING77, another intent dataset). VAST and DynaSent are not in its listed sources, but it also uses samples of instruction collections that contain many classification datasets. This favors the Qwen-based models, especially OneJev on CLINC.
- **Few-shot examples.** Each few-shot number comes from one random draw. Another draw, or another order, could move VAST and DynaSent by several points. I also didn't try picking the closest training examples for each text (retrieval), which usually works better.
- **How I ran the LLMs.** The BF16 weights take about 8 GB; 4-bit weights would take about 2.5 GB. But scoring each label separately also makes latency and memory grow with the number of labels (10 to 11 GB with three labels, 18 GB with 151), and quantization doesn't change that part. Numbered labels read in a single token would matter more. Either way, I'd expect the encoder to stay far ahead.
- **One seed, one prompt, no tuning.** A better prompt or learning rate could move some numbers by a point or two. On DynaSent, the prompts and the OneJev request are mine, not the index's.
- **One LLM, not fine-tuned.** A single 4B model stands for "an LLM" here. The best index entrants (27B and 31B) give an idea of what a bigger one brings: 97.6 on CLINC, 84.2 on VAST. Fine-tuning one with LoRA is for a later post.

## What's next

- **How small can a classifier be?** The encoder side: from 17M to 150M parameters, how many labels each size needs, CPU or GPU. Quantization too, for the encoders and the 4B models alike, so the cost comparison is fair. And how they compare with ready-made models that need no labels or only a few (sentence embeddings with a logistic regression, SetFit).
- **Fine-tune or optimize the prompt?** Same tasks: plain vs. GEPA-optimized prompt, base vs. LoRA weights.
- **No labels, but an encoder anyway?** A large LLM labels the training set, then a small encoder is fine-tuned on its answers (a teacher and a student). How close does the student get, how many labels does it need, and what does it cost?

## Related reading

- [Beating BERT? Small LLMs vs Fine-Tuned Encoders for Classification](https://alex-jacobs.com/posts/beatingbert/), by Alex Jacobs. Fine-tuned BERT and DeBERTa-v3 against small LLMs, zero-shot and few-shot, on SST-2, RTE, BoolQ and ANLI. DeBERTa wins three tasks out of four.
- [Fine-Tuned "Small" LLMs (Still) Significantly Outperform Zero-Shot Generative AI Models in Text Classification](https://arxiv.org/abs/2406.08660), by Martin Juan José Bucher and Marco Martini (2024). Fine-tuned BERT-style models against zero-shot GPT-3.5, GPT-4 and Claude Opus, stance included. The fine-tuned models always win. Same here, except on DynaSent, where it's a tie.
- [Do BERT-Like Bidirectional Models Still Perform Better on Text Classification in the Era of LLMs?](https://aclanthology.org/2025.findings-emnlp.1033/), by Junyan Zhang et al. (Findings of EMNLP 2025). Encoders win on pattern-driven tasks, LLMs on tasks that need deep semantics. CLINC fits the first part. VAST only fits the second part for the decision model: the prompted LLM is 22 points behind the encoder. DynaSent fits better, with a tie.
