---
title: "One Billion Rows, 35 Minutes: Letting an Agent Optimize My Go Code"
date: 2026-07-19T10:30:00+02:00
tags: ["challenge", "golang", "optimization", "performance", "ai", "coding-agents"]
showTableOfContents: true
draft: false
---

Two years ago, I took a Go tortoise to the [One Billion Row Challenge]({{< ref "posts/1brc" >}}) and taught it to run twice as fast in half a workday. That post ended with a promise: *"My next goal? Get this solution running as fast as the top performers out there."* I never wrote that follow-up. I knew what it would cost me: days of profiling, SIMD tricks, and benchmark discipline.

Then the ground shifted. Coding agents went from clever autocomplete to tools that can edit, build, run, and measure code unattended. And Andrej Karpathy put a name on a deceptively simple idea: [autoresearch](https://github.com/karpathy/autoresearch), which is giving an agent something to modify and an objective to measure against, then letting it loop. I wanted to know whether that recipe worked outside of machine learning models, say, on a Go program I already knew intimately.

So the tortoise is back. This time it has a coach that never gets bored, and the coach delivered on my two-year-old promise in **35 minutes**: a program that runs within 6% of the fastest this disk can physically be read.

## 1BRC in thirty seconds

The [One Billion Row Challenge](https://www.morling.dev/blog/one-billion-row-challenge/) was introduced by Gunnar Morling in January 2024, originally as a Java contest, and was quickly ported to about every language with a compiler. The input is a text file of one billion lines, each a station name and a temperature reading:

```
Hamburg;12.3
Bulawayo;8.9
Palembang;38.8
```

The task: compute the min, mean, and max temperature per station and print them sorted by name. That's it. No tricks in the problem; all the trickery is in doing it fast, because at ~17 GB the program is really a gauntlet of every systems bottleneck in sequence: how you read (I/O), how you parse (branchy inner loops), how you aggregate (a hash map hit a billion times), and whether you can do all of it on every core at once. The hard floor is physics: no correct program can finish faster than the disk can deliver the bytes, that is, faster than `cat measurements.txt > /dev/null`.

## Autoresearch: something to tweak, a way to measure

The original autoresearch scenario optimizes an ML model against a benchmark. Strip it down and the recipe generalizes to almost anything:

1. **Something to modify**: here, `main.go`, a single-file Go solution to 1BRC.
2. **A way to measure**: correctness against reference outputs, then wall-clock time on a benchmark dataset.
3. **A loop**: the agent edits, verifies, benchmarks, keeps wins, reverts losses, and stops when progress stalls.

![The autoresearch loop in four steps: define the problem and pick one metric, define the checklist, run the loop (generate, test and score, analyze, refine), keep the best solution](loop-steps.webp "The autoresearch loop, in four steps")

The interesting work is not in the agent. It is in designing the measurement so the loop can't fool itself. My protocol lives in a single file, [`program.md`](https://github.com/driquet/1brc-autoresearch/blob/main/program.md), that the agent follows literally:

- **Correctness is a hard gate.** Every candidate is diffed against reference output *before* being timed, first on a small 1M-row dataset, then on the benchmark output itself. A faster program with wrong output is rejected outright. The baseline deliberately uses integer-tenths arithmetic[^tenths] so that any correct parallelization reproduces its output byte-for-byte: the oracle leaves no wiggle room.
- **Benchmarks are cold and boring.** Three cold-cache[^coldcache] runs per candidate ([hyperfine](https://github.com/sharkdp/hyperfine), page cache purged before each run, a 20-second cooldown so thermals don't drift), median as the score.
- **A win must be a real win.** A candidate is accepted only if its median beats the champion's by **at least 3%**. Below that, median-of-3 noise could crown a fluke.
- **The loop stops itself.** Five consecutive rounds without an accepted improvement, and the experiment is over.
- **Git is the story.** Accepted rounds are commits; every attempt, including the failures, is logged to a [`JOURNAL.md`](https://github.com/driquet/1brc-autoresearch/blob/main/JOURNAL.md).

[^tenths]: Temperatures have exactly one decimal digit, so the program stores them as integers of tenths of a degree (`-12.3` becomes `-123`) and divides by ten only at output. Integer math is faster and, crucially, exact: ten workers summing their slice and merging reproduce the single-threaded result bit-for-bit, which floating-point addition would not guarantee.
[^coldcache]: The operating system keeps recently read file data in spare RAM (the *page cache*) so a second read is served from memory rather than disk. A *cold* run purges that cache first, forcing every byte to come from the SSD. It is slower, but it is what makes one run comparable to the next.

{{< alert >}}
**Why 250M rows and not the full billion?** The loop times candidates on a 250M-row (4.4 GB) dataset, not the full 17 GB file. Purely for iteration speed: early candidates took ~45 seconds per cold run at full scale, and with three runs and 20-second cooldowns per candidate, a single full-scale round would have cost over three minutes before the loop learned anything. The 250M dataset keeps the workload's character (same format, same ~400 stations) while making each round quick. This experiment isn't chasing the single fastest 1BRC solution on Earth; it's testing whether the autoresearch recipe produces a good one on its own. The champion gets one honest run at the full scale at the end.
{{< /alert >}}

One round of the loop looks like this:

![Flowchart of one round: edit main.go with one idea, build it, check correctness on 1M rows, run three cold-cache benchmarks on 250M rows, check correctness again, accept and commit if at least 3% faster than the champion, otherwise reject and revert; after five rounds without a win, stop](autoresearch-loop.png "One round of the loop")

The run itself was [Claude Code](https://github.com/anthropics/claude-code) running Fable 5, unattended, with permission prompts disabled (scoped: the only `sudo` it got was the one command that purges the page cache). But nothing in the recipe depends on that choice. `program.md` is the actual driver, and any agent that can edit a file, run a build, and read a benchmark result can execute it.

One rule of the game, carried over in spirit from the 2024 post: the program must stay **idiomatic, stdlib-only Go**. Goroutines and `syscall` are fair game; `unsafe`, assembly, cgo, and third-party dependencies are not. The question is still *how far does clean Go go*, just asked by someone with infinite patience.

The rest (generator, baseline, final code) lives in the same [repo](https://github.com/driquet/1brc-autoresearch).

## New machine, new baseline

{{< alert >}}
**Don't compare these numbers to the 2024 post.** That experiment ran on an i7 laptop with 16 GB of RAM and an encrypted SSD; this one runs on an Apple M5 MacBook (10 cores, 24 GB RAM). The 2024 figures (96 seconds for the baseline, 43 for the optimized version) are history. For this experiment, everything (the naive baseline, my 2024 manual solution, and the agent's champion) was re-benchmarked on the M5, cold cache, same dataset. Every comparison below is same-machine.
{{< /alert >}}

On the M5, the naive baseline (`bufio.Scanner`, built-in map, the code you'd write if nobody told you there were a billion rows) processes the full dataset in **44.8 seconds**. My 2024 manual solution, ported to the new machine, does it in **20.1 seconds**. Those are the two numbers to beat.

It is worth pausing on *why* those two numbers are so far apart, because the gap isn't only about effort. My 2024 attempt was shaped by two constraints that have since lifted:

- **Go's standard library caught up.** Back then I reached for a third-party Swiss-table map ([dolthub/swiss](https://www.dolthub.com/blog/2023-03-28-swiss-map/)) because the built-in map was the bottleneck. As of [Go 1.24](https://go.dev/blog/swisstable) (February 2025), the built-in map *is* a Swiss table, up to 60% faster on map-heavy microbenchmarks. Part of what I hand-optimized in 2024 now ships for free in the language.
- **The old machine ruled out the biggest lever.** With 16 GB of RAM and an encrypted SSD, memory-mapping a 17 GB file[^mmap] was never realistic in 2024: the file doesn't fit in RAM, and encryption taxes every page fault. So my manual solution was single-threaded chunked reads by necessity as much as by design. The M5's 24 GB and fast unencrypted storage put mmap (and then something better) back on the table, which is exactly where the loop started.

[^mmap]: `mmap` (memory-map) asks the kernel to map a file directly into the process's address space, so the program reads it as an ordinary byte array, with pages pulled in from disk on demand rather than copied through explicit `read` calls.

Some of the distance to the champion is the agent, then, and some of it is two years of Go releases and a machine that no longer fights back.

## Thirty-five minutes, fourteen rounds

The loop ran for 35 minutes wall clock: 14 rounds, roughly 2½ minutes per round, almost all of it spent inside the benchmark itself (three cold runs, each behind a 20-second cooldown and a cache purge). Here is the whole story in one picture:

{{< chart >}}
type: 'line',
data: {
  labels: ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14'],
  datasets: [
    {
      label: 'Champion (accepted)',
      data: [11.104, 8.567, 2.040, 1.750, 1.750, 1.750, 1.750, 0.831, 0.770, 0.740, 0.740, 0.740, 0.740, 0.740, 0.740],
      stepped: true,
      borderColor: document.documentElement.classList.contains('dark') ? '#3987e5' : '#2a78d6',
      backgroundColor: document.documentElement.classList.contains('dark') ? '#3987e5' : '#2a78d6',
      borderWidth: 2,
      pointRadius: [4, 4, 4, 4, 0, 0, 0, 4, 4, 4, 0, 0, 0, 0, 0],
      pointHoverRadius: 6
    },
    {
      label: 'Rejected candidate',
      data: [null, null, null, null, 1.725, 1.717, null, null, null, null, 0.777, 0.780, 0.802, 0.768, 0.756],
      showLine: false,
      pointStyle: 'crossRot',
      pointRadius: 6,
      pointHoverRadius: 8,
      borderWidth: 2,
      borderColor: document.documentElement.classList.contains('dark') ? '#d95926' : '#eb6834',
      backgroundColor: 'transparent'
    }
  ]
},
options: {
  plugins: {
    legend: { labels: { color: '#898781', usePointStyle: true } },
    tooltip: { callbacks: { label: (c) => c.dataset.label + ': ' + c.parsed.y + ' s' } }
  },
  scales: {
    x: {
      title: { display: true, text: 'round', color: '#898781' },
      ticks: { color: '#898781' },
      grid: { display: false }
    },
    y: {
      type: 'logarithmic',
      min: 0.6,
      title: { display: true, text: 'median time on 250M rows (s, log scale)', color: '#898781' },
      ticks: { color: '#898781' },
      grid: { color: document.documentElement.classList.contains('dark') ? '#2c2c2a' : '#e1e0d9' }
    }
  }
}
{{< /chart >}}

The blue steps are accepted rounds; the orange crosses are candidates that were benchmarked and reverted. Round 6 has neither (a build failure, more on that below). Note the crosses at rounds 4 and 5 sitting slightly *below* the champion line: those candidates were faster, just not by the 3% the protocol demands. Keep an eye on them, because they come back.

Fourteen rounds fall naturally into five phases.

### Structural wins (rounds 1 to 3)

The loop opened exactly the way an optimization textbook says you should: biggest structural problems first.

- **Round 1, mmap the file** (11.10 down to 8.57 seconds, −23% runtime). Drop `bufio.Scanner` and its per-line string allocation (250 million of them), map the file, and scan bytes in place.
- **Round 2, go parallel** (8.57 down to 2.04 seconds, −76% runtime). Split the file into one newline-aligned chunk per core; each of the 10 workers scans into a private map, merged at the end. The single biggest win of the run, and, worth noting, the thing my 2024 solution never attempted.
- **Round 3, replace the map** (2.04 down to 1.75 seconds, −14% runtime). A fixed 32k-slot open-addressing hash table[^openaddr] per worker, with an FNV hash[^fnv] computed in the same pass that scans for the semicolon. In 2024 I reached for a third-party Swiss map; the loop's stdlib-only rule forced it to build its own, and its own turned out faster.

[^openaddr]: An open-addressing hash table stores entries directly in one flat array. On a collision it probes the next slot in line rather than following pointers to a separate linked list, which keeps lookups in cache and avoids per-entry allocations.
[^fnv]: FNV (Fowler-Noll-Vo) is a simple, fast, non-cryptographic hash: start from a fixed seed, then for each chunk of input, XOR it in and multiply by a fixed prime.

Three rounds, six minutes, and 6.3 times faster.

### The first plateau (rounds 4 to 6)

Then the loop hit a wall. A fixed-format temperature parser gained only 1.4%; a clever SWAR[^swar] trick to scan station names 8 bytes at a time gained 1.9%. Both faster, both below the 3% bar, both reverted. Round 6 tried `madvise`[^madvise] to widen the kernel's read-ahead and didn't even compile: macOS's `syscall` package doesn't expose it, and the raw-syscall escape hatch needs `unsafe`, which the rules forbid.

[^swar]: SWAR (SIMD Within A Register) processes several bytes at once by packing them into a single wide integer (here a 64-bit word holds 8 bytes) and manipulating them with ordinary arithmetic and bitwise operations, getting byte-parallelism without dedicated vector instructions.
[^madvise]: `madvise` is a syscall that tells the kernel how a memory-mapped region will be accessed (for example, sequentially), so it can tune how aggressively it reads ahead. Go's `syscall` package doesn't expose it on macOS.

Three straight rejects. The journal entry for round 5 shows the loop drawing the right conclusion: *two straight sub-2% wins on compute ideas imply the cold 4.4 GB read dominates; switch focus to I/O.*

### The breakthrough (round 7)

Round 7 is the counterintuitive one: **drop mmap**, the very thing round 1 introduced. Instead, each worker issues a `pread`[^pread] for its own byte range in 4 MB blocks into a private reused buffer. A cold mmap serializes on the page-fault-then-read-ahead path; ten explicit read streams give the SSD real queue depth and overlap I/O with parsing for free.

[^pread]: `pread` reads a fixed byte range from a file at an explicit offset in a single syscall, without a shared file cursor, so many threads can read different parts of the same file at the same time without stepping on each other.

Median: 1.75 seconds down to 0.83. **−52% runtime**, the biggest single-idea win of the run after parallelism itself, and a reminder that an "obvious best practice" (mmap for big files!) is only best against a particular bottleneck profile.

### Resurrection (rounds 8 to 9)

Here is my favorite part of the journal. With I/O fixed, the loop went back to its own rejects. The SWAR name scan, worth 1.9% in round 5, was retried in round 8: **−7.3% runtime, accepted.** The fixed-format parser, worth 1.4% in round 4, was retried in round 9: **−3.9% runtime, accepted.** The champion now stood at 0.740 seconds.

The same two ideas, the same code, four rounds apart, rejected once and accepted later. The lesson generalizes to any optimization work, human or otherwise: **a rejected idea is only rejected against the current bottleneck.** While mmap page faults dominated, shaving the parse loop was invisible; once round 7 unblocked I/O, the same shavings cleared the bar easily. The loop didn't need to be clever about ordering. The accept/reject discipline sorted it out mechanically.

### Trying to out-schedule the kernel (rounds 10 to 14)

At 0.740 seconds on 250M rows the program reads at roughly 5.9 GB/s. How close is that to the physical limit? To find out, the loop measured a floor with `dd`[^dd]: copy the file straight to `/dev/null`, no parsing, no aggregation, nothing but reading bytes off the disk. After a cache purge that took 0.65 seconds. Since the champion has to read every one of those same bytes, `dd` is the wall it can never pass: the fastest any correct solution can possibly be is the time it takes to just *read* the file. At 0.740 seconds against a 0.65-second floor, the champion was already at roughly 88% of the disk's raw throughput. The last five rounds were the loop trying to claim that final sliver:

[^dd]: `dd` is a standard Unix tool that copies bytes from one place to another. Pointing it at the measurements file with `/dev/null` as the destination reads the whole file and throws it away, so its runtime is pure read throughput with zero processing, the hard floor for anything that must read the file.

| Round | Idea | Result |
|-------|------|--------|
| 10 | double-buffered read-ahead per worker | +5.0% runtime |
| 11 | 1 MB read blocks | +5.5% runtime |
| 12 | 16 MB read blocks | +8.3% runtime |
| 13 | work-stealing 32 MB grains | +3.7% runtime |
| 14 | 2x goroutine oversubscription | +2.2% runtime |

Every single one made things *worse*. The pattern is consistent: ten long contiguous read streams with 4 MB requests is exactly what macOS's read-ahead wants, and every scheme that fragmented, reshuffled, or second-guessed those streams paid more than it gained. Five consecutive rejects: the plateau rule fired, and the loop stopped itself.

You can see this phase in the commit log without reading a line of code: the accepted rounds cluster two minutes apart, and then there's a final twelve-minute gap where five candidates were built, benchmarked, and quietly reverted.

## What the loop built

The final `main.go` is still idiomatic, stdlib-only Go: no `unsafe`, no assembly, ~250 lines. Five mechanisms, layered:

1. **Parallel pread**: one worker per core, each reading its own newline-aligned range in 4 MB blocks (round 7).
2. **SWAR scanning**: station names consumed 8 bytes per step, the `;` located with a zero-byte bit trick, an FNV-style hash folded over whole words in the same pass (round 8).
3. **Custom hash table**: a fixed 32k-slot open-addressing table per worker; names copied only on first insert (round 3).
4. **Fixed-format parse**: temperatures decoded with straight-line code exploiting the `d.d` / `dd.d` grammar (round 9).
5. **Integer-tenths arithmetic end-to-end**: so ten workers merging their tables reproduce the single-threaded baseline byte-for-byte.

The snippet I keep coming back to is the semicolon finder, the kind of code I *understand* but would never have sat down to write on a Tuesday evening:

```go
// semiMask returns a word with the high bit set in each byte of w that
// equals ';' (classic SWAR zero-byte detection on w XOR ';;;;;;;;').
func semiMask(w uint64) uint64 {
	x := w ^ 0x3b3b3b3b3b3b3b3b
	return (x - 0x0101010101010101) &^ x & 0x8080808080808080
}

// ...in the scan loop: load 8 bytes, hash the whole word, and only
// stop when the mask says one of them is the semicolon.
w := binary.LittleEndian.Uint64(buf[i : i+8])
if m := semiMask(w); m != 0 {
	k := bits.TrailingZeros64(m) >> 3 // byte index of ';'
	...
}
```

## Results

The loop optimized against 250M rows; the honest number is the full scale. One final validation run, one billion rows, ~17 GB, cold cache, output diffed against the reference:

| Candidate | Wall time | vs. read floor |
|-----------|----------:|---------------:|
| `dd` (cold sequential read, no parsing) | 2.78 s | 1.00x |
| **Champion** (14 rounds of the loop) | **2.96 s** | 1.06x |
| My 2024 manual solution | 20.09 s | 7.2x |
| Naive baseline | 44.82 s | 16.1x |

The `dd` row is the read floor again, now at full scale: 2.78 seconds to read 17 GB off this disk and do absolutely nothing with it. The champion does the entire challenge, one billion rows parsed and aggregated, in **2.96 seconds**, just 6% over the cost of reading the file at all. That is roughly 15 times the baseline. At that point the program is no longer meaningfully "parsing a file"; it is *reading* a file, and the parsing rides along almost for free. The speedup also transferred cleanly: the loop measured 15.0x on 250M rows and the full run delivered 15.1x, consistent with a program that scales with the disk, not with the cache.

A word about that table, because it invites a lazy reading. My 2024 solution sitting at 20 seconds next to the champion's 3 is **not** "AI beats human." The 2024 experiment had a different goal, to prove that a 2x improvement was cheap, in service of [Eroom-Nitot's law]({{< ref "posts/1brc" >}}), and it stopped exactly where it aimed, on a different (and more constrained) machine, after half a day. It's a reference point, not a contestant: it tells you what informed manual effort buys per unit of time. What changed between the two columns isn't intelligence. It's that **the cost of iteration collapsed**. Fourteen disciplined benchmark rounds, every candidate built, verified byte-for-byte, benchmarked three times cold, logged, and committed or reverted, is not something a human does for fun on a Thursday. An agent does it without noticing, and the whole session (setup and all fourteen rounds included) cost about **$21** in tokens.

## Limitations, for honesty's sake

- The loop optimized a 250M-row proxy, not the full file; the final validation caught no divergence, but per-round decisions weren't made at full scale.
- One machine, laptop numbers. Every accepted round is a fact about *this* M5 and *this* SSD (a feature for me), and your mileage will vary.
- The dataset comes from my own generator (~400 stations, same format as the official challenge, not byte-identical), so nothing here is comparable to the official leaderboard.

## Closing thoughts

Let me state the headline fact plainly: in **35 unattended minutes**, the loop produced a program more optimized, and more precisely tuned to my specific hardware, than I would have produced in a full day of manual work. Not because it knows tricks I couldn't learn (SWAR scanning and pread-versus-mmap are all over the existing 1BRC literature), but because it *tried everything and believed nothing*. It benchmarked its way out of the mmap dogma, resurrected its own rejected ideas when the bottleneck moved, and had the discipline to stop when the hardware said stop.

That's the part I want you to take away, because none of it is specific to 1BRC, or to Go, or to this agent. The recipe is three ingredients: **something to tweak, a benchmark you trust, and a loop.** The craft, the genuinely human part, went into the middle ingredient: reference outputs that leave no wiggle room, cold-cache medians, a threshold that filters noise, a rule for giving up. Get the measurement right and the loop is honest by construction; get it wrong and you'll optimize your way into fiction. If you have a slow script, a bloated Docker image, a flaky test suite, anything with a number attached that you'd like to see move, you have an autoresearch problem.

Everything is in the repo if you want to replay it or point the protocol at your own problem: [github.com/driquet/1brc-autoresearch](https://github.com/driquet/1brc-autoresearch).

Two years ago I closed by promising to chase the top performers. The tortoise got there in the end. It just turned out the trick wasn't running faster. It was hiring a coach with infinite patience. 🐢

## Recommended related reading

- [My 2024 post]({{< ref "posts/1brc" >}}): the manual half of this story, with profiling, Swiss maps, and Eroom-Nitot's law.
- [Andrej Karpathy's autoresearch](https://github.com/karpathy/autoresearch): the original idea, applied to ML models.
- [Gunnar Morling's One Billion Row Challenge](https://www.morling.dev/blog/one-billion-row-challenge/): where it all started.
- [Ben Hoyt, The One Billion Row Challenge in Go](https://benhoyt.com/writings/go-1brc/): the classic manual walkthrough, and the source of several ideas the loop rediscovered on its own.
